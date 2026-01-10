# ✦ Rarity ✦

A handcrafted, static, Markdown-driven website generation engine inspired by  
90s personal pages, demoscene aesthetics and Rarity's elegance.

No JavaScript.  
No trackers.  
No runtime dependencies.

Built automatically with GitHub Actions.  
Served via GitHub Pages.

---

## Features

- Markdown articles stored in a **separate repository**
- Automatic article dates (from file modification time)
- Folder-based categories
- Per-article image folders
- ASCII tree index
- Folder & file icons
- Automatic dark mode
- Extremely fast (pure HTML + CSS)

---

## Repository Model

This project is intentionally split into **two repositories**:

### 1. Engine Repository (this repo)
- Public
- Contains:
  - Static site generator
  - HTML templates
  - CSS theme and icons
  - GitHub Actions workflow

### 2. Content Repository
- Separate repository
- Can be **private**
- Contains:
  - Markdown articles
  - Images

The engine **consumes content at build time** via GitHub Actions.  
Content is never committed to this repository.

---

## Content Repository Structure

The content repository must expose the following structure:

```text
content/
└─ articles/
   └─ category/
      ├─ article.md
      └─ article/
         └─ image.png
```

### Content Rules

| Element | Meaning |
|-------|--------|
| Folder name | Category |
| Markdown filename | Article title |
| File modification time | Article date |
| Matching folder | Images for that article |

---

## Writing Articles

### Create a new article

```bash
mkdir content/articles/rarity
nano content/articles/rarity/she_is_beautiful.md
```

### Add images

```bash
mkdir content/articles/rarity/she_is_beautiful
cp image.png content/articles/rarity/she_is_beautiful/
```

### Reference images in Markdown

```md
![Dress](she_is_beautiful/dress.png)
```

---

## Engine Repository Structure

```text
.
├─ build/            # Static site generator (Python)
├─ templates/        # HTML templates
├─ theme/            # CSS + icons
├─ example-content/  # Demo content for forks
├─ wwwroot/          # GENERATED output (CI only)
└─ .github/          # GitHub Actions
```

> `wwwroot/` is generated and must never be edited manually.

---

## Configuring the Content Repository (GitHub Actions)

The engine repository’s GitHub Actions workflow checks out **two repositories**.

### Required workflow step

```yaml
- name: Checkout content
  uses: actions/checkout@v4
  with:
    repository: YOUR_USERNAME/YOUR_CONTENT_REPO
    path: content
    token: ${{ secrets.CONTENT_REPO_TOKEN }}
```

### Required secret

Create a **GitHub token** with:

- Repository access: *content repository only*
- Permission: `Contents: Read`

Add it to the engine repository as:

```
Settings → Secrets → Actions
Name: CONTENT_REPO_TOKEN
```

This allows CI to read private articles without exposing them.

---

## Local Development

Install dependencies:

```bash
pip install markdown
```

Build the site:

```bash
python build/build.py
```

Output will be written to:

```text
wwwroot/
```

For local testing, you may manually place a `content/` directory at the project root.

---

## Deployment

This engine can automatically rebuild whenever the **private content repository** is updated.  

### How it works

1. **Private content repo workflow** triggers on every push to `main`.  
   It sends a `repository_dispatch` event to the engine repo.
2. **Engine repo workflow** listens for this event.  
   It checks out:
   - The engine repository
   - The private content repository
3. The engine builds the site and deploys it to GitHub Pages automatically.

### Setup Steps

#### 1. Create a Personal Access Token (PAT)

- Go to your GitHub **Settings → Developer settings → Personal access tokens → Fine-grained tokens**.
- Scope: **Engine repo only**
- Permissions: `Contents: Write`, `Workflows: Trigger`
- Add this PAT to the **content repo** as `RARITY_ENGINE_REPO_PAT`.

#### 2. Add a Token for Content Repo in Engine Repo

- Create a token in GitHub with **read access** to the content repo.
- Add it to **engine repo secrets** as `RARITY_CONTENT_REPO_TOKEN`.

#### 3. Add the Workflows

- Content repo workflow triggers the engine build
- Engine repo workflow handles the dispatch event and builds the site

#### 4. Enable GitHub Pages

- Repository → Settings → Pages
- Source: **GitHub Actions**

---

## Forking This Repository

When forked:

- No content is included
- `example-content/` shows the expected structure
- You must provide your own content repository or local `content/` directory

---

## License

💎 Do whatever you want, just keep it elegant 💎

---
