"""Tests for iteration 23: leaderboard scopes, /me/rank-scopes, /me/school,
and by-class reports (studio reports + assessment reports)."""
import os

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")
API = f"{BASE_URL}/api"

GUIDE_TOK = "em_guide_tok"
EXP_TOK = "em_exp_tok"
GUIDE_EXP_ID = "exp_61e14d36b5eb"
GUIDE_SCHOOL = "Northgate Middle School"


@pytest.fixture(scope="module")
def guide():
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {GUIDE_TOK}", "Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def explorer():
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {EXP_TOK}", "Content-Type": "application/json"})
    return s


# ---------------- auth sanity ----------------
class TestAuth:
    def test_guide_me(self, guide):
        r = guide.get(f"{API}/auth/me")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["role"] == "guide"
        assert d.get("school") == GUIDE_SCHOOL, f"expected school preserved, got {d.get('school')}"

    def test_explorer_me(self, explorer):
        r = explorer.get(f"{API}/auth/me")
        assert r.status_code == 200, r.text
        assert r.json()["role"] == "explorer"

    def test_leaderboard_requires_auth(self):
        r = requests.get(f"{API}/leaderboard")
        assert r.status_code in (401, 403), r.status_code


# ---------------- /me/rank-scopes ----------------
class TestRankScopes:
    def test_guide_scopes(self, guide):
        r = guide.get(f"{API}/me/rank-scopes")
        assert r.status_code == 200, r.text
        d = r.json()
        assert isinstance(d["classes"], list) and len(d["classes"]) > 0
        assert any(c["expedition_id"] == GUIDE_EXP_ID for c in d["classes"])
        assert d["teacher"]["guide_id"] == "em-guide"
        assert d["school"] == GUIDE_SCHOOL

    def test_explorer_scopes(self, explorer):
        r = explorer.get(f"{API}/me/rank-scopes")
        assert r.status_code == 200, r.text
        d = r.json()
        assert "classes" in d and isinstance(d["classes"], list)
        # em-exp is expected to be in no class -> empty classes, teacher None
        assert d["classes"] == [], f"expected em-exp in no class, got {d['classes']}"
        assert d.get("teacher") in (None, {})


