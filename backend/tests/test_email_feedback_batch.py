"""Skill Studio EMAIL track — classroom-feedback batch (blank-send fix, Bcc task, padded inboxes).

Covers:
- CRITICAL anti-blank-send grading on email-m3 (reply) and email-m7 (new).
- email-b2 4-task shape with 'picked' bcc.
- GET /api/studio/email -> 14 missions, inboxes padded to ~10.
- Regression: m4 (reply-all), m8 (attachments) full pass; m10 AI sanity.
Sticky-score caveat: every grading assertion uses a FRESH explorer session.
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
GH = {"Authorization": "Bearer em_guide_tok", "Content-Type": "application/json"}


def _db():
    cli = pymongo.MongoClient(os.environ.get("MONGO_URL") or _be.get("MONGO_URL"))
    return cli[os.environ.get("DB_NAME") or _be.get("DB_NAME")]


@pytest.fixture
def fresh_explorer():
    db = _db()
    uid = f"TEST_fb_{uuid.uuid4().hex[:10]}"
    tok = f"TEST_tok_{uuid.uuid4().hex[:12]}"
    db.users.insert_one({
        "user_id": uid, "email": f"{uid}@test.com", "name": "TEST Feedback Batch",
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
    assert r.status_code == 200, r.text[:400]
    return r.json()


QUOTED = "\n---\nMs. Lee wrote:\nHi! We meet Wednesday after school. Can you come?"
GOOD_REPLY = ("Hi Ms. Lee,\n\nThank you for the invitation. I can come to the study group on "
              "Wednesday after school and I will bring my notes.\n\nThanks,\nJordan")


# ---------- CRITICAL: blank send must not score 100 ----------
class TestBlankSendM3:
    def test_blank_reply_scores_low(self, fresh_explorer):
        doc = {"messages": [
            {"id": "e1", "folder": "inbox", "read": True},
            {"id": "s1", "folder": "sent", "kind": "reply", "inReplyTo": "e1",
             "to": ["ms.lee@horizonmiddle.edu"], "cc": [], "bcc": [],
             "subject": "Re: Are you joining the study group?",
             "body": QUOTED, "bodyStudent": "", "attachments": [], "read": True},
        ]}
        r = _submit(fresh_explorer["headers"], "email-m3", doc)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        res = _res(d)
        assert d["score"] < 100, d
        assert res["t3"] is False, "greeting must not pass on quoted-only body"
        assert res["t4"] is False, "sign-off must not pass on quoted-only body"
        assert res["t5"] is False, "12-word body must not pass on quoted-only body"
        assert res["t1"] is True and res["t2"] is True
        assert d["score"] == 40, d
        assert d.get("mastery") is not True

    def test_proper_reply_scores_100(self, fresh_explorer):
        doc = {"messages": [
            {"id": "e1", "folder": "inbox", "read": True},
            {"id": "s1", "folder": "sent", "kind": "reply", "inReplyTo": "e1",
             "to": ["ms.lee@horizonmiddle.edu"], "cc": [], "bcc": [],
             "subject": "Re: Are you joining the study group?",
             "body": GOOD_REPLY + QUOTED, "bodyStudent": GOOD_REPLY,
             "attachments": [], "read": True},
        ]}
        d = _submit(fresh_explorer["headers"], "email-m3", doc).json()
        assert _res(d) == {"t1": True, "t2": True, "t3": True, "t4": True, "t5": True}, d
        assert d["score"] == 100 and d["grade"] == "A", d
        assert d["mastery"] is True

    def test_short_body_fails_word_count(self, fresh_explorer):
        short = "Hi Ms. Lee,\n\nOk.\n\nThanks,\nJordan"
        doc = {"messages": [
            {"id": "e1", "folder": "inbox", "read": True},
            {"id": "s1", "folder": "sent", "kind": "reply", "inReplyTo": "e1",
             "to": ["ms.lee@horizonmiddle.edu"], "cc": [], "bcc": [],
             "subject": "Re: Are you joining the study group?",
             "body": short + QUOTED, "bodyStudent": short, "attachments": [], "read": True},
        ]}
        res = _res(_submit(fresh_explorer["headers"], "email-m3", doc).json())
        assert res["t3"] is True and res["t4"] is True and res["t5"] is False, res

    def test_legacy_doc_without_bodystudent_falls_back(self, fresh_explorer):
        """Old saved docs have no bodyStudent -> grading falls back to full body."""
        doc = {"messages": [
            {"id": "e1", "folder": "inbox", "read": True},
            {"id": "s1", "folder": "sent", "kind": "reply", "inReplyTo": "e1",
             "to": ["ms.lee@horizonmiddle.edu"], "cc": [], "bcc": [],
             "subject": "Re: Are you joining the study group?",
             "body": GOOD_REPLY, "attachments": [], "read": True},
        ]}
        d = _submit(fresh_explorer["headers"], "email-m3", doc).json()
        assert d["score"] == 100, d


class TestBlankSendM7:
    def test_recipients_only_not_100(self, fresh_explorer):
        doc = {"messages": [
            {"id": "s1", "folder": "sent", "kind": "new",
             "to": ["ms.lee@horizonmiddle.edu"], "cc": ["principal@horizonmiddle.edu"],
             "bcc": ["you@horizonmiddle.edu"], "subject": "", "body": "",
             "bodyStudent": "", "attachments": [], "read": True},
        ]}
        r = _submit(fresh_explorer["headers"], "email-m7", doc)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        res = _res(d)
        assert d["score"] == 50, d
        assert res["t1"] and res["t2"] and res["t3"]
        assert res["t4"] is False and res["t5"] is False and res["t6"] is False
        assert d.get("mastery") is not True

    def test_complete_email_scores_100(self, fresh_explorer):
        body = ("Hello Ms. Lee,\n\nI wanted to let you know that I finished the group project "
                "outline and will bring it tomorrow.\n\nSincerely,\nJordan")
        doc = {"messages": [
            {"id": "s1", "folder": "sent", "kind": "new",
             "to": ["ms.lee@horizonmiddle.edu"], "cc": ["principal@horizonmiddle.edu"],
             "bcc": ["you@horizonmiddle.edu"], "subject": "Group project outline",
             "body": body, "bodyStudent": body, "attachments": [], "read": True},
        ]}
        d = _submit(fresh_explorer["headers"], "email-m7", doc).json()
        assert d["score"] == 100, d
        assert all(_res(d).values())


# ---------- email-b2: 4 tasks + bcc ----------
class TestEmailB2Bcc:
    def test_task_shape(self, track):
        b2 = {m["id"]: m for m in track["missions"]}["email-b2"]
        tasks = {t["id"]: t["check"] for t in b2["tasks"]}
        assert len(tasks) == 4, tasks
        assert tasks["t1"] == {"kind": "email_opened", "id": "e1"}
        assert tasks["t2"] == {"kind": "picked", "field": "to"}
        assert tasks["t3"] == {"kind": "picked", "field": "cc"}
        assert tasks["t4"] == {"kind": "picked", "field": "bcc"}
        msg = b2["doc"]["messages"][0]
        assert msg["id"] == "e1" and msg["bcc"] == ["principal@horizonmiddle.edu"], msg

    def test_all_picked_100(self, fresh_explorer):
        doc = {"messages": [{"id": "e1", "folder": "inbox", "read": True}],
               "picked": ["to", "cc", "bcc"]}
        d = _submit(fresh_explorer["headers"], "email-b2", doc).json()
        assert d["score"] == 100 and d["total"] == 4 and d["passed"] == 4, d
        assert d["mastery"] is True

    def test_missing_bcc_75(self, fresh_explorer):
        doc = {"messages": [{"id": "e1", "folder": "inbox", "read": True}],
               "picked": ["to", "cc"]}
        d = _submit(fresh_explorer["headers"], "email-b2", doc).json()
        assert d["score"] == 75, d
        assert _res(d)["t4"] is False


# ---------- Track / inbox padding ----------
class TestTrackAndInboxes:
    def test_14_missions(self, track):
        assert len(track["missions"]) == 14, [m["id"] for m in track["missions"]]

    def test_inboxes_padded_to_10(self, track):
        counts = {}
        for m in track["missions"]:
            inbox = [x for x in (m["doc"].get("messages") or []) if x.get("folder") == "inbox"]
            counts[m["id"]] = len(inbox)
        assert counts["email-m6"] == 10, counts
        assert counts["email-m1"] == 10, counts
        assert counts["email-b1"] == 10, counts
        # every mission inbox should hold ~10 messages
        assert all(v == 10 for v in counts.values()), counts

    def test_filler_rows_have_gmail_fields(self, track):
        m6 = {m["id"]: m for m in track["missions"]}["email-m6"]
        for msg in m6["doc"]["messages"]:
            assert msg.get("subject") and msg.get("fromName") and msg.get("date"), msg
            assert "external" in msg

    def test_no_mongo_id_leak(self, track):
        assert "_id" not in track
        for m in track["missions"]:
            assert "_id" not in m


# ---------- Regression ----------
class TestRegression:
    def test_m4_reply_all_full_pass(self, fresh_explorer):
        body = ("Hi Ms. Lee,\n\nThank you for the update about the group project. I can finish "
                "the slides tonight and share them with everyone.\n\nThanks,\nJordan")
        doc = {"messages": [
            {"id": "e1", "folder": "inbox", "read": True},
            {"id": "s1", "folder": "sent", "kind": "replyall", "inReplyTo": "e1",
             "to": ["ms.lee@horizonmiddle.edu"],
             "cc": ["alex@horizonmiddle.edu", "jamie@horizonmiddle.edu"], "bcc": [],
             "subject": "Re: Group project meeting", "body": body + QUOTED,
             "bodyStudent": body, "attachments": [], "read": True},
        ]}
        r = _submit(fresh_explorer["headers"], "email-m4", doc)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d["score"] == 100, d

    def test_m4_blank_replyall_not_100(self, fresh_explorer):
        doc = {"messages": [
            {"id": "e1", "folder": "inbox", "read": True},
            {"id": "s1", "folder": "sent", "kind": "replyall", "inReplyTo": "e1",
             "to": ["ms.lee@horizonmiddle.edu"],
             "cc": ["alex@horizonmiddle.edu", "jamie@horizonmiddle.edu"], "bcc": [],
             "subject": "Re: Group project meeting", "body": QUOTED,
             "bodyStudent": "", "attachments": [], "read": True},
        ]}
        d = _submit(fresh_explorer["headers"], "email-m4", doc).json()
        assert d["score"] < 100, d

    def test_m8_attachment_full_pass(self, fresh_explorer):
        body = ("Hello Mr. Diaz,\n\nI signed the field trip form and attached it here so you have "
                "it before Friday.\n\nThank you,\nJordan")
        doc = {"messages": [
            {"id": "e1", "folder": "inbox", "read": True},
            {"id": "s1", "folder": "sent", "kind": "reply", "inReplyTo": "e1",
             "to": ["mr.diaz@horizonmiddle.edu"], "cc": [], "bcc": [],
             "subject": "Re: Field trip form needed", "body": body,
             "bodyStudent": body, "attachments": [{"name": "Field Trip Form.pdf"}], "read": True},
        ]}
        d = _submit(fresh_explorer["headers"], "email-m8", doc).json()
        assert d["score"] == 100, d

    def test_m8_blank_with_attachment_not_100(self, fresh_explorer):
        doc = {"messages": [
            {"id": "e1", "folder": "inbox", "read": True},
            {"id": "s1", "folder": "sent", "kind": "reply", "inReplyTo": "e1",
             "to": ["mr.diaz@horizonmiddle.edu"], "cc": [], "bcc": [],
             "subject": "Re: Field trip form needed",
             "body": "\n---\nMr. Diaz wrote:\nHi, please send back your signed field trip form. Thanks!",
             "bodyStudent": "", "attachments": [{"name": "Field Trip Form.pdf"}], "read": True},
        ]}
        d = _submit(fresh_explorer["headers"], "email-m8", doc).json()
        assert d["score"] == 40, d

    def test_m5_forward_full_pass(self, fresh_explorer):
        body = ("Hi Coach Rivera,\n\nI am forwarding this message because it has the tryout details "
                "you asked me about earlier today.\n\nThanks,\nJordan")
        doc = {"messages": [
            {"id": "e1", "folder": "inbox", "read": True},
            {"id": "s1", "folder": "sent", "kind": "forward", "inReplyTo": "e1",
             "to": ["mom@family.com"], "cc": [], "bcc": [],
             "subject": "Fwd: Basketball tryouts Friday", "body": body + QUOTED,
             "bodyStudent": body, "attachments": [], "read": True},
        ]}
        d = _submit(fresh_explorer["headers"], "email-m5", doc).json()
        res = _res(d)
        assert res.get("t4") is True and res.get("t5") is True and res.get("t6") is True, d

    def test_m10_ai_sanity(self, fresh_explorer):
        body = ("Dear Mr. Patel,\n\nThank you for mentoring me during my internship. I appreciate "
                "your guidance on the inventory project. Would you prefer the spreadsheet organized "
                "by product category or by supplier?\n\nSincerely,\nAlex Rivera")
        doc = {"messages": [
            {"id": "s1", "folder": "sent", "kind": "new", "to": ["mentor@company.com"],
             "cc": [], "bcc": [], "subject": "Thank you and a question about my project",
             "body": body, "bodyStudent": body, "attachments": [], "read": True},
        ]}
        t0 = time.time()
        r = _submit(fresh_explorer["headers"], "email-m10", doc, timeout=200)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d["ai_rating"] in ("Excellent", "Good", "Needs work"), d
        assert isinstance(d.get("ai_feedback"), str) and d["ai_feedback"]
        assert d["score"] >= 50, d
        print(f"m10 AI grading {time.time() - t0:.1f}s rating={d['ai_rating']} score={d['score']}")


# ---------- Guide preview (non-explorer submit) ----------
class TestGuidePreview:
    def test_guide_gets_preview_result_no_persistence(self):
        doc = {"messages": [{"id": "e1", "folder": "inbox", "read": True},
                            {"id": "x", "folder": "inbox", "read": True}],
               "picked": ["to", "cc", "bcc"]}
        r = requests.post(f"{API}/studio/email/email-b2/submit", headers=GH,
                          json={"doc": doc}, timeout=60)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d.get("preview") is True, d
        assert d.get("points_awarded", 0) == 0, d
        assert d["score"] == 100, d
        prog = requests.get(f"{API}/studio/email", headers=GH, timeout=20).json().get("progress", {})
        assert "email-b2" not in (prog or {}), prog
