"""HorizonQuest Skill Studio — guided, auto-graded productivity-software missions.
Phase 1: Word Processing (docs). Phase 2: Spreadsheets (sheets). Each mission teaches a
"chunk" of the app, loads a starter document, and lists tasks graded by inspecting the
student's document state. Grading logic is mirrored on the client for live ticking.
"""
import re

# Per-track toolbar option sets shared with the client so tasks reference exact values.
DOCS_CONFIG = {
    "fonts": ["Arial", "Times New Roman", "Verdana", "Garamond", "Helvetica", "Georgia", "Courier New", "Brush Script MT"],
    "sizes": [10, 11, 12, 14, 16, 18, 20, 24, 30, 36],
    "colors": [
        {"name": "Black", "hex": "#0f172a"},
        {"name": "Red", "hex": "#dc2626"},
        {"name": "Orange", "hex": "#ea580c"},
        {"name": "Green", "hex": "#16a34a"},
        {"name": "Blue", "hex": "#2563eb"},
        {"name": "Purple", "hex": "#7c3aed"},
    ],
    "spacings": [1.0, 1.15, 1.5, 2.0],
    "symbols": ["®", "™", "©", "•", "→", "★", "°", "½", "é", "ñ"],
}

SHEETS_CONFIG = {
    "functions": ["SUM", "AVERAGE", "COUNT", "MAX", "MIN"],
    "chartTypes": [{"id": "bar", "name": "Bar chart"}, {"id": "pie", "name": "Pie chart"}],
}

TRACK_CONFIG = {"docs": DOCS_CONFIG, "sheets": SHEETS_CONFIG}
# Back-compat alias
STUDIO_CONFIG = DOCS_CONFIG

_GALLERY = [
    {"id": "classroom", "label": "Classroom", "url": "https://images.unsplash.com/photo-1509062522246-3755977927d7?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NjZ8MHwxfHNlYXJjaHwxfHxjbGFzc3Jvb20lMjBzdHVkZW50cyUyMGxlYXJuaW5nfGVufDB8fHx8MTc4NTg0OTM2OHww&ixlib=rb-4.1.0&q=85"},
    {"id": "planets", "label": "Planets", "url": "https://images.unsplash.com/photo-1701014159143-09482059f571?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2ODl8MHwxfHNlYXJjaHwyfHxzb2xhciUyMHN5c3RlbSUyMHBsYW5ldHMlMjBzcGFjZXxlbnwwfHx8fDE3ODU4NDkzNjh8MA&ixlib=rb-4.1.0&q=85"},
    {"id": "forest", "label": "Forest", "url": "https://images.unsplash.com/photo-1674916251976-b64824a5f3de?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDZ8MHwxfHNlYXJjaHwyfHxncmVlbiUyMGZvcmVzdCUyMG5hdHVyZSUyMGxhbmRzY2FwZXxlbnwwfHx8fDE3ODU4NDkzNjd8MA&ixlib=rb-4.1.0&q=85"},
    {"id": "food", "label": "Healthy food", "url": "https://images.unsplash.com/photo-1610832958506-aa56368176cf?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMzV8MHwxfHNlYXJjaHwxfHxoZWFsdGh5JTIwZm9vZCUyMGZydWl0cyUyMHZlZ2V0YWJsZXN8ZW58MHx8fHwxNzg1ODQ5MzY4fDA&ixlib=rb-4.1.0&q=85"},
    {"id": "laptop", "label": "Technology", "url": "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2ODl8MHwxfHNlYXJjaHwxfHx0ZWNobm9sb2d5JTIwbGFwdG9wJTIwY29tcHV0ZXJ8ZW58MHx8fHwxNzg1ODQ5MzY4fDA&ixlib=rb-4.1.0&q=85"},
    {"id": "mountain", "label": "Mountains", "url": "https://images.unsplash.com/photo-1691823234579-388866863711?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDZ8MHwxfHNlYXJjaHwxfHxncmVlbiUyMGZvcmVzdCUyMG5hdHVyZSUyMGxhbmRzY2FwZXxlbnwwfHx8fDE3ODU4NDkzNjd8MA&ixlib=rb-4.1.0&q=85"},
]

SLIDES_CONFIG = {
    "layouts": [
        {"id": "title", "name": "Title slide"},
        {"id": "title-content", "name": "Title & content"},
        {"id": "two-content", "name": "Two content"},
        {"id": "blank", "name": "Blank"},
    ],
    "themes": [
        {"id": "midnight", "name": "Midnight", "bg": "#0B1E3B", "fg": "#E8F4FF", "accent": "#22D3EE"},
        {"id": "sunrise", "name": "Sunrise", "bg": "#FFF7ED", "fg": "#7C2D12", "accent": "#EA580C"},
        {"id": "ocean", "name": "Ocean", "bg": "#04211E", "fg": "#D1FAF5", "accent": "#34D399"},
        {"id": "paper", "name": "Paper", "bg": "#FFFFFF", "fg": "#0F172A", "accent": "#2563EB"},
    ],
    "gallery": _GALLERY,
    "animations": [
        {"id": "none", "name": "None"}, {"id": "fade", "name": "Fade in"},
        {"id": "fly", "name": "Fly in"}, {"id": "zoom", "name": "Zoom in"},
    ],
    "transitions": [
        {"id": "none", "name": "None"}, {"id": "fade", "name": "Fade"},
        {"id": "slide", "name": "Slide"}, {"id": "push", "name": "Push"},
    ],
    "chartTypes": [{"id": "bar", "name": "Bar chart"}, {"id": "pie", "name": "Pie chart"}],
}

TRACK_CONFIG["slides"] = SLIDES_CONFIG

TRACKS = {
    "docs": {"id": "docs", "name": "Word Processing", "subtitle": "Google Docs · Microsoft Word · Pages",
             "standard": "PA.2.A", "color": "#22D3EE",
             "intro": "Master the document editor one ribbon chunk at a time — then prove it on real editing tasks."},
    "sheets": {"id": "sheets", "name": "Spreadsheets", "subtitle": "Google Sheets · Microsoft Excel · Numbers",
               "standard": "PA.2.B", "color": "#34D399",
               "intro": "Enter data, build formulas (SUM, AVERAGE, COUNT, MAX, MIN), sort, and chart — one skill at a time."},
    "slides": {"id": "slides", "name": "Presentations", "subtitle": "Google Slides · PowerPoint · Keynote",
               "standard": "PA.2.C", "color": "#F59E0B",
               "intro": "Build clean, engaging decks — layouts, the 5×5 rule, images, charts, animations, and delivery."},
}


def _b(bid, text, btype="paragraph", **fmt):
    base = {"bold": False, "italic": False, "underline": False, "fontFamily": "Arial",
            "fontSize": 11, "color": "#0f172a", "align": "left", "lineSpacing": 1.0, "link": ""}
    base.update(fmt)
    return {"id": bid, "type": btype, "text": text, "fmt": base}


def _doc(blocks, header="", footer_page=False):
    return {"header": header, "footerPageNumber": footer_page, "blocks": blocks}


def _t(tid, label, check, hint=""):
    return {"id": tid, "label": label, "check": check, "hint": hint}


