"""HorizonQuest v1 Curriculum — CTE Learning Platform.
4 Territories mapped to the four CTE modules, 33 quests, DOK 2-4, auto-grading answer keys.
Territories: Summit of Leadership, Productivity Peaks, The Cyber Frontier, Data Delta.
"""

_PTS = {2: 100, 3: 150, 4: 200}

TERRITORIES = [
    {
        "id": "t1",
        "name": "Summit of Leadership",
        "subtitle": "Business & Leadership",
        "order": 1,
        "color": "#FB923C",
        "position": {"x": 16, "y": 70},
        "lore": "Nordic fortress peaks where Explorers learn to lead, meet, and decide.",
    },
    {
        "id": "t2",
        "name": "Productivity Peaks",
        "subtitle": "Productivity Tools & AI",
        "order": 2,
        "color": "#22D3EE",
        "position": {"x": 40, "y": 34},
        "lore": "Crystalline tech spires where documents, data, and AI come alive.",
    },
    {
        "id": "t3",
        "name": "The Cyber Frontier",
        "subtitle": "Cybersecurity",
        "order": 3,
        "color": "#A855F7",
        "position": {"x": 64, "y": 62},
        "lore": "Neon shield rune-gates guarding the secrets of safe systems.",
    },
    {
        "id": "t4",
        "name": "Data Delta",
        "subtitle": "Data Science",
        "order": 4,
        "color": "#34D399",
        "position": {"x": 87, "y": 28},
        "lore": "Glowing binary streams where data becomes decisions.",
    },
]


def _q(qid, prompt, options, answer):
    return {"id": qid, "type": "mc", "prompt": prompt, "options": options, "answer": answer}


