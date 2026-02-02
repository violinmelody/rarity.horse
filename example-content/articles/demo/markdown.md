# Example Markdown Page

This is a standard text.

> This is a blockquote.  
> It can span multiple lines and include **bold**, *italic*, and `inline code`.

---

## Table of Contents
- [Text](#text)
- [Links & Images](#links--images)
- [Lists](#lists)
- [Code](#code)
- [Tables](#tables)
- [Task Lists](#task-lists)
- [Details (HTML)](#details-html)
- [Math](#math)
- [Footnotes](#footnotes)
- [Emoji](#emoji)

---

## Text

### Emphasis
- **Bold**
- *Italic*
- ***Bold + Italic***
- ~~Strikethrough~~
- <ins>Underline (HTML)</ins>
- <mark>Highlight (HTML)</mark>
- Subscript (HTML): H<sub>2</sub>O
- Superscript (HTML): x<sup>2</sup>

### Inline Code
Use `command` to execute a command.

### Line Breaks
This is a line with two spaces at the end.  
This is the next line.

### Escape Characters
Use backslashes to escape characters: \*not italic\*, \# not a heading.

---

## Links & Images

### Links
- Standard link: [rarity.horse](https://rarity.horse)
- Link with title: [rarity.horse](https://rarity.horse "Rarity Horse")
- Auto-link: <https://rarity.horse>
- Email auto-link: <opal@rarity.horse>

### Reference Links
This is a [reference link][ref].

[ref]: https://rarity.horse "Reference Link Title"

### Images
![Placeholder image alt text](https://derpicdn.net/img/view/2026/2/2/3757859.jpg?text=Markdown+Image)

### Image as a Link
[![Clickable image](https://derpicdn.net/img/view/2026/2/2/3757859.jpg)](https://rarity.horse)

---

## Lists

### Unordered List
- Item A
- Item B
  - Nested item B.1
  - Nested item B.2
    - Nested item B.2.a

### Ordered List
1. First
2. Second
3. Third
   1. Nested third.1
   2. Nested third.2

### Mixed List
1. Step one
   - Note A
   - Note B
2. Step two
   - Note C

### Definition List (not supported everywhere)
Term 1
: Definition for term 1

Term 2
: Definition for term 2

---

## Code

### Fenced Code Block
```
This is a plain code block.
It preserves whitespace and formatting.
```

### Fenced Code Block (with language)
```python
def pony(name: str) -> str:
    return f"Hello, {name}!"

print(pony("Rarity"))
```

### Inline Code in a Sentence
Run `python build/build.py` to build the site.

---

## Tables

| Column A | Column B | Column C |
|---------:|:---------|:--------:|
| Right    | Left     | Center   |
| 123      | abc      | ✅        |
| 456      | def      | ❌        |

### Table with Inline Formatting
| Feature | Status | Notes |
|---|---|---|
| **Bold** | ✅ | Works in most renderers |
| *Italic* | ✅ | Works in most renderers |
| `Code` | ✅ | Works in most renderers |

---

## Task Lists

- [x] Done item
- [ ] Not done item
- [ ] Another item
  - [x] Nested done
  - [ ] Nested not done

---

## Horizontal Rules

---
***
___

---

## Headings

# H1
## H2
### H3
#### H4
##### H5
###### H6

---

## Blockquotes

> Single level quote.
>
> > Nested quote.
> >
> > Back to nested content.

---

## Callouts / Admonitions (renderer-specific)

> [!NOTE]
> This is a “note” style callout (works on GitHub, not all Markdown parsers).

> [!WARNING]
> This is a warning callout.

---

## Details (HTML)

<details>
  <summary>Click to expand</summary>

  This content is hidden by default.

  - It can contain lists
  - **Bold text**
  - `inline code`

</details>

---

## Math

Inline math: $E = mc^2$

Block math:

$$
\int_{0}^{\infty} e^{-x} \, dx = 1
$$

---

## Footnotes

Here is a statement with a footnote.[^1]  
And another footnote reference.[^long]

[^1]: This is the first footnote.
[^long]: This is a longer footnote that can include multiple lines.
    Indented lines are part of the same footnote.

---

## HTML Mixed In

<div style="padding: 10px; border: 1px solid #ccc; border-radius: 8px;">
  <strong>Custom HTML block:</strong> You can embed HTML in Markdown in many renderers.
</div>

---

## Emoji

- 😀 😅 🚀 ✅ ❌ 🎉
- GitHub-style shortcodes (renderer-specific): :rocket: :tada: :white_check_mark:

---

## End

Rarity is best pony!

~Author
