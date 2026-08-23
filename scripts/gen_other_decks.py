"""Generate themed starter decks for Word Processing, Spreadsheets & Presentations."""
import sys
sys.path.insert(0, "/app/scripts")
import gen_email_decks as g  # reuse themed helpers (also regenerates email decks, harmless)


def build(track, blocks):
    for i, (kicker, title, sub, slides) in enumerate(blocks, 1):
        d = g.new_deck()
        g.title_slide(d, kicker, title, sub)
        for st, bl in slides:
            g.content_slide(d, st, bl)
        d.save(f"/app/frontend/public/decks/horizonquest_{track}_block{i}.pptx")


def goals(items):
    return [("By the end of this lesson you will be able to:", 0, "muted")] + [(x, 0, "accent") for x in items]


def remember(items):
    return [(x, 0, "accent") for x in items]


# ============ WORD PROCESSING ============
build("docs", [
    ("WORD PROCESSING · BLOCK 1", "The Interface & Text Basics", "Meet the Ribbon and style text with confidence.", [
        ("Learning Goals", goals(["Find tools on the Ribbon", "Apply Bold, Italic & Underline", "Change the font family and size", "Change text color"])),
        ("The Ribbon", [("The Ribbon is the strip of tabs and buttons across the top.", 0, "body"), ("The Home tab holds your everyday tools: fonts, styles, alignment.", 0, "body"), ("Tip: hover a button to see what it does.", 0, "muted")]),
        ("Bold, Italic & Underline", [("Bold = thicker/darker (Ctrl+B)", 0, "body"), ("Italic = slanted (Ctrl+I)", 0, "body"), ("Underline = a line beneath (Ctrl+U)", 0, "body"), ("Select your text first, then click the button.", 0, "accent")]),
        ("Font Family & Size", [("Font family = the typeface (Arial, Calibri, Times...)", 0, "body"), ("Font size is measured in points — bigger number = bigger text", 0, "body"), ("Use a larger, bold font for titles.", 0, "accent")]),
        ("Text Color", [("The Text Color button changes the color of the letters.", 0, "body"), ("Its icon is a letter 'A' with a colored bar underneath.", 0, "body"), ("Use color for emphasis — don't overdo it.", 0, "muted")]),
        ("Remember", remember(["The Ribbon holds your tools", "Select text before you format it", "Bold/Italic/Underline add emphasis", "Titles: larger + bold"])),
    ]),
    ("WORD PROCESSING · BLOCK 2", "Paragraphs, Spacing & Lists", "Shape how your text sits on the page.", [
        ("Learning Goals", goals(["Align text left, center, right, or justified", "Adjust line spacing", "Make bulleted and numbered lists", "Insert symbols and hyperlinks"])),
        ("Alignment", [("Left = lines up on the left (normal for body text)", 0, "body"), ("Center = centered (great for titles)", 0, "body"), ("Right = lines up on the right (dates)", 0, "body"), ("Justify = straight on BOTH edges, like a newspaper", 0, "body")]),
        ("Line Spacing", [("Controls the vertical space between lines.", 0, "body"), ("Single (1.0), 1.5, and Double (2.0) are common.", 0, "body"), ("More spacing = easier to read and mark up.", 0, "accent")]),
        ("Lists", [("Bulleted list = items with no particular order", 0, "body"), ("Numbered list = steps in a specific order", 0, "body"), ("Select the lines, then click the list button.", 0, "accent")]),
        ("Symbols & Hyperlinks", [("Insert -> Symbol adds characters not on the keyboard (like Omega or ©).", 0, "body"), ("A hyperlink lets a reader click to jump to a web page.", 0, "body"), ("The display text is what the reader sees and clicks.", 0, "muted")]),
        ("Remember", remember(["Left = body, Center = titles, Justify = both edges", "More line spacing = easier to read", "Numbered = order matters; bulleted = it doesn't", "Insert -> Symbol for special characters"])),
    ]),
    ("WORD PROCESSING · BLOCK 3", "Tools & Finishing Your Document", "Edit smart, organize with tables, and export clean.", [
        ("Learning Goals", goals(["Use Find & Replace", "Build and edit tables", "Add headers, footers & page numbers", "Export your document as a PDF"])),
        ("Find & Replace", [("Locates text and can swap it for new text.", 0, "body"), ("'Replace All' changes every match in one click.", 0, "body"), ("Great for fixing a repeated typo everywhere.", 0, "accent")]),
        ("Tables", [("A table organizes data in rows and columns of cells.", 0, "body"), ("A cell is where a row and column meet.", 0, "body"), ("3x4 = columns x rows. Right-click to add rows/columns.", 0, "muted")]),
        ("Headers, Footers & Page Numbers", [("Header = top margin of every page; Footer = bottom margin.", 0, "body"), ("Put your name or page numbers here to appear on every page.", 0, "body"), ("Added from the Insert menu.", 0, "muted")]),
        ("Export to PDF", [("A PDF looks the same on any device and can't be easily edited.", 0, "body"), ("File -> Download/Export as PDF.", 0, "body"), ("Proofread and check formatting before you export.", 0, "accent")]),
        ("Remember", remember(["Find & Replace fixes text fast", "Tables = rows + columns of cells", "Name/page numbers go in the header or footer", "Submit as a PDF so your layout stays put"])),
    ]),
])

