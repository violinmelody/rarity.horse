import shutil
from pathlib import Path
from datetime import datetime
import markdown
import subprocess
import html
from urllib.parse import quote
import re
import io

# Optional dependencies for emoji conversion
try:
    from PIL import Image, ImageOps  # type: ignore
except Exception:
    Image = None
    ImageOps = None

try:
    import cairosvg  # type: ignore
except Exception:
    cairosvg = None

ROOT = Path(__file__).resolve().parent.parent
CONTENT = Path("content/articles")
META = Path("content/meta")
OUT = ROOT / "wwwroot"
THEME = ROOT / "theme"
TEMPLATES = ROOT / "templates"

MD_EXT = ["extra", "sane_lists", "smarty"]

# ---------------- Templates ----------------

def tpl(name: str) -> str:
    return (TEMPLATES / name).read_text()

base_tpl = tpl("base.html")
article_tpl = tpl("article.html")
tree_tpl = tpl("tree.html")
category_tpl = tpl("category.html")

def render(t: str, **ctx) -> str:
    for k, v in ctx.items():
        t = t.replace("{{ " + k + " }}", v)
    return t

# ---------------- Markdown ----------------

def preprocess_markdown(text: str) -> str:
    """
    A signature is a standalone markdown line:
        ~Name
    """
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("~") and " " not in stripped:
            out.append(f"<p class='signature'>{stripped}</p>")
        else:
            out.append(line)
    return "\n".join(out)

def title_from_file(p: Path) -> str:
    return p.stem.replace("_", " ").title()

def slug_from_stem(stem: str) -> str:
    """
    Convert a filename stem into a URL/file-safe slug.
    We currently only normalize spaces -> underscores so titles can keep spaces.
    """
    return stem.replace(" ", "_")

def out_rel_from_md(rel_md: Path) -> Path:
    """
    Given a content-relative markdown path like:
        some/folder/My Post.md
    produce the output-relative HTML path:
        some/folder/My_Post.html

    Only the filename is normalized (spaces -> underscores).
    Folder names are left unchanged.
    """
    return rel_md.with_name(slug_from_stem(rel_md.stem) + ".html")

def link_from_file(l: Path) -> str:
    # Kept for compatibility; returns the slug used in output filenames/URLs.
    return slug_from_stem(l.stem)

# ---------------- Meta ----------------

def load_meta_file(name: str, default: str = "") -> str:
    f = META / name
    return f.read_text().strip() if f.exists() else default

SITE_TITLE = load_meta_file("title.md", "✦ RARITY.HORSE ✦")
SITE_MOTD = load_meta_file("motd.md", "generosity is magic, darling~")
SITE_FOOTER = load_meta_file("footer.md", "handcrafted • static • beautiful")

# ---------------- Theme ----------------

def load_theme_css() -> str:
    raw = load_meta_file("theme.md", "boutique").strip().lower()
    if not raw:
        raw = "boutique"
    css = f"{raw}.css"
    return css if (THEME / css).exists() else "boutique.css"

THEME_CSS = load_theme_css()

# ---------------- Output ----------------

OUT.mkdir(exist_ok=True)
tree = {}

# ---------------- Custom emojis ----------------
# Put your source emoji files here:
#   content/meta/emojis/*
# Use them in markdown like:
#   :my_emoji:
#
# Output is generated as:
#   wwwroot/emojis/my_emoji.png  (always 128x128 PNG)

EMOJIS_DIR = META / "emojis"
EMOJIS_OUT = OUT / "emojis"

_EMOJI_TOKEN_RE = re.compile(r":([A-Za-z0-9_-]+):")

def _normalize_emoji_key(stem: str) -> str:
    """
    Normalize emoji keys so they can be referenced in markdown as :key:
    - replaces whitespace and unsupported chars with underscores
    - collapses multiple underscores
    - strips leading/trailing underscores
    """
    s = stem.strip()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")

def _imagemagick_convert_128(src: Path, dst: Path) -> bool:
    """
    Fallback converter using ImageMagick (magick/convert) if available.
    Produces a 128x128 PNG, preserving aspect ratio and padding with transparency.
    """
    for bin_name in ("magick", "convert"):
        try:
            subprocess.check_call(
                [
                    bin_name,
                    str(src),
                    "-background",
                    "none",
                    "-gravity",
                    "center",
                    "-resize",
                    "128x128",
                    "-extent",
                    "128x128",
                    str(dst),
                ]
            )
            return True
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return False

