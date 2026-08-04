"""HorizonQuest Skill Studio — guided, auto-graded productivity-software missions.
Phase 1: Word Processing (docs track). Each mission teaches a "chunk" of the editor
ribbon, loads a starter document, and lists tasks that are graded by inspecting the
student's document state. Grading logic is mirrored on the client for live ticking.
"""

# Toolbar option sets shared with the client so tasks reference exact values.
STUDIO_CONFIG = {
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

TRACKS = {
    "docs": {"id": "docs", "name": "Word Processing", "subtitle": "Google Docs · Microsoft Word · Pages",
             "standard": "PA.2.A", "color": "#22D3EE",
             "intro": "Master the document editor one ribbon chunk at a time — then prove it on real editing tasks."},
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
            _t("t2", "Set every line to 12pt", {"kind": "fmt_all", "attr": "fontSize", "equals": 12}),
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
            "## Practice",
            "Open up the essay paragraph so it's easier to read.",
        ],
        "doc": _doc([
            _b("b1", "Essay: Why Reading Matters"),
            _b("b2", "Reading builds vocabulary, focus, and empathy. It lets us explore ideas far beyond our own experience."),
            _b("b3", "That is why daily reading is a habit worth keeping."),
        ]),
        "tasks": [
            _t("t1", "Set the two body lines to 1.5 line spacing", {"kind": "fmt_multi", "blocks": ["b2", "b3"], "attr": "lineSpacing", "equals": 1.5}),
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
            "- A **hyperlink** turns text into a clickable link to a website. Select a line and use the link button to add a URL.",
            "## Practice",
            "Finish the product blurb.",
        ],
        "doc": _doc([
            _b("b1", "SkyPad Tablet"),
            _b("b2", "Now trademarked and better than ever."),
            _b("b3", "Learn more at our website"),
        ]),
        "tasks": [
            _t("t1", "Insert the ® symbol somewhere in the product name line", {"kind": "text_contains", "block": "b1", "value": "®"}),
            _t("t2", "Turn 'Learn more at our website' into a hyperlink", {"kind": "link", "block": "b3"}),
        ],
        "points": 100,
    },
    {
        "id": "docs-m9", "track": "docs", "order": 9,
        "title": "Find & Replace", "chunk": "Edit menu · Find and replace",
        "instruction": [
            "## Find & Replace",
            "**Find and replace** swaps every copy of one word for another across the whole document in one step — perfect for fixing a name or wording everywhere at once.",
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
    return {"track": track, "config": STUDIO_CONFIG, "missions": MISSIONS.get(track_id, [])}