# ---------------- leaderboard scopes ----------------
class TestLeaderboardScopes:
    def _assert_shape(self, d, scope):
        assert d["scope"] == scope
        assert isinstance(d["entries"], list)
        assert isinstance(d["fleets"], list)
        assert isinstance(d.get("scope_label"), str) and d["scope_label"]
        for e in d["entries"]:
            for k in ("rank", "user_id", "name", "score", "horizon_points", "is_me", "tier"):
                assert k in e, f"missing {k} in entry"
            assert "_id" not in e

    def test_global(self, guide):
        r = guide.get(f"{API}/leaderboard", params={"scope": "global"})
        assert r.status_code == 200, r.text
        d = r.json()
        self._assert_shape(d, "global")
        assert d["metric"] == "overall"
        assert len(d["entries"]) > 0

    def test_class_scope(self, guide):
        r = guide.get(f"{API}/leaderboard", params={"scope": "class", "expedition_id": GUIDE_EXP_ID})
        assert r.status_code == 200, r.text
        d = r.json()
        self._assert_shape(d, "class")
        assert d["scope_label"] == "Test Class Assign"
        assert len(d["entries"]) > 0, "class scope returned no explorers"
        # CRITICAL regression: points must be non-zero for a class that earned points
        assert max(e["score"] for e in d["entries"]) > 0, "class scope individual points all zero"
        assert max(f["points"] for f in d["fleets"]) > 0, "class scope fleet points all zero"

    def test_class_scope_missing_expedition_id(self, guide):
        r = guide.get(f"{API}/leaderboard", params={"scope": "class"})
        assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text}"

    def test_class_scope_bad_expedition_id(self, guide):
        r = guide.get(f"{API}/leaderboard", params={"scope": "class", "expedition_id": "nope_123"})
        assert r.status_code == 404, r.status_code

    def test_teacher_scope(self, guide):
        r = guide.get(f"{API}/leaderboard", params={"scope": "teacher"})
        assert r.status_code == 200, r.text
        d = r.json()
        self._assert_shape(d, "teacher")
        assert "Explorers" in d["scope_label"]
        assert len(d["entries"]) > 0
        # North Star fleet should be non-zero (regression from the zeros bug)
        north = [f for f in d["fleets"] if f["fleet"] == "North Star"]
        assert north, f"North Star fleet missing: {d['fleets']}"
        assert north[0]["points"] > 0, "North Star fleet points are 0 (regression)"

    def test_school_scope(self, guide):
        r = guide.get(f"{API}/leaderboard", params={"scope": "school"})
        assert r.status_code == 200, r.text
        d = r.json()
        self._assert_shape(d, "school")
        assert d["scope_label"] == GUIDE_SCHOOL
        assert len(d["entries"]) > 0

    def test_school_scope_unknown_school(self, guide):
        r = guide.get(f"{API}/leaderboard", params={"scope": "school", "school": "No Such School XYZ"})
        assert r.status_code == 200, r.text
        assert r.json()["entries"] == []

    def test_week_period(self, guide):
        r = guide.get(f"{API}/leaderboard", params={"scope": "teacher", "period": "week"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["metric"] == "week"
        self._assert_shape(d, "teacher")

    def test_total_points_include_studio_and_checkpoints(self, guide):
        """Score in overall metric must equal horizon_points (total), not quest-only."""
        r = guide.get(f"{API}/leaderboard", params={"scope": "class", "expedition_id": GUIDE_EXP_ID})
        d = r.json()
        for e in d["entries"]:
            assert e["score"] == e["horizon_points"], e


# ---------------- by-class reports ----------------
class TestByClassReports:
    def test_studio_reports_by_class(self, guide):
        r = guide.get(f"{API}/studio/reports/all", params={"expedition_id": GUIDE_EXP_ID})
        assert r.status_code == 200, r.text
        d = r.json()
        assert isinstance(d, (list, dict))

    def test_studio_reports_bad_class(self, guide):
        r = guide.get(f"{API}/studio/reports/all", params={"expedition_id": "nope_123"})
        assert r.status_code in (400, 403, 404), r.status_code

    def test_assessment_reports_by_class(self, guide):
        r = guide.get(f"{API}/assessments/reports", params={"expedition_id": GUIDE_EXP_ID})
        assert r.status_code == 200, r.text

    def test_assessment_reports_bad_class(self, guide):
        r = guide.get(f"{API}/assessments/reports", params={"expedition_id": "nope_123"})
        assert r.status_code in (400, 403, 404), r.status_code

    def test_reports_require_guide(self, explorer):
        r = explorer.get(f"{API}/studio/reports/all", params={"expedition_id": GUIDE_EXP_ID})
        assert r.status_code in (401, 403), r.status_code


# ---------------- POST /me/school ----------------
class TestSchoolUpdate:
    def test_set_and_restore_school(self, guide):
        r = guide.post(f"{API}/me/school", json={"school": "TEST_QA School"})
        assert r.status_code == 200, r.text
        assert r.json()["school"] == "TEST_QA School"
        assert guide.get(f"{API}/auth/me").json()["school"] == "TEST_QA School"
        # restore
        r2 = guide.post(f"{API}/me/school", json={"school": GUIDE_SCHOOL})
        assert r2.status_code == 200
        assert guide.get(f"{API}/auth/me").json()["school"] == GUIDE_SCHOOL

    def test_explorer_cannot_set_school(self, explorer):
        r = explorer.post(f"{API}/me/school", json={"school": "Hack School"})
        assert r.status_code in (401, 403), r.status_code
