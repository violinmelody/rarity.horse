import shutil
from pathlib import Path
from datetime import datetime
import markdown
import subprocess

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

def render_md(text: str) -> str:
    return markdown.markdown(text, extensions=MD_EXT)

def title_from_file(p: Path) -> str:
    return p.stem.replace("_", " ").title()

# ---------------- Meta ----------------

def load_meta_file(name: str, default: str = "") -> str:
    f = META / name
    return f.read_text().strip() if f.exists() else default

SITE_TITLE = load_meta_file("title.md", "✦ RARITY.HORSE ✦")
SITE_MOTD = load_meta_file("motd.md", "generosity is magic, darling~")

# ---------------- Theme selection ----------------

def load_theme_css() -> str:
    raw = load_meta_file("theme.md", "boutique").strip().lower()
    if not raw:
        raw = "boutique"

    candidate = f"{raw}.css"
    if (THEME / candidate).exists():
        return candidate

    return "boutique.css"

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

# ---------------- Articles ----------------

for md_file in CONTENT.rglob("*.md"):
    rel = md_file.relative_to(CONTENT)
    category = rel.parent.as_posix() or "."

    date = git_commit_date(md_file)
    tree.setdefault(category, []).append((rel, date))

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
        theme_css=THEME_CSS,
        content=article_html,
    )

    out_file = OUT / "articles" / rel.with_suffix(".html")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(full_html)

    img_dir = md_file.with_suffix("")
    if img_dir.exists():
        shutil.copytree(img_dir, out_file.parent / img_dir.name, dirs_exist_ok=True)

# ---------------- Tree helpers ----------------

def build_tree_for(entries, base_link="articles/") -> str:
    html = ""
    for i, (f, date) in enumerate(sorted(entries)):
        branch = "└──" if i == len(entries) - 1 else "├──"
        title = title_from_file(f)
        link = f"{base_link}{f.with_suffix('.html')}"
        html += (
            "<div class='tree-file'>"
            f"<span class='tree-branch'>{branch}</span> "
            "<img src='/theme/icons/file_gem.png' alt='[f]'> "
            f"<a href='/{link}'>{title}</a>"
            f"<span class='tree-date'> · {date}</span>"
            "</div>"
        )
    return html

def build_main_tree(tree) -> str:
    html = "<div class='tree'>"
    for category, entries in sorted(tree.items()):
        html += (
            "<div class='tree-folder'>"
            "<img src='/theme/icons/folder_purple.png' alt='[+]'> "
            f"<a href='articles/{category}/index.html'>{category}</a>"
            "</div>"
        )
        html += build_tree_for(entries)
    html += "</div>"
    return html

# ---------------- Categories ----------------

for category, entries in tree.items():
    title = category if category != "." else "Articles"

    category_html = render(
        category_tpl,
        category_title=title,
        category_tree=build_tree_for(entries),
    )

    full_html = render(
        base_tpl,
        title=f"{title} – {SITE_TITLE}",
        site_title=SITE_TITLE,
        site_motd=SITE_MOTD,
        theme_css=THEME_CSS,
        content=category_html,
    )

    out_dir = OUT / "articles" / category
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(full_html)

# ---------------- Index ----------------

def load_about() -> str:
    f = META / "about.md"
    if not f.exists():
        return ""
    return f"<section class='about'><div class='markdown'>{render_md(f.read_text())}</div></section>"

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
    theme_css=THEME_CSS,
    content=(
        load_about()
        + render(tree_tpl, tree=build_main_tree(tree))
        + load_buttons()
    ),
)

(OUT / "index.html").write_text(index_html)

# ---------------- Assets ----------------

if (META / "buttons").exists():
    shutil.copytree(META / "buttons", OUT / "buttons", dirs_exist_ok=True)

shutil.copytree(THEME, OUT / "theme", dirs_exist_ok=True)
