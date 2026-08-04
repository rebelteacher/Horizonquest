"""Tests for the 3 new features: Curriculum objectives/learner goals,
Cipher Playground lab (t3-q6), Phishing Spotter lab (t3-q5), and Pigpen bonus challenge.

Uses an ISOLATED explorer session `qa_cipher_tok` (user_id=qa-cipher-exp) that is
pre-seeded so tests are independent from other test files.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://explorer-journey-4.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

EXP_TOK = "qa_cipher_tok"
GUIDE_TOK = "qa_guide_tok"
EH = {"Authorization": f"Bearer {EXP_TOK}", "Content-Type": "application/json"}
GH = {"Authorization": f"Bearer {GUIDE_TOK}", "Content-Type": "application/json"}


def _reset_user():
    import pymongo
    c = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    db = c[os.environ.get("DB_NAME", "test_database")]
    db.users.update_one({"user_id": "qa-cipher-exp"}, {"$set": {"horizon_points": 0, "compass_marks": 0}})
    db.lab_completions.delete_many({"user_id": "qa-cipher-exp"})
    db.challenge_completions.delete_many({"user_id": "qa-cipher-exp"})
    db.points_events.delete_many({"user_id": "qa-cipher-exp"})


# --------- Curriculum: Objectives & Learner Goals ----------
class TestCurriculumObjectives:
    def test_curriculum_shape(self):
        r = requests.get(f"{API}/curriculum")
        assert r.status_code == 200
        d = r.json()
        assert len(d["territories"]) == 4
        assert len(d["quests"]) == 33

    def test_every_quest_has_objective_and_learner_goal(self):
        r = requests.get(f"{API}/curriculum").json()
        for q in r["quests"]:
            assert isinstance(q.get("objective"), str) and len(q["objective"]) > 0, f"{q['id']} missing objective"
            assert isinstance(q.get("learner_goal"), str) and len(q["learner_goal"]) > 0, f"{q['id']} missing learner_goal"
            assert q["learner_goal"].lower().startswith("i can"), f"{q['id']} learner_goal doesn't start with 'I can': {q['learner_goal']!r}"
            assert "standard" in q and q["standard"].get("code") and q["standard"].get("description")

    def test_specific_learner_goals(self):
        r = requests.get(f"{API}/curriculum").json()
        by_id = {q["id"]: q for q in r["quests"]}
        assert "cipher" in by_id["t3-q6"]["learner_goal"].lower() or "encode" in by_id["t3-q6"]["learner_goal"].lower()
        assert "phishing" in by_id["t3-q5"]["learner_goal"].lower()


# --------- Cipher Playground Lab (t3-q6) ----------
class TestCipherLab:
    def test_cipher_lab_first_award_75(self):
        _reset_user()
        r = requests.post(f"{API}/labs/t3-q6/complete", headers=EH)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["already_completed"] is False
        assert d["bonus"] == 75
        assert d["horizon_points"] >= 75

    def test_cipher_lab_idempotent(self):
        # first call already ran; second call should be idempotent
        r1 = requests.post(f"{API}/labs/t3-q6/complete", headers=EH)
        assert r1.status_code == 200
        # Now second call
        r = requests.post(f"{API}/labs/t3-q6/complete", headers=EH)
        assert r.status_code == 200
        d = r.json()
        assert d["already_completed"] is True
        assert d["bonus"] == 0

    def test_cipher_lab_guide_forbidden(self):
        r = requests.post(f"{API}/labs/t3-q6/complete", headers=GH)
        assert r.status_code == 403

    def test_cipher_lab_unauth(self):
        r = requests.post(f"{API}/labs/t3-q6/complete")
        assert r.status_code == 401


# --------- Phishing Spotter Lab (t3-q5) ----------
class TestPhishingLab:
    def test_phishing_lab_first_award_75(self):
        # ensure clean slate for phishing quest
        import pymongo
        c = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
        db = c[os.environ.get("DB_NAME", "test_database")]
        db.lab_completions.delete_many({"user_id": "qa-cipher-exp", "quest_id": "t3-q5"})

        pre = requests.get(f"{API}/auth/me", headers=EH).json()["horizon_points"]
        r = requests.post(f"{API}/labs/t3-q5/complete", headers=EH)
        assert r.status_code == 200
        d = r.json()
        assert d["already_completed"] is False
        assert d["bonus"] == 75
        assert d["horizon_points"] >= pre + 75

    def test_phishing_lab_idempotent(self):
        r = requests.post(f"{API}/labs/t3-q5/complete", headers=EH)
        assert r.status_code == 200
        d = r.json()
        assert d["already_completed"] is True
        assert d["bonus"] == 0

    def test_phishing_lab_guide_forbidden(self):
        r = requests.post(f"{API}/labs/t3-q5/complete", headers=GH)
        assert r.status_code == 403


# --------- Pigpen Bonus Challenge (cipher-pigpen) ----------
class TestPigpenChallenge:
    def test_pigpen_first_award_50(self):
        import pymongo
        c = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
        db = c[os.environ.get("DB_NAME", "test_database")]
        db.challenge_completions.delete_many({"user_id": "qa-cipher-exp", "challenge_id": "cipher-pigpen"})

        r = requests.post(f"{API}/challenges/cipher-pigpen/complete", headers=EH)
        assert r.status_code == 200
        d = r.json()
        assert d["already_completed"] is False
        assert d["bonus"] == 50
        # horizon_points should be at least 50 (parallel workers may add more)
        assert d["horizon_points"] >= 50

    def test_pigpen_idempotent(self):
        r = requests.post(f"{API}/challenges/cipher-pigpen/complete", headers=EH)
        assert r.status_code == 200
        d = r.json()
        assert d["already_completed"] is True
        assert d["bonus"] == 0

    def test_unknown_challenge_404(self):
        r = requests.post(f"{API}/challenges/does-not-exist/complete", headers=EH)
        assert r.status_code == 404

    def test_challenge_guide_forbidden(self):
        r = requests.post(f"{API}/challenges/cipher-pigpen/complete", headers=GH)
        assert r.status_code == 403

    def test_challenge_unauth(self):
        r = requests.post(f"{API}/challenges/cipher-pigpen/complete")
        assert r.status_code == 401


# --------- Points event logged for lab & challenge ----------
class TestPointsEvents:
    def test_points_events_logged(self):
        import pymongo
        c = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
        db = c[os.environ.get("DB_NAME", "test_database")]
        ev_lab = db.points_events.find_one({"user_id": "qa-cipher-exp", "quest_id": "t3-q6", "type": "lab"})
        assert ev_lab is not None
        assert ev_lab["delta"] == 75
        ev_ch = db.points_events.find_one({"user_id": "qa-cipher-exp", "challenge_id": "cipher-pigpen", "type": "challenge"})
        assert ev_ch is not None
        assert ev_ch["delta"] == 50