# ------------------------------ DOCS MISSIONS ------------------------------
DOCS_MISSIONS = [
    {
        "id": "docs-m1", "track": "docs", "order": 1,
        "title": "Meet the Ribbon", "chunk": "Interface · Tabs, Menus & Toolbar",
        "instruction": [
            "## The editor interface",
            "The bar across the top of a document editor is the **Ribbon**. It holds **Tabs** (File, Edit, Insert, Format…) and the **Toolbar** — the row of shortcut buttons you use most.",
            "- Click a line of text to **select** it (a blue outline appears).",
            "- The toolbar buttons then apply to the selected line.",
            "In this Studio you select a line, then use the toolbar just like the real thing.",
            "## Try it",
            "Select the title line and make it **bold**. Then *italicize* the subtitle.",
        ],
        "doc": _doc([
            _b("b1", "My First Document"),
            _b("b2", "A quick tour of the editor"),
            _b("b3", "Click any line above to select it, then use the toolbar."),
        ]),
        "tasks": [
            _t("t1", "Bold the title line ('My First Document')", {"kind": "fmt", "block": "b1", "attr": "bold", "equals": True}),
            _t("t2", "Italicize the subtitle ('A quick tour of the editor')", {"kind": "fmt", "block": "b2", "attr": "italic", "equals": True}),
        ],
        "points": 100,
    },
    {
        "id": "docs-m2", "track": "docs", "order": 2,
        "title": "Font Style: Bold, Italic, Underline", "chunk": "Font group · B / I / U",
        "instruction": [
            "## Emphasis: B, I, U",
            "- **Bold** (B) makes text heavy — great for titles and key terms.",
            "- *Italic* (I) slants text — used for quotes, titles of works, and emphasis.",
            "- Underline (U) draws a line beneath text.",
            "Select a line, then click B, I, or U in the toolbar. Click again to turn it off.",
            "## Book report",
            "Format the book report below using emphasis.",
        ],
        "doc": _doc([
            _b("b1", "The Great Gatsby"),
            _b("b2", "Written by F. Scott Fitzgerald"),
            _b("b3", "This novel explores wealth and ambition in 1920s America."),
        ]),
        "tasks": [
            _t("t1", "Bold the book title", {"kind": "fmt", "block": "b1", "attr": "bold", "equals": True}),
            _t("t2", "Italicize the author's name", {"kind": "fmt", "block": "b2", "attr": "italic", "equals": True}),
            _t("t3", "Underline the summary sentence", {"kind": "fmt", "block": "b3", "attr": "underline", "equals": True}),
        ],
        "points": 100,
    },
    {
        "id": "docs-m3", "track": "docs", "order": 3,
        "title": "Font Family & Size", "chunk": "Font group · Typeface & point size",
        "instruction": [
            "## Choosing a typeface and size",
            "- The **Font** menu changes the typeface (e.g., *Times New Roman*, *Verdana*).",
            "- The **Font size** menu changes how big the text is, measured in **points (pt)**.",
            "Titles are usually larger; body text is often **12pt**.",
            "## Practice",
            "Give the whole book report a consistent font, and make the title stand out.",
        ],
        "doc": _doc([
            _b("b1", "The Great Gatsby"),
            _b("b2", "Written by F. Scott Fitzgerald"),
            _b("b3", "A classic American novel."),
        ]),
        "tasks": [
            _t("t1", "Set every line to Times New Roman", {"kind": "fmt_all", "attr": "fontFamily", "equals": "Times New Roman"}),
            _t("t2", "Set the two body lines to 12pt", {"kind": "fmt_multi", "blocks": ["b2", "b3"], "attr": "fontSize", "equals": 12}),
            _t("t3", "Make the title ('The Great Gatsby') 24pt", {"kind": "fmt", "block": "b1", "attr": "fontSize", "equals": 24}),
        ],
        "points": 100,
    },
    {
        "id": "docs-m4", "track": "docs", "order": 4,
        "title": "Text Color", "chunk": "Font group · Text color",
        "instruction": [
            "## Adding color",
            "The **Text color** button (A with a colored bar) changes the color of selected text.",
            "Use color sparingly — for headings or to highlight one important idea.",
            "## Practice",
            "Color-code the newsletter below.",
        ],
        "doc": _doc([
            _b("b1", "Field Trip to the Science Museum"),
            _b("b2", "Our class visited the Science Museum last week."),
            _b("b3", "Reminder: permission slips are due Friday."),
        ]),
        "tasks": [
            _t("t1", "Make the headline blue", {"kind": "fmt", "block": "b1", "attr": "color", "equals": "#2563eb"}),
            _t("t2", "Make the reminder line red", {"kind": "fmt", "block": "b3", "attr": "color", "equals": "#dc2626"}),
        ],
        "points": 100,
    },
    {
        "id": "docs-m5", "track": "docs", "order": 5,
        "title": "Paragraph Alignment", "chunk": "Paragraph group · Align & justify",
        "instruction": [
            "## Alignment",
            "- **Left** — text lines up on the left (default).",
            "- **Center** — text is centered; great for titles.",
            "- **Right** — text lines up on the right.",
            "- **Justify** — text stretches to both margins evenly.",
            "## Practice",
            "Lay out the poem below.",
        ],
        "doc": _doc([
            _b("b1", "Whispers of the Forest"),
            _b("b2", "The trees sway gently in the breeze,"),
            _b("b3", "Leaves dance with sunlight's golden rays."),
            _b("b4", "— A. Poet"),
        ]),
        "tasks": [
            _t("t1", "Center the poem title", {"kind": "fmt", "block": "b1", "attr": "align", "equals": "center"}),
            _t("t2", "Center the two poem lines", {"kind": "fmt_multi", "blocks": ["b2", "b3"], "attr": "align", "equals": "center"}),
            _t("t3", "Right-align the author credit", {"kind": "fmt", "block": "b4", "attr": "align", "equals": "right"}),
        ],
        "points": 100,
    },
    {
        "id": "docs-m6", "track": "docs", "order": 6,
        "title": "Line & Paragraph Spacing", "chunk": "Paragraph group · Line spacing",
        "instruction": [
            "## Spacing",
            "**Line spacing** controls the gap between lines. **1.0** is single-spaced; **1.5** and **2.0** (double) add breathing room and are common for school papers.",
            "## How to change it",
            "- Click a line to **select** it.",
            "- In the toolbar, open the **line-spacing menu** — the small box that reads **1.0×** (just right of the alignment buttons) — and choose **1.5×**.",
            "- Do this for **each** body line you want to open up.",
            "## Practice",
            "Set all four body lines to 1.5× spacing and bold the essay title.",
        ],
        "doc": _doc([
            _b("b1", "Essay: Why Reading Matters"),
            _b("b2", "Reading builds vocabulary, focus, and empathy every single day."),
            _b("b3", "It lets us explore ideas and places far beyond our own experience."),
            _b("b4", "A good book can carry us to new times, worlds, and points of view."),
            _b("b5", "That is why making time for daily reading is a habit worth keeping."),
        ]),
        "tasks": [
            _t("t1", "Set all four body lines to 1.5 line spacing", {"kind": "fmt_multi", "blocks": ["b2", "b3", "b4", "b5"], "attr": "lineSpacing", "equals": 1.5}),
            _t("t2", "Bold the essay title", {"kind": "fmt", "block": "b1", "attr": "bold", "equals": True}),
        ],
        "points": 100,
    },
    {
        "id": "docs-m7", "track": "docs", "order": 7,
        "title": "Lists: Bullets & Numbers", "chunk": "Paragraph group · Bulleted & numbered lists",
        "instruction": [
            "## Lists",
            "- A **bulleted list** shows items of equal importance.",
            "- A **numbered list** shows steps or ranked items in order.",
            "Select a line and click the bullet or numbered-list button to convert it.",
            "## Practice",
            "Turn the packing notes into a proper list.",
        ],
        "doc": _doc([
            _b("b1", "Field Trip Packing List"),
            _b("b2", "Water bottle"),
            _b("b3", "Notebook and pencil"),
            _b("b4", "Permission slip"),
        ]),
        "tasks": [
            _t("t1", "Make 'Water bottle' a bullet", {"kind": "type", "block": "b2", "equals": "bullet"}),
            _t("t2", "Make 'Notebook and pencil' a bullet", {"kind": "type", "block": "b3", "equals": "bullet"}),
            _t("t3", "Make 'Permission slip' a bullet", {"kind": "type", "block": "b4", "equals": "bullet"}),
        ],
        "points": 100,
    },
    {
        "id": "docs-m8", "track": "docs", "order": 8,
        "title": "Insert: Symbols & Hyperlinks", "chunk": "Insert menu · Special characters & links",
        "instruction": [
            "## Inserting extras",
            "- **Special characters** are symbols not on the keyboard, like ® ™ © °. Use the Ω (Insert Symbol) button.",
            "- A **hyperlink** turns text into a clickable link to a website. Select the line, click the link button, and type **any real web address** — for example `https://www.example.com`.",
            "## Practice",
            "Finish the product blurb: add the ® symbol and turn the last line into a hyperlink (any web address works).",
        ],
        "doc": _doc([
            _b("b1", "SkyPad Tablet"),
            _b("b2", "Now trademarked and better than ever."),
            _b("b3", "Learn more at our website"),
        ]),
        "tasks": [
            _t("t1", "Insert the ® symbol somewhere in the product name line", {"kind": "text_contains", "block": "b1", "value": "®"}),
            _t("t2", "Turn 'Learn more at our website' into a hyperlink (type any web address, e.g. https://www.skypad.com)", {"kind": "link", "block": "b3"}),
        ],
        "points": 100,
    },
    {
        "id": "docs-m9", "track": "docs", "order": 9,
        "title": "Find & Replace", "chunk": "Edit menu · Find and replace",
        "instruction": [
            "## Find & Replace",
            "**Find and replace** swaps every copy of one word for another across the whole document in one step — perfect for fixing a name or wording everywhere at once.",
            "## How to use it",
            "- Click the **Find & replace** button (the magnifier 🔍) in the toolbar.",
            "- Type the word to **find** (`donation`) and the word to **replace** it with (`gift`).",
            "- Click **Replace all** — every match changes at once.",
            "## Practice",
            "The flyer uses the word 'donation' but the club decided to say 'gift'. Replace it everywhere.",
        ],
        "doc": _doc([
            _b("b1", "Community Book Drive"),
            _b("b2", "Every donation helps a student."),
            _b("b3", "Drop your donation in the front office."),
        ]),
        "tasks": [
            _t("t1", "Replace 'donation' with 'gift' in the second line", {"kind": "text_replaced", "block": "b2", "remove": "donation", "add": "gift"}),
            _t("t2", "Replace 'donation' with 'gift' in the third line", {"kind": "text_replaced", "block": "b3", "remove": "donation", "add": "gift"}),
        ],
        "points": 100,
    },
    {
        "id": "docs-m10", "track": "docs", "order": 10,
        "title": "Tables", "chunk": "Insert menu · Tables",
        "instruction": [
            "## Tables",
            "A **table** organizes information into **rows** and **columns**. Use the Insert Table button and choose the size (e.g., 3 columns × 2 rows), then click a cell to type.",
            "## Practice",
            "Add a table to hold the class schedule.",
        ],
        "doc": _doc([
            _b("b1", "Monday Schedule"),
            _b("b2", "Insert a table below to organize the periods."),
        ]),
        "tasks": [
            _t("t1", "Insert a table with 3 columns and 2 rows", {"kind": "table", "cols": 3, "rows": 2}),
            _t("t2", "Type a heading in the table's first cell", {"kind": "table_cell_filled", "row": 0, "col": 0}),
        ],
        "points": 100,
    },
    {
        "id": "docs-m11", "track": "docs", "order": 11,
        "title": "Headers, Footers & Page Numbers", "chunk": "Insert menu · Headers & footers",
        "instruction": [
            "## Headers & footers",
            "- A **header** repeats at the **top** of every page — often your name or the document title.",
            "- A **footer** repeats at the **bottom** — a common place for **page numbers**.",
            "## Practice",
            "Add a header and turn on page numbers for this report.",
        ],
        "doc": _doc([
            _b("b1", "Water Cycle Report"),
            _b("b2", "The water cycle describes how water moves through the environment."),
        ]),
        "tasks": [
            _t("t1", "Add the header text: Water Cycle Report", {"kind": "header_contains", "value": "Water Cycle Report"}),
            _t("t2", "Turn on page numbers in the footer", {"kind": "footer_pagenum"}),
        ],
        "points": 100,
    },
    {
        "id": "docs-m12", "track": "docs", "order": 12,
        "title": "Capstone: Format & Export to PDF", "chunk": "Everything · plus File → Download as PDF",
        "instruction": [
            "## Put it all together",
            "This capstone uses the skills from every mission. Format the newsletter cleanly, then **export it to PDF** — the standard way to share a finished document so its formatting never changes.",
            "## Your tasks",
            "Follow the checklist. When every task is green, download your PDF and submit for a grade.",
        ],
        "doc": _doc([
            _b("b1", "The Voyager Times"),
            _b("b2", "Class Newsletter — June Edition"),
            _b("b3", "This month our crew explored ciphers, charts, and leadership."),
            _b("b4", "Highlights"),
            _b("b5", "Cipher Playground launch"),
            _b("b6", "Mock Meeting champions"),
        ]),
        "tasks": [
            _t("t1", "Center the masthead title ('The Voyager Times')", {"kind": "fmt", "block": "b1", "attr": "align", "equals": "center"}),
            _t("t2", "Make the masthead title 30pt and bold", {"kind": "fmt_and", "block": "b1", "checks": [["fontSize", 30], ["bold", True]]}),
            _t("t3", "Italicize the edition line", {"kind": "fmt", "block": "b2", "attr": "italic", "equals": True}),
            _t("t4", "Bold the 'Highlights' heading", {"kind": "fmt", "block": "b4", "attr": "bold", "equals": True}),
            _t("t5", "Make the two highlight lines bullets", {"kind": "type_multi", "blocks": ["b5", "b6"], "equals": "bullet"}),
            _t("t6", "Set the whole newsletter to Georgia font", {"kind": "fmt_all", "attr": "fontFamily", "equals": "Georgia"}),
            _t("t7", "Export the document to PDF", {"kind": "exported"}),
        ],
        "points": 150,
    },
]

MISSIONS = {"docs": DOCS_MISSIONS}


# ------------------------------ SHEET FORMULA ENGINE ------------------------------
def _col_to_idx(col):
    idx = 0
    for ch in col:
        idx = idx * 26 + (ord(ch.upper()) - 64)
    return idx - 1


def _idx_to_col(i):
    s = ""; i += 1
    while i > 0:
        i, r = divmod(i - 1, 26); s = chr(65 + r) + s
    return s


def _parse_ref(ref):
    m = re.match(r"^([A-Za-z]+)(\d+)$", (ref or "").strip())
    if not m:
        return None
    return (_col_to_idx(m.group(1)), int(m.group(2)) - 1)


def _expand_range(rng):
    rng = rng.strip()
    if ":" in rng:
        a, b = rng.split(":", 1)
        pa, pb = _parse_ref(a), _parse_ref(b)
        if not pa or not pb:
            return []
        refs = []
        for r in range(min(pa[1], pb[1]), max(pa[1], pb[1]) + 1):
            for c in range(min(pa[0], pb[0]), max(pa[0], pb[0]) + 1):
                refs.append(f"{_idx_to_col(c)}{r + 1}")
        return refs
    return [rng]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def eval_ref(cells, ref, seen=None):
    seen = seen or set()
    if ref in seen:
        return None
    raw = (cells.get(ref) or "").strip()
    if raw == "":
        return None
    if raw.startswith("="):
        return eval_formula(cells, raw, seen | {ref})
    n = _num(raw)
    return n if n is not None else raw


def eval_formula(cells, raw, seen):
    m = re.match(r"^=\s*([A-Za-z]+)\s*\((.*)\)\s*$", raw)
    if not m:
        return "#ERR"
    fn = m.group(1).upper()
    refs = []
    for part in m.group(2).split(","):
        part = part.strip()
        if part:
            refs.extend(_expand_range(part))
    vals = []
    for r in refs:
        v = eval_ref(cells, r, seen)
        n = v if isinstance(v, (int, float)) else _num(v) if v is not None else None
        if isinstance(n, (int, float)):
            vals.append(n)
    if fn == "SUM":
        return sum(vals)
    if fn == "COUNT":
        return len(vals)
    if fn == "AVERAGE":
        return round(sum(vals) / len(vals), 4) if vals else 0
    if fn == "MAX":
        return max(vals) if vals else 0
    if fn == "MIN":
        return min(vals) if vals else 0
    return "#ERR"


# ------------------------------ SHEETS MISSIONS ------------------------------
def _sheet(name, rows, cols, cells):
    return {"name": name, "rows": rows, "cols": cols, "cells": cells}


def _sdoc(sheets, charts=None):
    return {"sheets": sheets, "activeSheet": 0, "charts": charts or []}


