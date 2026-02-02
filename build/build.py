import shutil
from pathlib import Path
from datetime import datetime
import markdown
import subprocess
import html
from urllib.parse import quote

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

def render_md(text: str) -> str:
    text = preprocess_markdown(text)
    return markdown.markdown(text, extensions=MD_EXT)

def title_from_file(p: Path) -> str:
    return p.stem.replace("_", " ").title()

def link_from_file(l: Path) -> str:
    return l.stem.replace(" ", "_").title()

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

    out_file = OUT / "articles" / rel.with_suffix(".html")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(full_html)

    img_dir = md_file.with_suffix("")
    if img_dir.exists():
        shutil.copytree(img_dir, out_file.parent / img_dir.name, dirs_exist_ok=True)

# ---------------- Tree rendering ----------------

def _tree_html(s: str) -> str:
    """
    Preserve tree spacing in HTML without any CSS edits.
    Browsers collapse normal spaces, so we convert spaces to &nbsp;.
    """
    return html.escape(s).replace(" ", "&nbsp;")

def _url_quote_path(p: str) -> str:
    """
    Quote URL path while keeping slashes so nested folders work.
    """
    return quote(p, safe="/")

def render_tree(node, prefix="", depth=0, path=()):
    """
    Tree renderer that supports arbitrary nesting and correct nested links.

    Uses ASCII drawing:
      ├──   for middle items
      └──   for last items
      │     for vertical continuation
    """
    html_out = ""

    folders = sorted(
        (k for k in node if k != "__files__"),
        key=lambda k: newest_date(node[k]),
        reverse=True,
    )
    files = sorted(node.get("__files__", []), key=lambda x: x[1], reverse=True)

    # Determine "last" correctly across folders + files
    items = [("folder", f) for f in folders] + [("file", f, d) for (f, d) in files]

    for idx, entry in enumerate(items):
        is_last = idx == len(items) - 1
        branch = "└── " if is_last else "├── "

        if entry[0] == "folder":
            folder = entry[1]

            # Keep the original "root folders are headings" feel:
            # no branch at depth 0, but branches for nested folders.
            show_branch = depth > 0
            line_prefix = prefix + (branch if show_branch else "")

            folder_rel = "/".join((*path, folder))
            folder_href = "/articles/" + _url_quote_path(folder_rel) + "/index.html"

            html_out += (
                "<div class='tree-folder'>"
                f"<span class='tree-branch'>{_tree_html(line_prefix + '[+] ')}</span>"
                f"<a href='{html.escape(folder_href)}'>{html.escape(folder)}</a>"
                "</div>"
            )

            # Child prefix: continue vertical line if this folder isn't last.
            child_prefix = prefix + ("    " if is_last else "│   ")

            # For top-level headings (depth==0), just indent children.
            if depth == 0:
                child_prefix = prefix + "    "

            html_out += render_tree(
                node[folder],
                prefix=child_prefix,
                depth=depth + 1,
                path=path + (folder,),
            )

        else:
            f, date = entry[1], entry[2]

            file_rel_html = f.with_suffix(".html").as_posix()
            file_href = "/articles/" + _url_quote_path(file_rel_html)

            html_out += (
                "<div class='tree-file' style='margin-left:0; padding-left:0;'>"
                f"<span class='tree-branch'>{_tree_html(prefix + branch + '[f] ')}</span>"
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
