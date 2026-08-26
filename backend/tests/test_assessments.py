"""Assessments module tests: randomization, grading, retake limits, points, unlock gate,
final exam, guide preview, gradebook, student scores."""
import os
import uuid

import pytest
import requests
from dotenv import dotenv_values
from pymongo import MongoClient

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/") + "/api"

backend_env = dotenv_values("/app/backend/.env")
MONGO_URL = os.environ.get("MONGO_URL") or backend_env.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME") or backend_env.get("DB_NAME")

CP1 = "email-cp1"
CP1_COVERS = ["email-b1", "email-b2", "email-m1", "email-m2"]

GUIDE_TOK = "em_guide_tok"
GUIDE_EXPEDITION = "exp_61e14d36b5eb"


@pytest.fixture(scope="session")
def mongo():
    client = MongoClient(MONGO_URL)
    yield client[DB_NAME]
    client.close()


@pytest.fixture(scope="session")
def qa_explorer(mongo):
    """Fresh explorer with the email-cp1 covered missions passed (checkpoint unlocked)."""
    uid = "qa-asmt-" + uuid.uuid4().hex[:6]
    tok = "qa_asmt_tok_" + uuid.uuid4().hex[:8]
    mongo.users.insert_one({"user_id": uid, "email": f"TEST_{uid}@test.com", "name": "TEST Assess Explorer",
                            "picture": "", "role": "explorer", "horizon_points": 0, "compass_marks": 0,
                            "fleet": None, "expedition_ids": [GUIDE_EXPEDITION]})
    mongo.user_sessions.insert_one({"user_id": uid, "session_token": tok,
                                    "expires_at": "2099-01-01T00:00:00+00:00"})
    yield {"uid": uid, "token": tok}
    mongo.users.delete_many({"user_id": uid})
    mongo.user_sessions.delete_many({"user_id": uid})
    mongo.assessment_attempts.delete_many({"user_id": uid})
    mongo.studio_progress.delete_many({"user_id": uid})
    mongo.points_events.delete_many({"user_id": uid})