SHEETS_MISSIONS = [
    {
        "id": "sheets-m1", "track": "sheets", "order": 1,
        "title": "Meet the Spreadsheet", "chunk": "Cells, rows & columns",
        "instruction": [
            "## The grid",
            "A spreadsheet is a grid of **cells**. **Columns** are labeled with letters (A, B, C…) and **rows** with numbers (1, 2, 3…).",
            "- Each cell has an **address** like `A1` (column A, row 1) or `B3`.",
            "- Click a cell and type to enter a **label** (text) or a **value** (number).",
            "## Practice",
            "Type the headers and first data row for a simple score sheet.",
        ],
        "doc": _sdoc([_sheet("Sheet1", 6, 4, {})]),
        "tasks": [
            _t("t1", "Type 'Player' in cell A1", {"kind": "cell_text", "sheet": 0, "cell": "A1", "equals": "Player"}),
            _t("t2", "Type 'Score' in cell B1", {"kind": "cell_text", "sheet": 0, "cell": "B1", "equals": "Score"}),
            _t("t3", "Type a number (e.g. 20) in cell B2", {"kind": "cell_value", "sheet": 0, "cell": "B2", "equals": 20}),
        ],
        "points": 100,
    },
    {
        "id": "sheets-m2", "track": "sheets", "order": 2,
        "title": "The SUM Formula", "chunk": "Formulas · =SUM",
        "instruction": [
            "## Adding with =SUM",
            "A **formula** always starts with `=`. `=SUM(B2:B5)` adds every value from B2 through B5.",
            "- `B2:B5` is a **range** — a block of cells.",
            "- Click the total cell, type the formula, and press Enter to see the answer.",
            "## Practice",
            "Total the sales below in cell B6.",
        ],
        "doc": _sdoc([_sheet("Sales", 7, 3, {"A1": "Day", "B1": "Sales", "A2": "Mon", "B2": "40", "A3": "Tue", "B3": "55", "A4": "Wed", "B4": "30", "A5": "Thu", "B5": "25", "A6": "Total"})]),
        "tasks": [
            _t("t1", "In B6, use =SUM(B2:B5) to total the sales", {"kind": "cell_formula", "sheet": 0, "cell": "B6", "fn": "SUM", "range": "B2:B5"}),
            _t("t2", "The total in B6 should equal 150", {"kind": "cell_value", "sheet": 0, "cell": "B6", "equals": 150}),
        ],
        "points": 100,
    },
    {
        "id": "sheets-m3", "track": "sheets", "order": 3,
        "title": "The AVERAGE Formula", "chunk": "Formulas · =AVERAGE",
        "instruction": [
            "## Finding the mean with =AVERAGE",
            "`=AVERAGE(B2:B5)` adds the values and divides by how many there are — the **mean**.",
            "## Practice",
            "Find the average quiz score in B6.",
        ],
        "doc": _sdoc([_sheet("Quiz", 7, 3, {"A1": "Student", "B1": "Quiz", "A2": "Ana", "B2": "80", "A3": "Ben", "B3": "90", "A4": "Cy", "B4": "70", "A5": "Di", "B5": "100", "A6": "Average"})]),
        "tasks": [
            _t("t1", "In B6, use =AVERAGE(B2:B5)", {"kind": "cell_formula", "sheet": 0, "cell": "B6", "fn": "AVERAGE", "range": "B2:B5"}),
            _t("t2", "The average in B6 should equal 85", {"kind": "cell_value", "sheet": 0, "cell": "B6", "equals": 85}),
        ],
        "points": 100,
    },
    {
        "id": "sheets-m4", "track": "sheets", "order": 4,
        "title": "The COUNT Formula", "chunk": "Formulas · =COUNT",
        "instruction": [
            "## Counting numbers with =COUNT",
            "`=COUNT(B2:B6)` tells you **how many cells contain numbers** in a range (it ignores empty cells and text).",
            "## Practice",
            "Count how many students turned in a score.",
        ],
        "doc": _sdoc([_sheet("Turnins", 8, 3, {"A1": "Student", "B1": "Score", "A2": "Ana", "B2": "88", "A3": "Ben", "B3": "", "A4": "Cy", "B4": "72", "A5": "Di", "B5": "95", "A6": "Ed", "B6": "", "A7": "Count"})]),
        "tasks": [
            _t("t1", "In B7, use =COUNT(B2:B6)", {"kind": "cell_formula", "sheet": 0, "cell": "B7", "fn": "COUNT", "range": "B2:B6"}),
            _t("t2", "The count in B7 should equal 3", {"kind": "cell_value", "sheet": 0, "cell": "B7", "equals": 3}),
        ],
        "points": 100,
    },
    {
        "id": "sheets-m5", "track": "sheets", "order": 5,
        "title": "MAX and MIN", "chunk": "Formulas · =MAX and =MIN",
        "instruction": [
            "## Highest and lowest",
            "- `=MAX(B2:B6)` returns the **largest** number in a range.",
            "- `=MIN(B2:B6)` returns the **smallest** number in a range.",
            "These are perfect for finding a top score or a lowest temperature.",
            "## Practice",
            "Find the highest and lowest game scores.",
        ],
        "doc": _sdoc([_sheet("Scores", 8, 3, {"A1": "Game", "B1": "Points", "A2": "G1", "B2": "12", "A3": "G2", "B3": "27", "A4": "G3", "B4": "8", "A5": "G4", "B5": "19", "A6": "Highest", "A7": "Lowest"})]),
        "tasks": [
            _t("t1", "In B6, use =MAX(B2:B5) for the highest score", {"kind": "cell_formula", "sheet": 0, "cell": "B6", "fn": "MAX", "range": "B2:B5"}),
            _t("t2", "In B7, use =MIN(B2:B5) for the lowest score", {"kind": "cell_formula", "sheet": 0, "cell": "B7", "fn": "MIN", "range": "B2:B5"}),
            _t("t3", "B6 (highest) should equal 27", {"kind": "cell_value", "sheet": 0, "cell": "B6", "equals": 27}),
            _t("t4", "B7 (lowest) should equal 8", {"kind": "cell_value", "sheet": 0, "cell": "B7", "equals": 8}),
        ],
        "points": 100,
    },
    {
        "id": "sheets-m6", "track": "sheets", "order": 6,
        "title": "A Full Summary Row", "chunk": "Formulas · combine SUM, AVERAGE, MAX, MIN",
        "instruction": [
            "## Putting formulas together",
            "Real analysis uses several formulas side by side. Build a summary for this month's reading minutes.",
            "## Practice",
            "Fill the summary cells using the right formulas over B2:B5.",
        ],
        "doc": _sdoc([_sheet("Reading", 9, 3, {"A1": "Week", "B1": "Minutes", "A2": "W1", "B2": "120", "A3": "W2", "B3": "90", "A4": "W3", "B4": "150", "A5": "W4", "B5": "60", "A6": "Total", "A7": "Average", "A8": "Most", "A9": "Least"})]),
        "tasks": [
            _t("t1", "B6 Total: =SUM(B2:B5)", {"kind": "cell_formula", "sheet": 0, "cell": "B6", "fn": "SUM", "range": "B2:B5"}),
            _t("t2", "B7 Average: =AVERAGE(B2:B5)", {"kind": "cell_formula", "sheet": 0, "cell": "B7", "fn": "AVERAGE", "range": "B2:B5"}),
            _t("t3", "B8 Most: =MAX(B2:B5)", {"kind": "cell_formula", "sheet": 0, "cell": "B8", "fn": "MAX", "range": "B2:B5"}),
            _t("t4", "B9 Least: =MIN(B2:B5)", {"kind": "cell_formula", "sheet": 0, "cell": "B9", "fn": "MIN", "range": "B2:B5"}),
        ],
        "points": 100,
    },
    {
        "id": "sheets-m7", "track": "sheets", "order": 7,
        "title": "Sorting Data", "chunk": "Data · Sort a column",
        "instruction": [
            "## Ordering values",
            "**Sorting** puts a column in order. **Ascending (A→Z)** goes smallest to largest; **descending (Z→A)** goes largest to smallest.",
            "Click a cell in the column, then use the Sort A→Z / Z→A buttons.",
            "## Practice",
            "Sort the temperatures in column B from smallest to largest.",
        ],
        "doc": _sdoc([_sheet("Temps", 7, 2, {"B1": "Temp", "B2": "31", "B3": "12", "B4": "25", "B5": "8", "B6": "19"})]),
        "tasks": [
            _t("t1", "Sort column B (B2:B6) in ascending order (smallest → largest)", {"kind": "sorted", "sheet": 0, "col": "B", "from": 2, "to": 6, "order": "asc"}),
        ],
        "points": 100,
    },
    {
        "id": "sheets-m8", "track": "sheets", "order": 8,
        "title": "Bar Charts", "chunk": "Insert · Chart (bar)",
        "instruction": [
            "## Comparing categories",
            "A **bar chart** compares amounts across categories. Insert a chart, choose **Bar**, and give it the data range (labels + values).",
            "## Practice",
            "Chart the fruit sales below as a bar chart of A1:B4.",
        ],
        "doc": _sdoc([_sheet("Fruit", 5, 3, {"A1": "Apples", "B1": "12", "A2": "Bananas", "B2": "9", "A3": "Cherries", "B3": "15", "A4": "Dates", "B4": "6"})]),
        "tasks": [
            _t("t1", "Insert a BAR chart of the range A1:B4", {"kind": "chart_range", "type": "bar", "range": "A1:B4"}),
        ],
        "points": 100,
    },
    {
        "id": "sheets-m9", "track": "sheets", "order": 9,
        "title": "Pie Charts", "chunk": "Insert · Chart (pie)",
        "instruction": [
            "## Parts of a whole",
            "A **pie chart** shows how parts make up a whole (like percentages of a budget). Insert a chart and choose **Pie**.",
            "## Practice",
            "Show the class pet vote as a pie chart of A1:B4.",
        ],
        "doc": _sdoc([_sheet("Pets", 5, 3, {"A1": "Dogs", "B1": "10", "A2": "Cats", "B2": "8", "A3": "Fish", "B3": "5", "A4": "Birds", "B4": "3"})]),
        "tasks": [
            _t("t1", "Insert a PIE chart of the range A1:B4", {"kind": "chart_range", "type": "pie", "range": "A1:B4"}),
        ],
        "points": 100,
    },
    {
        "id": "sheets-m10", "track": "sheets", "order": 10,
        "title": "Multiple Worksheets", "chunk": "Sheets · Add & rename tabs",
        "instruction": [
            "## Organizing with worksheets",
            "A spreadsheet file can hold many **worksheets** (tabs at the bottom). Use them to separate data — e.g., one sheet per month.",
            "Use the **+** to add a sheet, and double-click a tab to **rename** it.",
            "## Practice",
            "Add a second worksheet and name it 'Summary'.",
        ],
        "doc": _sdoc([_sheet("Data", 5, 3, {"A1": "Item", "B1": "Amount"})]),
        "tasks": [
            _t("t1", "Add a second worksheet (2 sheets total)", {"kind": "sheet_count", "equals": 2}),
            _t("t2", "Name the second worksheet 'Summary'", {"kind": "sheet_named", "index": 1, "name": "Summary"}),
        ],
        "points": 100,
    },
    {
        "id": "sheets-m11", "track": "sheets", "order": 11,
        "title": "Capstone: Build a Gradebook", "chunk": "Everything · plus Export to PDF",
        "instruction": [
            "## Put it all together",
            "Build a mini gradebook: enter the data, compute a class summary with every formula, chart the scores, then **export to PDF**.",
            "## Your tasks",
            "Work the checklist top to bottom. When it's all green, download your PDF and submit.",
        ],
        "doc": _sdoc([_sheet("Gradebook", 9, 4, {"A1": "Student", "B1": "Score", "A2": "Ana", "B2": "88", "A3": "Ben", "B3": "76", "A4": "Cy", "B4": "94", "A5": "Di", "B5": "82", "A6": "Total", "A7": "Average", "A8": "Highest", "A9": "Lowest"})]),
        "tasks": [
            _t("t1", "B6 Total: =SUM(B2:B5)", {"kind": "cell_formula", "sheet": 0, "cell": "B6", "fn": "SUM", "range": "B2:B5"}),
            _t("t2", "B7 Average: =AVERAGE(B2:B5)", {"kind": "cell_formula", "sheet": 0, "cell": "B7", "fn": "AVERAGE", "range": "B2:B5"}),
            _t("t3", "B8 Highest: =MAX(B2:B5)", {"kind": "cell_formula", "sheet": 0, "cell": "B8", "fn": "MAX", "range": "B2:B5"}),
            _t("t4", "B9 Lowest: =MIN(B2:B5)", {"kind": "cell_formula", "sheet": 0, "cell": "B9", "fn": "MIN", "range": "B2:B5"}),
            _t("t5", "Insert a BAR chart of A1:B5", {"kind": "chart_range", "type": "bar", "range": "A1:B5"}),
            _t("t6", "Export the gradebook to PDF", {"kind": "exported"}),
        ],
        "points": 150,
    },
]