# (id, territory, order, title, dok, standard_code, standard_desc, [questions], reflection)
_RAW = [
    # ---------------- T1: Summit of Leadership (Business & Leadership) ----------------
    ("t1-q1", "t1", 1, "Meeting Structure & Order of Business", 2, "BL.1.A", "Identify the parts and correct order of a business meeting.", [
        _q("a", "What is the FIRST step in a formal meeting?", ["Call the meeting to order", "Adjourn", "Vote on motions", "Read new business"], "Call the meeting to order"),
        _q("b", "The written plan of what a meeting will cover is the:", ["Agenda", "Minutes", "Motion", "Quorum"], "Agenda"),
        _q("c", "'Minutes' of a meeting are:", ["The official written record", "The length of the meeting", "A type of motion", "The break time"], "The official written record"),
    ], "Why does following an agenda make a meeting more effective?"),

    ("t1-q2", "t1", 2, "Opening & Closing Procedures", 2, "BL.1.B", "Apply proper opening and closing procedures.", [
        _q("a", "To officially end a meeting, a member moves to:", ["Adjourn", "Second", "Table", "Nominate"], "Adjourn"),
        _q("b", "A 'quorum' is:", ["The minimum members needed to conduct business", "The meeting leader", "A written report", "A closing prayer"], "The minimum members needed to conduct business"),
        _q("c", "Who typically leads/opens the meeting?", ["The chair (president)", "The newest member", "A guest", "No one"], "The chair (president)"),
    ], "Describe how you would open a club meeting from start to first agenda item."),

    ("t1-q3", "t1", 3, "Motions & Parliamentary Basics", 3, "BL.1.C", "Use motions and voting in parliamentary procedure.", [
        _q("a", "After a member makes a motion, what must happen next?", ["Another member seconds it", "It passes automatically", "The meeting ends", "It is filed"], "Another member seconds it"),
        _q("b", "'Table a motion' means to:", ["Set it aside for later", "Approve it instantly", "Reject it forever", "Read it aloud"], "Set it aside for later"),
        _q("c", "A motion usually passes with a:", ["Majority vote", "Single vote", "Unanimous vote always", "Coin flip"], "Majority vote"),
    ], "Write a motion you might make in a student organization and how it would be voted on."),

    ("t1-q4", "t1", 4, "Business Etiquette & Norms", 2, "BL.1.D", "Demonstrate professional etiquette and workplace norms.", [
        _q("a", "Professional etiquette includes:", ["Being punctual and respectful", "Interrupting often", "Ignoring emails", "Arriving late"], "Being punctual and respectful"),
        _q("b", "A professional email should have:", ["A clear subject and polite tone", "All caps", "No greeting", "Slang only"], "A clear subject and polite tone"),
        _q("c", "When someone else is speaking in a meeting you should:", ["Listen actively", "Talk over them", "Check your phone", "Leave the room"], "Listen actively"),
    ], "Give two etiquette rules you'd set for a classroom business team."),

    ("t1-q5", "t1", 5, "Characteristics of Effective Leaders", 2, "BL.1.E", "Identify traits of effective leaders.", [
        _q("a", "An effective leader most importantly:", ["Communicates clearly and listens", "Never asks for input", "Takes all the credit", "Avoids decisions"], "Communicates clearly and listens"),
        _q("b", "Integrity means a leader:", ["Does the right thing even when it's hard", "Follows the crowd", "Hides mistakes", "Breaks promises"], "Does the right thing even when it's hard"),
        _q("c", "A leader shows empathy by:", ["Understanding others' feelings", "Ignoring the team", "Only focusing on tasks", "Rushing everyone"], "Understanding others' feelings"),
    ], "Name a leader you admire and one trait that makes them effective."),

    ("t1-q6", "t1", 6, "Leadership Styles", 3, "BL.1.F", "Compare leadership styles and their effects.", [
        _q("a", "A 'democratic' leader:", ["Involves the team in decisions", "Decides alone always", "Gives no direction", "Ignores the team"], "Involves the team in decisions"),
        _q("b", "An 'autocratic' leader:", ["Makes decisions without much input", "Always votes", "Never leads", "Only follows"], "Makes decisions without much input"),
        _q("c", "A 'laissez-faire' style means the leader:", ["Gives the team lots of freedom", "Controls every detail", "Never trusts anyone", "Cancels all meetings"], "Gives the team lots of freedom"),
    ], "Which leadership style fits you best and why?"),

    ("t1-q7", "t1", 7, "Scenario Decisions: What Would You Do?", 3, "BL.1.G", "Make and justify leadership decisions in scenarios.", [
        _q("a", "Two teammates argue over a task. A good leader first:", ["Listens to both sides", "Picks a favorite", "Ignores it", "Ends the project"], "Listens to both sides"),
        _q("b", "The team will miss a deadline. You should:", ["Communicate early and adjust the plan", "Hide it", "Blame one person", "Do nothing"], "Communicate early and adjust the plan"),
        _q("c", "A member has a great idea but is shy. A leader:", ["Invites and encourages their input", "Talks over them", "Ignores them", "Mocks the idea"], "Invites and encourages their input"),
    ], "Describe a tough team decision and how you'd handle it as a leader."),

    ("t1-q8", "t1", 8, "Capstone: Lead a Mock Meeting", 4, "BL.1.CAP", "Plan and lead a complete business meeting.", [
        _q("a", "The correct order is:", ["Call to order → agenda → motions → adjourn", "Adjourn → agenda → order", "Motions → call to order → agenda", "Agenda → adjourn → order"], "Call to order → agenda → motions → adjourn"),
        _q("b", "To keep the meeting on track, the chair uses:", ["The agenda and time limits", "Random topics", "No plan", "Only jokes"], "The agenda and time limits"),
        _q("c", "A successful leader closes the meeting by:", ["Summarizing decisions and adjourning", "Leaving silently", "Starting new arguments", "Deleting the minutes"], "Summarizing decisions and adjourning"),
    ], "Draft the agenda for a 15-minute meeting you would lead."),

    # ---------------- T2: Productivity Peaks (Productivity Tools & AI) ----------------
    ("t2-q1", "t2", 1, "Document Formatting", 2, "PA.2.A", "Apply formatting: styles, headers, footers.", [
        _q("a", "A header appears:", ["At the top of every page", "Only on page 1", "At the bottom", "Never"], "At the top of every page"),
        _q("b", "To make text stand out as a title you use:", ["A heading style", "Random spaces", "All lowercase", "A footnote"], "A heading style"),
        _q("c", "Page numbers are usually placed in the:", ["Footer", "Title", "Margin note", "Table of contents only"], "Footer"),
    ], "When is consistent formatting important in a real document?"),

    ("t2-q2", "t2", 2, "Spreadsheet Formulas", 3, "PA.2.B", "Use Sum, Average, and Count formulas.", [
        _q("a", "=SUM(A1:A5) will:", ["Add the values in A1 through A5", "Count the cells", "Average them", "Delete them"], "Add the values in A1 through A5"),
        _q("b", "To find the average of a range you use:", ["=AVERAGE(range)", "=SUM(range)", "=COUNT(range)", "=MAX(range)"], "=AVERAGE(range)"),
        _q("c", "=COUNT(B1:B10) returns:", ["The number of numeric cells", "Their total", "Their average", "The largest value"], "The number of numeric cells"),
    ], "Describe a real situation where AVERAGE is more useful than SUM."),

    ("t2-q3", "t2", 3, "Charts & Sorting Data", 3, "PA.2.C", "Create charts and sort data meaningfully.", [
        _q("a", "To compare categories, the best chart is often a:", ["Bar chart", "Random scatter", "Blank cell", "Formula"], "Bar chart"),
        _q("b", "Sorting data 'ascending' means:", ["Smallest to largest", "Largest to smallest", "Random order", "Deleting rows"], "Smallest to largest"),
        _q("c", "A pie chart is best for showing:", ["Parts of a whole", "Change over years", "Raw formulas", "Page numbers"], "Parts of a whole"),
    ], "Pick a dataset from your life and say which chart would show it best."),

    ("t2-q4", "t2", 4, "Slide Design & the 5x5 Rule", 2, "PA.2.D", "Design clear slides using the 5x5 rule.", [
        _q("a", "The 5x5 rule suggests about:", ["5 lines per slide, 5 words per line", "50 words per slide", "5 slides total", "5 fonts per slide"], "5 lines per slide, 5 words per line"),
        _q("b", "Good slides use:", ["Few words and clear visuals", "Full paragraphs", "Tiny font", "Clashing colors"], "Few words and clear visuals"),
        _q("c", "Slides should support the speaker by:", ["Highlighting key points", "Reading every word aloud", "Distracting the audience", "Hiding the topic"], "Highlighting key points"),
    ], "Rewrite a wordy slide idea into a clean 5x5 version."),

    ("t2-q5", "t2", 5, "AI Assist: Grammar, Data & Design", 3, "PA.2.E", "Use AI tools to improve writing, data, and design.", [
        _q("a", "An AI grammar assistant helps you:", ["Fix spelling and clarity", "Grade math tests", "Cook dinner", "Delete files"], "Fix spelling and clarity"),
        _q("b", "An AI data helper is best used to:", ["Suggest summaries and patterns", "Guarantee perfect answers", "Replace all thinking", "Hide the data"], "Suggest summaries and patterns"),
        _q("c", "You should always ______ AI suggestions.", ["Review and verify", "Blindly accept", "Ignore completely", "Copy without reading"], "Review and verify"),
    ], "How can AI help you work faster without doing your thinking for you?"),

    ("t2-q6", "t2", 6, "Chatbot Forge & Prompt Engineering", 3, "PA.2.F", "Build a simple chatbot and refine prompts.", [
        _q("a", "A clear prompt to an AI should be:", ["Specific about the task and goal", "Vague and short", "Empty", "All in symbols"], "Specific about the task and goal"),
        _q("b", "If an AI answer is off, a good next step is to:", ["Refine the prompt with more detail", "Give up", "Ask the exact same thing", "Turn off the computer"], "Refine the prompt with more detail"),
        _q("c", "A chatbot's 'persona/system message' defines:", ["How it should behave and respond", "The user's password", "The wifi", "The battery level"], "How it should behave and respond"),
    ], "Write a prompt for a study-helper chatbot and explain your choices."),

    ("t2-q7", "t2", 7, "Ethics of AI in Productivity", 3, "PA.2.G", "Evaluate ethical use of AI tools.", [
        _q("a", "Using AI to do your homework and claiming it as your own is:", ["Academic dishonesty", "Good practice", "Encouraged", "Required"], "Academic dishonesty"),
        _q("b", "A responsible AI user should:", ["Give credit and check for bias", "Hide AI use", "Trust it blindly", "Share private data"], "Give credit and check for bias"),
        _q("c", "AI outputs can sometimes be:", ["Wrong or biased", "Always perfect", "Never useful", "Impossible to check"], "Wrong or biased"),
    ], "Describe one ethical rule you'd follow when using AI for schoolwork."),

    ("t2-q8", "t2", 8, "Career Pathways Explorer", 2, "PA.2.H", "Explore productivity-related career pathways.", [
        _q("a", "A data analyst mainly:", ["Interprets data to inform decisions", "Fixes plumbing", "Drives trucks", "Teaches gym"], "Interprets data to inform decisions"),
        _q("b", "A digital marketer focuses on:", ["Promoting products online", "Writing legal contracts", "Building bridges", "Repairing engines"], "Promoting products online"),
        _q("c", "An administrative professional often:", ["Organizes and supports office operations", "Performs surgery", "Flies planes", "Designs microchips"], "Organizes and supports office operations"),
    ], "Which of these careers interests you and what skill would you build first?"),

    # ---------------- T3: The Cyber Frontier (Cybersecurity) ----------------
    ("t3-q1", "t3", 1, "Why Cybersecurity Matters", 2, "CY.3.A", "Explain the importance of cybersecurity.", [
        _q("a", "Cybersecurity protects:", ["Data, systems, and people", "Only games", "Nothing important", "Just printers"], "Data, systems, and people"),
        _q("b", "A data breach can lead to:", ["Stolen personal information", "Faster internet", "Better grades", "Free software"], "Stolen personal information"),
        _q("c", "Everyone online should care about security because:", ["Threats can affect anyone", "Only companies are targets", "It's not real", "Hackers are polite"], "Threats can affect anyone"),
    ], "Why does protecting your own data matter, even as a student?"),

    ("t3-q2", "t3", 2, "Threat Types: Malware, Phishing, Ransomware", 2, "CY.3.B", "Identify common cyber threats.", [
        _q("a", "Phishing is an attempt to:", ["Trick you into revealing info", "Speed up your PC", "Back up files", "Update software"], "Trick you into revealing info"),
        _q("b", "Ransomware typically:", ["Locks files and demands payment", "Cleans your disk", "Improves security", "Sends fan mail"], "Locks files and demands payment"),
        _q("c", "'Malware' is short for:", ["Malicious software", "Mail hardware", "Manual warning", "Major wire"], "Malicious software"),
    ], "Describe a phishing message you might receive and one red flag in it."),

    ("t3-q3", "t3", 3, "The CIA Triad", 3, "CY.3.C", "Apply the CIA triad (Confidentiality, Integrity, Availability).", [
        _q("a", "In the CIA triad, 'C' stands for:", ["Confidentiality", "Computer", "Coding", "Control"], "Confidentiality"),
        _q("b", "'Integrity' means data is:", ["Accurate and unaltered", "Always hidden", "Deleted", "Slow"], "Accurate and unaltered"),
        _q("c", "'Availability' means:", ["Authorized users can access data when needed", "No one can log in", "Data is public", "Servers are off"], "Authorized users can access data when needed"),
    ], "Give a real example of protecting confidentiality at school."),

    ("t3-q4", "t3", 4, "Safe Practices & Password Strength", 2, "CY.3.D", "Use safe practices and strong passwords.", [
        _q("a", "The strongest password is:", ["A long mix of letters, numbers, symbols", "'password'", "Your name", "'12345'"], "A long mix of letters, numbers, symbols"),
        _q("b", "Two-factor authentication (2FA) adds:", ["A second verification step", "More spam", "A slower PC", "A new password only"], "A second verification step"),
        _q("c", "You should ______ reuse the same password everywhere.", ["never", "always", "sometimes must", "be required to"], "never"),
    ], "Describe how you'd create a strong, memorable password."),

    ("t3-q5", "t3", 5, "Phishing Spotter", 3, "CY.3.E", "Detect red flags in suspicious messages.", [
        _q("a", "A phishing red flag is:", ["Urgent threats and odd links", "A known sender", "Correct grammar", "A normal signature"], "Urgent threats and odd links"),
        _q("b", "A suspicious email asks for your password. You should:", ["Never send it and report the email", "Reply with it", "Click all links", "Forward to friends"], "Never send it and report the email"),
        _q("c", "Hovering over a link lets you:", ["See the real destination URL", "Download it instantly", "Delete your account", "Change your grade"], "See the real destination URL"),
    ], "List three things you'd check before trusting an email."),

    ("t3-q6", "t3", 6, "Cipher Playground: Caesar, Pigpen, Substitution", 3, "CY.3.F", "Encode and decode with classic ciphers.", [
        _q("a", "A Caesar cipher works by:", ["Shifting each letter by a fixed amount", "Deleting letters", "Adding emojis", "Reversing words only"], "Shifting each letter by a fixed amount"),
        _q("b", "With a Caesar shift of +1, 'A' becomes:", ["B", "Z", "A", "C"], "B"),
        _q("c", "A substitution cipher replaces:", ["Each letter with another symbol/letter", "Whole sentences with images", "Numbers with colors only", "Nothing"], "Each letter with another symbol/letter"),
    ], "Encode the word 'HI' with a Caesar shift of +1 and show your work."),

    ("t3-q7", "t3", 7, "Symmetric vs Asymmetric & AI Detection", 3, "CY.3.G", "Compare encryption types; AI in security.", [
        _q("a", "Symmetric encryption uses:", ["The same key to encrypt and decrypt", "Two different keys", "No key", "A password hint"], "The same key to encrypt and decrypt"),
        _q("b", "Asymmetric encryption uses:", ["A public and a private key", "One shared key", "No keys", "A single symbol"], "A public and a private key"),
        _q("c", "AI helps cybersecurity by:", ["Detecting unusual (anomalous) activity", "Creating more viruses only", "Slowing defenses", "Guessing passwords for hackers"], "Detecting unusual (anomalous) activity"),
    ], "Why might a bank use asymmetric encryption? Explain simply."),

    ("t3-q8", "t3", 8, "Adversarial Thinking Challenge", 4, "CY.3.CAP", "Analyze a system, find weaknesses, propose defenses.", [
        _q("a", "'Thinking like an attacker' helps you:", ["Find vulnerabilities before they do", "Break laws", "Ignore risks", "Trust everything"], "Find vulnerabilities before they do"),
        _q("b", "A weak point in a school network might be:", ["Shared, simple passwords", "Strong 2FA", "Regular updates", "Encrypted data"], "Shared, simple passwords"),
        _q("c", "A good defense against phishing is:", ["Training people to spot red flags", "Turning off email forever", "Ignoring reports", "Sharing passwords"], "Training people to spot red flags"),
    ], "Pick a system (phone, app, or network) — name one weakness and one defense."),

    # ---------------- T4: Data Delta (Data Science) ----------------
    ("t4-q1", "t4", 1, "The Data Problem-Solving Process", 2, "DS.4.A", "Follow the steps of the data problem-solving process.", [
        _q("a", "The data process usually starts with:", ["Defining a question", "Making a chart", "Deleting data", "Guessing"], "Defining a question"),
        _q("b", "After collecting data you should:", ["Clean and organize it", "Ignore errors", "Publish immediately", "Delete it"], "Clean and organize it"),
        _q("c", "The final step is often to:", ["Communicate the findings", "Hide the results", "Start over randomly", "Erase everything"], "Communicate the findings"),
    ], "Write a data question you'd like to investigate about your school."),

    ("t4-q2", "t4", 2, "Choosing Data Representations", 3, "DS.4.B", "Select appropriate representations for data.", [
        _q("a", "To show change over time, use a:", ["Line graph", "Pie chart", "Word cloud", "Single number"], "Line graph"),
        _q("b", "To compare amounts across groups, use a:", ["Bar chart", "Timeline", "Paragraph", "Formula"], "Bar chart"),
        _q("c", "A table is best when you need:", ["Exact values", "A quick visual trend", "Emotion", "Decoration"], "Exact values"),
    ], "Give an example where the wrong chart could mislead someone."),

    ("t4-q3", "t4", 3, "ASCII & Binary Lab", 3, "DS.4.C", "Encode and decode text and numbers in binary.", [
        _q("a", "Binary uses only the digits:", ["0 and 1", "0 through 9", "A and B", "1 and 2"], "0 and 1"),
        _q("b", "The binary number 10 in decimal is:", ["2", "10", "1", "0"], "2"),
        _q("c", "ASCII is a system that:", ["Maps characters to numbers", "Compresses videos", "Encrypts wifi", "Draws charts"], "Maps characters to numbers"),
    ], "Convert the decimal number 5 to binary and show your steps."),

    ("t4-q4", "t4", 4, "Data Cleaning Workbench", 3, "DS.4.D", "Remove irrelevant/erroneous data.", [
        _q("a", "Data cleaning includes:", ["Fixing typos and removing duplicates", "Adding fake rows", "Random deleting", "Nothing"], "Fixing typos and removing duplicates"),
        _q("b", "'Irrelevant data' is data that:", ["Doesn't help answer the question", "Is always useful", "Must be kept", "Is encrypted"], "Doesn't help answer the question"),
        _q("c", "Dirty data can cause:", ["Wrong conclusions", "Perfect results", "Faster analysis", "No effect"], "Wrong conclusions"),
    ], "Describe a messy dataset and one thing you'd clean first."),

    ("t4-q5", "t4", 5, "Building & Reading Bar Charts", 2, "DS.4.E", "Build and interpret bar charts.", [
        _q("a", "In a bar chart, taller bars mean:", ["Larger values", "Smaller values", "Errors", "Nothing"], "Larger values"),
        _q("b", "Axis labels should:", ["Explain what is measured", "Be blank", "Be random", "Be hidden"], "Explain what is measured"),
        _q("c", "A bar chart is best for:", ["Comparing categories", "Showing exact formulas", "Encrypting data", "Writing essays"], "Comparing categories"),
    ], "What data from your class would you turn into a bar chart?"),

    ("t4-q6", "t4", 6, "Patterns & Supporting a Claim", 4, "DS.4.F", "Spot patterns and support a claim with data.", [
        _q("a", "A trend is:", ["A general pattern in the data", "A single value", "A random guess", "A title"], "A general pattern in the data"),
        _q("b", "A strong data claim is:", ["Backed by evidence from the data", "Just an opinion", "Ignoring the numbers", "Always negative"], "Backed by evidence from the data"),
        _q("c", "Correlation means two things:", ["Move together, may not cause each other", "Always cause each other", "Are unrelated", "Are equal"], "Move together, may not cause each other"),
    ], "Make a claim from imaginary data and cite the evidence you'd show."),

    ("t4-q7", "t4", 7, "Decision Algorithm Builder", 4, "DS.4.G", "Design a simple data-driven decision algorithm.", [
        _q("a", "A decision algorithm is:", ["A step-by-step rule for choosing", "A random pick", "A single number", "A drawing"], "A step-by-step rule for choosing"),
        _q("b", "'IF temperature > 30 THEN suggest water' is an example of:", ["A conditional rule", "A pie chart", "A cipher", "A footer"], "A conditional rule"),
        _q("c", "Good algorithms use ______ to decide.", ["data and clear rules", "guesses only", "feelings only", "no inputs"], "data and clear rules"),
    ], "Write a simple IF-THEN rule that helps make a decision from data."),

    ("t4-q8", "t4", 8, "AI in Data Science: ML & Data Mining", 3, "DS.4.H", "Explain ML and data mining concepts.", [
        _q("a", "Machine learning lets computers:", ["Learn patterns from data", "Only follow fixed rules", "Never improve", "Delete data"], "Learn patterns from data"),
        _q("b", "'Data mining' means:", ["Finding useful patterns in large data", "Digging for gold", "Deleting databases", "Printing reports"], "Finding useful patterns in large data"),
        _q("c", "An ML model improves when it gets:", ["More quality training data", "Less data", "No feedback", "Random noise only"], "More quality training data"),
    ], "Describe one everyday app that uses machine learning and how."),

    ("t4-q9", "t4", 9, "Career Clusters Explorer", 2, "DS.4.I", "Explore data-related career clusters.", [
        _q("a", "A cybersecurity analyst works to:", ["Protect systems and data", "Design clothing", "Cook food", "Teach music"], "Protect systems and data"),
        _q("b", "Genetics/bioinformatics uses data to:", ["Study genes and biology", "Fix cars", "Sell shoes", "Build roads"], "Study genes and biology"),
        _q("c", "A business data role helps a company:", ["Make smarter decisions with data", "Ignore its customers", "Avoid all planning", "Lose money on purpose"], "Make smarter decisions with data"),
    ], "Which data career cluster excites you most, and why?"),
]


