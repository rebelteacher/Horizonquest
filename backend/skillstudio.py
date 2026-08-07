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
MISSION_INDEX = {m["id"]: m for track in MISSIONS.values() for m in track}


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
    except Exception:
        return False
    return False


def grade_mission(mission_id, doc):
    mission = MISSION_INDEX.get(mission_id)
    if not mission:
        return None
    results = []
    passed = 0
    for task in mission["tasks"]:
        ok = _check_one(task["check"], doc or {})
        if ok:
            passed += 1
        results.append({"id": task["id"], "passed": ok})
    total = len(mission["tasks"])
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
    return {"track": track, "config": TRACK_CONFIG.get(track_id, {}), "missions": MISSIONS.get(track_id, [])}