MISSIONS["sheets"] = SHEETS_MISSIONS


# ------------------------------ SLIDES MISSIONS ------------------------------
def _sl(sid, title="", bullets=None, layout="title-content", theme="midnight",
        image=None, chart=None, animation="none", transition="none", notes=""):
    return {"id": sid, "layout": layout, "theme": theme, "title": title,
            "bullets": bullets or [], "image": image, "chart": chart,
            "animation": animation, "transition": transition, "notes": notes}


def _pdoc(slides):
    return {"slides": slides, "activeSlide": 0}


SLIDES_MISSIONS = [
    {
        "id": "slides-m1", "track": "slides", "order": 1,
        "title": "Meet a Slide", "chunk": "Create & edit · the title slide",
        "instruction": [
            "## What is a slide?",
            "A **presentation** is a stack of **slides**. The first slide is usually a **title slide** — it names your topic and, often, who made it.",
            "- Click the big title and type your topic.",
            "- Add a **subtitle** line underneath (your name or a tagline).",
            "## Practice",
            "Give this title slide a title and a subtitle.",
        ],
        "doc": _pdoc([_sl("s0", layout="title", theme="midnight")]),
        "tasks": [
            _t("t1", "Type a title on the slide", {"kind": "slide_title_nonempty", "slide": 0}),
            _t("t2", "Add a subtitle line (1 bullet)", {"kind": "slide_bullets_min", "slide": 0, "min": 1}),
        ],
        "points": 100,
    },
    {
        "id": "slides-m2", "track": "slides", "order": 2,
        "title": "Building a Deck", "chunk": "Add slides · give each a title",
        "instruction": [
            "## Adding slides",
            "Use the **+ New slide** button to add more slides. A good deck has one clear idea per slide, and **every slide has a title** so the audience can follow along.",
            "## Practice",
            "Build a 3-slide deck where each slide has a title (e.g., Intro, Main Idea, Conclusion).",
        ],
        "doc": _pdoc([_sl("s0", layout="title")]),
        "tasks": [
            _t("t1", "Have 3 slides in the deck", {"kind": "slide_count", "equals": 3}),
            _t("t2", "Title on slide 1", {"kind": "slide_title_nonempty", "slide": 0}),
            _t("t3", "Title on slide 2", {"kind": "slide_title_nonempty", "slide": 1}),
            _t("t4", "Title on slide 3", {"kind": "slide_title_nonempty", "slide": 2}),
        ],
        "points": 100,
    },
    {
        "id": "slides-m3", "track": "slides", "order": 3,
        "title": "Bulleted Content", "chunk": "Content · body bullet points",
        "instruction": [
            "## Body content",
            "Below the title, most slides use **bullet points** — short lines that list your key points. Click the content area and press Enter for each new bullet.",
            "## Practice",
            "Add at least **3 bullet points** about your favorite hobby.",
        ],
        "doc": _pdoc([_sl("s0", title="My Favorite Hobby", layout="title-content")]),
        "tasks": [
            _t("t1", "Add at least 3 bullet points", {"kind": "slide_bullets_min", "slide": 0, "min": 3}),
        ],
        "points": 100,
    },
    {
        "id": "slides-m4", "track": "slides", "order": 4,
        "title": "The 5×5 Rule", "chunk": "Design habits · 5×5 rule",
        "instruction": [
            "## Don't crowd your slides",
            "The **5×5 rule**: use **no more than 5 bullets** per slide, and **no more than 5 words** per bullet. Slides are cue cards, not essays — you say the details out loud.",
            "## Practice",
            "This slide is way too wordy. Trim it so it follows the 5×5 rule (≤5 short bullets, ≤5 words each).",
        ],
        "doc": _pdoc([_sl("s0", title="Why Recycling Matters", layout="title-content", bullets=[
            "Recycling helps reduce the amount of waste that ends up in landfills",
            "It saves natural resources like trees water and precious minerals",
            "Recycling saves a lot of energy compared to making new products",
            "It reduces pollution in our air and in our local waterways",
            "Recycling can create brand new green jobs in our community",
            "Everyone in the whole school can help by sorting their trash",
        ])]),
        "tasks": [
            _t("t1", "Make this slide follow the 5×5 rule (≤5 bullets, ≤5 words each)", {"kind": "five_by_five", "slide": 0}),
        ],
        "points": 100,
    },
    {
        "id": "slides-m5", "track": "slides", "order": 5,
        "title": "Choosing Layouts", "chunk": "Format · slide layouts",
        "instruction": [
            "## Layouts",
            "A **layout** decides where things sit on a slide:",
            "- **Title slide** — for the opening slide.",
            "- **Title & content** — a title with bullets below.",
            "- **Two content** — two columns side by side.",
            "## Practice",
            "Set the right layout for each slide.",
        ],
        "doc": _pdoc([_sl("s0", title="Our Trip", layout="blank"), _sl("s1", title="Highlights", layout="blank"), _sl("s2", title="Compare", layout="blank")]),
        "tasks": [
            _t("t1", "Slide 1 → Title slide layout", {"kind": "slide_layout", "slide": 0, "equals": "title"}),
            _t("t2", "Slide 2 → Title & content layout", {"kind": "slide_layout", "slide": 1, "equals": "title-content"}),
            _t("t3", "Slide 3 → Two content layout", {"kind": "slide_layout", "slide": 2, "equals": "two-content"}),
        ],
        "points": 100,
    },
    {
        "id": "slides-m6", "track": "slides", "order": 6,
        "title": "Themes & Formatting", "chunk": "Format · apply a theme",
        "instruction": [
            "## Themes",
            "A **theme** sets the colors and style for your whole deck so it looks consistent and professional. Pick one that fits your topic.",
            "## Practice",
            "Apply the **Ocean** theme to this slide.",
        ],
        "doc": _pdoc([_sl("s0", title="Marine Life", layout="title-content", theme="paper", bullets=["Coral reefs", "Deep sea creatures"])]),
        "tasks": [
            _t("t1", "Apply the Ocean theme to the slide", {"kind": "slide_theme", "slide": 0, "equals": "ocean"}),
        ],
        "points": 100,
    },
    {
        "id": "slides-m7", "track": "slides", "order": 7,
        "title": "Adding Images", "chunk": "Insert · images",
        "instruction": [
            "## Pictures tell the story",
            "A good **image** makes a slide memorable. Use the **Insert Image** button and pick one from the gallery. Choose an image that matches your point.",
            "## Practice",
            "Add an image to this slide.",
        ],
        "doc": _pdoc([_sl("s0", title="Explore Space", layout="title-content", theme="midnight", bullets=["The planets", "Our solar system"])]),
        "tasks": [
            _t("t1", "Insert an image on the slide", {"kind": "slide_has_image", "slide": 0}),
        ],
        "points": 100,
    },
    {
        "id": "slides-m8", "track": "slides", "order": 8,
        "title": "Charts on Slides", "chunk": "Insert · charts",
        "instruction": [
            "## Show the data",
            "A **chart** turns numbers into a picture your audience understands instantly. Insert a **bar chart** to compare amounts.",
            "## Practice",
            "Add a bar chart to this slide.",
        ],
        "doc": _pdoc([_sl("s0", title="Our Reading Data", layout="title-content", theme="paper", bullets=["Books read this month"])]),
        "tasks": [
            _t("t1", "Insert a BAR chart on the slide", {"kind": "slide_has_chart", "slide": 0, "type": "bar"}),
        ],
        "points": 100,
    },
    {
        "id": "slides-m9", "track": "slides", "order": 9,
        "title": "Animations", "chunk": "Animate · build effects",
        "instruction": [
            "## Bring content in",
            "An **animation** controls how content appears — like a **Fade in** or **Fly in**. Used lightly, it keeps the audience focused on one point at a time. Don't overdo it!",
            "## Practice",
            "Add a build animation (any except None) to this slide's content.",
        ],
        "doc": _pdoc([_sl("s0", title="Big Reveal", layout="title-content", theme="midnight", bullets=["Point one", "Point two"])]),
        "tasks": [
            _t("t1", "Apply an animation to the slide content", {"kind": "slide_animation", "slide": 0}),
        ],
        "points": 100,
    },
    {
        "id": "slides-m10", "track": "slides", "order": 10,
        "title": "Transitions", "chunk": "Deliver · slide transitions",
        "instruction": [
            "## Moving between slides",
            "A **transition** is the effect when you move from one slide to the next (like **Fade** or **Slide**). It makes your delivery feel smooth and polished.",
            "## Practice",
            "Add a transition (any except None) to this slide.",
        ],
        "doc": _pdoc([_sl("s0", title="Smooth Moves", layout="title-content", theme="sunrise", bullets=["Transitions connect ideas"])]),
        "tasks": [
            _t("t1", "Apply a transition to the slide", {"kind": "slide_transition", "slide": 0}),
        ],
        "points": 100,
    },
    {
        "id": "slides-m11", "track": "slides", "order": 11,
        "title": "Speaker Notes", "chunk": "Deliver · speaker notes",
        "instruction": [
            "## What you'll say",
            "**Speaker notes** are the words you plan to say for a slide — the audience doesn't see them. Great presenters put details in the notes and keep the slide itself clean (remember 5×5!).",
            "## Practice",
            "Write speaker notes (at least 8 words) for what you'd say on this slide.",
        ],
        "doc": _pdoc([_sl("s0", title="My Big Idea", layout="title-content", theme="ocean", bullets=["Keep the slide simple", "Say the rest out loud"])]),
        "tasks": [
            _t("t1", "Write speaker notes of at least 8 words", {"kind": "slide_notes_min_words", "slide": 0, "min": 8}),
        ],
        "points": 100,
    },
    {
        "id": "slides-m12", "track": "slides", "order": 12,
        "title": "Capstone: Build & Present a Deck", "chunk": "Everything · plus Export to PDF",
        "instruction": [
            "## Put it all together",
            "Build a short, polished 3-slide deck that uses every skill: a themed title slide, a clean 5×5 content slide, an image, a chart, an animation, a transition, and speaker notes. Then **export it to PDF**.",
            "## Your tasks",
            "Work the checklist. When it's all green, export your PDF and submit.",
        ],
        "doc": _pdoc([
            _sl("s0", layout="title", theme="paper"),
            _sl("s1", title="Key Points", layout="title-content", theme="paper"),
            _sl("s2", title="The Evidence", layout="title-content", theme="paper"),
        ]),
        "tasks": [
            _t("t1", "Have 3 slides", {"kind": "slide_count", "equals": 3}),
            _t("t2", "Give the title slide a title", {"kind": "slide_title_nonempty", "slide": 0}),
            _t("t3", "Apply the Midnight theme to the title slide", {"kind": "slide_theme", "slide": 0, "equals": "midnight"}),
            _t("t4", "Make slide 2 follow the 5×5 rule", {"kind": "five_by_five", "slide": 1}),
            _t("t5", "Add an image to slide 3", {"kind": "slide_has_image", "slide": 2}),
            _t("t6", "Add a bar chart to slide 3", {"kind": "slide_has_chart", "slide": 2, "type": "bar"}),
            _t("t7", "Animate slide 2's content", {"kind": "slide_animation", "slide": 1}),
            _t("t8", "Add a transition to the title slide", {"kind": "slide_transition", "slide": 0}),
            _t("t9", "Write speaker notes (8+ words) on the title slide", {"kind": "slide_notes_min_words", "slide": 0, "min": 8}),
            _t("t10", "Export the deck to PDF", {"kind": "exported"}),
        ],
        "points": 150,
    },
]