def _pil_resample_filter():
    # Pillow API changed: Image.Resampling.LANCZOS exists on newer versions.
    if Image is None:
        return None
    if hasattr(Image, "Resampling"):
        return Image.Resampling.LANCZOS
    return getattr(Image, "LANCZOS", 1)

def _pil_convert_128(src: Path, dst: Path) -> bool:
    """
    Convert using Pillow (recommended).
    Produces a 128x128 PNG, preserving aspect ratio and padding with transparency.
    """
    if Image is None:
        return False

    try:
        img = Image.open(src)
        # If animated (e.g., GIF), use the first frame.
        try:
            img.seek(0)
        except Exception:
            pass

        img = img.convert("RGBA")

        resample = _pil_resample_filter()

        # Fit within 128x128 while preserving aspect ratio
        if ImageOps is not None and hasattr(ImageOps, "contain"):
            img = ImageOps.contain(img, (128, 128), method=resample)
        else:
            img.thumbnail((128, 128), resample=resample)

        # Pad to exactly 128x128
        canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        x = (128 - img.width) // 2
        y = (128 - img.height) // 2
        canvas.paste(img, (x, y), img)

        dst.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(dst, format="PNG")
        return True
    except Exception:
        return False

def _svg_convert_128(src: Path, dst: Path) -> bool:
    """
    Convert SVG to 128x128 PNG.
    Tries cairosvg first, then ImageMagick fallback.
    """
    if cairosvg is not None:
        try:
            png_bytes = cairosvg.svg2png(url=str(src), output_width=128, output_height=128)
            if Image is not None:
                img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
                # Ensure padding/exact sizing is consistent with other formats
                resample = _pil_resample_filter()
                if ImageOps is not None and hasattr(ImageOps, "contain"):
                    img = ImageOps.contain(img, (128, 128), method=resample)
                else:
                    img.thumbnail((128, 128), resample=resample)

                canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
                x = (128 - img.width) // 2
                y = (128 - img.height) // 2
                canvas.paste(img, (x, y), img)
                dst.parent.mkdir(parents=True, exist_ok=True)
                canvas.save(dst, format="PNG")
                return True

            # If Pillow isn't available, just write cairosvg output (already 128x128)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(png_bytes)
            return True
        except Exception:
            pass

    # Try ImageMagick (may support SVG if delegates are installed)
    return _imagemagick_convert_128(src, dst)

def _convert_emoji_to_png_128(src: Path, dst: Path) -> bool:
    ext = src.suffix.lower()
    if ext == ".svg":
        return _svg_convert_128(src, dst)

    # Prefer Pillow for raster formats
    if _pil_convert_128(src, dst):
        return True

    # Fallback to ImageMagick if Pillow isn't available or failed
    return _imagemagick_convert_128(src, dst)

def build_emojis() -> dict:
    """
    Scans content/meta/emojis for image files and builds a map:
        emoji_key -> "/emojis/emoji_key.png"
    Also converts/copies emojis into wwwroot/emojis as 128x128 PNGs.
    """
    if not EMOJIS_DIR.exists():
        return {}

    # (Re)create output folder to avoid stale emoji files hanging around
    if EMOJIS_OUT.exists():
        shutil.rmtree(EMOJIS_OUT, ignore_errors=True)
    EMOJIS_OUT.mkdir(parents=True, exist_ok=True)

    emoji_map: dict[str, str] = {}

    # Allow common raster formats + svg (svg needs cairosvg or ImageMagick delegate)
    allowed_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".svg"}

    for src in sorted([p for p in EMOJIS_DIR.rglob("*") if p.is_file() and p.suffix.lower() in allowed_exts]):
        key = _normalize_emoji_key(src.stem)
        if not key:
            continue

        dst = EMOJIS_OUT / f"{key}.png"

        ok = _convert_emoji_to_png_128(src, dst)
        if not ok:
            # Leave the token untouched in markdown if conversion fails.
            print(f"[emoji] WARNING: Could not convert {src} -> {dst}. Install Pillow and/or ImageMagick.")
            continue

        # Map both the normalized key and a lowercase alias (convenience).
        url = "/emojis/" + quote(dst.name)
        emoji_map[key] = url
        emoji_map[key.lower()] = url

    return emoji_map

EMOJI_MAP = build_emojis()