def hdr(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def unlock_cp1(mongo, uid):
    # The checkpoint gate requires the block's lessons AND its Block Task to be passed.
    for mid in list(CP1_COVERS) + ["email-task1"]:
        mongo.studio_progress.update_one({"user_id": uid, "mission_id": mid},
                                         {"$set": {"score": 100, "track": "email"}}, upsert=True)


def start(tok, aid=CP1):
    return requests.post(f"{BASE_URL}/assessments/{aid}/start", headers=hdr(tok), timeout=30)


def answer_all(mongo, attempt_id, correct=True):
    doc = mongo.assessment_attempts.find_one({"attempt_id": attempt_id})
    key = doc["answer_key"]
    if correct:
        return {q: i for q, i in key.items()}
    return {q: (i + 1) % 4 for q, i in key.items()}


def submit(tok, attempt_id, answers):
    return requests.post(f"{BASE_URL}/assessments/attempts/{attempt_id}/submit",
                         headers=hdr(tok), json={"answers": answers}, timeout=30)


# ---------------- Unlock gate ----------------
class TestUnlockGate:
    def test_locked_before_missions(self, mongo, qa_explorer):
        mongo.studio_progress.delete_many({"user_id": qa_explorer["uid"]})
        r = requests.get(f"{BASE_URL}/assessments/track/email", headers=hdr(qa_explorer["token"]), timeout=30)
        assert r.status_code == 200
        cps = r.json()["checkpoints"]
        assert len(cps) == 3
        cp1 = next(c for c in cps if c["id"] == CP1)
        assert cp1["unlocked"] is False
        assert cp1["locked_reason"]
        assert cp1["covers"] == CP1_COVERS
        assert cp1["question_count"] == 20 and cp1["pass"] == 70 and cp1["max_attempts"] == 2

    def test_start_locked_403(self, qa_explorer):
        r = start(qa_explorer["token"])
        assert r.status_code == 403, r.text
        assert "block" in r.json()["detail"].lower() or "lesson" in r.json()["detail"].lower()

    def test_unlocks_after_missions_passed(self, mongo, qa_explorer):
        unlock_cp1(mongo, qa_explorer["uid"])
        r = requests.get(f"{BASE_URL}/assessments/track/email", headers=hdr(qa_explorer["token"]), timeout=30)
        cp1 = next(c for c in r.json()["checkpoints"] if c["id"] == CP1)
        assert cp1["unlocked"] is True
        s = start(qa_explorer["token"])
        assert s.status_code == 200, s.text
        mongo.assessment_attempts.delete_many({"user_id": qa_explorer["uid"]})


# ---------------- Randomization / anti-cheat ----------------
class TestRandomization:
    def test_two_starts_differ(self, mongo, qa_explorer):
        unlock_cp1(mongo, qa_explorer["uid"])
        mongo.assessment_attempts.delete_many({"user_id": qa_explorer["uid"]})
        a = start(qa_explorer["token"])
        assert a.status_code == 200, a.text
        # An unsubmitted attempt is intentionally reused, so submit A before drawing B.
        aid = a.json()["attempt_id"]
        submit(qa_explorer["token"], aid, answer_all(mongo, aid, correct=False))
        b = start(qa_explorer["token"])
        assert b.status_code == 200, b.text
        qa, qb = a.json()["questions"], b.json()["questions"]
        assert len(qa) == 20 and len(qb) == 20
        for q in qa + qb:
            assert len(q["options"]) == 4
            assert len(set(q["options"])) == 4
        sig_a = [(q["question"], tuple(q["options"])) for q in qa]
        sig_b = [(q["question"], tuple(q["options"])) for q in qb]
        assert sig_a != sig_b, "Two attempts produced identical question/option ordering"
        mongo.assessment_attempts.delete_many({"user_id": qa_explorer["uid"]})


# ---------------- Grading, points, retakes ----------------
class TestGradingAndPoints:
    def test_fail_then_pass_points_and_retake_limit(self, mongo, qa_explorer):
        uid, tok = qa_explorer["uid"], qa_explorer["token"]
        unlock_cp1(mongo, uid)
        mongo.assessment_attempts.delete_many({"user_id": uid})
        mongo.users.update_one({"user_id": uid}, {"$set": {"horizon_points": 0}})

        # Attempt 1: fail
        a1 = start(tok)
        assert a1.status_code == 200
        aid1 = a1.json()["attempt_id"]
        r1 = submit(tok, aid1, answer_all(mongo, aid1, correct=False))
        assert r1.status_code == 200, r1.text
        d1 = r1.json()
        assert d1["score"] == 0 and d1["passed"] is False
        assert d1["total"] == 20 and d1["correct"] == 0
        assert d1["points_awarded"] == 0
        assert d1["attempts_used"] == 1 and d1["attempts_remaining"] == 1
        assert len(d1["review"]) == 20
        assert all(set(x) >= {"question", "options", "correct", "chosen"} for x in d1["review"])
        u = mongo.users.find_one({"user_id": uid})
        assert u["horizon_points"] == 0

        # double submit blocked
        assert submit(tok, aid1, {"q0": 0}).status_code == 400

        # Attempt 2: pass with 100%
        a2 = start(tok)
        assert a2.status_code == 200
        aid2 = a2.json()["attempt_id"]
        r2 = submit(tok, aid2, answer_all(mongo, aid2, correct=True))
        d2 = r2.json()
        assert d2["score"] == 100 and d2["passed"] is True and d2["correct"] == 20
        assert d2["points_awarded"] == 150
        assert d2["attempts_used"] == 2 and d2["attempts_remaining"] == 0
        u = mongo.users.find_one({"user_id": uid})
        assert u["horizon_points"] == 150, f"points not incremented: {u['horizon_points']}"

        # 3rd start blocked
        a3 = start(tok)
        assert a3.status_code == 403, a3.text
        assert a3.json()["detail"] == "No attempts remaining"

        # /me/assessments reflects results
        me = requests.get(f"{BASE_URL}/me/assessments", headers=hdr(tok), timeout=30)
        assert me.status_code == 200
        items = me.json()
        assert len(items) == 13
        cp1 = next(i for i in items if i["id"] == CP1)
        assert cp1["best_score"] == 100 and cp1["passed"] is True and cp1["attempts_used"] == 2
        other = next(i for i in items if i["id"] == "docs-cp1")
        assert other["best_score"] is None and other["attempts_used"] == 0
        assert any(i["id"] == "final" for i in items)

    def test_no_double_points_on_second_pass(self, mongo, qa_explorer):
        """A second passing attempt must award 0 points."""
        uid, tok = qa_explorer["uid"], qa_explorer["token"]
        unlock_cp1(mongo, uid)
        mongo.assessment_attempts.delete_many({"user_id": uid})
        mongo.users.update_one({"user_id": uid}, {"$set": {"horizon_points": 0}})
        aid1 = start(tok).json()["attempt_id"]
        d1 = submit(tok, aid1, answer_all(mongo, aid1, True)).json()
        assert d1["points_awarded"] == 150
        aid2 = start(tok).json()["attempt_id"]
        d2 = submit(tok, aid2, answer_all(mongo, aid2, True)).json()
        assert d2["passed"] is True
        assert d2["points_awarded"] == 0, "points awarded twice for the same checkpoint"
        u = mongo.users.find_one({"user_id": uid})
        assert u["horizon_points"] == 150
        mongo.assessment_attempts.delete_many({"user_id": uid})


# ---------------- Final exam ----------------
class TestFinalExam:
    def test_final_meta(self, qa_explorer):
        r = requests.get(f"{BASE_URL}/assessments/final/meta", headers=hdr(qa_explorer["token"]), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["question_count"] == 25 and d["pass"] == 70 and d["max_attempts"] == 1
        assert d["pool_size"] >= 30 and d["unlocked"] is True

    def test_final_single_attempt(self, mongo, qa_explorer):
        uid, tok = qa_explorer["uid"], qa_explorer["token"]
        mongo.assessment_attempts.delete_many({"user_id": uid, "assessment_id": "final"})
        a = start(tok, "final")
        assert a.status_code == 200, a.text
        qs = a.json()["questions"]
        assert len(qs) == 25
        aid = a.json()["attempt_id"]
        d = submit(tok, aid, answer_all(mongo, aid, True)).json()
        assert d["score"] == 100 and d["passed"] is True
        assert d["points_awarded"] == 0, "final exam should not award checkpoint points"
        assert d["attempts_remaining"] == 0
        a2 = start(tok, "final")
        assert a2.status_code == 403, a2.text
        mongo.assessment_attempts.delete_many({"user_id": uid})

    def test_unknown_assessment_404(self, qa_explorer):
        r = start(qa_explorer["token"], "does-not-exist")
        assert r.status_code == 404


# ---------------- Guide preview ----------------
class TestGuidePreview:
    def test_guide_preview_not_persisted(self, mongo):
        before = mongo.users.find_one({"user_id": "em-guide"}).get("horizon_points", 0)
        a = start(GUIDE_TOK, CP1)  # locked for explorers; guides bypass
        assert a.status_code == 200, a.text
        aid = a.json()["attempt_id"]
        d = submit(GUIDE_TOK, aid, answer_all(mongo, aid, True)).json()
        assert d["preview"] is True
        assert d["points_awarded"] == 0
        assert d["score"] == 100
        assert mongo.assessment_attempts.find_one({"attempt_id": aid}) is None, "guide attempt persisted"
        assert mongo.assessment_attempts.count_documents({"user_id": "em-guide"}) == 0
        after = mongo.users.find_one({"user_id": "em-guide"}).get("horizon_points", 0)
        assert after == before

    def test_guide_ignores_attempt_cap(self, mongo):
        for _ in range(3):
            a = start(GUIDE_TOK, CP1)
            assert a.status_code == 200
            mongo.assessment_attempts.delete_one({"attempt_id": a.json()["attempt_id"]})


# ---------------- Gradebook ----------------
class TestGradebook:
    def test_reports_guide_only(self, qa_explorer):
        r = requests.get(f"{BASE_URL}/assessments/reports", headers=hdr(qa_explorer["token"]), timeout=30)
        assert r.status_code == 403

    def test_reports_columns_and_rows(self, mongo, qa_explorer):
        uid, tok = qa_explorer["uid"], qa_explorer["token"]
        unlock_cp1(mongo, uid)
        mongo.assessment_attempts.delete_many({"user_id": uid})
        aid = start(tok).json()["attempt_id"]
        submit(tok, aid, answer_all(mongo, aid, True))

        r = requests.get(f"{BASE_URL}/assessments/reports", headers=hdr(GUIDE_TOK), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        col_ids = [c["id"] for c in d["columns"]]
        # 4 tracks x 3 checkpoints + the final, followed by the Block Task columns.
        assert col_ids[:13] == [f"{t}-cp{i}" for t in ("docs", "sheets", "slides", "email") for i in (1, 2, 3)] + ["final"], col_ids
        assert "final" in col_ids
        row = next((s for s in d["students"] if s["user_id"] == uid), None)
        assert row is not None, "explorer missing from guide gradebook"
        assert row["scores"][CP1] == 100
        assert row["scores"]["docs-cp1"] is None
        assert "_id" not in row
        mongo.assessment_attempts.delete_many({"user_id": uid})
