"""Skill Studio batch: NO REWARD FOR BLANK, DRAFTS persistence, ASSIGN MISSIONS.

Modules covered:
- POST /api/studio/email/{mission}/submit  (blank_send -> points_awarded = 0)
- GET/PUT /api/studio/{track}/{mission}/drafts (explorer-only writes)
- POST/GET/DELETE /api/assignments + GET /api/me/assignments (guide RBAC, done map @ 60%)
- Regression: guide teaching-preview (0 points, no persistence), email-b2 identify grading.
All grading assertions use a FRESH explorer (submit returns a sticky best score).
"""
import os
import uuid

import pymongo
import pytest
import requests
from dotenv import dotenv_values

_fe = dotenv_values("/app/frontend/.env")
_be = dotenv_values("/app/backend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _fe.get("REACT_APP_BACKEND_URL")).rstrip("/")
API = f"{BASE_URL}/api"
GH = {"Authorization": "Bearer em_guide_tok", "Content-Type": "application/json"}
EH = {"Authorization": "Bearer em_exp_tok", "Content-Type": "application/json"}


def _db():
    cli = pymongo.MongoClient(os.environ.get("MONGO_URL") or _be.get("MONGO_URL"))
    return cli[os.environ.get("DB_NAME") or _be.get("DB_NAME")]


def _mk_explorer(db, expedition_ids=None):
    uid = f"TEST_da_{uuid.uuid4().hex[:10]}"
    tok = f"TEST_tok_{uuid.uuid4().hex[:12]}"
    db.users.insert_one({
        "user_id": uid, "email": f"{uid}@test.com", "name": f"TEST Drafts {uid[-4:]}",
        "picture": "", "role": "explorer", "horizon_points": 0, "compass_marks": 0,
        "fleet": None, "expedition_ids": expedition_ids or [], "created_at": "2026-07-01T00:00:00",
    })
    db.user_sessions.insert_one({
        "user_id": uid, "session_token": tok,
        "expires_at": "2030-01-01T00:00:00", "created_at": "2026-07-01T00:00:00",
    })
    return uid, {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def _cleanup_user(db, uid):
    db.users.delete_many({"user_id": uid})
    db.user_sessions.delete_many({"user_id": uid})
    db.studio_progress.delete_many({"user_id": uid})
    db.studio_drafts.delete_many({"user_id": uid})
    db.points_events.delete_many({"user_id": uid})


@pytest.fixture
def fresh_explorer():
    db = _db()
    uid, headers = _mk_explorer(db)
    yield {"uid": uid, "headers": headers}
    _cleanup_user(db, uid)


def _submit(headers, mission_id, doc, timeout=150):
    return requests.post(f"{API}/studio/email/{mission_id}/submit", headers=headers,
                         json={"doc": doc}, timeout=timeout)


GOOD_BODY = ("Hi Ms. Lee,\n\nI was absent yesterday and I wanted to ask what homework I missed "
             "so I can finish it tonight.\n\nThank you,\nJordan")


def _m6_doc(body_student):
    return {"messages": [
        {"id": "s1", "folder": "sent", "kind": "new", "inReplyTo": None,
         "fromName": "You", "fromEmail": "you@horizonmiddle.edu",
         "to": ["ms.lee@horizonmiddle.edu"], "cc": [], "bcc": [],
         "subject": "Question about missed homework",
         "body": body_student, "bodyStudent": body_student,
         "attachments": [], "read": True},
    ]}


# ---------------- NO REWARD FOR BLANK ----------------
class TestBlankSendNoReward:
    def test_blank_new_email_awards_zero_points(self, fresh_explorer):
        r = _submit(fresh_explorer["headers"], "email-m6", _m6_doc(""))
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d["blank_send"] is True, d
        assert d["points_awarded"] == 0, d
        assert d["score"] < 100, f"blank email should not reach 100: {d}"
        assert 20 <= d["score"] <= 70, f"expected partial ~40-60%, got {d['score']}"
        assert d["mastery"] is False, d
        # nothing awarded to the user's balance
        me = requests.get(f"{API}/auth/me", headers=fresh_explorer["headers"], timeout=20).json()
        assert me["horizon_points"] == 0, me

    def test_short_body_under_five_words_is_blank(self, fresh_explorer):
        r = _submit(fresh_explorer["headers"], "email-m6", _m6_doc("ok thanks bye"))
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d["blank_send"] is True, d
        assert d["points_awarded"] == 0, d

    def test_good_email_awards_points(self, fresh_explorer):
        r = _submit(fresh_explorer["headers"], "email-m6", _m6_doc(GOOD_BODY))
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d["blank_send"] is False, d
        assert d["points_awarded"] > 0, d
        assert d["score"] >= 60, d
        me = requests.get(f"{API}/auth/me", headers=fresh_explorer["headers"], timeout=20).json()
        assert me["horizon_points"] == d["points_awarded"], me

    def test_guide_preview_blank_flag_and_zero_points(self):
        r = _submit(GH, "email-m6", _m6_doc(""))
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d["preview"] is True and d["blank_send"] is True, d
        assert d["points_awarded"] == 0, d
        # no persistence for guides
        assert _db().studio_progress.count_documents({"user_id": "em-guide"}) == 0


# ---------------- DRAFTS ----------------
class TestDrafts:
    def test_explorer_save_and_get_drafts(self, fresh_explorer):
        h = fresh_explorer["headers"]
        drafts = [{"id": "d1", "folder": "drafts", "kind": "new", "to": ["ms.lee@horizonmiddle.edu"],
                   "cc": [], "bcc": [], "subject": "Half done", "body": "Hi Ms. Lee, I started",
                   "bodyStudent": "Hi Ms. Lee, I started", "attachments": [], "read": True}]
        p = requests.put(f"{API}/studio/email/email-m3/drafts", headers=h, json={"drafts": drafts}, timeout=30)
        assert p.status_code == 200, p.text[:300]
        assert p.json().get("ok") is True and not p.json().get("skipped")

        g = requests.get(f"{API}/studio/email/email-m3/drafts", headers=h, timeout=30)
        assert g.status_code == 200, g.text[:300]
        got = g.json()["drafts"]
        assert len(got) == 1 and got[0]["subject"] == "Half done", got
        assert got[0]["folder"] == "drafts"

    def test_drafts_are_per_mission_and_overwrite(self, fresh_explorer):
        h = fresh_explorer["headers"]
        requests.put(f"{API}/studio/email/email-m3/drafts", headers=h, json={"drafts": [{"id": "a"}]}, timeout=30)
        # other mission unaffected
        g2 = requests.get(f"{API}/studio/email/email-m6/drafts", headers=h, timeout=30)
        assert g2.json()["drafts"] == []
        # overwrite
        requests.put(f"{API}/studio/email/email-m3/drafts", headers=h, json={"drafts": []}, timeout=30)
        g3 = requests.get(f"{API}/studio/email/email-m3/drafts", headers=h, timeout=30)
        assert g3.json()["drafts"] == []

    def test_guide_put_skipped_and_get_empty(self):
        p = requests.put(f"{API}/studio/email/email-m3/drafts", headers=GH,
                         json={"drafts": [{"id": "g1"}]}, timeout=30)
        assert p.status_code == 200 and p.json().get("skipped") is True, p.text[:300]
        g = requests.get(f"{API}/studio/email/email-m3/drafts", headers=GH, timeout=30)
        assert g.status_code == 200 and g.json()["drafts"] == [], g.text[:300]

    def test_drafts_requires_auth(self):
        r = requests.get(f"{API}/studio/email/email-m3/drafts", timeout=30)
        assert r.status_code in (401, 403), r.status_code


# ---------------- ASSIGNMENTS ----------------
@pytest.fixture(scope="class")
def guide_expedition():
    db = _db()
    r = requests.post(f"{API}/expeditions", headers=GH,
                      json={"name": "TEST_Assign Class"}, timeout=30)
    assert r.status_code in (200, 201), r.text[:300]
    exp = r.json()
    exp_id = exp["expedition_id"]
    uid, h = _mk_explorer(db, [exp_id])
    yield {"exp": exp, "exp_id": exp_id, "student_uid": uid, "student_headers": h}
    _cleanup_user(db, uid)
    db.expeditions.delete_many({"expedition_id": exp_id})
    db.assignments.delete_many({"expedition_id": exp_id})


class TestAssignments:
    def test_create_filters_invalid_missions(self, guide_expedition):
        r = requests.post(f"{API}/assignments", headers=GH, json={
            "expedition_id": guide_expedition["exp_id"], "track": "email",
            "mission_ids": ["email-m3", "email-b1", "email-does-not-exist"],
            "note": "TEST note",
        }, timeout=30)
        assert r.status_code == 200, r.text[:300]
        a = r.json()
        assert "_id" not in a
        assert sorted(a["mission_ids"]) == ["email-b1", "email-m3"], a
        guide_expedition["assignment_id"] = a["assignment_id"]

    def test_create_rejects_expedition_not_owned(self):
        r = requests.post(f"{API}/assignments", headers=GH, json={
            "expedition_id": "exp_does_not_exist", "track": "email", "mission_ids": ["email-m3"],
        }, timeout=30)
        assert r.status_code == 404, r.text[:300]

    def test_create_rejects_all_invalid_missions(self, guide_expedition):
        r = requests.post(f"{API}/assignments", headers=GH, json={
            "expedition_id": guide_expedition["exp_id"], "track": "email", "mission_ids": ["nope"],
        }, timeout=30)
        assert r.status_code == 400, r.text[:300]

    def test_explorer_forbidden_on_assignments(self):
        assert requests.get(f"{API}/assignments", headers=EH, timeout=30).status_code == 403
        assert requests.post(f"{API}/assignments", headers=EH, json={
            "expedition_id": "x", "track": "email", "mission_ids": ["email-m3"]}, timeout=30).status_code == 403

    def test_list_shows_card_and_done_map(self, guide_expedition):
        aid = guide_expedition["assignment_id"]
        cards = requests.get(f"{API}/assignments", headers=GH, timeout=40).json()
        card = next(c for c in cards if c["assignment_id"] == aid)
        assert card["expedition_name"] == "TEST_Assign Class"
        assert set(card["mission_titles"].keys()) == {"email-b1", "email-m3"}
        assert card["member_count"] == 1, card
        row = next(s for s in card["students"] if s["user_id"] == guide_expedition["student_uid"])
        assert row["done"] == {"email-b1": False, "email-m3": False}, row
        assert row["done_count"] == 0

    def test_done_true_only_when_score_at_least_60(self, guide_expedition):
        db = _db()
        uid = guide_expedition["student_uid"]
        db.studio_progress.update_one(
            {"user_id": uid, "mission_id": "email-m3"},
            {"$set": {"user_id": uid, "track": "email", "mission_id": "email-m3",
                      "score": 59, "grade": "F", "points_earned": 0, "mastery": False,
                      "updated_at": "2026-07-01T00:00:00"}}, upsert=True)
        cards = requests.get(f"{API}/assignments", headers=GH, timeout=40).json()
        row = next(s for c in cards if c["assignment_id"] == guide_expedition["assignment_id"]
                   for s in c["students"] if s["user_id"] == uid)
        assert row["done"]["email-m3"] is False, "59% must not count as done"

        db.studio_progress.update_one({"user_id": uid, "mission_id": "email-m3"}, {"$set": {"score": 60}})
        cards = requests.get(f"{API}/assignments", headers=GH, timeout=40).json()
        row = next(s for c in cards if c["assignment_id"] == guide_expedition["assignment_id"]
                   for s in c["students"] if s["user_id"] == uid)
        assert row["done"]["email-m3"] is True, "60% must count as done"
        assert row["done_count"] == 1

    def test_me_assignments_for_explorer(self, guide_expedition):
        r = requests.get(f"{API}/me/assignments", headers=guide_expedition["student_headers"], timeout=30)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert any(a["assignment_id"] == guide_expedition["assignment_id"] for a in data), data
        assert all("_id" not in a for a in data)

    def test_me_assignments_empty_for_unenrolled(self, fresh_explorer):
        r = requests.get(f"{API}/me/assignments", headers=fresh_explorer["headers"], timeout=30)
        assert r.status_code == 200 and r.json() == [], r.text[:300]

    def test_delete_assignment(self, guide_expedition):
        aid = guide_expedition["assignment_id"]
        d = requests.delete(f"{API}/assignments/{aid}", headers=GH, timeout=30)
        assert d.status_code == 200, d.text[:300]
        cards = requests.get(f"{API}/assignments", headers=GH, timeout=40).json()
        assert all(c["assignment_id"] != aid for c in cards)
        assert requests.get(f"{API}/me/assignments", headers=guide_expedition["student_headers"],
                            timeout=30).json() == []


# ---------------- REGRESSION ----------------
class TestRegression:
    def test_email_b2_identify_grading(self, fresh_explorer):
        doc = {"picked": {"to": "ms.lee@horizonmiddle.edu", "cc": "coach@horizonmiddle.edu",
                          "bcc": "parent@example.com"}}
        r = _submit(fresh_explorer["headers"], "email-b2", doc)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d["total"] >= 3, d
        assert isinstance(d["score"], int)

    def test_track_listing_has_14_missions(self):
        r = requests.get(f"{API}/studio/email", headers=EH, timeout=30)
        assert r.status_code == 200, r.text[:300]
        missions = r.json()["missions"]
        assert len(missions) == 14, len(missions)