MISSIONS["slides"] = SLIDES_MISSIONS


# ------------------------------ EMAIL STUDIO ------------------------------
STUDENT_EMAIL = "you@horizonmiddle.edu"

EMAIL_CONFIG = {
    "studentEmail": STUDENT_EMAIL,
    "fileLibrary": ["Field Trip Form.pdf", "Science Report.docx", "Team Roster.xlsx", "Project Slides.pdf", "Event Flyer.png", "Resume.pdf"],
    "signature": "\n\n—\nJordan Rivera\nHorizon Middle School",
    "types": [
        {"id": "formal", "name": "Formal", "desc": "For people you don't know well or in authority (principal, employer). Full greeting & closing, no slang."},
        {"id": "professional", "name": "Professional", "desc": "Workplace tone — clear, polite, to the point (manager, coworker, client)."},
        {"id": "semiformal", "name": "Semi-formal", "desc": "For teachers/coaches you know — polite but a little warmer."},
        {"id": "informal", "name": "Informal", "desc": "For friends & classmates — casual and friendly."},
    ],
}
TRACK_CONFIG["email"] = EMAIL_CONFIG

TRACKS["email"] = {"id": "email", "name": "Email & Communication", "subtitle": "Gmail · Outlook · professional email",
                   "standard": "PA.2.D", "color": "#818CF8",
                   "intro": "Locate, read, reply, forward, and write professional emails — with etiquette coached by AI."}


def _msg(mid, folder, from_name, from_email, subject, body, to=None, cc=None, bcc=None,
         read=False, kind="seed", attachments=None, in_reply_to=None,
         has_bold=False, has_bullets=False, has_signature=False, date="Aug 21", external=False):
    return {"id": mid, "folder": folder, "fromName": from_name, "fromEmail": from_email,
            "to": to or [STUDENT_EMAIL], "cc": cc or [], "bcc": bcc or [], "subject": subject,
            "body": body, "attachments": attachments or [], "read": read, "kind": kind,
            "inReplyTo": in_reply_to, "hasBold": has_bold, "hasBullets": has_bullets, "hasSignature": has_signature,
            "date": date, "external": external, "bodyStudent": None}


def _edoc(messages):
    return {"messages": messages, "searched": False}


def _ai(tid, label, dim):
    return {"id": tid, "label": label, "check": {"kind": "ai", "dim": dim}, "hint": "Graded by the AI Coach on submit"}


