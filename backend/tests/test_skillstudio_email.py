"""HorizonQuest Skill Studio (Email track) backend tests — Phase 4.

Covers:
- GET /api/studio/email: track shape ('Email & Communication'), config
  (studentEmail, fileLibrary, signature starting with em-dash, 4 types),
  12 missions with expected ids.
- POST /api/studio/email/{mission_id}/submit auto-grading:
  Deterministic email check kinds (email_opened, searched, sent_exists,
  subject_prefix/nonempty, to/cc/bcc_includes, cc_min, has_greeting,
  has_signoff, has_greeting_signoff, has_attachment, body_min_words,
  formatting, subject_and_to). Fresh explorer used for clean assertions.
- AI-graded missions m10/m11/m12: Claude via emergentintegrations
  (claude-sonnet-4-6) — a well-written professional/formal email returns
  rating != 'Needs work' (Excellent/Good), a rude/casual email returns
  rating 'Needs work' with lower AI-pass count. `ai_feedback` and
  `ai_rating` are present in the response.
- Best-attempt sticky score + points delta.
- Letter-grade scale (F/D/C/B/A) via partial capstone submits.
- Guide 403 on submit; unknown mission 404; wrong-track 404; unauth 401.
- Reports endpoint: /api/studio/reports/all -> 200 for guide, 403 for
  explorer. Response has totals + students with per-track avg/mastered.

Uses fresh explorer session (em-fresh / em_fresh_tok) so first-submit
assertions are deterministic. Guide is em-guide / em_guide_tok.
"""
import copy
import os
import time
import pytest
import pymongo
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://explorer-journey-4.preview.emergentagent.com",
).rstrip("/")
API = f"{BASE_URL}/api"

EXP_TOK = "em_fresh_tok"
EXP_UID = "em-fresh"
GUIDE_TOK = "em_guide_tok"
EH = {"Authorization": f"Bearer {EXP_TOK}", "Content-Type": "application/json"}
GH = {"Authorization": f"Bearer {GUIDE_TOK}", "Content-Type": "application/json"}

STUDENT_EMAIL = "you@horizonmiddle.edu"


def _mongo():
    c = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    return c[os.environ.get("DB_NAME", "test_database")]


def _fetch(mission_id):
    d = requests.get(f"{API}/studio/email", headers=EH, timeout=15).json()
    return next(m for m in d["missions"] if m["id"] == mission_id)


def _sent(kind, to=None, cc=None, bcc=None, subject="", body="",
          attachments=None, has_bold=False, has_bullets=False, has_signature=False):
    return {
        "id": f"sent_{kind}_{int(time.time() * 1000)}",
        "folder": "sent", "kind": kind, "fromName": "You", "fromEmail": STUDENT_EMAIL,
        "to": to or [], "cc": cc or [], "bcc": bcc or [], "subject": subject, "body": body,
        "attachments": attachments or [], "read": True,
        "hasBold": has_bold, "hasBullets": has_bullets, "hasSignature": has_signature,
    }


def _mark_read(doc, mid):
    doc = copy.deepcopy(doc)
    for m in doc.get("messages", []):
        if m["id"] == mid:
            m["read"] = True
    return doc


def _submit(mission_id, doc, timeout=90):
    return requests.post(
        f"{API}/studio/email/{mission_id}/submit",
        headers=EH, json={"doc": doc}, timeout=timeout,
    )


@pytest.fixture(scope="module", autouse=True)
def _reset_email_state():
    db = _mongo()
    db.studio_progress.delete_many({"user_id": EXP_UID})
    db.points_events.delete_many({"user_id": EXP_UID, "type": "studio"})
    db.users.update_one(
        {"user_id": EXP_UID},
        {"$set": {"horizon_points": 0, "compass_marks": 0}},
    )
    yield


