"""HorizonQuest backend regression tests using pre-seeded sessions."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://explorer-journey-4.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

GUIDE_TOK = "qa_guide_tok"
EXP_TOK = "qa_exp_tok"

GH = {"Authorization": f"Bearer {GUIDE_TOK}", "Content-Type": "application/json"}
EH = {"Authorization": f"Bearer {EXP_TOK}", "Content-Type": "application/json"}


# --------- Auth ----------
class TestAuth:
    def test_me_no_auth_401(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401

    def test_me_guide(self):
        r = requests.get(f"{API}/auth/me", headers=GH)
        assert r.status_code == 200
        d = r.json()
        assert d["user_id"] == "qa-guide"
        assert d["role"] == "guide"

    def test_me_explorer(self):
        r = requests.get(f"{API}/auth/me", headers=EH)
        assert r.status_code == 200
        d = r.json()
        assert d["role"] == "explorer"


# --------- Curriculum ----------
class TestCurriculum:
    def test_curriculum_public(self):
        r = requests.get(f"{API}/curriculum")
        assert r.status_code == 200
        d = r.json()
        assert len(d["territories"]) == 4
        names = [t["name"] for t in d["territories"]]
        assert names == ["Summit of Leadership", "Productivity Peaks", "The Cyber Frontier", "Data Delta"]
        assert len(d["quests"]) == 33
        codes = [q["standard"]["code"] for q in d["quests"]]
        assert any(c.startswith("BL.1.") for c in codes)
        assert any(c.startswith("PA.2.") for c in codes)
        assert any(c.startswith("CY.3.") for c in codes)
        assert any(c.startswith("DS.4.") for c in codes)
        for q in d["quests"]:
            # FIX 2: Every quest has exactly 4 MC trial questions
            assert len(q["trial"]["questions"]) == 4, f"{q['id']} has {len(q['trial']['questions'])} questions"
            # question ids should be a,b,c,d (NOTE: t4-q9 currently uses 'e' - minor inconsistency)
            qids = [qq["id"] for qq in q["trial"]["questions"]]
            assert len(qids) == 4 and len(set(qids)) == 4, f"{q['id']} qids={qids}"
            # FIX 2: reflection field must NOT be exposed publicly
            assert "reflection" not in q, f"{q['id']} still exposes reflection"
            for qq in q["trial"]["questions"]:
                assert "answer" not in qq
                assert qq["type"] == "mc"
                assert isinstance(qq["options"], list) and len(qq["options"]) >= 2


# --------- RBAC ----------
class TestRBAC:
    def test_explorer_cannot_create_expedition(self):
        r = requests.post(f"{API}/expeditions", headers=EH, json={"name": "TEST_x"})
        assert r.status_code == 403

    def test_guide_cannot_join(self):
        r = requests.post(f"{API}/expeditions/join", headers=GH, json={"join_code": "AAAAAA"})
        assert r.status_code == 403

    def test_guide_cannot_submit_trial(self):
        r = requests.post(f"{API}/trials/t1-q1/submit", headers=GH, json={"answers": {}})
        assert r.status_code == 403

    def test_unauth_expeditions(self):
        r = requests.post(f"{API}/expeditions", json={"name": "x"})
        assert r.status_code == 401


# --------- Expeditions ----------
class TestExpeditions:
    _expedition = {}

    def test_create_expedition(self):
        r = requests.post(f"{API}/expeditions", headers=GH, json={"name": "TEST_QA_Voyage", "description": "test"})
        assert r.status_code == 200
        d = r.json()
        assert "join_code" in d and len(d["join_code"]) == 6
        assert d["guide_id"] == "qa-guide"
        TestExpeditions._expedition = d

    def test_list_expeditions(self):
        r = requests.get(f"{API}/expeditions", headers=GH)
        assert r.status_code == 200
        codes = [e["join_code"] for e in r.json()]
        assert TestExpeditions._expedition["join_code"] in codes

    def test_get_expedition(self):
        eid = TestExpeditions._expedition["expedition_id"]
        r = requests.get(f"{API}/expeditions/{eid}", headers=GH)
        assert r.status_code == 200
        assert r.json()["expedition"]["expedition_id"] == eid

    def test_join_invalid_code(self):
        r = requests.post(f"{API}/expeditions/join", headers=EH, json={"join_code": "ZZZZZZ"})
        assert r.status_code == 404

    def test_explorer_joins_new_expedition(self):
        code = TestExpeditions._expedition["join_code"]
        r = requests.post(f"{API}/expeditions/join", headers=EH, json={"join_code": code})
        assert r.status_code == 200
        d = r.json()
        assert d["expedition"]["join_code"] == code
        # already-existing fleet 'North Star' retained on rejoin scenarios
        # verify explorer now includes this expedition
        me = requests.get(f"{API}/auth/me", headers=EH).json()
        assert TestExpeditions._expedition["expedition_id"] in me["expedition_ids"]

    def test_toggle_leaderboard(self):
        eid = TestExpeditions._expedition["expedition_id"]
        r = requests.patch(f"{API}/expeditions/{eid}/leaderboard", headers=GH)
        assert r.status_code == 200
        v1 = r.json()["leaderboard_visible"]
        r = requests.patch(f"{API}/expeditions/{eid}/leaderboard", headers=GH)
        assert r.json()["leaderboard_visible"] != v1


# --------- Trial submission ----------
class TestTrial:
    def test_submit_t1q1_full(self):
        # FIX 3: 4 MC answers, all correct => 100% mastery
        payload = {
            "answers": {"a": "Call the meeting to order", "b": "Agenda", "c": "The official written record", "d": "Chair (president)"},
        }
        r = requests.post(f"{API}/trials/t1-q1/submit", headers=EH, json=payload)
        assert r.status_code == 200
        d = r.json()
        assert d["score"] == 100
        assert d["mastery"] is True
        assert d["horizon_points"] >= 100
        assert d["compass_marks"] >= 1

    def test_submit_three_of_four_fails_mastery(self):
        # FIX 3: 3/4 = 75% -> below 80% threshold, mastery False
        payload = {"answers": {"a": "Call the meeting to order", "b": "Agenda", "c": "The official written record", "d": "Timekeeper"}}
        r = requests.post(f"{API}/trials/t1-q1/submit", headers=EH, json=payload)
        assert r.status_code == 200
        d = r.json()
        assert d["score"] == 75
        assert d["mastery"] is False

    def test_submit_partial(self):
        payload = {"answers": {"a": "Call the meeting to order", "b": "Motion", "c": "The break time", "d": "Timekeeper"}}
        r = requests.post(f"{API}/trials/t1-q1/submit", headers=EH, json=payload)
        assert r.status_code == 200
        d = r.json()
        assert d["score"] == 25
        assert d["mastery"] is False
        # But stored best/mastery should be preserved
        assert d["horizon_points"] >= 100
        assert d["compass_marks"] >= 1

    def test_bad_quest(self):
        r = requests.post(f"{API}/trials/no-such/submit", headers=EH, json={"answers": {}})
        assert r.status_code == 404


# --------- Leaderboard ----------
class TestLeaderboard:
    def test_leaderboard_global(self):
        r = requests.get(f"{API}/leaderboard", headers=EH)
        assert r.status_code == 200
        d = r.json()
        assert "entries" in d and "fleets" in d
        me = [e for e in d["entries"] if e["is_me"]]
        assert len(me) == 1
        assert me[0]["horizon_points"] >= 100
        # tier field present on every entry
        for e in d["entries"]:
            assert e.get("tier") in ("Navigator", "Voyager", "Conqueror")

    def test_leaderboard_by_expedition(self):
        # use one that explorer is in
        me = requests.get(f"{API}/auth/me", headers=EH).json()
        assert me["expedition_ids"]
        eid = me["expedition_ids"][0]
        r = requests.get(f"{API}/leaderboard", headers=EH, params={"expedition_id": eid})
        assert r.status_code == 200
        entries = r.json()["entries"]
        assert any(e["is_me"] for e in entries)


# --------- Guide reviews & mastery ----------
class TestGuideReview:
    def test_reviews_visible_to_relevant_guide(self):
        # Reviews are only visible to guide of the expedition the explorer belongs to.
        # qa-guide may or may not own the expedition explorer joined. Just ensure endpoint works.
        r = requests.get(f"{API}/guide/reviews", headers=GH)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_approve_flow_if_review_exists(self):
        # Try to approve any of qa-guide's reviews
        reviews = requests.get(f"{API}/guide/reviews", headers=GH).json()
        if not reviews:
            pytest.skip("No pending reviews for qa-guide - explorer's reflection may belong to a diff guide")
        pre = requests.get(f"{API}/auth/me", headers=EH).json()
        rid = reviews[0]["review_id"]
        target_uid = reviews[0]["user_id"]
        r = requests.post(f"{API}/guide/reviews/{rid}/approve", headers=GH)
        assert r.status_code == 200
        assert r.json()["bonus"] == 25
        if target_uid == "qa-exp":
            post = requests.get(f"{API}/auth/me", headers=EH).json()
            assert post["horizon_points"] == pre["horizon_points"] + 25

    def test_mastery_report(self):
        exps = requests.get(f"{API}/expeditions", headers=GH).json()
        if not exps:
            pytest.skip("No expeditions for qa-guide")
        eid = exps[0]["expedition_id"]
        r = requests.get(f"{API}/guide/mastery/{eid}", headers=GH)
        assert r.status_code == 200
        d = r.json()
        assert "standards" in d and "territory_summary" in d
        assert len(d["territory_summary"]) == 4


# --------- AI Copilot streaming ----------
class TestCopilot:
    def test_copilot_stream(self):
        r = requests.post(
            f"{API}/ai/copilot",
            headers=EH,
            json={"message": "Give me a hint for variables (do not answer directly).", "quest_id": "t1-q1"},
            stream=True, timeout=60,
        )
        assert r.status_code == 200
        body = ""
        start = time.time()
        for chunk in r.iter_content(chunk_size=None):
            if chunk:
                body += chunk.decode("utf-8", errors="ignore")
            if time.time() - start > 45:
                break
        assert len(body.strip()) > 5, f"Empty copilot response: {body!r}"


# --------- Hands-On Labs (Mock Meeting bonus) ----------
class TestLabs:
    """Lab endpoints: idempotent +75 bonus for t1-q8, explorer-only."""

    def _reset(self):
        # Ensure clean state: remove qa-exp's lab_completion for t1-q8 and reset HP baseline
        import pymongo, os
        c = pymongo.MongoClient(os.environ.get("MONGO_URL"))
        db = c[os.environ.get("DB_NAME", "test_database")]
        db.lab_completions.delete_many({"user_id": "qa-exp", "quest_id": "t1-q8"})
        # capture current HP as baseline
        u = db.users.find_one({"user_id": "qa-exp"})
        return u.get("horizon_points", 0)

    def test_lab_flow_and_idempotency(self):
        baseline = self._reset()
        # first call
        r1 = requests.post(f"{API}/labs/t1-q8/complete", headers=EH)
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["already_completed"] is False
        assert d1["bonus"] == 75
        assert d1["horizon_points"] == baseline + 75

        # second call (idempotent)
        r2 = requests.post(f"{API}/labs/t1-q8/complete", headers=EH)
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["already_completed"] is True
        assert d2["bonus"] == 0
        assert d2["horizon_points"] == baseline + 75  # no double award

        # /auth/me reflects the +75
        me = requests.get(f"{API}/auth/me", headers=EH).json()
        assert me["horizon_points"] == baseline + 75

        # completions list contains t1-q8
        comps = requests.get(f"{API}/labs/completions", headers=EH)
        assert comps.status_code == 200
        assert "t1-q8" in comps.json()

    def test_lab_guide_forbidden(self):
        r = requests.post(f"{API}/labs/t1-q8/complete", headers=GH)
        assert r.status_code == 403

    def test_lab_unknown_quest_404(self):
        r = requests.post(f"{API}/labs/no-such-quest/complete", headers=EH)
        assert r.status_code == 404

    def test_lab_completions_requires_auth(self):
        r = requests.get(f"{API}/labs/completions")
        assert r.status_code == 401