def _replace_emojis_outside_code(text: str) -> str:
    """
    Replace :emoji: tokens with <img> tags, while avoiding:
      - fenced code blocks (``` or ~~~)
      - inline code spans (`like this`)
    """
    if not EMOJI_MAP:
        return text

    def repl(m: re.Match) -> str:
        key = m.group(1)
        url = EMOJI_MAP.get(key) or EMOJI_MAP.get(key.lower())
        if not url:
            return m.group(0)

        # Inline HTML is allowed by python-markdown and renders inside paragraphs nicely.
        safe_url = html.escape(url, quote=True)
        safe_key = html.escape(key, quote=True)
        return (
            f"<img class='emoji' src='{safe_url}' alt=':{safe_key}:' "
            f"title=':{safe_key}:' width='128' height='128'>"
        )

    out_lines = []
    in_fence = False
    fence_marker = ""

    for line in text.splitlines():
        stripped = line.lstrip()

        # Toggle fenced blocks on ``` or ~~~
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            else:
                if marker == fence_marker:
                    in_fence = False
                    fence_marker = ""
            out_lines.append(line)
            continue

        if in_fence:
            out_lines.append(line)
            continue

        # Protect inline code by splitting on backticks
        parts = line.split("`")
        for i in range(0, len(parts), 2):  # even indices are outside code spans
            parts[i] = _EMOJI_TOKEN_RE.sub(repl, parts[i])
        out_lines.append("`".join(parts))

    return "\n".join(out_lines)

def render_md(text: str) -> str:
    text = preprocess_markdown(text)
    text = _replace_emojis_outside_code(text)
    return markdown.markdown(text, extensions=MD_EXT)

# ---------------- Git commit dates ----------------

def git_commit_date(file_path: Path) -> str:
    try:
        out = subprocess.check_output(
            [
                "git",
                "-C",
                str(CONTENT),
                "log",
                "-1",
                "--format=%cI",
                str(file_path.relative_to(CONTENT)),
            ],
            text=True,
        ).strip()
        if out:
            return out[:10]
    except Exception:
        pass
    return datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d")

# ---------------- Tree construction ----------------

def insert(node, parts, rel, date):
    if not parts:
        node.setdefault("__files__", []).append((rel, date))
        return
    node.setdefault(parts[0], {})
    insert(node[parts[0]], parts[1:], rel, date)

def newest_date(node):
    dates = [d for _, d in node.get("__files__", [])]
    for k, v in node.items():
        if k != "__files__":
            d = newest_date(v)
            if d:
                dates.append(d)
    return max(dates) if dates else ""

# ---------------- Articles ----------------

for md_file in CONTENT.rglob("*.md"):
    rel = md_file.relative_to(CONTENT)
    date = git_commit_date(md_file)
    insert(tree, list(rel.parent.parts), rel, date)

    html_body = render_md(md_file.read_text())
    title = title_from_file(md_file)

    article_html = render(
        article_tpl,
        article_title=title,
        article_date=date,
        article_body=f"<div class='markdown'>{html_body}</div>",
    )

    full_html = render(
        base_tpl,
        title=f"{title} – {SITE_TITLE}",
        site_title=SITE_TITLE,
        site_motd=SITE_MOTD,
        site_footer=SITE_FOOTER,
        theme_css=THEME_CSS,
        content=article_html,
    )

    # Normalize spaces -> underscores in output HTML filename
    out_rel = out_rel_from_md(rel)
    out_file = OUT / "articles" / out_rel
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(full_html)

    img_dir = md_file.with_suffix("")
    if img_dir.exists():
        # Keep the image folder name unchanged (including spaces) so existing markdown links keep working.
        shutil.copytree(img_dir, out_file.parent / img_dir.name, dirs_exist_ok=True)

# ---------------- Tree rendering ----------------

# Indent segments
INDENT = "    "   # 4 spaces
PIPE = "│       "     # '│' + 7 spaces

def _tree_html(s: str) -> str:
    """
    Preserve box-drawing alignment in HTML without editing CSS.
    Browsers collapse normal spaces, so we convert them to &nbsp;.
    """
    return html.escape(s).replace(" ", "&nbsp;")

def _url_quote_path(p: str) -> str:
    """
    Quote a URL path while keeping slashes so nested folders work.
    """
    return quote(p, safe="/")

