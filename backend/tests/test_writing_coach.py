"""Backend tests for the AI Writing Coach feature:
- POST /api/ai/proofread
- GET/PUT /api/studio/writing-gate (route ordering vs /studio/{track_id})
- Mission submit with writing_issues -> writing_flag in /api/studio/reports/all
"""
import os
import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base.rstrip("/")

EXP_TOK = "em_exp_tok"
GUIDE_TOK = "em_guide_tok"

MESSY = "i dont no wut to rite for this asignment. my teacher sayed it was due yesterday  can you help me"
CLEAN = "I finished my science homework last night. My teacher said it is due on Friday."


def H(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def sess():
    s = requests.Session()
    return s


# ---------- proofread ----------
class TestProofread:
    def test_auth_required(self, sess):
        r = sess.post(f"{BASE_URL}/api/ai/proofread", json={"text": MESSY})
        assert r.status_code in (401, 403), r.text

    def test_messy_text_returns_issues(self, sess):
        r = sess.post(f"{BASE_URL}/api/ai/proofread", headers=H(EXP_TOK), json={"text": MESSY}, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        assert isinstance(d.get("issues"), list)
        assert not d.get("unavailable"), f"LLM unavailable: {d}"
        assert len(d["issues"]) > 0, f"expected issues for messy text, got {d}"
        for iss in d["issues"]:
            assert iss["text"] in MESSY, f"issue.text not an exact substring: {iss}"
            assert iss["type"] in ("spelling", "grammar", "capitalization", "punctuation"), iss
            assert isinstance(iss["message"], str) and iss["message"]
        assert isinstance(d.get("corrected"), str) and d["corrected"].strip()

    def test_clean_text_no_issues(self, sess):
        r = sess.post(f"{BASE_URL}/api/ai/proofread", headers=H(EXP_TOK), json={"text": CLEAN}, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["issues"] == [], f"clean text flagged: {d['issues']}"

    def test_empty_text(self, sess):
        r = sess.post(f"{BASE_URL}/api/ai/proofread", headers=H(EXP_TOK), json={"text": "   "})
        assert r.status_code == 200
        assert r.json() == {"issues": [], "corrected": ""}

    def test_missing_field_422(self, sess):
        r = sess.post(f"{BASE_URL}/api/ai/proofread", headers=H(EXP_TOK), json={})
        assert r.status_code == 422

    def test_punctuation_and_capitalization_detected(self, sess):
        text = "my name is sven i live in norway  its cold there"
        r = sess.post(f"{BASE_URL}/api/ai/proofread", headers=H(EXP_TOK), json={"text": text}, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        types = {i["type"] for i in d["issues"]}
        assert d["issues"], "no issues found for un-capitalized/unpunctuated text"
        assert types & {"capitalization", "punctuation", "grammar"}, types


# ---------- writing gate ----------
class TestWritingGate:
    def test_route_not_captured_by_track_route(self, sess):
        r = sess.get(f"{BASE_URL}/api/studio/writing-gate", headers=H(EXP_TOK))
        assert r.status_code == 200, f"gate route shadowed by /studio/{{track_id}}: {r.status_code} {r.text}"
        assert isinstance(r.json().get("gate"), bool)

    def test_guide_can_set_and_explorer_inherits(self, sess):
        try:
            r = sess.put(f"{BASE_URL}/api/studio/writing-gate", headers=H(GUIDE_TOK), json={"gate": False})
            assert r.status_code == 200, r.text
            assert r.json()["gate"] is False
            assert sess.get(f"{BASE_URL}/api/studio/writing-gate", headers=H(GUIDE_TOK)).json()["gate"] is False
            # explorer in guide's expedition inherits
            assert sess.get(f"{BASE_URL}/api/studio/writing-gate", headers=H(EXP_TOK)).json()["gate"] is False
        finally:
            sess.put(f"{BASE_URL}/api/studio/writing-gate", headers=H(GUIDE_TOK), json={"gate": True})
        assert sess.get(f"{BASE_URL}/api/studio/writing-gate", headers=H(EXP_TOK)).json()["gate"] is True

    def test_explorer_cannot_set_gate(self, sess):
        r = sess.put(f"{BASE_URL}/api/studio/writing-gate", headers=H(EXP_TOK), json={"gate": False})
        assert r.status_code == 403, r.text

    def test_unauth_gate(self, sess):
        assert sess.get(f"{BASE_URL}/api/studio/writing-gate").status_code in (401, 403)

    def test_invalid_payload(self, sess):
        r = sess.put(f"{BASE_URL}/api/studio/writing-gate", headers=H(GUIDE_TOK), json={"gate": "nope"})
        assert r.status_code == 422, r.text


# ---------- submit with writing_issues -> reports writing_flag ----------
class TestWritingFlagReports:
    MISSION = "docs-m1"

    def _submit(self, sess, issues):
        return sess.post(f"{BASE_URL}/api/studio/docs/{self.MISSION}/submit", headers=H(EXP_TOK),
                         json={"doc": {"blocks": [{"id": "b1", "type": "p", "text": "hello"}]},
                               "writing_issues": issues}, timeout=120)

    def test_submit_records_flag_and_reports_show_it(self, sess):
        r = self._submit(sess, 3)
        assert r.status_code == 200, r.text
        row = None
        rep = sess.get(f"{BASE_URL}/api/studio/reports/all", headers=H(GUIDE_TOK), timeout=60)
        assert rep.status_code == 200, rep.text
        for s in rep.json()["students"]:
            if s["user_id"] == "em-exp":
                row = s
        assert row is not None, "em-exp not in guide reports"
        assert row["tracks"].get("docs", {}).get("writing_flag") is True, row["tracks"].get("docs")

    def test_resubmit_clean_clears_flag(self, sess):
        r = self._submit(sess, 0)
        assert r.status_code == 200, r.text
        rep = sess.get(f"{BASE_URL}/api/studio/reports/all", headers=H(GUIDE_TOK), timeout=60).json()
        row = next(s for s in rep["students"] if s["user_id"] == "em-exp")
        assert row["tracks"]["docs"]["writing_flag"] is False, "flag not cleared after clean resubmit"

    def test_submit_defaults_writing_issues(self, sess):
        r = sess.post(f"{BASE_URL}/api/studio/docs/{self.MISSION}/submit", headers=H(EXP_TOK),
                      json={"doc": {"blocks": []}}, timeout=120)
        assert r.status_code == 200, r.text

    def test_reports_requires_guide(self, sess):
        r = sess.get(f"{BASE_URL}/api/studio/reports/all", headers=H(EXP_TOK))
        assert r.status_code == 403
