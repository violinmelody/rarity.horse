import shutil
from pathlib import Path
from datetime import datetime
import markdown

ROOT = Path(__file__).resolve().parent.parent
CONTENT = Path("content/articles")
META = Path("content/meta")
OUT = ROOT / "wwwroot"
THEME = ROOT / "theme"
TEMPLATES = ROOT / "templates"

MD_EXT = ["extra"]

def tpl(name):
    return (TEMPLATES / name).read_text()

base_tpl = tpl("base.html")
article_tpl = tpl("article.html")
tree_tpl = tpl("tree.html")
category_tpl = tpl("category.html")

def render(t, **ctx):
    for k, v in ctx.items():
        t = t.replace("{{ " + k + " }}", v)
    return t

def title_from_file(p):
    return p.stem.replace("_", " ").title()

def render_md(text):
    return markdown.markdown(text, extensions=MD_EXT)

tree = {}

OUT.mkdir(exist_ok=True)

for md_file in CONTENT.rglob("*.md"):
    rel = md_file.relative_to(CONTENT)
    category = rel.parent.as_posix() or "."

    date = datetime.fromtimestamp(md_file.stat().st_mtime).strftime("%Y-%m-%d")
    tree.setdefault(category, []).append((rel, date))

    html_body = render_md(md_file.read_text())
    title = title_from_file(md_file)

    article_html = render(
        article_tpl,
        article_title=title,
        article_date=date,
        article_body=f"<div class='markdown'>{html_body}</div>"
    )

    full_html = render(
        base_tpl,
        title=title,
        content=article_html
    )

    out_file = OUT / "articles" / rel.with_suffix(".html")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(full_html)

    # Copy article images
    img_dir = md_file.with_suffix("")
    if img_dir.exists():
        shutil.copytree(
            img_dir,
            out_file.parent / img_dir.name,
            dirs_exist_ok=True
        )

def build_tree_for(entries, base_link="articles/"):
    html = ""

    for i, (f, date) in enumerate(sorted(entries)):
        branch = "└──" if i == len(entries) - 1 else "├──"
        title = title_from_file(f)
        link = f"{base_link}{f.with_suffix('.html')}"

        html += (
            "<div class='tree-file'>"
            f"<span class='tree-branch'>{branch}</span> "
            "<img src='/theme/icons/file.png' alt='[f]'> "
            f"<a href='/{link}'>{title}</a>"
            f"<span class='tree-date'> · {date}</span>"
            "</div>"
        )

    return html

def build_main_tree(tree):
    html = "<div class='tree'>"

    for category, entries in sorted(tree.items()):
        html += (
            "<div class='tree-folder'>"
            "<img src='/theme/icons/folder.png' alt='[+]'> "
            f"<a href='articles/{category}/index.html'>{category}</a>"
            "</div>"
        )

        html += build_tree_for(entries)

    html += "</div>"
    return html

for category, entries in tree.items():
    category_title = category if category != "." else "Articles"

    category_html = render(
        category_tpl,
        category_title=category_title,
        category_tree=build_tree_for(entries, base_link="articles/")
    )

    full_html = render(
        base_tpl,
        title=f"{category_title} – rarity.horse",
        content=category_html
    )

    out_dir = OUT / "articles" / category
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(full_html)

def load_about():
    about_md = META / "about.md"
    if not about_md.exists():
        return ""

    html = render_md(about_md.read_text())
    return (
        "<section class='about'>\n"
        "<div class='markdown'>\n"
        f"{html}\n"
        "</div>\n"
        "</section>\n"
    )

def load_buttons():
    buttons_md = META / "buttons.md"
    if not buttons_md.exists():
        return ""

    html = render_md(buttons_md.read_text())
    return (
        "<section class='buttons'>\n"
        f"{html}\n"
        "</section>\n"
    )

index_html = render(
    base_tpl,
    title="rarity.horse",
    content=(
        load_about()
        + render(tree_tpl, tree=build_main_tree(tree))
        + load_buttons()
    )
)

(OUT / "index.html").write_text(index_html)

if (META / "buttons").exists():
    shutil.copytree(
        META / "buttons",
        OUT / "buttons",
        dirs_exist_ok=True
    )

shutil.copytree(THEME, OUT / "theme", dirs_exist_ok=True)