# ============ SPREADSHEETS ============
build("sheets", [
    ("SPREADSHEETS · BLOCK 1", "Spreadsheet Basics & Formulas", "Cells, references, and your first formulas.", [
        ("Learning Goals", goals(["Name cells with column-row references", "Start every formula with =", "Use SUM and AVERAGE", "Use COUNT"])),
        ("Cells & References", [("A cell is a single box; columns are letters, rows are numbers.", 0, "body"), ("'B3' means column B, row 3.", 0, "body"), ("A range like A1:A5 means cells A1 through A5.", 0, "accent")]),
        ("Formulas Start With =", [("Every formula begins with the equals sign.", 0, "body"), ("=A1+A2 adds two cells.", 0, "body"), ("No = sign? It shows as plain text and won't calculate.", 0, "muted")]),
        ("SUM & AVERAGE", [("=SUM(A1:A5) adds the values in the range.", 0, "body"), ("=AVERAGE(B1:B4) finds the mean (adds, then divides).", 0, "body"), ("Change a number and the formula updates automatically.", 0, "accent")]),
        ("COUNT", [("=COUNT(A1:A10) counts how many cells contain numbers.", 0, "body"), ("COUNT counts; SUM totals — don't mix them up.", 0, "muted")]),
        ("Remember", remember(["Reference = column letter + row number (B3)", "Every formula starts with =", "SUM totals, AVERAGE means, COUNT counts", "Formulas update when the data changes"])),
    ]),
    ("SPREADSHEETS · BLOCK 2", "Analyzing & Charting Data", "Find highs and lows, sort, and visualize.", [
        ("Learning Goals", goals(["Use MAX and MIN", "Build a summary row", "Sort data correctly", "Make a bar chart"])),
        ("MAX & MIN", [("=MAX(A1:A10) returns the largest value.", 0, "body"), ("=MIN(A1:A10) returns the smallest value.", 0, "body"), ("Perfect for finding top and bottom scores fast.", 0, "accent")]),
        ("Summary Rows", [("A summary row often combines SUM, AVERAGE, MAX and MIN.", 0, "body"), ("Usually placed at the bottom of your data.", 0, "muted")]),
        ("Sorting", [("Ascending = A->Z or smallest->largest.", 0, "body"), ("Descending = largest->smallest.", 0, "body"), ("Select the WHOLE table so rows stay together.", 0, "accent")]),
        ("Bar Charts", [("A bar chart compares amounts across categories.", 0, "body"), ("Select your data, then Insert -> Chart.", 0, "body"), ("Give the chart a clear title.", 0, "muted")]),
        ("Remember", remember(["MAX = highest, MIN = lowest", "Summary rows go at the bottom", "Sort the whole table, not one column", "Bar charts compare categories"])),
    ]),
    ("SPREADSHEETS · BLOCK 3", "Charts & Organizing Workbooks", "Pie charts, worksheet tabs, and a real gradebook.", [
        ("Learning Goals", goals(["Make a pie chart", "Use multiple worksheet tabs", "Organize a gradebook with formulas"])),
        ("Pie Charts", [("A pie chart shows parts of a whole (percentages).", 0, "body"), ("Each slice is a portion of the total; slices add up to 100%.", 0, "body"), ("Great for budgets or survey shares.", 0, "accent")]),
        ("Worksheets & Tabs", [("A workbook (file) can hold several worksheets.", 0, "body"), ("Sheet tabs are at the bottom; the + adds a new one.", 0, "body"), ("Rename tabs (e.g., 'Term 1') to stay organized.", 0, "muted")]),
        ("Capstone: Gradebook", [("Use formulas to average grades and find the top/low scores.", 0, "body"), ("Add a summary row and a chart to see the class at a glance.", 0, "accent")]),
        ("Remember", remember(["Pie chart = parts of a whole (100%)", "One workbook can hold many worksheets", "Rename tabs to stay organized", "Combine formulas + charts in a gradebook"])),
    ]),
])