def _lesson_for(title, sdesc):
    return [
        f"Welcome, Explorer. This quest sharpens one real skill: {title}. {sdesc}",
        "Study the lesson, ask the Copilot for a hint if you get stuck, and score at least 80% to earn your Compass Mark and full Horizon Points.",
    ]


def _build():
    quests = []
    for qid, tid, order, title, dok, code, sdesc, questions, reflection in _RAW:
        quests.append({
            "id": qid,
            "territory_id": tid,
            "order": order,
            "title": title,
            "dok": dok,
            "points": _PTS[dok],
            "standard": {"code": code, "description": sdesc},
            "lesson": _lesson_for(title, sdesc),
            "trial": {"questions": questions, "pass_threshold": 80},
            "reflection": reflection,
        })
    return quests


QUESTS = _build()
QUEST_INDEX = {q["id"]: q for q in QUESTS}
TERRITORY_INDEX = {t["id"]: t for t in TERRITORIES}


def public_curriculum():
    out_territories = []
    for t in TERRITORIES:
        tq = [q for q in QUESTS if q["territory_id"] == t["id"]]
        out_territories.append({**t, "quest_count": len(tq)})
    out_quests = []
    for q in QUESTS:
        out_quests.append({
            "id": q["id"],
            "territory_id": q["territory_id"],
            "order": q["order"],
            "title": q["title"],
            "dok": q["dok"],
            "points": q["points"],
            "standard": q["standard"],
            "lesson": q["lesson"],
            "reflection": q["reflection"],
            "trial": {
                "pass_threshold": q["trial"]["pass_threshold"],
                "questions": [
                    {"id": qq["id"], "type": qq["type"], "prompt": qq["prompt"], "options": qq["options"]}
                    for qq in q["trial"]["questions"]
                ],
            },
        })
    return {"territories": out_territories, "quests": out_quests}


def grade(quest_id, answers):
    quest = QUEST_INDEX.get(quest_id)
    if not quest:
        return None
    questions = quest["trial"]["questions"]
    total = len(questions)
    correct = 0
    per_question = {}
    for qq in questions:
        picked = answers.get(qq["id"])
        is_correct = picked is not None and picked == qq["answer"]
        if is_correct:
            correct += 1
        per_question[qq["id"]] = {"correct": is_correct, "answer": qq["answer"], "picked": picked}
    score = round((correct / total) * 100) if total else 0
    return score, correct, total, per_question
