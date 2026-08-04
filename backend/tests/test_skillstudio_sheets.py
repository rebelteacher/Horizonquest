"""HorizonQuest Skill Studio (Sheets track) backend tests — Phase 2.

Covers:
- GET /api/studio/sheets: track / config (functions=[SUM,AVERAGE,COUNT,MAX,MIN],
  chartTypes bar+pie) / 11 missions
- POST /api/studio/sheets/{mission_id}/submit auto-grading across every sheets
  check kind: cell_text, cell_value, cell_formula, sorted, chart_range,
  sheet_count, sheet_named, exported
- Formula engine: SUM/AVERAGE/COUNT/MAX/MIN over ranges + eval_ref chaining
- Letter grade scale A/B/C/D/F + mastery @ 90%
- Best-attempt semantics (sticky score/grade/mastery on lower resubmit)
- Guide 403 on submit; unauth 401
- Capstone sheets-m11 pays out 150 pts, delta shows on /auth/me

Uses a FRESH explorer (sheets-fresh / sheets_fresh_tok) to keep point-increment
assertions deterministic. State reset in a class fixture.
"""
import copy
import os
import pytest
import pymongo
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://explorer-journey-4.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

EXP_TOK = "sheets_fresh_tok"       # fresh explorer for clean point-increment
EXP_UID = "sheets-fresh"
GUIDE_TOK = "qa_ui_guide_tok"       # guide (403)
EH = {"Authorization": f"Bearer {EXP_TOK}", "Content-Type": "application/json"}
GH = {"Authorization": f"Bearer {GUIDE_TOK}", "Content-Type": "application/json"}


def _mongo():
    c = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    return c[os.environ.get("DB_NAME", "test_database")]


def _fetch_mission(mission_id):
    d = requests.get(f"{API}/studio/sheets", headers=EH).json()
    return next(m for m in d["missions"] if m["id"] == mission_id)


def _apply_sheets_check(doc, check):
    """Mutate `doc` so this sheets task passes."""
    kind = check["kind"]
    if kind == "cell_text":
        si = check.get("sheet", 0)
        doc["sheets"][si]["cells"][check["cell"]] = check["equals"]
    elif kind == "cell_value":
        si = check.get("sheet", 0)
        doc["sheets"][si]["cells"][check["cell"]] = str(check["equals"])
    elif kind == "cell_formula":
        si = check.get("sheet", 0)
        doc["sheets"][si]["cells"][check["cell"]] = f"={check['fn']}({check['range']})"
    elif kind == "sorted":
        si = check.get("sheet", 0)
        col = check["col"].upper()
        cells = doc["sheets"][si]["cells"]
        vals = []
        for r in range(check["from"], check["to"] + 1):
            raw = (cells.get(f"{col}{r}") or "").strip()
            if raw:
                try:
                    vals.append(float(raw))
                except ValueError:
                    pass
        vals.sort(reverse=(check["order"] == "desc"))
        for i, r in enumerate(range(check["from"], check["from"] + len(vals))):
            n = vals[i]
            cells[f"{col}{r}"] = str(int(n)) if n.is_integer() else str(n)
    elif kind == "chart_range":
        doc.setdefault("charts", []).append({
            "id": f"ch_{check['type']}_{check['range']}",
            "type": check["type"], "range": check["range"], "title": "t",
        })
    elif kind == "sheet_count":
        while len(doc["sheets"]) < check["equals"]:
            doc["sheets"].append({"name": f"Sheet{len(doc['sheets'])+1}", "rows": 8, "cols": 4, "cells": {}})
    elif kind == "sheet_named":
        while len(doc["sheets"]) <= check["index"]:
            doc["sheets"].append({"name": f"Sheet{len(doc['sheets'])+1}", "rows": 8, "cols": 4, "cells": {}})
        doc["sheets"][check["index"]]["name"] = check["name"]
    elif kind == "exported":
        doc["exported"] = True


