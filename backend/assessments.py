"""Assessment engine: checkpoint tests (every 4 Skill Studio lessons) + a comprehensive final.

Anti-cheating: each attempt draws a random subset from a larger pool and shuffles the
answer options per student. Correct answers are stored in the bank as the FIRST option and
never leave the server except as a scrambled position inside the attempt record.
"""
import random

from bank_docs import DOCS
from bank_sheets import SHEETS
from bank_slides import SLIDES
from bank_email import EMAIL
from bank_final import FINAL

CHECKPOINT_DRAW = 20          # questions shown per checkpoint attempt
CHECKPOINT_PASS = 70          # % needed to pass a checkpoint
CHECKPOINT_POINTS = 150       # Horizon Points for passing a checkpoint (first pass)
CHECKPOINT_MAX_ATTEMPTS = 2   # original + 1 retake
FINAL_MAX_ATTEMPTS = 1        # no retakes

# Ordered checkpoints per track (used to build the Studio hub cards in order).
CHECKPOINTS = {}
for _bank in (DOCS, SHEETS, SLIDES, EMAIL):
    CHECKPOINTS.update(_bank)

TRACK_CHECKPOINTS = {
    "docs": ["docs-cp1", "docs-cp2", "docs-cp3"],
    "sheets": ["sheets-cp1", "sheets-cp2", "sheets-cp3"],
    "slides": ["slides-cp1", "slides-cp2", "slides-cp3"],
    "email": ["email-cp1", "email-cp2", "email-cp3"],
}

FINAL_ID = "final"


def _norm(pool_item):
    """Bank item [question, correct, w1, w2, w3] -> (question, correct_text, [all options])."""
    q = pool_item[0]
    correct = pool_item[1]
    opts = list(pool_item[1:])
    return q, correct, opts


def assessment_meta(assessment_id):
    if assessment_id == FINAL_ID:
        return {
            "id": FINAL_ID, "kind": "final", "title": FINAL["title"],
            "question_count": FINAL.get("draw", 25), "pass": FINAL.get("pass", 70),
            "max_attempts": FINAL_MAX_ATTEMPTS, "pool_size": len(FINAL["pool"]),
        }
    cp = CHECKPOINTS.get(assessment_id)
    if not cp:
        return None
    return {
        "id": assessment_id, "kind": "checkpoint", "track": cp["track"], "title": cp["title"],
        "covers": cp["covers"], "question_count": CHECKPOINT_DRAW, "pass": CHECKPOINT_PASS,
        "max_attempts": CHECKPOINT_MAX_ATTEMPTS, "pool_size": len(cp["pool"]),
        "points": CHECKPOINT_POINTS,
    }


def track_checkpoint_metas(track):
    return [assessment_meta(cid) for cid in TRACK_CHECKPOINTS.get(track, [])]


def build_attempt_questions(assessment_id):
    """Draw a randomized, option-shuffled set of questions for one attempt.

    Returns (public_questions, answer_key) where answer_key maps qid -> correct option index
    within that attempt's shuffled options.
    """
    if assessment_id == FINAL_ID:
        pool, draw = FINAL["pool"], FINAL.get("draw", 25)
    else:
        cp = CHECKPOINTS.get(assessment_id)
        if not cp:
            return None, None
        pool, draw = cp["pool"], CHECKPOINT_DRAW

    n = min(draw, len(pool))
    chosen = random.sample(pool, n)
    public, key = [], {}
    for i, item in enumerate(chosen):
        _q, correct, opts = _norm(item)
        shuffled = opts[:]
        random.shuffle(shuffled)
        qid = f"q{i}"
        key[qid] = shuffled.index(correct)
        public.append({"qid": qid, "question": _q, "options": shuffled})
    return public, key


def grade_attempt(answer_key, answers):
    """answers: {qid: chosen_index}. Returns (score_pct, correct_count, total)."""
    total = len(answer_key)
    correct = 0
    for qid, correct_idx in answer_key.items():
        try:
            if int(answers.get(qid, -1)) == correct_idx:
                correct += 1
        except (TypeError, ValueError):
            pass
    score = round(correct / total * 100) if total else 0
    return score, correct, total



def _dump(assessment_id, cfg):
    return {"id": assessment_id, "title": cfg["title"],
            "questions": [{"n": i + 1, "q": it[0], "correct": it[1], "options": list(it[1:])}
                          for i, it in enumerate(cfg["pool"])]}


def full_bank():
    """Guide-only: every question with its correct answer, for review/approval."""
    out = {"tracks": {}, "final": _dump(FINAL_ID, FINAL)}
    for track, cids in TRACK_CHECKPOINTS.items():
        out["tracks"][track] = [_dump(cid, CHECKPOINTS[cid]) for cid in cids]
    return out
