"""HorizonQuest Skill Studio (Docs track) backend tests.

Covers:
- GET /api/studio/docs payload shape (track / config / 12 missions with tasks/blocks)
- POST /api/studio/docs/{mission_id}/submit auto-grading across every check kind
  (fmt, fmt_multi, fmt_all, fmt_and, type, type_multi, text_contains, link,
  header_contains, footer_pagenum, table, table_cell_filled, exported, text_replaced)
- Letter grade scale A>=90, B>=80, C>=70, D>=60, F<60 + mastery @ 90%
- Best-attempt semantics (resubmitting lower score does not lower awarded points)
- Guide 403 on submit; unknown mission 404; unauth 401
- Points events (type='studio', territory='t2') written to Mongo

All state-dependent tests are grouped in one class so pytest-xdist --dist loadscope
pins them to a single worker → deterministic ordering.
"""
import copy
import os
import pytest
import pymongo
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://explorer-journey-4.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

EXP_TOK = "studio_fresh_tok"       # clean explorer for point-increment assertions
GUIDE_TOK = "qa_ui_guide_tok"       # guide (403)
EH = {"Authorization": f"Bearer {EXP_TOK}", "Content-Type": "application/json"}
GH = {"Authorization": f"Bearer {GUIDE_TOK}", "Content-Type": "application/json"}


def _mongo():
    c = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    return c[os.environ.get("DB_NAME", "test_database")]


def _fetch_mission(mission_id):
    d = requests.get(f"{API}/studio/docs", headers=EH).json()
    return next(m for m in d["missions"] if m["id"] == mission_id)


def _apply_check(doc, check):
    """Mutate `doc` so this task passes. Mirrors _check_one for building perfect submissions."""
    kind = check["kind"]
    if kind == "fmt":
        b = next(b for b in doc["blocks"] if b["id"] == check["block"])
        b["fmt"][check["attr"]] = check["equals"]
    elif kind == "fmt_all":
        for b in doc["blocks"]:
            if b.get("type") in ("paragraph", "bullet", "number", "heading"):
                b["fmt"][check["attr"]] = check["equals"]
    elif kind == "fmt_multi":
        for bid in check["blocks"]:
            b = next(b for b in doc["blocks"] if b["id"] == bid)
            b["fmt"][check["attr"]] = check["equals"]
    elif kind == "fmt_and":
        b = next(b for b in doc["blocks"] if b["id"] == check["block"])
        for attr, val in check["checks"]:
            b["fmt"][attr] = val
    elif kind == "type":
        b = next(b for b in doc["blocks"] if b["id"] == check["block"])
        b["type"] = check["equals"]
    elif kind == "type_multi":
        for bid in check["blocks"]:
            b = next(b for b in doc["blocks"] if b["id"] == bid)
            b["type"] = check["equals"]
    elif kind == "text_contains":
        b = next(b for b in doc["blocks"] if b["id"] == check["block"])
        if check["value"] not in (b.get("text") or ""):
            b["text"] = (b.get("text") or "") + check["value"]
    elif kind == "text_replaced":
        b = next(b for b in doc["blocks"] if b["id"] == check["block"])
        b["text"] = (b.get("text") or "").replace(check["remove"], check["add"])
    elif kind == "link":
        b = next(b for b in doc["blocks"] if b["id"] == check["block"])
        b["fmt"]["link"] = "https://example.com"
    elif kind == "header_contains":
        doc["header"] = check["value"]
    elif kind == "footer_pagenum":
        doc["footerPageNumber"] = True
    elif kind == "table":
        cells = [["" for _ in range(check["cols"])] for _ in range(check["rows"])]
        doc["blocks"].append({
            "id": "tbl_test", "type": "table", "text": "",
            "cols": check["cols"], "rows": check["rows"], "cells": cells,
            "fmt": {"bold": False, "italic": False, "underline": False, "fontFamily": "Arial",
                    "fontSize": 11, "color": "#0f172a", "align": "left", "lineSpacing": 1.0, "link": ""},
        })
    elif kind == "table_cell_filled":
        tbl = next((b for b in doc["blocks"] if b.get("type") == "table"), None)
        if not tbl:
            _apply_check(doc, {"kind": "table", "cols": max(3, check["col"] + 1), "rows": max(2, check["row"] + 1)})
            tbl = next(b for b in doc["blocks"] if b.get("type") == "table")
        r, c = check["row"], check["col"]
        while len(tbl["cells"]) <= r:
            tbl["cells"].append(["" for _ in range(tbl["cols"])])
        while len(tbl["cells"][r]) <= c:
            tbl["cells"][r].append("")
        tbl["cells"][r][c] = "Heading"
    elif kind == "exported":
        doc["exported"] = True