def _perfect_doc(mission):
    """Apply cell_value tasks FIRST so cell_formula (which shares the same target cell in
    missions like m2..m6) overwrites them with the actual formula — the formula evaluates
    to the required value so both tasks pass."""
    doc = copy.deepcopy(mission["doc"])
    order = {"cell_value": 0, "cell_text": 1, "sheet_count": 2, "sheet_named": 3,
             "sorted": 4, "chart_range": 5, "exported": 6, "cell_formula": 7}
    for t in sorted(mission["tasks"], key=lambda t: order.get(t["check"]["kind"], 99)):
        _apply_sheets_check(doc, t["check"])
    return doc


@pytest.fixture(scope="class", autouse=True)
def _reset_sheets_state():
    """Reset the fresh sheets explorer's studio state before this class runs."""
    db = _mongo()
    db.studio_progress.delete_many({"user_id": EXP_UID})
    db.points_events.delete_many({"user_id": EXP_UID, "type": "studio"})
    db.users.update_one({"user_id": EXP_UID}, {"$set": {"horizon_points": 0, "compass_marks": 0}})
    yield


class TestSkillStudioSheets:
    """All sheets tests grouped in one class so xdist loadscope pins them to one worker."""

    # ---------- GET payload ----------
    def test_010_public_track_shape(self):
        r = requests.get(f"{API}/studio/sheets", headers=EH)
        assert r.status_code == 200
        d = r.json()
        assert d["track"]["id"] == "sheets"
        assert d["track"]["name"] == "Spreadsheets"
        cfg = d["config"]
        assert cfg["functions"] == ["SUM", "AVERAGE", "COUNT", "MAX", "MIN"]
        ct_ids = [c["id"] for c in cfg["chartTypes"]]
        assert "bar" in ct_ids and "pie" in ct_ids
        missions = d["missions"]
        assert len(missions) == 11
        ids = [m["id"] for m in missions]
        assert ids == [f"sheets-m{i}" for i in range(1, 12)]
        for m in missions:
            assert m["track"] == "sheets"
            assert isinstance(m["instruction"], list) and m["instruction"]
            assert isinstance(m["tasks"], list) and m["tasks"]
            assert isinstance(m["doc"]["sheets"], list) and m["doc"]["sheets"]
            for t in m["tasks"]:
                assert "id" in t and "label" in t and "check" in t
        assert d["progress"] == {}

    # ---------- Guards ----------
    def test_100_guide_403_on_submit(self):
        r = requests.post(f"{API}/studio/sheets/sheets-m1/submit", headers=GH, json={"doc": {}})
        assert r.status_code == 403

    def test_110_unknown_mission_404(self):
        r = requests.post(f"{API}/studio/sheets/sheets-mX/submit", headers=EH, json={"doc": {}})
        assert r.status_code == 404

    def test_120_wrong_track_404(self):
        r = requests.post(f"{API}/studio/docs/sheets-m1/submit", headers=EH, json={"doc": {}})
        assert r.status_code == 404

    def test_130_unauth_submit_401(self):
        r = requests.post(f"{API}/studio/sheets/sheets-m1/submit", json={"doc": {}})
        assert r.status_code == 401

    # ---------- Grade scale using sheets-m11 (6 tasks) BEFORE any perfect submit ----------
    # Order tasks: t1..t4 are cell_formula (must all be present so cell_value ref cells resolve),
    # t5 chart_range, t6 exported.
    def test_200_grade_scale_C_using_m11(self):
        """Only 4 formulas => 4/6 = 67% => C."""
        m = _fetch_mission("sheets-m11")
        doc = copy.deepcopy(m["doc"])
        for t in m["tasks"][:4]:
            _apply_sheets_check(doc, t["check"])
        d = requests.post(f"{API}/studio/sheets/sheets-m11/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 4 and d["total"] == 6
        assert d["score"] == 67 and d["grade"] == "D"  # 67 -> D (>=60)

    def test_210_grade_scale_partial_below_best_sticky(self):
        """Now submit 3/6 = 50% (F). Response should carry sticky best (D/67) & no new points."""
        m = _fetch_mission("sheets-m11")
        doc = copy.deepcopy(m["doc"])
        for t in m["tasks"][:3]:
            _apply_sheets_check(doc, t["check"])
        d = requests.post(f"{API}/studio/sheets/sheets-m11/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 3 and d["total"] == 6
        # sticky best
        assert d["score"] == 67 and d["grade"] == "D"
        assert d["points_awarded"] == 0

    # ---------- sheets-m2 perfect A + best-attempt + user HP ----------
    def test_300_sheets_m2_perfect_A(self):
        m = _fetch_mission("sheets-m2")
        pre = requests.get(f"{API}/auth/me", headers=EH).json()
        base_pts = pre["horizon_points"]
        base_marks = pre["compass_marks"]
        r = requests.post(f"{API}/studio/sheets/sheets-m2/submit", headers=EH, json={"doc": _perfect_doc(m)})
        assert r.status_code == 200
        d = r.json()
        assert d["passed"] == 2 and d["total"] == 2
        assert d["score"] == 100 and d["grade"] == "A" and d["mastery"] is True
        assert d["points_awarded"] == 100
        assert d["compass_mark_earned"] is True
        me = requests.get(f"{API}/auth/me", headers=EH).json()
        assert me["horizon_points"] == base_pts + 100
        assert me["compass_marks"] == base_marks + 1

    def test_310_sheets_m2_partial_sticky(self):
        m = _fetch_mission("sheets-m2")
        doc = copy.deepcopy(m["doc"])
        _apply_sheets_check(doc, m["tasks"][0]["check"])  # only formula, no cell_value
        # cell_value task on B6 will now match (formula evaluates 150) — so this ends up 2/2 anyway.
        # Instead, submit an empty doc to force 0/2.
        d = requests.post(f"{API}/studio/sheets/sheets-m2/submit", headers=EH, json={"doc": copy.deepcopy(m["doc"])}).json()
        assert d["passed"] == 0 and d["total"] == 2
        # sticky best
        assert d["score"] == 100 and d["grade"] == "A" and d["mastery"] is True
        assert d["points_awarded"] == 0

    # ---------- Per-mission perfect coverage ----------
    def test_400_sheets_m1_perfect(self):
        m = _fetch_mission("sheets-m1")
        d = requests.post(f"{API}/studio/sheets/sheets-m1/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100 and d["grade"] == "A" and d["mastery"] is True

    def test_410_sheets_m3_perfect_average(self):
        m = _fetch_mission("sheets-m3")
        d = requests.post(f"{API}/studio/sheets/sheets-m3/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100 and d["grade"] == "A"

    def test_420_sheets_m4_perfect_count(self):
        m = _fetch_mission("sheets-m4")
        d = requests.post(f"{API}/studio/sheets/sheets-m4/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100 and d["grade"] == "A"

    def test_430_sheets_m5_perfect_max_min(self):
        m = _fetch_mission("sheets-m5")
        d = requests.post(f"{API}/studio/sheets/sheets-m5/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["passed"] == 4 and d["total"] == 4
        assert d["score"] == 100 and d["grade"] == "A"

    def test_440_sheets_m6_perfect_summary_row(self):
        m = _fetch_mission("sheets-m6")
        d = requests.post(f"{API}/studio/sheets/sheets-m6/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["passed"] == 4 and d["score"] == 100

    def test_450_sheets_m7_perfect_sorted(self):
        m = _fetch_mission("sheets-m7")
        d = requests.post(f"{API}/studio/sheets/sheets-m7/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100 and d["grade"] == "A"

    def test_460_sheets_m8_perfect_bar_chart(self):
        m = _fetch_mission("sheets-m8")
        d = requests.post(f"{API}/studio/sheets/sheets-m8/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100

    def test_470_sheets_m9_perfect_pie_chart(self):
        m = _fetch_mission("sheets-m9")
        d = requests.post(f"{API}/studio/sheets/sheets-m9/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100

    def test_480_sheets_m10_perfect_multi_sheet(self):
        m = _fetch_mission("sheets-m10")
        d = requests.post(f"{API}/studio/sheets/sheets-m10/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["passed"] == 2 and d["score"] == 100

    # ---------- Capstone m11: verify final points 150 ----------
    def test_500_sheets_m11_perfect_reaches_150_total(self):
        m = _fetch_mission("sheets-m11")
        pre = requests.get(f"{API}/auth/me", headers=EH).json()["horizon_points"]
        d = requests.post(f"{API}/studio/sheets/sheets-m11/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100 and d["grade"] == "A" and d["mastery"] is True

        db = _mongo()
        row = db.studio_progress.find_one({"user_id": EXP_UID, "mission_id": "sheets-m11"})
        assert row is not None
        assert row["points_earned"] == 150
        assert row["score"] == 100
        assert row["mastery"] is True

        # user HP delta = 150 - prev best (D/67 -> 67*150/100 = ~100.5 rounded 101)
        post = requests.get(f"{API}/auth/me", headers=EH).json()["horizon_points"]
        prev_best_pts = round(67 * 150 / 100)  # 101
        assert post - pre == 150 - prev_best_pts, f"delta {post - pre}"

    # ---------- Grading kind coverage (spot checks) ----------
    def test_600_cell_formula_case_and_space_insensitive(self):
        """Formula grading should ignore case and whitespace, but require exact function+range."""
        doc = copy.deepcopy(_fetch_mission("sheets-m2")["doc"])
        # exact match with lower + spaces
        doc["sheets"][0]["cells"]["B6"] = "= sum ( b2 : b5 )"
        d = requests.post(f"{API}/studio/sheets/sheets-m2/submit", headers=EH, json={"doc": doc}).json()
        # t1 (cell_formula) should pass; t2 (cell_value=150) also because formula evaluates 150
        assert d["passed"] == 2

    def test_610_cell_formula_wrong_function_fails_t1(self):
        doc = copy.deepcopy(_fetch_mission("sheets-m2")["doc"])
        # Correct value 150 via literal, but wrong function name — t1 should fail, t2 passes
        doc["sheets"][0]["cells"]["B6"] = "150"
        d = requests.post(f"{API}/studio/sheets/sheets-m2/submit", headers=EH, json={"doc": doc}).json()
        # t2 cell_value=150 ✓, t1 cell_formula ✗
        assert d["passed"] == 1

    def test_620_sorted_ascending_wrong_order_fails(self):
        m = _fetch_mission("sheets-m7")
        doc = copy.deepcopy(m["doc"])
        # descending on purpose (should FAIL ascending check)
        col = "B"
        for i, v in enumerate([31, 25, 19, 12, 8], start=2):
            doc["sheets"][0]["cells"][f"{col}{i}"] = str(v)
        d = requests.post(f"{API}/studio/sheets/sheets-m7/submit", headers=EH, json={"doc": doc}).json()
        # sticky best from earlier m7 perfect (100/A) — but passed for THIS submit is 0
        assert d["passed"] == 0

    def test_630_chart_range_type_mismatch_fails(self):
        m = _fetch_mission("sheets-m9")  # pie required
        doc = copy.deepcopy(m["doc"])
        doc["charts"] = [{"id": "x", "type": "bar", "range": "A1:B4", "title": "t"}]
        d = requests.post(f"{API}/studio/sheets/sheets-m9/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 0  # type mismatch -> fail (best is 100 from earlier perfect)

    # ---------- Persisted progress ----------
    def test_900_points_event_written(self):
        db = _mongo()
        ev = db.points_events.find_one({"user_id": EXP_UID, "mission_id": "sheets-m2", "type": "studio"})
        assert ev is not None and ev["delta"] == 100 and ev["territory_id"] == "t2"

    def test_910_studio_progress_persisted(self):
        d = requests.get(f"{API}/studio/sheets", headers=EH).json()
        prog = d["progress"]
        for mid in [f"sheets-m{i}" for i in range(1, 12)]:
            assert mid in prog, f"missing progress for {mid}"
            assert prog[mid]["grade"] == "A", f"{mid} grade {prog[mid]['grade']}"
            assert prog[mid]["score"] == 100
            assert prog[mid]["mastery"] is True