EMAIL_MISSIONS = [
    {
        "id": "email-b1", "track": "email", "order": 1, "title": "Whose Email Is It?", "chunk": "Locate · find the right sender",
        "instruction": ["## Not every message is from a person", "Your inbox mixes real people with **automatic notices** (like **Google Classroom** or the school store). Read the **sender name** and **email address** to find who really wrote to you.",
                        "## Practice", "Open the email your teacher **Mr. Diaz** sent you — not the Google Classroom notice."],
        "doc": _edoc([
            _msg("gc", "inbox", "Google Classroom", "no-reply@classroom.google.com", "New assignment posted", "An assignment was posted in your class. Do not reply to this message."),
            _msg("store", "inbox", "School Store", "store@horizonmiddle.edu", "Spirit wear sale!", "Hoodies are 20% off this week."),
            _msg("teacher", "inbox", "Mr. Diaz", "mr.diaz@horizonmiddle.edu", "Reading homework for tonight", "Please read chapter 4 tonight and answer question 2. — Mr. Diaz"),
        ]),
        "tasks": [{"id": "t1", "label": "Open the email your teacher Mr. Diaz sent (not Google Classroom)", "check": {"kind": "email_opened", "id": "teacher"}}],
        "points": 100,
    },
    {
        "id": "email-b2", "track": "email", "order": 2, "title": "Reading the Address Lines", "chunk": "Identify · From, To, Cc & Bcc",
        "instruction": ["## Who's on an email?", "- **From** — who sent it.", "- **To** — the main person it's for.", "- **Cc** — others who got a copy.", "- **Bcc** — a *hidden* copy (normally other people can't see this line).",
                        "In the reading pane you can **click an address** to identify it. We've shown the Bcc line here so you can learn to spot every part.", "## Practice", "Open the email from Ms. Lee, then click the address on the **To**, **Cc**, and **Bcc** lines to find each part."],
        "doc": _edoc([_msg("e1", "inbox", "Ms. Lee", "ms.lee@horizonmiddle.edu", "Group project update", "Here is the update for our group project.", to=[STUDENT_EMAIL], cc=["alex@horizonmiddle.edu", "jamie@horizonmiddle.edu"], bcc=["principal@horizonmiddle.edu"])]),
        "tasks": [
            {"id": "t1", "label": "Open the email from Ms. Lee", "check": {"kind": "email_opened", "id": "e1"}},
            {"id": "t2", "label": "Click the address on the To line", "check": {"kind": "picked", "field": "to"}},
            {"id": "t3", "label": "Click an address on the Cc line", "check": {"kind": "picked", "field": "cc"}},
            {"id": "t4", "label": "Click the address on the Bcc line", "check": {"kind": "picked", "field": "bcc"}},
        ],
        "points": 100,
    },
    {
        "id": "email-m1", "track": "email", "order": 3, "title": "Meet Your Inbox", "chunk": "Locate & open · parts of an email",
        "instruction": ["## Your inbox", "The **Inbox** holds emails you receive. Each row shows the **sender**, the **subject**, and a preview. A dot means **unread**.",
                        "- Click an email to **open** and read it.", "## Practice", "Open the two emails in your inbox."],
        "doc": _edoc([
            _msg("e1", "inbox", "Coach Rivera", "coach.rivera@horizonmiddle.edu", "Basketball tryouts Friday", "Tryouts are Friday at 3pm in the gym. Bring water and sneakers.\nCoach Rivera"),
            _msg("e2", "inbox", "Ms. Lee", "ms.lee@horizonmiddle.edu", "Science project reminder", "Don't forget your science project is due next Tuesday.\nMs. Lee"),
        ]),
        "tasks": [
            {"id": "t1", "label": "Open the email from Coach Rivera", "check": {"kind": "email_opened", "id": "e1"}},
            {"id": "t2", "label": "Open the email from Ms. Lee", "check": {"kind": "email_opened", "id": "e2"}},
        ], "points": 100,
    },
    {
        "id": "email-m2", "track": "email", "order": 4, "title": "Searching Your Inbox", "chunk": "Locate · search",
        "instruction": ["## Finding an email fast", "When your inbox is full, use the **Search** bar to find an email by sender or keyword instead of scrolling.",
                        "## Practice", "Use search to find the email about the field trip, then open it."],
        "doc": _edoc([
            _msg("e1", "inbox", "Mr. Diaz", "mr.diaz@horizonmiddle.edu", "Field trip permission form", "Please return the attached field trip form by Friday.", attachments=[{"name": "Field Trip Form.pdf"}]),
            _msg("e2", "inbox", "Library", "library@horizonmiddle.edu", "Book due soon", "Your library book is due in 3 days."),
            _msg("e3", "inbox", "Art Club", "art.club@horizonmiddle.edu", "Meeting moved", "Art club moves to Thursday this week."),
        ]),
        "tasks": [
            {"id": "t1", "label": "Use the search bar to search your inbox", "check": {"kind": "searched"}},
            {"id": "t2", "label": "Open the field trip email from Mr. Diaz", "check": {"kind": "email_opened", "id": "e1"}},
        ], "points": 100,
    },
    {
        "id": "email-m3", "track": "email", "order": 5, "title": "Replying to an Email", "chunk": "Reply · Re: subject, greeting & sign-off",
        "instruction": ["## Replying", "**Reply** answers the sender. The subject keeps a **Re:** so they know it's a response.",
                        "- Start with a **greeting** (Dear/Hi + name).", "- End with a **sign-off** (Thanks/Sincerely + your name).",
                        "## Practice", "Reply to Ms. Lee. Keep the Re: subject, and include a greeting and a sign-off."],
        "doc": _edoc([_msg("e1", "inbox", "Ms. Lee", "ms.lee@horizonmiddle.edu", "Are you joining the study group?", "Hi! We meet Wednesday after school. Can you come?", read=True)]),
        "tasks": [
            {"id": "t1", "label": "Send a Reply to Ms. Lee", "check": {"kind": "sent_exists", "sentKind": "reply"}},
            {"id": "t2", "label": "Keep the subject starting with 'Re:'", "check": {"kind": "subject_prefix", "sentKind": "reply", "prefix": "Re:"}},
            {"id": "t3", "label": "Include a greeting (Dear/Hi/Hello)", "check": {"kind": "has_greeting", "sentKind": "reply"}},
            {"id": "t4", "label": "Include a sign-off (Thanks/Sincerely + name)", "check": {"kind": "has_signoff", "sentKind": "reply"}},
            {"id": "t5", "label": "Write a real message of your own (12+ words)", "check": {"kind": "body_min_words", "sentKind": "reply", "min": 12}},
        ], "points": 100,
    },
    {
        "id": "email-m4", "track": "email", "order": 6, "title": "Reply vs Reply All", "chunk": "Reply-All · keep everyone in the loop",
        "instruction": ["## Reply All", "**Reply All** answers the sender **and** everyone who was on the email (the CC list). Use it when the whole group needs your answer — but don't overuse it!",
                        "## Practice", "This group email needs everyone to see your answer. Use **Reply All** so the CC'd teammates stay in the loop."],
        "doc": _edoc([_msg("e1", "inbox", "Sam (Group Lead)", "sam@horizonmiddle.edu", "Project meeting time?", "Team, what time works for our project meeting?",
                          cc=["alex@horizonmiddle.edu", "jamie@horizonmiddle.edu"], read=True)]),
        "tasks": [
            {"id": "t1", "label": "Use Reply All", "check": {"kind": "sent_exists", "sentKind": "replyall"}},
            {"id": "t2", "label": "Keep the teammates on CC (alex & jamie)", "check": {"kind": "cc_min", "sentKind": "replyall", "min": 2}},
            {"id": "t3", "label": "Keep the 'Re:' subject", "check": {"kind": "subject_prefix", "sentKind": "replyall", "prefix": "Re:"}},
            {"id": "t4", "label": "Start with a greeting (Dear/Hi/Hello)", "check": {"kind": "has_greeting", "sentKind": "replyall"}},
            {"id": "t5", "label": "End with a sign-off (Thanks/Sincerely + name)", "check": {"kind": "has_signoff", "sentKind": "replyall"}},
            {"id": "t6", "label": "Write a real message of your own (12+ words)", "check": {"kind": "body_min_words", "sentKind": "replyall", "min": 12}},
        ], "points": 100,
    },
    {
        "id": "email-m5", "track": "email", "order": 7, "title": "Forwarding an Email", "chunk": "Forward · Fwd: to a new person",
        "instruction": ["## Forwarding", "**Forward** sends an email you received to **someone new**. The subject gets a **Fwd:**. Add a short note explaining why you're forwarding it.",
                        "## Practice", "Forward Coach's schedule to your teammate at alex@horizonmiddle.edu with a short note."],
        "doc": _edoc([_msg("e1", "inbox", "Coach Rivera", "coach.rivera@horizonmiddle.edu", "Game schedule", "Here is the game schedule for this month. Games are Tuesdays and Thursdays.", read=True)]),
        "tasks": [
            {"id": "t1", "label": "Forward the email", "check": {"kind": "sent_exists", "sentKind": "forward"}},
            {"id": "t2", "label": "Send it to alex@horizonmiddle.edu", "check": {"kind": "to_includes", "sentKind": "forward", "email": "alex@horizonmiddle.edu"}},
            {"id": "t3", "label": "Keep the 'Fwd:' subject", "check": {"kind": "subject_prefix", "sentKind": "forward", "prefix": "Fwd:"}},
            {"id": "t4", "label": "Start with a greeting (Dear/Hi/Hello)", "check": {"kind": "has_greeting", "sentKind": "forward"}},
            {"id": "t5", "label": "Add a real note of your own (12+ words) explaining why you're forwarding it", "check": {"kind": "body_min_words", "sentKind": "forward", "min": 12}},
            {"id": "t6", "label": "End with a sign-off (Thanks/Sincerely + name)", "check": {"kind": "has_signoff", "sentKind": "forward"}},
        ], "points": 100,
    },
    {
        "id": "email-m6", "track": "email", "order": 8, "title": "Composing a New Email", "chunk": "Compose · To, subject, greeting & body",
        "instruction": ["## Writing a new email", "Click **Compose** to start fresh. Fill the **To** field, write a clear **Subject**, then a greeting, your message, and a sign-off.",
                        "## Practice", "Write a new email to ms.lee@horizonmiddle.edu asking about the homework you missed."],
        "doc": _edoc([]),
        "tasks": [
            {"id": "t1", "label": "Compose a new email", "check": {"kind": "sent_exists", "sentKind": "new"}},
            {"id": "t2", "label": "Send it to ms.lee@horizonmiddle.edu", "check": {"kind": "to_includes", "sentKind": "new", "email": "ms.lee@horizonmiddle.edu"}},
            {"id": "t3", "label": "Write a subject line", "check": {"kind": "subject_nonempty", "sentKind": "new"}},
            {"id": "t4", "label": "Include a greeting and a sign-off", "check": {"kind": "has_greeting_signoff", "sentKind": "new"}},
            {"id": "t5", "label": "Write a real message of your own (12+ words)", "check": {"kind": "body_min_words", "sentKind": "new", "min": 12}},
        ], "points": 100,
    },
    {
        "id": "email-m7", "track": "email", "order": 9, "title": "To, CC, and BCC", "chunk": "Recipients · the right field for each person",
        "instruction": ["## To, CC, BCC", "- **To**: the main person who must act.", "- **CC** (carbon copy): people who should **see** it, for their info.",
                        "- **BCC**: hidden copy — others can't see this address.", "## Practice", "Email your teacher (ms.lee@…) in **To**, CC the principal (principal@horizonmiddle.edu), and BCC yourself (you@horizonmiddle.edu)."],
        "doc": _edoc([]),
        "tasks": [
            {"id": "t1", "label": "To: ms.lee@horizonmiddle.edu", "check": {"kind": "to_includes", "sentKind": "new", "email": "ms.lee@horizonmiddle.edu"}},
            {"id": "t2", "label": "CC: principal@horizonmiddle.edu", "check": {"kind": "cc_includes", "sentKind": "new", "email": "principal@horizonmiddle.edu"}},
            {"id": "t3", "label": "BCC: you@horizonmiddle.edu", "check": {"kind": "bcc_includes", "sentKind": "new", "email": "you@horizonmiddle.edu"}},
            {"id": "t4", "label": "Write a subject line", "check": {"kind": "subject_nonempty", "sentKind": "new"}},
            {"id": "t5", "label": "Include a greeting and a sign-off", "check": {"kind": "has_greeting_signoff", "sentKind": "new"}},
            {"id": "t6", "label": "Write a real message of your own (12+ words)", "check": {"kind": "body_min_words", "sentKind": "new", "min": 12}},
        ], "points": 100,
    },
    {
        "id": "email-m8", "track": "email", "order": 10, "title": "Attachments", "chunk": "Attach · send a file",
        "instruction": ["## Attaching a file", "An **attachment** is a file you send with your email (a form, report, or photo). Use the **Attach** button and pick a file, then say in the body what you attached.",
                        "## Practice", "Reply to Mr. Diaz and attach the 'Field Trip Form.pdf'."],
        "doc": _edoc([_msg("e1", "inbox", "Mr. Diaz", "mr.diaz@horizonmiddle.edu", "Field trip form needed", "Please send back your signed field trip form.", read=True)]),
        "tasks": [
            {"id": "t1", "label": "Reply to Mr. Diaz", "check": {"kind": "sent_exists", "sentKind": "reply"}},
            {"id": "t2", "label": "Attach 'Field Trip Form.pdf'", "check": {"kind": "has_attachment", "sentKind": "reply", "name": "Field Trip Form.pdf"}},
            {"id": "t3", "label": "Write a real message (12+ words) that mentions the attachment", "check": {"kind": "body_min_words", "sentKind": "reply", "min": 12}},
            {"id": "t4", "label": "Start with a greeting (Dear/Hi/Hello)", "check": {"kind": "has_greeting", "sentKind": "reply"}},
            {"id": "t5", "label": "End with a sign-off (Thanks/Sincerely + name)", "check": {"kind": "has_signoff", "sentKind": "reply"}},
        ], "points": 100,
    },
    {
        "id": "email-m9", "track": "email", "order": 11, "title": "Formatting Emails", "chunk": "Format · bold, bullets & signature",
        "instruction": ["## Making emails easy to read", "- **Bold** important details (dates, times).", "- Use **bullets** for lists.", "- Add a **signature** with your name at the end.",
                        "## Practice", "Compose an email to your team (team@horizonmiddle.edu) with a bold detail, a bulleted list, and a signature."],
        "doc": _edoc([]),
        "tasks": [
            {"id": "t1", "label": "Compose to team@horizonmiddle.edu", "check": {"kind": "to_includes", "sentKind": "new", "email": "team@horizonmiddle.edu"}},
            {"id": "t2", "label": "Bold at least one detail", "check": {"kind": "formatting", "sentKind": "new", "feature": "bold"}},
            {"id": "t3", "label": "Use a bulleted list", "check": {"kind": "formatting", "sentKind": "new", "feature": "bullets"}},
            {"id": "t4", "label": "Add a signature", "check": {"kind": "formatting", "sentKind": "new", "feature": "signature"}},
            {"id": "t5", "label": "Start with a greeting (Dear/Hi/Hello)", "check": {"kind": "has_greeting", "sentKind": "new"}},
            {"id": "t6", "label": "Write a real message of your own (12+ words)", "check": {"kind": "body_min_words", "sentKind": "new", "min": 12}},
        ], "points": 100,
    },
    {
        "id": "email-m10", "track": "email", "order": 12, "title": "Etiquette & Tone", "chunk": "Etiquette · polite, professional writing (AI-graded)",
        "instruction": ["## Email etiquette", "Good emails are **polite, clear, and match the reader**. Use a proper greeting, no slang or ALL CAPS, be respectful, and proofread for **grammar & spelling**.",
                        "## Practice", "Write a **professional** email to your internship mentor (mentor@company.com) thanking them and asking one good question about your project.",
                        "Your **tone, etiquette, and grammar** will be graded by the AI Coach."],
        "doc": _edoc([]), "ai_target": {"sentKind": "new", "register": "professional", "recipient": "an internship mentor at a company"},
        "tasks": [
            {"id": "t1", "label": "Compose to mentor@company.com with a subject", "check": {"kind": "subject_and_to", "sentKind": "new", "email": "mentor@company.com"}},
            _ai("t2", "Professional, respectful tone for a mentor", "tone"),
            _ai("t3", "Good email etiquette (greeting, closing, no slang)", "etiquette"),
            _ai("t4", "Correct grammar & spelling", "grammar"),
            {"id": "t5", "label": "Start with a proper greeting", "check": {"kind": "has_greeting", "sentKind": "new"}},
            {"id": "t6", "label": "End with a proper sign-off", "check": {"kind": "has_signoff", "sentKind": "new"}},
            {"id": "t7", "label": "Write a real message of your own (12+ words)", "check": {"kind": "body_min_words", "sentKind": "new", "min": 12}},
        ], "points": 120,
    },
    {
        "id": "email-m11", "track": "email", "order": 13, "title": "Email Types & Registers", "chunk": "Formal · Professional · Semi-formal · Informal (AI-graded)",
        "instruction": ["## Match your tone to the reader", "- **Formal** — principal, employer: full greeting/closing, no slang.", "- **Professional** — manager, client: clear and polite.",
                        "- **Semi-formal** — a teacher you know: polite but warmer.", "- **Informal** — a friend: casual.",
                        "## Practice", "Write a **formal** email to the principal (principal@horizonmiddle.edu) requesting permission to start a new club. The AI Coach grades tone, etiquette, and grammar."],
        "doc": _edoc([]), "ai_target": {"sentKind": "new", "register": "formal", "recipient": "the school principal (a formal authority figure)"},
        "tasks": [
            {"id": "t1", "label": "Compose to principal@horizonmiddle.edu with a subject", "check": {"kind": "subject_and_to", "sentKind": "new", "email": "principal@horizonmiddle.edu"}},
            {"id": "t2", "label": "Include a formal greeting & closing", "check": {"kind": "has_greeting_signoff", "sentKind": "new"}},
            _ai("t3", "Correctly formal tone for a principal", "tone"),
            _ai("t4", "Strong etiquette (respectful, clear request)", "etiquette"),
            _ai("t5", "Correct grammar & spelling", "grammar"),
            {"id": "t6", "label": "Write a real message of your own (12+ words)", "check": {"kind": "body_min_words", "sentKind": "new", "min": 12}},
        ], "points": 120,
    },
    {
        "id": "email-m12", "track": "email", "order": 14, "title": "Capstone: Manage Your Morning Inbox", "chunk": "Everything · locate, reply, forward, compose (AI-graded)",
        "instruction": ["## Clear your inbox like a pro", "Handle three real situations: reply to your manager professionally, forward an update to a coworker, and compose a new email with an attachment.",
                        "## Your tasks", "Work the checklist. The reply's tone, etiquette, and grammar are graded by the AI Coach."],
        "doc": _edoc([
            _msg("e1", "inbox", "Manager Kim", "kim@company.com", "Can you send the weekly report?", "Hi, could you send me this week's report by end of day? Thanks, Kim", read=False),
            _msg("e2", "inbox", "IT Help", "it@company.com", "System update tonight", "The system will update tonight at 9pm. Save your work.", read=False),
        ]),
        "ai_target": {"sentKind": "reply", "register": "professional", "recipient": "your manager at work"},
        "tasks": [
            {"id": "t1", "label": "Open the email from Manager Kim", "check": {"kind": "email_opened", "id": "e1"}},
            {"id": "t2", "label": "Reply to Manager Kim (keep Re:)", "check": {"kind": "subject_prefix", "sentKind": "reply", "prefix": "Re:"}},
            {"id": "t3", "label": "Attach the 'Science Report.docx' to your reply", "check": {"kind": "has_attachment", "sentKind": "reply"}},
            {"id": "t4", "label": "Forward the IT update to alex@company.com", "check": {"kind": "to_includes", "sentKind": "forward", "email": "alex@company.com"}},
            {"id": "t5", "label": "Compose a new email to coworker@company.com with a subject", "check": {"kind": "subject_and_to", "sentKind": "new", "email": "coworker@company.com"}},
            _ai("t6", "Professional tone in your reply to your manager", "tone"),
            _ai("t7", "Good etiquette across your emails", "etiquette"),
            _ai("t8", "Correct grammar & spelling", "grammar"),
            {"id": "t9", "label": "Start your reply with a greeting", "check": {"kind": "has_greeting", "sentKind": "reply"}},
            {"id": "t10", "label": "End your reply with a sign-off", "check": {"kind": "has_signoff", "sentKind": "reply"}},
            {"id": "t11", "label": "Write a real reply message of your own (12+ words)", "check": {"kind": "body_min_words", "sentKind": "reply", "min": 12}},
        ], "points": 150,
    },
]

MISSIONS["email"] = EMAIL_MISSIONS