def render_tree(node, prefix="", depth=0, path=()):
    """
    Unicode box-drawing tree renderer that supports arbitrary nesting.

    Uses:
      ├──  middle entries
      └──  last entries
      │    vertical continuation

    Spacing is 5-wide per level to keep the “gaps” consistent even at depth 2+.
    """
    html_out = ""

    folders = sorted(
        (k for k in node if k != "__files__"),
        key=lambda k: newest_date(node[k]),
        reverse=True,
    )
    files = sorted(node.get("__files__", []), key=lambda x: x[1], reverse=True)

    entries = [("folder", f) for f in folders] + [("file", f, d) for (f, d) in files]

    for idx, entry in enumerate(entries):
        is_last = idx == len(entries) - 1
        connector = ("└── " if is_last else "├── ")

        if entry[0] == "folder":
            folder = entry[1]

            # Keep the "top-level folder as heading" look:
            # no connector at depth 0, but connectors for nested folders.
            show_connector = depth > 0
            line_prefix = prefix + (connector if show_connector else "")

            folder_rel = "/".join((*path, folder))
            folder_href = "/articles/" + _url_quote_path(folder_rel) + "/index.html"

            # Nested folders shouldn't get the big .tree-folder margin-top
            folder_style = "" if depth == 0 else " style='margin-top:0;'"

            html_out += (
                "<div class='tree-folder'" + folder_style + ">"
                f"<span class='tree-branch'>{_tree_html(line_prefix)}</span>"
                "<img src='/theme/icons/folder_purple.png' alt='[+]'> "
                f"<a href='{html.escape(folder_href)}'>{html.escape(folder)}</a>"
                "</div>"
            )

            if depth == 0:
                next_prefix = INDENT
            else:
                next_prefix = prefix + (INDENT if is_last else PIPE)

            html_out += render_tree(
                node[folder],
                prefix=next_prefix,
                depth=depth + 1,
                path=path + (folder,),
            )

        else:
            f, date = entry[1], entry[2]

            # Links use normalized filename (spaces -> underscores)
            file_rel_html = out_rel_from_md(f).as_posix()
            file_href = "/articles/" + _url_quote_path(file_rel_html)

            # Override theme-specific indent/padding that can break tree alignment.
            html_out += (
                "<div class='tree-file' style='margin-left:0; padding-left:0;'>"
                f"<span class='tree-branch'>{_tree_html(prefix + connector)}</span>"
                "<img src='/theme/icons/file_gem.png' alt='[f]'> "
                f"<a href='{html.escape(file_href)}'>{html.escape(title_from_file(f))}</a>"
                f"<span class='tree-date'> · {html.escape(date)}</span>"
                "</div>"
            )

    return html_out

def build_main_tree():
    return "<div class='tree'>" + render_tree(tree, path=()) + "</div>"

# ---------------- Categories ----------------

def build_categories(node, path=()):
    title = "/".join(path) if path else "Articles"

    category_html = render(
        category_tpl,
        category_title=title,
        category_tree=render_tree(node, path=path),
    )

    full_html = render(
        base_tpl,
        title=f"{title} – {SITE_TITLE}",
        site_title=SITE_TITLE,
        site_motd=SITE_MOTD,
        site_footer=SITE_FOOTER,
        theme_css=THEME_CSS,
        content=category_html,
    )

    out_dir = OUT / "articles" / "/".join(path)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(full_html)

    for k in node:
        if k != "__files__":
            build_categories(node[k], path + (k,))

build_categories(tree)

# ---------------- Index ----------------

def load_about() -> str:
    f = META / "about.md"
    if not f.exists():
        return ""
    return (
        "<section class='about'>"
        f"<div class='markdown'>{render_md(f.read_text())}</div>"
        "</section>"
    )

def load_buttons() -> str:
    f = META / "buttons.md"
    if not f.exists():
        return ""
    return f"<section class='buttons'>{render_md(f.read_text())}</section>"

index_html = render(
    base_tpl,
    title=SITE_TITLE,
    site_title=SITE_TITLE,
    site_motd=SITE_MOTD,
    site_footer=SITE_FOOTER,
    theme_css=THEME_CSS,
    content=(
        load_about()
        + render(tree_tpl, tree=build_main_tree())
        + load_buttons()
    ),
)

(OUT / "index.html").write_text(index_html)

# ---------------- Assets ----------------

if (META / "buttons").exists():
    shutil.copytree(META / "buttons", OUT / "buttons", dirs_exist_ok=True)

shutil.copytree(THEME, OUT / "theme", dirs_exist_ok=True)
