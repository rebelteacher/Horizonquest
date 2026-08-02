"""HorizonQuest v1 Curriculum Content Pack.
4 Territories, 33 quests. Standards mapped (DOK 2-4). Auto-grading answer keys included.
"""

# Point values by DOK level
_PTS = {2: 100, 3: 150, 4: 200}

TERRITORIES = [
    {
        "id": "t1",
        "name": "The Coding Coast",
        "subtitle": "Computational Thinking Foundations",
        "order": 1,
        "color": "#06B6D4",
        "position": {"x": 18, "y": 68},
        "lore": "Where every great expedition begins — the shores of logic and instruction.",
    },
    {
        "id": "t2",
        "name": "The Data Isles",
        "subtitle": "Data, Charts & Statistics",
        "order": 2,
        "color": "#D4AF37",
        "position": {"x": 42, "y": 32},
        "lore": "Scattered islands rich with numbers waiting to be read and understood.",
    },
    {
        "id": "t3",
        "name": "The Logic Highlands",
        "subtitle": "Reasoning & Argument",
        "order": 3,
        "color": "#A855F7",
        "position": {"x": 66, "y": 60},
        "lore": "Rugged peaks where only sound reasoning finds the safe path.",
    },
    {
        "id": "t4",
        "name": "The Frontier Peaks",
        "subtitle": "Problem-Solving & Capstone",
        "order": 4,
        "color": "#E11D48",
        "position": {"x": 86, "y": 24},
        "lore": "The final, uncharted summit. Only master Explorers plant their flag here.",
    },
]


def _q(qid, prompt, options, answer):
    return {"id": qid, "type": "mc", "prompt": prompt, "options": options, "answer": answer}