# ============ PRESENTATIONS ============
build("slides", [
    ("PRESENTATIONS · BLOCK 1", "Slide Basics", "Start a deck and keep it clean and readable.", [
        ("Learning Goals", goals(["Build a title slide", "Write clear bullet points", "Use the 5x5 rule", "Keep slides easy to read"])),
        ("The Title Slide", [("The first slide introduces your topic.", 0, "body"), ("Include a clear title (and your name).", 0, "body"), ("A 'deck' is the whole set of slides.", 0, "muted")]),
        ("Bullets & the 5x5 Rule", [("Body text should be short bullet points, not paragraphs.", 0, "body"), ("5x5 rule: about 5 bullets, ~5 words each.", 0, "body"), ("Short bullets keep the audience listening, not reading.", 0, "accent")]),
        ("Keep Slides Clean", [("Every slide needs a clear title.", 0, "body"), ("Too much text is hard to read from the back of the room.", 0, "body"), ("Split a crowded slide into two.", 0, "muted")]),
        ("Remember", remember(["Title slide introduces the topic", "Short bullets, not paragraphs", "5x5 keeps it readable", "The audience listens to YOU"])),
    ]),
    ("PRESENTATIONS · BLOCK 2", "Designing Your Slides", "Layouts, themes, images, and charts.", [
        ("Learning Goals", goals(["Pick the right slide layout", "Apply a consistent theme", "Add relevant images", "Insert a chart"])),
        ("Layouts", [("A layout decides where titles, text, and images sit.", 0, "body"), ("Pick the layout before adding content to save time.", 0, "accent")]),
        ("Themes", [("A theme controls colors, fonts, and the overall look.", 0, "body"), ("One theme across all slides keeps it consistent and professional.", 0, "body"), ("Choose colors with good contrast so text is readable.", 0, "muted")]),
        ("Images", [("Add clear, relevant images to support your point.", 0, "body"), ("Resize so images fit without covering text.", 0, "muted")]),
        ("Charts", [("A chart shows data visually — a trend or comparison at a glance.", 0, "body"), ("Insert -> Chart; give it a clear title.", 0, "muted")]),
        ("Remember", remember(["Layout first, then content", "One theme = consistent & professional", "Relevant images support the point", "Charts show trends at a glance"])),
    ]),
    ("PRESENTATIONS · BLOCK 3", "Delivering Your Presentation", "Animations, notes, and presenting with confidence.", [
        ("Learning Goals", goals(["Use animations and transitions well", "Write speaker notes", "Present confidently"])),
        ("Animations vs Transitions", [("Animation = how an element appears WITHIN a slide.", 0, "body"), ("Transition = how you move from one slide to the NEXT.", 0, "body"), ("Use them sparingly — too many distract.", 0, "accent")]),
        ("Speaker Notes", [("Private notes that help YOU present (the audience doesn't see them).", 0, "body"), ("Write key facts and reminders for each slide.", 0, "muted")]),
        ("Capstone: Present It", [("Rehearse using your speaker notes.", 0, "body"), ("Talk to the audience — don't read the slides.", 0, "body"), ("Clean slides + subtle transitions + good notes = a strong talk.", 0, "accent")]),
        ("Remember", remember(["Animation = within a slide; transition = between slides", "Use effects sparingly", "Speaker notes are just for you", "Rehearse, then talk TO the audience"])),
    ]),
])

print("Done: 9 decks saved to /app/frontend/public/decks/")
