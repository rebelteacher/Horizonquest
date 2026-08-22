"""HorizonQuest Skill Studio — Email track "classroom feedback" batch tests.

Covers:
- GET /api/studio/email: 14 missions, ordering (email-b1 #1, email-b2 #2,
  email-m1..m12 #3..#14), no duplicate order values.
- email-b1 grading (email_opened check on the teacher message).
- email-b2 NEW 'picked' grading (t1 email_opened e1, t2 picked cc, t3 picked to).
- Regression sanity on email-m1 (deterministic) and email-m8 (attachment).
- Guide-only reports endpoint used by CSV export (/api/studio/reports/all).

NOTE: submit returns a STICKY best score, so every grading test uses a
freshly created explorer session (created/torn down via pymongo).
"""
import os
import time
import uuid

import pymongo
import pytest
import requests
from dotenv import dotenv_values

_fe = dotenv_values("/app/frontend/.env")
_be = dotenv_values("/app/backend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _fe.get("REACT_APP_BACKEND_URL")).rstrip("/")
API = f"{BASE_URL}/api"

GUIDE_TOK = "em_guide_tok"
GH = {"Authorization": f"Bearer {GUIDE_TOK}", "Content-Type": "application/json"}

EXPECTED_ORDER = ["email-b1", "email-b2"] + [f"email-m{i}" for i in range(1, 13)]


def _db():
    cli = pymongo.MongoClient(os.environ.get("MONGO_URL") or _be.get("MONGO_URL"))
    return cli[os.environ.get("DB_NAME") or _be.get("DB_NAME")]


@pytest.fixture
def fresh_explorer():
    """Create an isolated explorer + session; clean up afterwards."""
    db = _db()
    uid = f"TEST_eb_{uuid.uuid4().hex[:10]}"
    tok = f"TEST_tok_{uuid.uuid4().hex[:12]}"
    db.users.insert_one({
        "user_id": uid, "email": f"{uid}@test.com", "name": "TEST Email Basics",
        "picture": "", "role": "explorer", "horizon_points": 0, "compass_marks": 0,
        "fleet": None, "expedition_ids": [], "created_at": "2026-07-01T00:00:00",
    })
    db.user_sessions.insert_one({
        "user_id": uid, "session_token": tok,
        "expires_at": "2030-01-01T00:00:00", "created_at": "2026-07-01T00:00:00",
    })
    yield {"uid": uid, "headers": {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}}
    db.users.delete_many({"user_id": uid})
    db.user_sessions.delete_many({"user_id": uid})
    db.studio_progress.delete_many({"user_id": uid})
    db.points_events.delete_many({"user_id": uid})


def _submit(headers, mission_id, doc, timeout=120):
    return requests.post(f"{API}/studio/email/{mission_id}/submit", headers=headers,
                         json={"doc": doc}, timeout=timeout)


def _res(payload):
    return {r["id"]: r["passed"] for r in payload["results"]}


@pytest.fixture(scope="module")
def track():
    r = requests.get(f"{API}/studio/email", headers=GH, timeout=20)
    if r.status_code != 200:
        r = requests.get(f"{API}/studio/email",
                         headers={"Authorization": "Bearer em_exp_tok"}, timeout=20)
    assert r.status_code == 200, r.text[:400]
    return r.json()


# ---------- Track ordering ----------
class TestEmailTrackOrdering:
    def test_mission_count(self, track):
        assert len(track["missions"]) == 14, [m["id"] for m in track["missions"]]

    def test_order_sequence(self, track):
        ms = sorted(track["missions"], key=lambda m: m["order"])
        assert [m["id"] for m in ms] == EXPECTED_ORDER
        assert [m["order"] for m in ms] == list(range(1, 15))

    def test_no_duplicate_orders(self, track):
        orders = [m["order"] for m in track["missions"]]
        assert len(set(orders)) == len(orders), orders

    def test_new_mission_titles(self, track):
        by_id = {m["id"]: m for m in track["missions"]}
        assert by_id["email-b1"]["title"] == "Whose Email Is It?"
        assert by_id["email-b2"]["title"] == "Reading the Address Lines"

    def test_b2_task_checks(self, track):
        by_id = {m["id"]: m for m in track["missions"]}
        tasks = {t["id"]: t["check"] for t in by_id["email-b2"]["tasks"]}
        assert tasks["t1"] == {"kind": "email_opened", "id": "e1"}
        assert tasks["t2"] == {"kind": "picked", "field": "to"}
        assert tasks["t3"] == {"kind": "picked", "field": "cc"}
        assert tasks["t4"] == {"kind": "picked", "field": "bcc"}

    def test_b2_seed_doc_has_to_and_cc(self, track):
        by_id = {m["id"]: m for m in track["missions"]}
        msg = by_id["email-b2"]["doc"]["messages"][0]
        assert msg["id"] == "e1"
        assert len(msg["to"]) >= 1 and len(msg["cc"]) >= 1 and len(msg["bcc"]) >= 1

    def test_no_mongo_id_leak(self, track):
        assert "_id" not in track
        for m in track["missions"]:
            assert "_id" not in m


# ---------- email-b1 ----------
class TestEmailB1:
    def test_pass_when_teacher_email_opened(self, fresh_explorer):
        doc = {"messages": [
            {"id": "gc", "folder": "inbox", "read": False},
            {"id": "store", "folder": "inbox", "read": False},
            {"id": "teacher", "folder": "inbox", "read": True},
        ]}
        r = _submit(fresh_explorer["headers"], "email-b1", doc)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d["score"] == 100, d
        assert d["grade"] == "A"
        assert _res(d)["t1"] is True

    def test_fail_when_only_notice_opened(self, fresh_explorer):
        doc = {"messages": [{"id": "gc", "folder": "inbox", "read": True}]}
        r = _submit(fresh_explorer["headers"], "email-b1", doc)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert _res(d)["t1"] is False
        assert d["score"] == 0


# ---------- email-b2 (new 'picked' grading) ----------
class TestEmailB2Picked:
    def test_full_pass(self, fresh_explorer):
        doc = {"messages": [{"id": "e1", "folder": "inbox", "read": True}],
               "picked": ["to", "cc", "bcc"]}
        r = _submit(fresh_explorer["headers"], "email-b2", doc)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d["score"] == 100, d
        assert d["total"] == 4 and d["passed"] == 4
        assert _res(d) == {"t1": True, "t2": True, "t3": True, "t4": True}
        assert d["mastery"] is True

    def test_picked_missing_fails_t2_t3(self, fresh_explorer):
        doc = {"messages": [{"id": "e1", "folder": "inbox", "read": True}]}
        r = _submit(fresh_explorer["headers"], "email-b2", doc)
        assert r.status_code == 200, r.text[:400]
        res = _res(r.json())
        assert res == {"t1": True, "t2": False, "t3": False, "t4": False}
        assert r.json()["score"] == 25

    def test_picked_empty_fails(self, fresh_explorer):
        doc = {"messages": [{"id": "e1", "folder": "inbox", "read": True}], "picked": []}
        res = _res(_submit(fresh_explorer["headers"], "email-b2", doc).json())
        assert res["t2"] is False and res["t3"] is False

    def test_partial_picked_cc_only(self, fresh_explorer):
        doc = {"messages": [{"id": "e1", "folder": "inbox", "read": True}], "picked": ["cc"]}
        d = _submit(fresh_explorer["headers"], "email-b2", doc).json()
        assert _res(d) == {"t1": True, "t2": False, "t3": True, "t4": False}
        assert d["score"] == 50

    def test_best_attempt_sticky_and_persisted(self, fresh_explorer):
        h = fresh_explorer["headers"]
        full = _submit(h, "email-b2", {"messages": [{"id": "e1", "folder": "inbox", "read": True}],
                                       "picked": ["to", "cc", "bcc"]}).json()
        assert full["score"] == 100
        partial = _submit(h, "email-b2", {"messages": [{"id": "e1", "folder": "inbox", "read": False}]}).json()
        assert partial["score"] == 100, "best score should be sticky"
        # GET verifies persistence
        prog = requests.get(f"{API}/studio/email", headers=h, timeout=20).json().get("progress", {})
        assert "email-b2" in prog and prog["email-b2"]["score"] == 100, prog


# ---------- Regression ----------
class TestEmailRegression:
    def test_m1_deterministic(self, fresh_explorer):
        doc = {"messages": [{"id": "e1", "folder": "inbox", "read": True},
                            {"id": "e2", "folder": "inbox", "read": True}]}
        d = _submit(fresh_explorer["headers"], "email-m1", doc).json()
        assert d["score"] == 100, d

    def test_m8_attachment(self, fresh_explorer):
        doc = {"messages": [
            {"id": "e1", "folder": "inbox", "read": True},
            {"id": "s1", "folder": "sent", "kind": "reply", "inReplyTo": "e1",
             "to": ["mr.diaz@horizonmiddle.edu"], "cc": [], "bcc": [],
             "subject": "Re: Field trip permission form",
             "body": "Hello Mr. Diaz,\n\nHere is the signed form attached.\n\nThank you,\nYou",
             "attachments": [{"name": "Field Trip Form.pdf"}], "read": True},
        ]}
        r = _submit(fresh_explorer["headers"], "email-m8", doc)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert isinstance(d.get("score"), int)
        assert any(v for v in _res(d).values()), d

    def test_ai_mission_m10_sanity(self, fresh_explorer):
        doc = {"messages": [
            {"id": "s1", "folder": "sent", "kind": "new",
             "to": ["mentor@company.com"], "cc": [], "bcc": [],
             "subject": "Thank you and a question about my project",
             "body": ("Dear Mr. Patel,\n\nThank you for taking the time to mentor me during my "
                      "internship. I really appreciate your guidance on the inventory project. "
                      "I have one question: would you prefer that I organize the spreadsheet by "
                      "product category or by supplier?\n\nThank you again for your help.\n\n"
                      "Sincerely,\nAlex Rivera"),
             "attachments": [], "read": True},
        ]}
        t0 = time.time()
        r = _submit(fresh_explorer["headers"], "email-m10", doc, timeout=180)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d["ai_rating"] in ("Excellent", "Good", "Needs work"), d
        assert isinstance(d.get("ai_feedback"), str) and d["ai_feedback"], d
        assert d["score"] >= 50, d
        print(f"m10 AI grading took {time.time() - t0:.1f}s rating={d['ai_rating']} score={d['score']}")

    def test_unknown_mission_404(self, fresh_explorer):
        r = _submit(fresh_explorer["headers"], "email-bXX", {"messages": []})
        assert r.status_code == 404

    def test_wrong_track_404(self, fresh_explorer):
        r = requests.post(f"{API}/studio/docs/email-b2/submit",
                          headers=fresh_explorer["headers"], json={"doc": {}}, timeout=30)
        assert r.status_code == 404

    def test_unauth_401(self):
        r = requests.post(f"{API}/studio/email/email-b2/submit", json={"doc": {}}, timeout=20)
        assert r.status_code in (401, 403)

    def test_guide_submit_returns_preview(self):
        """Guides now get a non-persisted teaching preview (0 points) instead of 403."""
        r = requests.post(f"{API}/studio/email/email-b2/submit", headers=GH,
                          json={"doc": {"messages": []}}, timeout=30)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d.get("preview") is True and d.get("points_awarded", 0) == 0, d


# ---------- Reports (CSV export data source) ----------
class TestReports:
    def test_guide_reports_ok(self):
        r = requests.get(f"{API}/studio/reports/all", headers=GH, timeout=30)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert "students" in d and isinstance(d["students"], list)
        for s in d["students"]:
            assert "_id" not in s

    def test_explorer_forbidden(self, fresh_explorer):
        r = requests.get(f"{API}/studio/reports/all", headers=fresh_explorer["headers"], timeout=30)
        assert r.status_code == 403