# Realistic "filler" inbox mail so every mission's inbox looks full (~10 emails), like a real inbox.
_FILLER_POOL = [
    {"fromName": "Little SIS Premium", "fromEmail": "no-reply@littlesis.net", "subject": "Little SIS updated your Google Classroom", "body": "Little SIS has made updates to your Google Classroom roster. No action is needed on your part.", "external": True, "date": "1:06 PM", "read": True},
    {"fromName": "Yearbook Club", "fromEmail": "yearbook@horizonmiddle.edu", "subject": "Last chance for baby photos", "body": "Send in your baby photo for the yearbook by Friday! Email it as an attachment to this address.", "external": False, "date": "Aug 21", "read": True},
    {"fromName": "Cafeteria", "fromEmail": "cafeteria@horizonmiddle.edu", "subject": "Next week's lunch menu", "body": "Here is the lunch menu for next week. Pizza is on Wednesday and taco day is Friday!", "external": False, "date": "Aug 20", "read": True},
    {"fromName": "Picture Day", "fromEmail": "orders@lifetouch.com", "subject": "Order your school pictures", "body": "School pictures are ready to order online. Use your student order code from the flyer.", "external": True, "date": "Aug 20", "read": True},
    {"fromName": "Band Director", "fromEmail": "band@horizonmiddle.edu", "subject": "Rehearsal moved to Room 12", "body": "Today's rehearsal is in Room 12 instead of the band hall. Bring your folder and a pencil.", "external": False, "date": "Aug 19", "read": True},
    {"fromName": "Student Council", "fromEmail": "stuco@horizonmiddle.edu", "subject": "Vote for spirit week themes", "body": "Cast your vote for next month's spirit week themes in the form linked in this email.", "external": False, "date": "Aug 19", "read": True},
    {"fromName": "Nurse Patterson", "fromEmail": "nurse@horizonmiddle.edu", "subject": "Updated health forms due", "body": "Please remind your family that updated health forms are due by the end of the month.", "external": False, "date": "Aug 18", "read": True},
    {"fromName": "Google Workspace", "fromEmail": "no-reply@google.com", "subject": "A security tip for your account", "body": "Keep your account safe. Never share your password with anyone, even a friend.", "external": True, "date": "Aug 18", "read": True},
    {"fromName": "PE Coach", "fromEmail": "pe@horizonmiddle.edu", "subject": "Bring sneakers on Thursday", "body": "We have the fitness challenge on Thursday. Don't forget to bring your sneakers to class.", "external": False, "date": "Aug 17", "read": True},
    {"fromName": "Library", "fromEmail": "library@horizonmiddle.edu", "subject": "Your hold is ready to pick up", "body": "The book you placed on hold is ready at the front desk. Please pick it up within three days.", "external": False, "date": "Aug 16", "read": True},
]


def _pad_inboxes(target=10):
    """Append filler inbox mail to each email mission so the inbox feels realistically full."""
    for m in EMAIL_MISSIONS:
        msgs = m["doc"]["messages"]
        idx = 0
        while len(msgs) < target and idx < len(_FILLER_POOL):
            f = _FILLER_POOL[idx]
            idx += 1
            msgs.append(_msg(f"fill-{m['id']}-{idx}", "inbox", f["fromName"], f["fromEmail"], f["subject"],
                             f["body"], read=f["read"], date=f["date"], external=f["external"]))


_pad_inboxes()

# ------------------------------ BLOCK TASKS (cumulative, before each checkpoint) ------------------------------
# One hands-on task per block: ~80% of that block's skills + ~20% review of earlier blocks.
_B1_LINES = [
    "Study Guide: The Solar System", "The Sun is the star at the center of our solar system.",
    "Mercury is the smallest planet and the closest to the Sun.", "Venus is the hottest planet because of its thick atmosphere.",
    "Earth is the only planet known to support life.", "Mars is called the Red Planet because of its rusty soil.",
    "Jupiter is the largest planet in the solar system.", "Saturn is famous for its bright, icy rings.",
    "Uranus rotates on its side as it orbits the Sun.", "Neptune is the farthest planet and very windy.",
    "A comet is a ball of ice and dust with a glowing tail.", "The Moon orbits Earth about once every 27 days.",
    "Key term: an orbit is the path one object takes around another.",
]
_B2_LINES = [
    "Science Club Open House", "All Explorers and families are welcome!",
    "Join us after school in Room 210 for a night of discovery.", "Here is what you can look forward to:",
    "Build and launch a paper rocket", "Watch a safe chemistry color-change demo",
    "Meet the Science Club officers and mentors", "Enjoy free snacks and door prizes",
    "Take home a mini experiment kit", "Space is limited this year.",
    "Please arrive by 3:15 so we can start on time.", "Parking is available in the west lot.",
    "RSVP here to save your spot",
]
_B3_LINES = [
    "Book Report: Hatchet", "By Gary Paulsen",
    "I recieve a lot of enjoyment from this exciting survival story.",
    "The main character must learn to live in a seperate, wild place.",
    "Add a 3x3 table below to compare the setting, characters, and theme.",
    "Finish by proofreading and exporting your report to PDF.",
]

DOCS_BLOCK_TASKS = [
    {
        "id": "docs-task1", "track": "docs", "order": 4.5, "is_block_task": True, "block_cp": "docs-cp1",
        "title": "Block 1 Task · Format a Study Guide",
        "chunk": "Apply Block 1 many times · Emphasis, Fonts, Size & Color",
        "instruction": [
            "## Block Task — real practice",
            "Format this study guide using **Block 1** skills, and use each skill **many times** — that repetition is how it sticks.",
            "You must pass this task to unlock the Checkpoint.",
        ],
        "doc": _doc([_b(f"b{i}", t) for i, t in enumerate(_B1_LINES, 1)]),
        "tasks": [
            _t("t1", "Use bold, italic, or underline on at least 10 lines", {"kind": "fmt_count", "attrs": ["bold", "italic", "underline"], "equals": True, "min": 10}),
            _t("t2", "Change the font (not Arial) on at least 10 lines", {"kind": "fmt_count", "attr": "fontFamily", "not_equals": "Arial", "min": 10}),
            _t("t3", "Change the font size on at least 6 lines", {"kind": "fmt_count", "attr": "fontSize", "not_equals": 11, "min": 6}),
            _t("t4", "Add text color to at least 4 lines", {"kind": "fmt_count", "attr": "color", "not_equals": "#0f172a", "min": 4}),
        ],
        "points": 150,
    },
    {
        "id": "docs-task2", "track": "docs", "order": 8.5, "is_block_task": True, "block_cp": "docs-cp2",
        "title": "Block 2 Task · Build an Event Flyer",
        "chunk": "Apply Block 2 many times · Alignment, Spacing, Lists & Links (+ review)",
        "instruction": [
            "## Block Task — real practice",
            "Use **Block 2** skills repeatedly — **alignment**, **line spacing**, **lists**, and a **hyperlink**. A few steps **review Block 1**.",
            "You must pass this task to unlock the Checkpoint.",
        ],
        "doc": _doc([_b(f"b{i}", t) for i, t in enumerate(_B2_LINES, 1)]),
        "tasks": [
            _t("t1", "Align at least 10 lines (center, right, or justify)", {"kind": "fmt_count", "attr": "align", "not_equals": "left", "min": 10}),
            _t("t2", "Change line spacing on at least 8 lines", {"kind": "fmt_count", "attr": "lineSpacing", "not_equals": 1.0, "min": 8}),
            _t("t3", "Turn at least 8 lines into list items (bulleted or numbered)", {"kind": "type_count", "types": ["bullet", "number"], "min": 8}),
            _t("t4", "Add a hyperlink on the RSVP line", {"kind": "link", "block": f"b{len(_B2_LINES)}"}),
            _t("t5", "Review: use bold/italic/underline on at least 4 lines", {"kind": "fmt_count", "attrs": ["bold", "italic", "underline"], "equals": True, "min": 4}),
            _t("t6", "Review: add text color to at least 2 lines", {"kind": "fmt_count", "attr": "color", "not_equals": "#0f172a", "min": 2}),
        ],
        "points": 150,
    },
    {
        "id": "docs-task3", "track": "docs", "order": 12.5, "is_block_task": True, "block_cp": "docs-cp3",
        "title": "Block 3 Task · Finish a Book Report",
        "chunk": "Apply Block 3 · Find & Replace, Tables, Headers/Footers, Export (+ review)",
        "instruction": [
            "## Block Task — real practice",
            "Use **Block 3** skills — **find & replace**, **tables**, **headers/footers with page numbers**, and **export to PDF**. A few steps **review earlier blocks**.",
            "You must pass this task to unlock the Checkpoint.",
        ],
        "doc": _doc([_b(f"b{i}", t) for i, t in enumerate(_B3_LINES, 1)]),
        "tasks": [
            _t("t1", "Fix the spelling: replace 'recieve' with 'receive'", {"kind": "text_replaced", "block": "b3", "remove": "recieve", "add": "receive"}),
            _t("t2", "Fix the spelling: replace 'seperate' with 'separate'", {"kind": "text_replaced", "block": "b4", "remove": "seperate", "add": "separate"}),
            _t("t3", "Insert a 3-column, 3-row table", {"kind": "table", "cols": 3, "rows": 3}),
            _t("t4", "Type a heading in the first table cell", {"kind": "table_cell_filled", "row": 0, "col": 0}),
            _t("t5", "Add a header that says 'Book Report'", {"kind": "header_contains", "value": "Book Report"}),
            _t("t6", "Add page numbers in the footer", {"kind": "footer_pagenum"}),
            _t("t7", "Export the finished report to PDF", {"kind": "exported"}),
            _t("t8", "Review: align at least 3 lines (center the title, etc.)", {"kind": "fmt_count", "attr": "align", "not_equals": "left", "min": 3}),
            _t("t9", "Review: use bold/italic/underline on at least 3 lines", {"kind": "fmt_count", "attrs": ["bold", "italic", "underline"], "equals": True, "min": 3}),
        ],
        "points": 150,
    },
]

# ------------------------------ SKILL DRILLS (single-skill repetition) ------------------------------
_DRILL_LINES = [
    "Practice line one: read carefully.", "Practice line two: apply the skill.",
    "Practice line three: keep going.", "Practice line four: build the habit.",
    "Practice line five: almost warmed up.", "Practice line six: nice work.",
    "Practice line seven: stay consistent.", "Practice line eight: looking good.",
    "Practice line nine: keep it up.", "Practice line ten: you're getting fluent.",
    "Practice line eleven: one more push.", "Practice line twelve: finish strong.",
]


def _drill(did, cp, order, title, chunk, instruction, tasks):
    return {"id": did, "track": "docs", "order": order, "is_drill": True, "block_cp": cp,
            "title": title, "chunk": chunk, "instruction": ["## Skill Drill", instruction, "Repetition builds fluency — apply the skill on as many lines as asked."],
            "doc": _doc([_b(f"b{i}", t) for i, t in enumerate(_DRILL_LINES, 1)]), "tasks": tasks, "points": 80}


DOCS_DRILLS = [
    _drill("docs-d1", "docs-cp1", 4.1, "Emphasis Drill", "B / I / U repetition",
           "Use **bold, italic, or underline** on at least 10 lines.",
           [_t("t1", "Use bold/italic/underline on at least 10 lines", {"kind": "fmt_count", "attrs": ["bold", "italic", "underline"], "equals": True, "min": 10})]),
    _drill("docs-d2", "docs-cp1", 4.2, "Font Family Drill", "Typeface repetition",
           "Change the **font** (to anything but Arial) on at least 10 lines.",
           [_t("t1", "Change the font on at least 10 lines", {"kind": "fmt_count", "attr": "fontFamily", "not_equals": "Arial", "min": 10})]),
    _drill("docs-d3", "docs-cp1", 4.3, "Font Size Drill", "Point size repetition",
           "Change the **font size** on at least 10 lines.",
           [_t("t1", "Change the font size on at least 10 lines", {"kind": "fmt_count", "attr": "fontSize", "not_equals": 11, "min": 10})]),
    _drill("docs-d4", "docs-cp1", 4.4, "Text Color Drill", "Color repetition",
           "Add **text color** to at least 8 lines.",
           [_t("t1", "Add text color to at least 8 lines", {"kind": "fmt_count", "attr": "color", "not_equals": "#0f172a", "min": 8})]),
    _drill("docs-d5", "docs-cp2", 8.1, "Alignment Drill", "Align repetition",
           "**Align** at least 10 lines (center, right, or justify).",
           [_t("t1", "Align at least 10 lines", {"kind": "fmt_count", "attr": "align", "not_equals": "left", "min": 10})]),
    _drill("docs-d6", "docs-cp2", 8.2, "Line Spacing Drill", "Spacing repetition",
           "Change the **line spacing** on at least 8 lines.",
           [_t("t1", "Change line spacing on at least 8 lines", {"kind": "fmt_count", "attr": "lineSpacing", "not_equals": 1.0, "min": 8})]),
    _drill("docs-d7", "docs-cp2", 8.3, "Lists Drill", "List repetition",
           "Turn at least 10 lines into **list items** (bulleted or numbered).",
           [_t("t1", "Turn at least 10 lines into list items", {"kind": "type_count", "types": ["bullet", "number"], "min": 10})]),
]