# Each entry: (id, territory, order, title, dok, standard_code, standard_desc, [questions], reflection)
_RAW = [
    # ---------------- Territory 1: The Coding Coast ----------------
    ("t1-q1", "t1", 1, "Variables & Values", 2, "CS.1.A", "Store and retrieve values using named variables.", [
        _q("a", "What does a variable do in a program?", ["Stores a value you can reuse", "Deletes the program", "Prints the screen color", "Slows the computer"], "Stores a value you can reuse"),
        _q("b", "If score = 5 and then score = 8, what is the value of score now?", ["5", "8", "13", "Error"], "8"),
        _q("c", "Which is a valid variable name?", ["2fast", "player_lives", "my name", "$$$"], "player_lives"),
    ], "In your own words, describe something in real life you could track with a variable."),

    ("t1-q2", "t1", 2, "Sequencing & Algorithms", 2, "CS.1.B", "Order steps correctly to accomplish a task.", [
        _q("a", "An algorithm is best described as:", ["A random guess", "A step-by-step set of instructions", "A type of computer", "A drawing"], "A step-by-step set of instructions"),
        _q("b", "To make toast, which step comes FIRST?", ["Spread butter", "Put bread in toaster", "Eat toast", "Wait for it to pop"], "Put bread in toaster"),
        _q("c", "Why does order matter in an algorithm?", ["It doesn't matter", "Wrong order can give a wrong result", "It makes it longer", "It saves battery"], "Wrong order can give a wrong result"),
    ], "Write a 4-step algorithm for a daily task you do."),

    ("t1-q3", "t1", 3, "Loops & Iteration", 3, "CS.1.C", "Use loops to repeat actions efficiently.", [
        _q("a", "A loop is used to:", ["Repeat a block of instructions", "End the program", "Store text", "Change the color"], "Repeat a block of instructions"),
        _q("b", "How many times does 'repeat 3 times: step forward' move you?", ["1", "2", "3", "Infinite"], "3"),
        _q("c", "Which task is BEST solved with a loop?", ["Printing 'hi' 100 times", "Adding two numbers once", "Naming a variable", "Turning off the screen"], "Printing 'hi' 100 times"),
    ], "Give an example of something repetitive a loop could automate for you."),

    ("t1-q4", "t1", 4, "Conditionals & Branching", 3, "CS.1.D", "Make decisions in code using if/else logic.", [
        _q("a", "An IF statement lets a program:", ["Make a decision", "Repeat forever", "Store a list", "Draw a circle"], "Make a decision"),
        _q("b", "'IF raining THEN take umbrella' — you take an umbrella when:", ["Always", "It is raining", "It is sunny", "Never"], "It is raining"),
        _q("c", "The ELSE branch runs when:", ["The IF condition is true", "The IF condition is false", "The program starts", "You press a key"], "The IF condition is false"),
    ], "Describe a decision in a game that could use an if/else."),

    ("t1-q5", "t1", 5, "Functions & Abstraction", 3, "CS.1.E", "Package reusable behavior into functions.", [
        _q("a", "A function is like:", ["A reusable mini-program", "A single number", "A screen", "A mouse"], "A reusable mini-program"),
        _q("b", "Why use functions?", ["To avoid repeating code", "To slow things down", "To use more memory", "To confuse people"], "To avoid repeating code"),
        _q("c", "'Abstraction' means:", ["Hiding details to focus on what matters", "Adding more details", "Deleting the code", "Painting"], "Hiding details to focus on what matters"),
    ], "Name a function you would create to help in a project."),

    ("t1-q6", "t1", 6, "Debugging Strategies", 3, "CS.1.F", "Locate and fix errors systematically.", [
        _q("a", "A 'bug' in code is:", ["An error or mistake", "A new feature", "A fast program", "An insect icon"], "An error or mistake"),
        _q("b", "A good FIRST debugging step is:", ["Delete everything", "Read the error and test small parts", "Restart the computer", "Give up"], "Read the error and test small parts"),
        _q("c", "Testing your code often helps you:", ["Find bugs early", "Make more bugs", "Skip planning", "Avoid learning"], "Find bugs early"),
    ], "Describe a time you fixed a mistake by breaking a problem into parts."),

    ("t1-q7", "t1", 7, "Decomposition", 3, "CS.1.G", "Break large problems into smaller solvable parts.", [
        _q("a", "Decomposition means:", ["Breaking a big problem into smaller ones", "Rotting food", "Adding complexity", "Ignoring the problem"], "Breaking a big problem into smaller ones"),
        _q("b", "Building a whole game is easier if you:", ["Do it all at once", "Split it into features", "Never plan", "Copy randomly"], "Split it into features"),
        _q("c", "Smaller sub-problems are usually:", ["Easier to solve and test", "Impossible", "Useless", "Slower always"], "Easier to solve and test"),
    ], "Break down 'plan a birthday party' into 3 smaller tasks."),

    ("t1-q8", "t1", 8, "Pattern Recognition", 4, "CS.1.H", "Identify patterns to generalize solutions.", [
        _q("a", "Recognizing patterns helps you:", ["Predict and reuse solutions", "Forget the problem", "Slow down", "Add errors"], "Predict and reuse solutions"),
        _q("b", "In 2, 4, 6, 8, ... the next number is:", ["9", "10", "12", "7"], "10"),
        _q("c", "Patterns let programmers:", ["Generalize one solution to many cases", "Avoid all thinking", "Write longer code always", "Break the internet"], "Generalize one solution to many cases"),
    ], "Describe a pattern you notice in nature or daily life and how you'd use it."),

    # ---------------- Territory 2: The Data Isles ----------------
    ("t2-q1", "t2", 1, "Reading Data Tables", 2, "DA.2.A", "Extract values from organized data tables.", [
        _q("a", "A data table organizes information into:", ["Rows and columns", "Circles", "Sounds", "Random piles"], "Rows and columns"),
        _q("b", "To find one student's score, you look at:", ["Their row", "The title only", "The last column always", "Nowhere"], "Their row"),
        _q("c", "Column headers tell you:", ["What each column means", "The password", "The date only", "Nothing"], "What each column means"),
    ], "Describe a table you might make to track your week."),

    ("t2-q2", "t2", 2, "Measures of Center", 2, "DA.2.B", "Compute mean, median, and mode.", [
        _q("a", "The mean of 2, 4, 6 is:", ["2", "4", "6", "12"], "4"),
        _q("b", "The median of 3, 7, 9 is:", ["3", "7", "9", "6"], "7"),
        _q("c", "The mode is the value that:", ["Appears most often", "Is largest", "Is smallest", "Is the average"], "Appears most often"),
    ], "When would the median be a better summary than the mean?"),

    ("t2-q3", "t2", 3, "Range & Spread", 3, "DA.2.C", "Measure how spread out data is.", [
        _q("a", "The range of 5, 2, 9 is:", ["7", "9", "2", "16"], "7"),
        _q("b", "A large range means the data is:", ["More spread out", "All the same", "Wrong", "Small"], "More spread out"),
        _q("c", "Range is calculated by:", ["Max minus min", "Adding all values", "Middle value", "Most common value"], "Max minus min"),
    ], "Give an example where knowing the spread matters more than the average."),

    ("t2-q4", "t2", 4, "Building Bar Charts", 2, "DA.2.D", "Represent categorical data with bar charts.", [
        _q("a", "Bar charts are best for comparing:", ["Categories", "One number", "Colors only", "Time of day"], "Categories"),
        _q("b", "Taller bars represent:", ["Larger values", "Smaller values", "Errors", "Nothing"], "Larger values"),
        _q("c", "The axis labels should:", ["Explain what is measured", "Be blank", "Be random", "Be hidden"], "Explain what is measured"),
    ], "What data from your class would you show in a bar chart?"),

    ("t2-q5", "t2", 5, "Interpreting Graphs", 3, "DA.2.E", "Draw meaning from visualized data.", [
        _q("a", "A line going up over time shows:", ["An increase", "A decrease", "No change", "An error"], "An increase"),
        _q("b", "The best way to spot a trend is to:", ["Look at the overall direction", "Read one point", "Ignore the axes", "Guess"], "Look at the overall direction"),
        _q("c", "A misleading graph often has:", ["A cut-off or unlabeled axis", "Clear labels", "Honest scale", "A title"], "A cut-off or unlabeled axis"),
    ], "Describe a graph you've seen and what story it told."),

    ("t2-q6", "t2", 6, "Probability Basics", 3, "DA.2.F", "Reason about the likelihood of events.", [
        _q("a", "The probability of flipping heads on a fair coin is:", ["1/2", "1/6", "1", "0"], "1/2"),
        _q("b", "A probability of 0 means the event is:", ["Impossible", "Certain", "Likely", "Unknown"], "Impossible"),
        _q("c", "Rolling a 7 on a normal 6-sided die has probability:", ["0", "1/6", "1/2", "1"], "0"),
    ], "Describe an event in your life that is 'likely' vs 'unlikely'."),

    ("t2-q7", "t2", 7, "Data Cleaning", 3, "DA.2.G", "Identify and handle messy or missing data.", [
        _q("a", "'Dirty data' might include:", ["Typos and missing values", "Perfect numbers", "Nothing", "Only titles"], "Typos and missing values"),
        _q("b", "Before analyzing, you should:", ["Clean and check the data", "Delete it all", "Ignore errors", "Add fake rows"], "Clean and check the data"),
        _q("c", "A missing value should be:", ["Handled carefully", "Always replaced with 0", "Ignored forever", "Randomized"], "Handled carefully"),
    ], "Why can bad data lead to bad decisions? Give an example."),

    ("t2-q8", "t2", 8, "Drawing Conclusions from Data", 4, "DA.2.H", "Make and defend claims supported by evidence.", [
        _q("a", "A good conclusion from data is:", ["Supported by the evidence", "A random opinion", "Ignoring the numbers", "Always negative"], "Supported by the evidence"),
        _q("b", "Correlation means two things:", ["Move together, but may not cause each other", "Are always cause and effect", "Are unrelated", "Are equal"], "Move together, but may not cause each other"),
        _q("c", "To trust a conclusion you should ask:", ["Is the data enough and fair?", "Is it colorful?", "Is it short?", "Who made it famous?"], "Is the data enough and fair?"),
    ], "Make a claim from imaginary data and explain your evidence."),

    # ---------------- Territory 3: The Logic Highlands ----------------
    ("t3-q1", "t3", 1, "True / False Statements", 2, "LO.3.A", "Classify statements as true or false.", [
        _q("a", "A statement that must be true or false is called a:", ["Proposition", "Question", "Command", "Guess"], "Proposition"),
        _q("b", "'The sky is green' is:", ["False", "True", "A question", "A command"], "False"),
        _q("c", "'2 + 2 = 4' is:", ["True", "False", "Unknown", "A guess"], "True"),
    ], "Write one true and one false statement about your favorite topic."),

    ("t3-q2", "t3", 2, "AND / OR / NOT", 2, "LO.3.B", "Combine conditions with logical operators.", [
        _q("a", "'A AND B' is true when:", ["Both are true", "Either is true", "Both are false", "Never"], "Both are true"),
        _q("b", "'A OR B' is true when:", ["At least one is true", "Both are false", "Never", "Only both"], "At least one is true"),
        _q("c", "'NOT true' equals:", ["False", "True", "Maybe", "Both"], "False"),
    ], "Describe a rule that uses AND (e.g., entry requires ticket AND ID)."),

    ("t3-q3", "t3", 3, "If-Then Reasoning", 3, "LO.3.C", "Evaluate conditional statements.", [
        _q("a", "'If it rains, then the ground is wet.' It rains. So:", ["The ground is wet", "It is sunny", "Nothing happens", "The ground is dry"], "The ground is wet"),
        _q("b", "The 'if' part of a conditional is the:", ["Hypothesis", "Conclusion", "Answer", "Error"], "Hypothesis"),
        _q("c", "A conditional can be false when:", ["The if is true but the then is false", "Both are true", "Both are false", "Never"], "The if is true but the then is false"),
    ], "Write an if-then rule for a game or a chore."),

    ("t3-q4", "t3", 4, "Logical Fallacies", 3, "LO.3.D", "Spot flawed reasoning.", [
        _q("a", "Attacking the person instead of their argument is called:", ["Ad hominem", "Evidence", "A fact", "A theorem"], "Ad hominem"),
        _q("b", "'Everyone does it, so it's right' is a:", ["Bandwagon fallacy", "Valid proof", "Statistic", "Definition"], "Bandwagon fallacy"),
        _q("c", "A strong argument relies on:", ["Evidence and logic", "Insults", "Popularity", "Volume"], "Evidence and logic"),
    ], "Describe a flawed argument you've heard and why it's weak."),

    ("t3-q5", "t3", 5, "Sets & Venn Diagrams", 3, "LO.3.E", "Represent groups and overlaps with sets.", [
        _q("a", "The overlap of two circles in a Venn diagram shows items that are:", ["In both sets", "In neither", "Only in one", "Deleted"], "In both sets"),
        _q("b", "The union of sets A and B contains:", ["Everything in A or B", "Only shared items", "Nothing", "Only A"], "Everything in A or B"),
        _q("c", "The intersection of {1,2,3} and {2,3,4} is:", ["{2,3}", "{1,4}", "{1,2,3,4}", "{}"], "{2,3}"),
    ], "Draw (describe) a Venn diagram for two of your interests."),

    ("t3-q6", "t3", 6, "Sequences & Patterns", 3, "LO.3.F", "Extend and generalize patterns.", [
        _q("a", "In 1, 3, 5, 7, ... the next is:", ["8", "9", "10", "11"], "9"),
        _q("b", "In 3, 6, 12, 24, ... the pattern is:", ["Double each time", "Add 3", "Subtract 3", "Random"], "Double each time"),
        _q("c", "A rule for a pattern helps you:", ["Predict future terms", "Forget the pattern", "Slow down", "Make errors"], "Predict future terms"),
    ], "Invent a number pattern and state its rule."),

    ("t3-q7", "t3", 7, "Deductive Reasoning", 4, "LO.3.G", "Reach valid conclusions from premises.", [
        _q("a", "All Explorers wear compasses. Mia is an Explorer. So Mia:", ["Wears a compass", "Has no compass", "Might be a Guide", "Is lost"], "Wears a compass"),
        _q("b", "Deduction moves from:", ["General rules to specific cases", "Guesses to facts", "Nothing to something", "Colors to sounds"], "General rules to specific cases"),
        _q("c", "A valid argument with true premises has:", ["A true conclusion", "A false conclusion", "No conclusion", "An error"], "A true conclusion"),
    ], "Write your own two premises that lead to a valid conclusion."),

    ("t3-q8", "t3", 8, "Puzzle Mastery", 4, "LO.3.H", "Apply combined reasoning to solve puzzles.", [
        _q("a", "The best puzzle strategy is to:", ["Use clues to eliminate options", "Guess wildly", "Give up", "Skip clues"], "Use clues to eliminate options"),
        _q("b", "If A > B and B > C, then:", ["A > C", "C > A", "A = C", "Unknown"], "A > C"),
        _q("c", "When stuck on a puzzle, a good move is to:", ["Re-check the clues", "Erase everything", "Panic", "Change the rules"], "Re-check the clues"),
    ], "Describe a puzzle you solved and the strategy you used."),

    # ---------------- Territory 4: The Frontier Peaks ----------------
    ("t4-q1", "t4", 1, "Defining the Problem", 3, "PS.4.A", "State a problem clearly before solving.", [
        _q("a", "A well-defined problem includes:", ["A clear goal and constraints", "Only a guess", "No details", "Random words"], "A clear goal and constraints"),
        _q("b", "Before solving, you should:", ["Understand what's being asked", "Start randomly", "Copy an answer", "Give up"], "Understand what's being asked"),
        _q("c", "A vague problem statement leads to:", ["Confused solutions", "Perfect answers", "Faster work", "No effort needed"], "Confused solutions"),
    ], "Restate a problem you face this week clearly, with its goal."),

    ("t4-q2", "t4", 2, "Breaking Down Complexity", 3, "PS.4.B", "Manage complexity with structured steps.", [
        _q("a", "Complex problems are handled best by:", ["Breaking them into parts", "Ignoring them", "Solving all at once", "Guessing"], "Breaking them into parts"),
        _q("b", "A milestone is:", ["A smaller checkpoint goal", "The final answer only", "A mistake", "A distraction"], "A smaller checkpoint goal"),
        _q("c", "Tracking sub-tasks helps you:", ["See progress", "Lose focus", "Add errors", "Skip work"], "See progress"),
    ], "List the milestones for a project you'd like to complete."),

    ("t4-q3", "t4", 3, "Estimation Skills", 3, "PS.4.C", "Make reasonable estimates to guide decisions.", [
        _q("a", "A good estimate is:", ["Close enough to be useful", "Always exact", "A random number", "Never needed"], "Close enough to be useful"),
        _q("b", "Estimating 19 x 21 is about:", ["400", "40", "4000", "20"], "400"),
        _q("c", "Estimation is useful when:", ["You need a quick, rough answer", "You have infinite time", "Exactness is impossible ever", "You want errors"], "You need a quick, rough answer"),
    ], "Estimate how many steps you take in a day and explain your reasoning."),

    ("t4-q4", "t4", 4, "Working Backwards", 3, "PS.4.D", "Solve by starting from the goal.", [
        _q("a", "Working backwards starts from:", ["The desired result", "A random step", "The middle", "Nothing"], "The desired result"),
        _q("b", "This strategy works well for:", ["Mazes and planning", "Nothing", "Only art", "Only sports"], "Mazes and planning"),
        _q("c", "To be home by 6, working backwards helps you find:", ["When to leave", "The weather", "Your shoe size", "A password"], "When to leave"),
    ], "Pick a goal and plan the last 3 steps backwards from it."),

    ("t4-q5", "t4", 5, "Modeling with Math", 4, "PS.4.E", "Represent real situations with math models.", [
        _q("a", "A model is:", ["A simplified representation of reality", "A perfect copy", "A guess", "A drawing only"], "A simplified representation of reality"),
        _q("b", "If a ticket costs 8 and you buy n, the cost model is:", ["8 * n", "8 + n", "8 - n", "n / 8"], "8 * n"),
        _q("c", "Good models help you:", ["Predict outcomes", "Ignore reality", "Slow down", "Add confusion"], "Predict outcomes"),
    ], "Describe a real situation and a simple math model for it."),

    ("t4-q6", "t4", 6, "Optimization Choices", 4, "PS.4.F", "Choose the best option under constraints.", [
        _q("a", "Optimization means finding the:", ["Best option given limits", "Slowest option", "Most expensive option", "Random option"], "Best option given limits"),
        _q("b", "A 'trade-off' is:", ["Giving up one thing for another", "Getting everything", "A free lunch", "A mistake"], "Giving up one thing for another"),
        _q("c", "With a tight budget you optimize for:", ["Value within the budget", "Highest price", "No plan", "Waste"], "Value within the budget"),
    ], "Describe a decision where you balanced two trade-offs."),

    ("t4-q7", "t4", 7, "Systems Thinking", 4, "PS.4.G", "See how parts of a system interact.", [
        _q("a", "Systems thinking focuses on:", ["How parts connect and affect each other", "One part alone", "Ignoring connections", "Random parts"], "How parts connect and affect each other"),
        _q("b", "A change in one part of a system can:", ["Affect other parts", "Never matter", "Only help", "Disappear"], "Affect other parts"),
        _q("c", "A feedback loop is when:", ["An output influences the input", "Nothing connects", "The system stops", "Data is deleted"], "An output influences the input"),
    ], "Describe a system you know and how its parts affect each other."),

    ("t4-q8", "t4", 8, "Ethical Tech Decisions", 4, "PS.4.H", "Weigh fairness and impact in technology.", [
        _q("a", "An ethical decision considers:", ["Fairness and impact on people", "Only speed", "Only profit", "Nothing"], "Fairness and impact on people"),
        _q("b", "Biased data in a system can cause:", ["Unfair outcomes", "Perfect fairness", "Faster results only", "No effect"], "Unfair outcomes"),
        _q("c", "Responsible creators should:", ["Consider consequences of their work", "Ignore users", "Hide problems", "Rush blindly"], "Consider consequences of their work"),
    ], "Describe a technology and one ethical question it raises."),

    ("t4-q9", "t4", 9, "Capstone: The Grand Expedition", 4, "PS.4.CAP", "Integrate all skills to solve a complex challenge.", [
        _q("a", "To plan a real expedition you'd FIRST:", ["Define the goal and constraints", "Buy random things", "Skip planning", "Start walking"], "Define the goal and constraints"),
        _q("b", "You'd use DATA skills to:", ["Compare routes and supplies", "Guess blindly", "Ignore facts", "Avoid math"], "Compare routes and supplies"),
        _q("c", "You'd use LOGIC to:", ["Reason through decisions", "Argue loudly", "Skip clues", "Panic"], "Reason through decisions"),
        _q("d", "A capstone shows that you can:", ["Combine many skills to solve a big problem", "Do only one thing", "Avoid challenges", "Forget everything"], "Combine many skills to solve a big problem"),
    ], "Design your own grand expedition: state the goal, the data you'd gather, and the key decisions."),
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


def _lesson_for(title, sdesc):
    return [
        f"Welcome, Explorer. In this trial you'll master {title}. {sdesc}",
        "Read carefully, use the Copilot if you get stuck, and aim for at least 80% to earn your Compass Mark and full Horizon Points.",
    ]


QUESTS = _build()

QUEST_INDEX = {q["id"]: q for q in QUESTS}
TERRITORY_INDEX = {t["id"]: t for t in TERRITORIES}


def public_curriculum():
    """Curriculum without answer keys (safe for the client)."""
    out_territories = []
    for t in TERRITORIES:
        tq = sorted([q for q in QUESTS if q["territory_id"] == t["id"]], key=lambda x: x["order"])
        out_territories.append({**t, "quest_count": len(tq)})
    out_quests = []
    for q in QUESTS:
        oq = {
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
        }
        out_quests.append(oq)
    return {"territories": out_territories, "quests": out_quests}


def grade(quest_id, answers):
    """answers: {question_id: selected_option}. Returns (score_pct, correct, total, per_question)."""
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