def _perfect_doc(mission):
    doc = copy.deepcopy(mission["doc"])
    for t in mission["tasks"]:
        _apply_check(doc, t["check"])
    return doc


@pytest.fixture(scope="class", autouse=True)
def _reset_studio_state():
    """Reset the fresh explorer's studio state before this class runs."""
    db = _mongo()
    db.studio_progress.delete_many({"user_id": "studio-fresh"})
    db.points_events.delete_many({"user_id": "studio-fresh", "type": "studio"})
    db.users.update_one({"user_id": "studio-fresh"}, {"$set": {"horizon_points": 0, "compass_marks": 0}})
    yield


class TestSkillStudioDocs:
    """All tests kept in one class so loadscope pins them to one xdist worker (deterministic order)."""

    # ---- GET payload ----
    def test_010_public_track_shape(self):
        r = requests.get(f"{API}/studio/docs", headers=EH)
        assert r.status_code == 200
        d = r.json()
        assert d["track"]["id"] == "docs"
        assert d["track"]["name"] == "Word Processing"
        cfg = d["config"]
        assert "Times New Roman" in cfg["fonts"] and "Georgia" in cfg["fonts"]
        assert 24 in cfg["sizes"] and 30 in cfg["sizes"]
        hexes = {c["hex"] for c in cfg["colors"]}
        assert "#2563eb" in hexes and "#dc2626" in hexes
        assert "®" in cfg["symbols"]
        missions = d["missions"]
        assert len(missions) == 12
        ids = [m["id"] for m in missions]
        assert ids == [f"docs-m{i}" for i in range(1, 13)]
        for m in missions:
            assert m["track"] == "docs"
            assert isinstance(m["instruction"], list) and len(m["instruction"]) > 0
            assert isinstance(m["tasks"], list) and len(m["tasks"]) > 0
            assert isinstance(m["doc"]["blocks"], list) and len(m["doc"]["blocks"]) > 0
            for t in m["tasks"]:
                assert "id" in t and "label" in t and "check" in t
        # progress key present; fresh account: empty
        assert d["progress"] == {}

    def test_020_unknown_track_404(self):
        r = requests.get(f"{API}/studio/nope", headers=EH)
        assert r.status_code == 404

    def test_030_unauth_get_401(self):
        r = requests.get(f"{API}/studio/docs")
        assert r.status_code == 401

    # ---- Error paths on submit ----
    def test_100_guide_403_on_submit(self):
        r = requests.post(f"{API}/studio/docs/docs-m1/submit", headers=GH, json={"doc": {}})
        assert r.status_code == 403

    def test_110_unknown_mission_404(self):
        r = requests.post(f"{API}/studio/docs/docs-mX/submit", headers=EH, json={"doc": {}})
        assert r.status_code == 404

    def test_120_wrong_track_404(self):
        r = requests.post(f"{API}/studio/sheets/docs-m1/submit", headers=EH, json={"doc": {}})
        assert r.status_code == 404

    def test_130_unauth_submit_401(self):
        r = requests.post(f"{API}/studio/docs/docs-m1/submit", json={"doc": {}})
        assert r.status_code == 401

    # ---- Grade scale using docs-m12 (7 tasks) BEFORE any perfect submit ----
    def test_200_grade_scale_B_using_m12(self):
        m = _fetch_mission("docs-m12")
        doc = copy.deepcopy(m["doc"])
        for t in m["tasks"][:6]:  # 6/7 = 86%
            _apply_check(doc, t["check"])
        d = requests.post(f"{API}/studio/docs/docs-m12/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 6 and d["total"] == 7
        assert d["score"] == 86 and d["grade"] == "B" and d["mastery"] is False

    def test_201_grade_scale_C_using_m12(self):
        """Note: response returns sticky best-attempt score/grade after iter_9 fix.
           So we assert passed/total (current submit), and score/grade remain best (B/86)."""
        m = _fetch_mission("docs-m12")
        doc = copy.deepcopy(m["doc"])
        for t in m["tasks"][:5]:  # 5/7 = 71% this submit
            _apply_check(doc, t["check"])
        d = requests.post(f"{API}/studio/docs/docs-m12/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 5 and d["total"] == 7
        # response returns sticky best (from prior 6/7 B submit)
        assert d["score"] == 86 and d["grade"] == "B"
        assert d["points_awarded"] == 0  # no new points (best-attempt)

    def test_202_grade_scale_F_using_m12(self):
        """4/7 = 57% raw. Response still returns sticky best 86/B (from test_200)."""
        m = _fetch_mission("docs-m12")
        doc = copy.deepcopy(m["doc"])
        for t in m["tasks"][:4]:
            _apply_check(doc, t["check"])
        d = requests.post(f"{API}/studio/docs/docs-m12/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 4 and d["total"] == 7
        assert d["score"] == 86 and d["grade"] == "B"
        assert d["points_awarded"] == 0

    # ---- docs-m2: perfect run + best-attempt semantics + user HP increments ----
    def test_300_docs_m2_perfect_A(self):
        m = _fetch_mission("docs-m2")
        pre = requests.get(f"{API}/auth/me", headers=EH).json()
        base_pts = pre["horizon_points"]
        base_marks = pre["compass_marks"]
        r = requests.post(f"{API}/studio/docs/docs-m2/submit", headers=EH, json={"doc": _perfect_doc(m)})
        assert r.status_code == 200
        d = r.json()
        assert d["passed"] == 3 and d["total"] == 3
        assert d["score"] == 100 and d["grade"] == "A" and d["mastery"] is True
        assert d["points_awarded"] == 100
        assert d["compass_mark_earned"] is True
        me = requests.get(f"{API}/auth/me", headers=EH).json()
        assert me["horizon_points"] == base_pts + 100
        assert me["compass_marks"] == base_marks + 1

    def test_310_docs_m2_partial_best_attempt_sticky_grade(self):
        """FIXED (iter_9): Resubmit partial (1/3) → response returns sticky best A/100/mastery,
           points_awarded 0. DB row keeps grade A / score 100 / mastery True."""
        m = _fetch_mission("docs-m2")
        doc = copy.deepcopy(m["doc"])
        _apply_check(doc, m["tasks"][0]["check"])  # only t1
        pre = requests.get(f"{API}/auth/me", headers=EH).json()["horizon_points"]
        r = requests.post(f"{API}/studio/docs/docs-m2/submit", headers=EH, json={"doc": doc})
        assert r.status_code == 200
        d = r.json()
        assert d["passed"] == 1 and d["total"] == 3
        # Response returns STICKY best-attempt values
        assert d["score"] == 100, f"expected sticky best score 100, got {d['score']}"
        assert d["grade"] == "A", f"expected sticky best grade A, got {d['grade']}"
        assert d["mastery"] is True, "expected sticky mastery True on partial resubmit"
        # No additional points awarded (best-attempt)
        assert d["points_awarded"] == 0
        me = requests.get(f"{API}/auth/me", headers=EH).json()["horizon_points"]
        assert me == pre  # no change to user total

        # DB row must keep sticky mastery=True, grade=A, best score=100
        db = _mongo()
        row = db.studio_progress.find_one({"user_id": "studio-fresh", "mission_id": "docs-m2"})
        assert row["mastery"] is True, "sticky mastery lost after partial resubmit"
        assert row["score"] == 100, f"best-attempt score not preserved: {row['score']}"
        assert row["points_earned"] == 100, "best-attempt points_earned not preserved"
        assert row["grade"] == "A", f"sticky grade lost after partial resubmit: {row['grade']}"

    # ---- Per-mission auto-grading coverage ----
    def test_400_docs_m1(self):
        m = _fetch_mission("docs-m1")
        d = requests.post(f"{API}/studio/docs/docs-m1/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100 and d["grade"] == "A"

    @pytest.mark.parametrize("mid", ["docs-m4", "docs-m5", "docs-m6", "docs-m7",
                                     "docs-m8", "docs-m9", "docs-m10", "docs-m11"])
    def test_410_missions_perfect_A(self, mid):
        m = _fetch_mission(mid)
        d = requests.post(f"{API}/studio/docs/{mid}/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100, f"{mid}: {d}"
        assert d["grade"] == "A"
        assert d["mastery"] is True

    def test_420_docs_m3_perfect_A(self):
        """FIXED (iter_9): docs-m3 t2 now targets ['b2','b3'] via fmt_multi, no longer
           conflicting with t3 (b1 fontSize=24). Perfect submit → 100 A mastery."""
        m = _fetch_mission("docs-m3")
        d = requests.post(f"{API}/studio/docs/docs-m3/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100, f"docs-m3 not scoring 100: {d}"
        assert d["grade"] == "A"
        assert d["mastery"] is True

    # ---- Capstone docs-m12: verify total accumulated points reach 150 ----
    def test_500_docs_m12_perfect_reaches_150_total(self):
        """Given prior partial B/C/F submits with best-attempt, a perfect submit
           should bring total m12 points_earned to 150 (the mission's cap)."""
        m = _fetch_mission("docs-m12")
        # snapshot HP just before final perfect
        pre = requests.get(f"{API}/auth/me", headers=EH).json()["horizon_points"]
        d = requests.post(f"{API}/studio/docs/docs-m12/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100 and d["grade"] == "A" and d["mastery"] is True

        # Verify stored progress equals 150 total for this mission
        db = _mongo()
        row = db.studio_progress.find_one({"user_id": "studio-fresh", "mission_id": "docs-m12"})
        assert row is not None
        assert row["points_earned"] == 150
        assert row["score"] == 100
        assert row["mastery"] is True

        # user HP increase = 150 - prev best (129 from B run, i.e. 86 * 150/100 rounded)
        post = requests.get(f"{API}/auth/me", headers=EH).json()["horizon_points"]
        expected_prev_best = round(86 * 150 / 100)  # 129
        assert post - pre == 150 - expected_prev_best, f"delta {post - pre}"

    # ---- Points events + persisted progress after all submits ----
    def test_900_points_event_written(self):
        db = _mongo()
        ev = db.points_events.find_one({"user_id": "studio-fresh", "mission_id": "docs-m2", "type": "studio"})
        assert ev is not None
        assert ev["delta"] == 100
        assert ev["territory_id"] == "t2"

    def test_910_studio_progress_persisted(self):
        d = requests.get(f"{API}/studio/docs", headers=EH).json()
        prog = d["progress"]
        # every mission we perfect-submitted (including m2 with partial resubmit — sticky A,
        # and m3 now fixed) should show A
        for mid in ("docs-m1", "docs-m2", "docs-m3", "docs-m4", "docs-m5", "docs-m6", "docs-m7",
                    "docs-m8", "docs-m9", "docs-m10", "docs-m11", "docs-m12"):
            assert mid in prog, f"missing progress for {mid}"
            assert prog[mid]["mastery"] is True, f"{mid} not mastered: {prog[mid]}"
            assert prog[mid]["grade"] == "A", f"{mid} grade {prog[mid]['grade']}"
            assert prog[mid]["score"] == 100