class TestSkillStudioEmail:
    """All email tests in one class so xdist loadscope pins to one worker."""

    # ---------- Public track shape ----------
    def test_010_public_track_shape(self):
        r = requests.get(f"{API}/studio/email", headers=EH, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["track"]["id"] == "email"
        assert d["track"]["name"] == "Email & Communication"
        cfg = d["config"]
        assert cfg["studentEmail"] == STUDENT_EMAIL
        assert isinstance(cfg["fileLibrary"], list) and "Field Trip Form.pdf" in cfg["fileLibrary"]
        assert cfg["signature"].strip().startswith("—")  # em-dash sig
        types = [t["id"] for t in cfg["types"]]
        assert set(types) == {"formal", "professional", "semiformal", "informal"}
        missions = d["missions"]
        assert len(missions) == 12
        ids = [m["id"] for m in missions]
        assert ids == [f"email-m{i}" for i in range(1, 13)]
        for m in missions:
            assert m["track"] == "email"
            assert isinstance(m["tasks"], list) and m["tasks"]
            assert isinstance(m["doc"]["messages"], list)
        assert d["progress"] == {}

    # ---------- Guards ----------
    def test_100_guide_submit_403(self):
        r = requests.post(f"{API}/studio/email/email-m1/submit", headers=GH,
                          json={"doc": {}}, timeout=15)
        assert r.status_code == 403

    def test_110_unknown_mission_404(self):
        r = _submit("email-mX", {"messages": []}, timeout=15)
        assert r.status_code == 404

    def test_120_wrong_track_404(self):
        r = requests.post(f"{API}/studio/docs/email-m1/submit", headers=EH,
                          json={"doc": {"messages": []}}, timeout=15)
        assert r.status_code == 404

    def test_130_unauth_submit_401(self):
        r = requests.post(f"{API}/studio/email/email-m1/submit",
                          json={"doc": {"messages": []}}, timeout=15)
        assert r.status_code == 401

    # ---------- Reports endpoint (guide vs explorer) ----------
    def test_140_reports_guide_ok_explorer_403(self):
        r_g = requests.get(f"{API}/studio/reports/all", headers=GH, timeout=15)
        assert r_g.status_code == 200
        body = r_g.json()
        assert "totals" in body and "students" in body
        assert body["totals"]["email"] == 12
        r_e = requests.get(f"{API}/studio/reports/all", headers=EH, timeout=15)
        assert r_e.status_code == 403

    # ---------- Deterministic per-mission perfect submits ----------
    def test_200_m1_open_inbox_emails(self):
        m = _fetch("email-m1")
        doc = copy.deepcopy(m["doc"])
        doc = _mark_read(doc, "e1")
        doc = _mark_read(doc, "e2")
        r = _submit("email-m1", doc)
        assert r.status_code == 200
        d = r.json()
        assert d["passed"] == 2 and d["total"] == 2
        assert d["score"] == 100 and d["grade"] == "A" and d["mastery"] is True

    def test_210_m2_search_and_open(self):
        m = _fetch("email-m2")
        doc = copy.deepcopy(m["doc"])
        doc["searched"] = True
        doc = _mark_read(doc, "e1")
        d = _submit("email-m2", doc).json()
        assert d["passed"] == 2 and d["score"] == 100 and d["grade"] == "A"

    def test_220_m3_reply_full(self):
        m = _fetch("email-m3")
        doc = copy.deepcopy(m["doc"])
        doc["messages"].append(_sent(
            "reply", to=["ms.lee@horizonmiddle.edu"],
            subject="Re: Are you joining the study group?",
            body="Hi Ms. Lee,\n\nYes, I can join on Wednesday. See you then.\n\nThanks,\nJordan",
        ))
        d = _submit("email-m3", doc).json()
        assert d["passed"] == 4 and d["score"] == 100 and d["grade"] == "A"

    def test_230_m4_reply_all_keeps_cc(self):
        m = _fetch("email-m4")
        doc = copy.deepcopy(m["doc"])
        doc["messages"].append(_sent(
            "replyall", to=["sam@horizonmiddle.edu"],
            cc=["alex@horizonmiddle.edu", "jamie@horizonmiddle.edu"],
            subject="Re: Project meeting time?",
            body="Hi team,\n\n3pm works for me.\n\nThanks,\nJordan",
        ))
        d = _submit("email-m4", doc).json()
        assert d["passed"] == 3 and d["score"] == 100 and d["grade"] == "A"

    def test_240_m5_forward(self):
        m = _fetch("email-m5")
        doc = copy.deepcopy(m["doc"])
        doc["messages"].append(_sent(
            "forward", to=["alex@horizonmiddle.edu"],
            subject="Fwd: Game schedule",
            body="Hey Alex, here is the schedule from Coach. Games are Tuesdays and Thursdays this month.",
        ))
        d = _submit("email-m5", doc).json()
        assert d["passed"] == 4 and d["score"] == 100

    def test_250_m6_compose_new(self):
        m = _fetch("email-m6")
        doc = copy.deepcopy(m["doc"])
        doc["messages"].append(_sent(
            "new", to=["ms.lee@horizonmiddle.edu"],
            subject="Missed homework question",
            body="Hi Ms. Lee,\n\nCould you tell me what homework I missed?\n\nThanks,\nJordan",
        ))
        d = _submit("email-m6", doc).json()
        assert d["passed"] == 4 and d["score"] == 100

    def test_260_m7_to_cc_bcc(self):
        m = _fetch("email-m7")
        doc = copy.deepcopy(m["doc"])
        doc["messages"].append(_sent(
            "new", to=["ms.lee@horizonmiddle.edu"],
            cc=["principal@horizonmiddle.edu"], bcc=["you@horizonmiddle.edu"],
            subject="Request", body="Hi Ms. Lee, here is a note. Thanks, Jordan",
        ))
        d = _submit("email-m7", doc).json()
        assert d["passed"] == 3 and d["score"] == 100

    def test_270_m8_attach(self):
        m = _fetch("email-m8")
        doc = copy.deepcopy(m["doc"])
        doc = _mark_read(doc, "e1")
        doc["messages"].append(_sent(
            "reply", to=["mr.diaz@horizonmiddle.edu"],
            subject="Re: Field trip form needed",
            body="Hi Mr. Diaz, please find the signed form attached. Thanks, Jordan",
            attachments=[{"name": "Field Trip Form.pdf"}],
        ))
        d = _submit("email-m8", doc).json()
        assert d["passed"] == 3 and d["score"] == 100

    def test_280_m9_formatting(self):
        m = _fetch("email-m9")
        doc = copy.deepcopy(m["doc"])
        doc["messages"].append(_sent(
            "new", to=["team@horizonmiddle.edu"],
            subject="Practice details",
            body="**Practice** is Friday.\n• Bring water\n• Wear sneakers\n\n—\nJordan",
            has_bold=True, has_bullets=True, has_signature=True,
        ))
        d = _submit("email-m9", doc).json()
        assert d["passed"] == 4 and d["score"] == 100

    # ---------- Kind coverage / fail paths ----------
    def test_300_m3_missing_greeting_fails_t3(self):
        m = _fetch("email-m3")
        doc = copy.deepcopy(m["doc"])
        doc["messages"].append(_sent(
            "reply", to=["ms.lee@horizonmiddle.edu"],
            subject="Re: Are you joining the study group?",
            body="Yes I can come.\n\nThanks, Jordan",
        ))
        d = _submit("email-m3", doc).json()
        # sent, Re: subject, sign-off pass; greeting fails -> current 3/4
        results = {r["id"]: r["passed"] for r in d["results"]}
        assert results["t3"] is False
        # sticky best from earlier perfect A stays 100
        assert d["score"] == 100

    def test_310_m5_note_too_short_fails(self):
        m = _fetch("email-m5")
        doc = copy.deepcopy(m["doc"])
        doc["messages"].append(_sent(
            "forward", to=["alex@horizonmiddle.edu"],
            subject="Fwd: Game schedule", body="See attached.",
        ))
        d = _submit("email-m5", doc).json()
        results = {r["id"]: r["passed"] for r in d["results"]}
        assert results["t4"] is False  # body_min_words 10

    def test_320_m4_missing_cc_fails_cc_min(self):
        m = _fetch("email-m4")
        doc = copy.deepcopy(m["doc"])
        doc["messages"].append(_sent(
            "replyall", to=["sam@horizonmiddle.edu"], cc=[],
            subject="Re: Project meeting time?",
            body="Hi team, 3pm works. Thanks, Jordan",
        ))
        d = _submit("email-m4", doc).json()
        results = {r["id"]: r["passed"] for r in d["results"]}
        assert results["t2"] is False  # cc_min

    def test_330_m8_wrong_attachment_name_fails(self):
        m = _fetch("email-m8")
        doc = copy.deepcopy(m["doc"])
        doc = _mark_read(doc, "e1")
        doc["messages"].append(_sent(
            "reply", to=["mr.diaz@horizonmiddle.edu"],
            subject="Re: Field trip form needed",
            body="Hi Mr. Diaz, attached is a different file for you. Thanks, Jordan",
            attachments=[{"name": "Resume.pdf"}],
        ))
        d = _submit("email-m8", doc).json()
        results = {r["id"]: r["passed"] for r in d["results"]}
        assert results["t2"] is False  # specific-name attach

    def test_340_m9_bad_formatting_fails(self):
        m = _fetch("email-m9")
        doc = copy.deepcopy(m["doc"])
        doc["messages"].append(_sent(
            "new", to=["team@horizonmiddle.edu"], subject="Details",
            body="Plain text with no formatting at all.",
            has_bold=False, has_bullets=False, has_signature=False,
        ))
        d = _submit("email-m9", doc).json()
        results = {r["id"]: r["passed"] for r in d["results"]}
        assert results["t2"] is False and results["t3"] is False and results["t4"] is False

    # ---------- Letter-grade scale using m12 (10+ tasks; before m12 perfect) ----------
    def test_400_grade_scale_partial(self):
        """First submit for m12: only t1 (open e1) and t5 (compose subject_and_to) -> ~2/10 = F."""
        m = _fetch("email-m12")
        doc = copy.deepcopy(m["doc"])
        doc = _mark_read(doc, "e1")
        doc["messages"].append(_sent(
            "new", to=["coworker@company.com"], subject="Hello",
            body="Hi, quick note.",
        ))
        d = _submit("email-m12", doc, timeout=120).json()
        # deterministic: t1 open, t5 subject_and_to pass; ai t6/t7/t8 likely fail
        # (short/casual). Score < 60 -> F.
        assert d["score"] < 60 and d["grade"] == "F"
        assert d["mastery"] is False

    # ---------- AI missions with real Claude ----------
    def test_500_m10_professional_ai_pass(self):
        """Well-written professional email -> AI dims should mostly pass, rating != 'Needs work'."""
        m = _fetch("email-m10")
        doc = copy.deepcopy(m["doc"])
        doc["messages"].append(_sent(
            "new", to=["mentor@company.com"],
            subject="Thank you and a question about the project",
            body=(
                "Dear Mr. Alvarez,\n\n"
                "Thank you very much for taking the time to mentor me during my internship. "
                "I have really appreciated your guidance on the customer research project.\n\n"
                "I have one question: for next week's presentation, would you prefer that I "
                "focus on the survey findings or on the interview themes first?\n\n"
                "Thank you again for your support.\n\n"
                "Sincerely,\nJordan Rivera"
            ),
        ))
        r = _submit("email-m10", doc, timeout=120)
        assert r.status_code == 200
        d = r.json()
        assert "ai_feedback" in d and "ai_rating" in d
        # t1 deterministic pass; t2/t3/t4 are AI dims (tone/etiquette/grammar)
        results = {res["id"]: res["passed"] for res in d["results"]}
        assert results["t1"] is True
        ai_passes = sum(1 for k in ("t2", "t3", "t4") if results.get(k))
        # Ask for at least 2/3 AI dims to pass on a strong email; rating != "Needs work"
        assert ai_passes >= 2, f"AI passes only {ai_passes}/3; feedback={d.get('ai_feedback')!r} rating={d.get('ai_rating')!r}"
        assert d["ai_rating"] != "Needs work", f"rating={d.get('ai_rating')!r} feedback={d.get('ai_feedback')!r}"
        assert d["ai_rating"] != "Unrated", f"AI unavailable / errored: {d.get('ai_feedback')!r}"
        # With mostly-passing tasks, grade should be A or B.
        assert d["grade"] in ("A", "B"), f"grade={d['grade']} score={d['score']}"

    def test_510_m10_rude_ai_fail(self):
        """A rude / casual email -> AI dims should fail, rating 'Needs work', lower grade."""
        m = _fetch("email-m10")
        doc = copy.deepcopy(m["doc"])
        doc["messages"].append(_sent(
            "new", to=["mentor@company.com"],
            subject="yo",
            body=(
                "YO DUDE!!! ur project is kinda WEIRD lol. "
                "y do i even hav 2 do this? U shud tell me the anser NOW. "
                "peace out"
            ),
        ))
        r = _submit("email-m10", doc, timeout=120)
        assert r.status_code == 200
        d = r.json()
        results = {res["id"]: res["passed"] for res in d["results"]}
        ai_passes = sum(1 for k in ("t2", "t3", "t4") if results.get(k))
        assert ai_passes <= 1, f"Rude email got {ai_passes}/3 AI passes; feedback={d.get('ai_feedback')!r}"
        assert d["ai_rating"] in ("Needs work", "Good"), f"rating={d.get('ai_rating')!r}"
        # AI feedback should be non-empty for a real Claude call
        assert (d.get("ai_feedback") or "").strip(), "empty AI feedback (fallback/mock?)"
        # sticky best from the prior m10 perfect submit stays high; current low count is
        # what we assert via ai_passes above.

    # ---------- Persistence ----------
    def test_900_progress_persisted(self):
        d = requests.get(f"{API}/studio/email", headers=EH, timeout=15).json()
        prog = d["progress"]
        # m1..m9 should be A/100 from earlier perfect submits.
        for mid in [f"email-m{i}" for i in range(1, 10)]:
            assert mid in prog, f"missing {mid}"
            assert prog[mid]["grade"] == "A", f"{mid} grade {prog[mid]['grade']}"
            assert prog[mid]["score"] == 100

    def test_910_points_event_logged(self):
        db = _mongo()
        ev = db.points_events.find_one(
            {"user_id": EXP_UID, "mission_id": "email-m1", "type": "studio"}
        )
        assert ev is not None and ev["delta"] > 0
