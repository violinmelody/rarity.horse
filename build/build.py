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

md = markdown.Markdown(extensions=["extra"])

def tpl(name):
    return (TEMPLATES / name).read_text()

base = tpl("base.html")
article_tpl = tpl("article.html")
tree_tpl = tpl("tree.html")

def render(t, **ctx):
    for k, v in ctx.items():
        t = t.replace("{{ " + k + " }}", v)
    return t

def title_from_file(p):
    return p.stem.replace("_", " ").title()

tree = {}

OUT.mkdir(exist_ok=True)

# --- Build articles ---
for md_file in CONTENT.rglob("*.md"):
    rel = md_file.relative_to(CONTENT)
    category = rel.parent.as_posix()
    tree.setdefault(category, []).append(rel)

    html_body = md.convert(md_file.read_text())
    md.reset()

    title = title_from_file(md_file)
    date = datetime.fromtimestamp(md_file.stat().st_mtime).strftime("%Y-%m-%d")

    article_html = render(
        article_tpl,
        article_title=title,
        article_date=date,
        article_body=html_body
    )

    full_html = render(
        base,
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

# --- ASCII tree builder ---
def build_ascii_tree(tree):
    html = "<div class='tree'>"

    for category, files in sorted(tree.items()):
        html += (
            "<div class='tree-folder'>"
            "<img src='/rarity.horse/theme/icons/folder.png' alt='[+]'> "
            f"{category}"
            "</div>"
        )

        for i, f in enumerate(sorted(files)):
            branch = "└──" if i == len(files) - 1 else "├──"
            title = title_from_file(f)
            link = f"articles/{f.with_suffix('.html')}"

            html += (
                "<div class='tree-file'>"
                f"<span class='tree-branch'>{branch}</span> "
                "<img src='/rarity.horse/theme/icons/file.png' alt='[f]'> "
                f"<a href='/rarity.horse/{link}'>{title}</a>"
                "</div>"
            )

    html += "</div>"
    return html

# --- Load 88x31 buttons ---
def load_buttons():
    buttons_md = META / "buttons.md"
    if not buttons_md.exists():
        return ""

    html = md.convert(buttons_md.read_text())
    md.reset()
    return f"<section class='buttons'>{html}</section>"

# --- Build index ---
index_html = render(
    base,
    title="Articles",
    content=(
        render(tree_tpl, tree=build_ascii_tree(tree))
        + load_buttons()
    )
)

(OUT / "index.html").write_text(index_html)

# --- Copy meta assets (buttons images) ---
if (META / "buttons").exists():
    shutil.copytree(
        META / "buttons",
        OUT / "buttons",
        dirs_exist_ok=True
    )

# --- Copy theme ---
shutil.copytree(THEME, OUT / "theme", dirs_exist_ok=True)