BLOCK_TASKS = {"docs": DOCS_BLOCK_TASKS}
DRILLS = {"docs": DOCS_DRILLS}
ALL_BLOCK_TASKS = [t for tasks in BLOCK_TASKS.values() for t in tasks]
ALL_DRILLS = [d for ds in DRILLS.values() for d in ds]
BLOCK_TASK_BY_CP = {t["block_cp"]: t for t in ALL_BLOCK_TASKS}

MISSION_INDEX = {m["id"]: m for track in MISSIONS.values() for m in track}
MISSION_INDEX.update({t["id"]: t for t in ALL_BLOCK_TASKS})
MISSION_INDEX.update({d["id"]: d for d in ALL_DRILLS})


def block_tasks_for(track_id):
    return BLOCK_TASKS.get(track_id, [])


def drills_for(track_id):
    return DRILLS.get(track_id, [])


def block_task_for_cp(cp_id):
    return BLOCK_TASK_BY_CP.get(cp_id)


# ------------------------------ GRADING ------------------------------
def _get_block(doc, bid):
    for b in doc.get("blocks", []):
        if b.get("id") == bid:
            return b
    return None


def _first_table(doc):
    for b in doc.get("blocks", []):
        if b.get("type") == "table":
            return b
    return None


def _check_one(check, doc):
    kind = check.get("kind")
    try:
        if kind == "fmt_count":
            # Count blocks whose formatting matches; used for "apply this skill at least N times".
            blocks = doc.get("blocks", [])
            attrs = check.get("attrs")
            values = check.get("values")
            has_ne = "not_equals" in check
            n = 0
            for b in blocks:
                fmt = b.get("fmt", {})
                if attrs:
                    if any(fmt.get(a) == check.get("equals", True) for a in attrs):
                        n += 1
                elif values is not None:
                    if fmt.get(check["attr"]) in values:
                        n += 1
                elif has_ne:
                    if fmt.get(check["attr"]) != check["not_equals"]:
                        n += 1
                else:
                    if fmt.get(check["attr"]) == check.get("equals"):
                        n += 1
            return n >= check["min"]
        if kind == "type_count":
            n = sum(1 for b in doc.get("blocks", []) if b.get("type") in (check.get("types") or [check.get("equals")]))
            return n >= check["min"]
        if kind == "fmt":
            b = _get_block(doc, check["block"])
            return bool(b) and b.get("fmt", {}).get(check["attr"]) == check["equals"]
        if kind == "fmt_all":
            blocks = [b for b in doc.get("blocks", []) if b.get("type") in ("paragraph", "bullet", "number", "heading")]
            return len(blocks) > 0 and all(b.get("fmt", {}).get(check["attr"]) == check["equals"] for b in blocks)
        if kind == "fmt_multi":
            return all((_get_block(doc, bid) or {}).get("fmt", {}).get(check["attr"]) == check["equals"] for bid in check["blocks"])
        if kind == "fmt_and":
            b = _get_block(doc, check["block"])
            if not b:
                return False
            return all(b.get("fmt", {}).get(attr) == val for attr, val in check["checks"])
        if kind == "type":
            b = _get_block(doc, check["block"])
            return bool(b) and b.get("type") == check["equals"]
        if kind == "type_multi":
            return all((_get_block(doc, bid) or {}).get("type") == check["equals"] for bid in check["blocks"])
        if kind == "text_contains":
            b = _get_block(doc, check["block"])
            return bool(b) and check["value"] in (b.get("text") or "")
        if kind == "text_replaced":
            b = _get_block(doc, check["block"])
            if not b:
                return False
            txt = (b.get("text") or "").lower()
            return check["remove"].lower() not in txt and check["add"].lower() in txt
        if kind == "link":
            b = _get_block(doc, check["block"])
            link = (b or {}).get("fmt", {}).get("link") or ""
            return link.startswith("http")
        if kind == "header_contains":
            return check["value"].lower() in (doc.get("header") or "").lower()
        if kind == "footer_pagenum":
            return bool(doc.get("footerPageNumber"))
        if kind == "table":
            t = _first_table(doc)
            return bool(t) and t.get("cols") == check["cols"] and t.get("rows") == check["rows"]
        if kind == "table_cell_filled":
            t = _first_table(doc)
            if not t:
                return False
            cells = t.get("cells") or []
            r, c = check["row"], check["col"]
            return r < len(cells) and c < len(cells[r]) and bool((cells[r][c] or "").strip())
        if kind == "exported":
            return bool(doc.get("exported"))
        # ---- sheets kinds ----
        if kind in ("cell_text", "cell_formula", "cell_value", "sorted"):
            sheets = doc.get("sheets") or []
            si = check.get("sheet", 0)
            if si >= len(sheets):
                return False
            cells = sheets[si].get("cells") or {}
            if kind == "cell_text":
                return (cells.get(check["cell"]) or "").strip().casefold() == check["equals"].casefold()
            if kind == "cell_formula":
                raw = (cells.get(check["cell"]) or "").replace(" ", "").upper()
                exp = f"={check['fn']}({check['range']})".replace(" ", "").upper()
                return raw == exp
            if kind == "cell_value":
                v = eval_ref(cells, check["cell"])
                return isinstance(v, (int, float)) and abs(v - check["equals"]) < 0.001
            if kind == "sorted":
                col = check["col"].upper()
                nums = []
                for r in range(check["from"], check["to"] + 1):
                    n = _num((cells.get(f"{col}{r}") or "").strip())
                    if n is not None:
                        nums.append(n)
                if len(nums) < 2:
                    return False
                if check["order"] == "asc":
                    return all(nums[i] <= nums[i + 1] for i in range(len(nums) - 1))
                return all(nums[i] >= nums[i + 1] for i in range(len(nums) - 1))
        if kind == "chart":
            return any(c.get("type") == check["type"] for c in (doc.get("charts") or []))
        if kind == "chart_range":
            want = check["range"].replace(" ", "").upper()
            return any(c.get("type") == check["type"] and (c.get("range", "").replace(" ", "").upper() == want) for c in (doc.get("charts") or []))
        if kind == "sheet_count":
            return len(doc.get("sheets") or []) == check["equals"]
        if kind == "sheet_named":
            sheets = doc.get("sheets") or []
            i = check["index"]
            return i < len(sheets) and (sheets[i].get("name", "").strip().casefold() == check["name"].casefold())
        # ---- slides kinds ----
        if kind in ("slide_count", "slide_title_nonempty", "slide_title_contains", "slide_bullets_min",
                    "five_by_five", "slide_layout", "slide_theme", "slide_has_image", "slide_has_chart",
                    "slide_animation", "slide_transition", "slide_notes_min_words"):
            slides = doc.get("slides") or []
            if kind == "slide_count":
                return len(slides) == check["equals"]
            si = check.get("slide", 0)
            if si >= len(slides):
                return False
            sl = slides[si]
            bullets = [b for b in (sl.get("bullets") or []) if (b or "").strip()]
            if kind == "slide_title_nonempty":
                return bool((sl.get("title") or "").strip())
            if kind == "slide_title_contains":
                return check["value"].casefold() in (sl.get("title") or "").casefold()
            if kind == "slide_bullets_min":
                return len(bullets) >= check["min"]
            if kind == "five_by_five":
                return len(bullets) >= 1 and len(bullets) <= 5 and all(len(b.split()) <= 5 for b in bullets)
            if kind == "slide_layout":
                return sl.get("layout") == check["equals"]
            if kind == "slide_theme":
                return sl.get("theme") == check["equals"]
            if kind == "slide_has_image":
                return bool(sl.get("image"))
            if kind == "slide_has_chart":
                ch = sl.get("chart")
                return bool(ch) and (("type" not in check) or ch.get("type") == check["type"])
            if kind == "slide_animation":
                return (sl.get("animation") or "none") != "none"
            if kind == "slide_transition":
                return (sl.get("transition") or "none") != "none"
            if kind == "slide_notes_min_words":
                return len((sl.get("notes") or "").split()) >= check["min"]
        # ---- email kinds ----
        if kind == "picked":
            return check["field"] in (doc.get("picked") or [])
        if kind in ("email_opened", "searched", "sent_exists", "subject_prefix", "subject_nonempty",
                    "subject_and_to", "to_includes", "cc_includes", "bcc_includes", "cc_min",
                    "has_greeting", "has_signoff", "has_greeting_signoff", "has_attachment",
                    "body_min_words", "formatting"):
            msgs = doc.get("messages") or []
            if kind == "email_opened":
                return any(m.get("id") == check["id"] and m.get("read") for m in msgs)
            if kind == "searched":
                return bool(doc.get("searched"))
            sent = [m for m in msgs if m.get("folder") == "sent" and m.get("kind") == check.get("sentKind")]
            m = sent[-1] if sent else None
            if kind == "sent_exists":
                return m is not None
            if not m:
                return False
            body = (m.get("body") or "")
            bl = body.lower()
            sbody = m.get("bodyStudent")
            sbody = sbody if sbody is not None else body
            sbl = sbody.lower()
            subj = (m.get("subject") or "").strip()
            if kind == "subject_prefix":
                return subj.lower().startswith(check["prefix"].lower())
            if kind == "subject_nonempty":
                return bool(subj)
            if kind == "subject_and_to":
                return bool(subj) and check["email"].casefold() in [x.casefold() for x in m.get("to", [])]
            if kind == "to_includes":
                return check["email"].casefold() in [x.casefold() for x in m.get("to", [])]
            if kind == "cc_includes":
                return check["email"].casefold() in [x.casefold() for x in m.get("cc", [])]
            if kind == "bcc_includes":
                return check["email"].casefold() in [x.casefold() for x in m.get("bcc", [])]
            if kind == "cc_min":
                return len(m.get("cc", [])) >= check["min"]
            if kind == "has_greeting":
                return any(g in sbl for g in _GREETINGS)
            if kind == "has_signoff":
                return any(s in sbl for s in _SIGNOFFS)
            if kind == "has_greeting_signoff":
                return any(g in sbl for g in _GREETINGS) and any(s in sbl for s in _SIGNOFFS)
            if kind == "has_attachment":
                atts = m.get("attachments", [])
                if "name" in check:
                    return any((a.get("name") == check["name"]) for a in atts)
                return len(atts) > 0
            if kind == "body_min_words":
                return len(sbody.split()) >= check["min"]
            if kind == "formatting":
                return {"bold": m.get("hasBold"), "bullets": m.get("hasBullets"), "signature": m.get("hasSignature")}.get(check["feature"], False)
    except Exception:
        return False
    return False


_GREETINGS = ("dear ", "hi ", "hi,", "hello", "good morning", "good afternoon", "hey ", "greetings")
_SIGNOFFS = ("thanks", "thank you", "sincerely", "best,", "best regards", "regards", "cheers", "respectfully", "yours")


def grade_mission(mission_id, doc):
    mission = MISSION_INDEX.get(mission_id)
    if not mission:
        return None
    results = []
    passed = 0
    for task in mission["tasks"]:
        if task["check"].get("kind") == "ai":
            continue
        ok = _check_one(task["check"], doc or {})
        if ok:
            passed += 1
        results.append({"id": task["id"], "passed": ok})
    total = len(results)
    score = round((passed / total) * 100) if total else 0
    return {"results": results, "passed": passed, "total": total, "score": score, "points": mission["points"]}


def letter_grade(score):
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def public_track(track_id):
    track = TRACKS.get(track_id)
    if not track:
        return None
    return {"track": track, "config": TRACK_CONFIG.get(track_id, {}), "missions": MISSIONS.get(track_id, []),
            "block_tasks": BLOCK_TASKS.get(track_id, []), "drills": DRILLS.get(track_id, [])}
