"""HorizonQuest Skill Studio (Slides track) backend tests — Phase 3.

Covers:
- GET /api/studio/slides: track / config (layouts x4, themes x4, gallery x6,
  animations x4, transitions x4, chartTypes bar+pie) / 12 missions.
- POST /api/studio/slides/{mission_id}/submit auto-grading across every slides
  check kind: slide_count, slide_title_nonempty, slide_bullets_min,
  five_by_five (positive + fail paths for >5 bullets and >5 words),
  slide_layout, slide_theme, slide_has_image, slide_has_chart, slide_animation,
  slide_transition, slide_notes_min_words, exported.
- Best-attempt semantics (sticky score/grade/mastery).
- Letter-grade scale (A/B/C/D/F) using capstone slides-m12 partial submits.
- Guide 403; unknown mission 404; wrong-track 404; unauth 401.
- Capstone slides-m12 pays 150 pts + compass mark; delta shows on /auth/me.

Uses a FRESH explorer (slides-fresh / slides_fresh_tok) so point-increment and
best-attempt fail-path assertions are deterministic.
"""
import copy
import os
import pytest
import pymongo
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://explorer-journey-4.preview.emergentagent.com",
).rstrip("/")
API = f"{BASE_URL}/api"

EXP_TOK = "slides_fresh_tok"
EXP_UID = "slides-fresh"
GUIDE_TOK = "qa_ui_guide_tok"
EH = {"Authorization": f"Bearer {EXP_TOK}", "Content-Type": "application/json"}
GH = {"Authorization": f"Bearer {GUIDE_TOK}", "Content-Type": "application/json"}


def _mongo():
    c = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    return c[os.environ.get("DB_NAME", "test_database")]


def _fetch_mission(mission_id):
    d = requests.get(f"{API}/studio/slides", headers=EH).json()
    return next(m for m in d["missions"] if m["id"] == mission_id)


def _ensure_slide(doc, idx):
    while len(doc["slides"]) <= idx:
        doc["slides"].append({
            "id": f"s{len(doc['slides'])}", "layout": "title-content",
            "theme": "midnight", "title": "", "bullets": [],
            "image": None, "chart": None, "animation": "none",
            "transition": "none", "notes": "",
        })


def _apply_slides_check(doc, check):
    """Mutate `doc` so this slides task passes."""
    kind = check["kind"]
    if kind == "slide_count":
        while len(doc["slides"]) < check["equals"]:
            _ensure_slide(doc, len(doc["slides"]))
        # Ensure we don't have extra
        doc["slides"] = doc["slides"][: check["equals"]]
        return
    if kind == "exported":
        doc["exported"] = True
        return
    si = check.get("slide", 0)
    _ensure_slide(doc, si)
    sl = doc["slides"][si]
    if kind == "slide_title_nonempty":
        if not (sl.get("title") or "").strip():
            sl["title"] = sl.get("title") or f"Slide {si + 1}"
    elif kind == "slide_title_contains":
        base = sl.get("title") or ""
        if check["value"].lower() not in base.lower():
            sl["title"] = (base + " " + check["value"]).strip()
    elif kind == "slide_bullets_min":
        bl = [b for b in (sl.get("bullets") or []) if (b or "").strip()]
        while len(bl) < check["min"]:
            bl.append(f"Point {len(bl) + 1}")
        sl["bullets"] = bl
    elif kind == "five_by_five":
        # 1..5 bullets, each <=5 words
        sl["bullets"] = ["Reduce landfill waste", "Save trees water minerals",
                         "Uses less energy overall", "Cuts pollution in air",
                         "Creates green community jobs"]
    elif kind == "slide_layout":
        sl["layout"] = check["equals"]
    elif kind == "slide_theme":
        sl["theme"] = check["equals"]
    elif kind == "slide_has_image":
        sl["image"] = {"id": "planets", "label": "Planets", "url": "https://example.com/x.jpg"}
    elif kind == "slide_has_chart":
        sl["chart"] = {"type": check.get("type", "bar")}
    elif kind == "slide_animation":
        sl["animation"] = "fade"
    elif kind == "slide_transition":
        sl["transition"] = "fade"
    elif kind == "slide_notes_min_words":
        sl["notes"] = " ".join([f"word{i}" for i in range(check["min"])])


def _perfect_doc(mission):
    """Build a doc that passes every task. slide_count first so later slide indexes exist."""
    doc = copy.deepcopy(mission["doc"])
    order = {"slide_count": 0}
    tasks = sorted(mission["tasks"], key=lambda t: order.get(t["check"]["kind"], 10))
    for t in tasks:
        _apply_slides_check(doc, t["check"])
    return doc


@pytest.fixture(scope="class", autouse=True)
def _reset_slides_state():
    db = _mongo()
    db.studio_progress.delete_many({"user_id": EXP_UID})
    db.points_events.delete_many({"user_id": EXP_UID, "type": "studio"})
    db.users.update_one(
        {"user_id": EXP_UID},
        {"$set": {"horizon_points": 0, "compass_marks": 0}},
    )
    yield


class TestSkillStudioSlides:
    """All slides tests grouped in one class so xdist loadscope pins them to one worker."""

    # ---------- GET payload ----------
    def test_010_public_track_shape(self):
        r = requests.get(f"{API}/studio/slides", headers=EH)
        assert r.status_code == 200
        d = r.json()
        assert d["track"]["id"] == "slides"
        assert d["track"]["name"] == "Presentations"
        cfg = d["config"]
        assert len(cfg["layouts"]) == 4
        layout_ids = [l["id"] for l in cfg["layouts"]]
        assert set(layout_ids) == {"title", "title-content", "two-content", "blank"}
        assert len(cfg["themes"]) == 4
        theme_ids = [t["id"] for t in cfg["themes"]]
        assert set(theme_ids) == {"midnight", "sunrise", "ocean", "paper"}
        assert len(cfg["gallery"]) == 6
        assert len(cfg["animations"]) == 4
        assert len(cfg["transitions"]) == 4
        ct_ids = [c["id"] for c in cfg["chartTypes"]]
        assert "bar" in ct_ids and "pie" in ct_ids
        missions = d["missions"]
        assert len(missions) == 12
        ids = [m["id"] for m in missions]
        assert ids == [f"slides-m{i}" for i in range(1, 13)]
        for m in missions:
            assert m["track"] == "slides"
            assert isinstance(m["instruction"], list) and m["instruction"]
            assert isinstance(m["tasks"], list) and m["tasks"]
            assert isinstance(m["doc"]["slides"], list) and m["doc"]["slides"]
            for t in m["tasks"]:
                assert "id" in t and "label" in t and "check" in t
        assert d["progress"] == {}

    # ---------- Guards ----------
    def test_100_guide_403_on_submit(self):
        r = requests.post(f"{API}/studio/slides/slides-m1/submit", headers=GH, json={"doc": {}})
        assert r.status_code == 403

    def test_110_unknown_mission_404(self):
        r = requests.post(f"{API}/studio/slides/slides-mX/submit", headers=EH, json={"doc": {}})
        assert r.status_code == 404

    def test_120_wrong_track_404(self):
        r = requests.post(f"{API}/studio/docs/slides-m1/submit", headers=EH, json={"doc": {}})
        assert r.status_code == 404

    def test_130_unauth_submit_401(self):
        r = requests.post(f"{API}/studio/slides/slides-m1/submit", json={"doc": {}})
        assert r.status_code == 401

    # ---------- Grade scale using capstone slides-m12 (10 tasks) BEFORE any perfect submit ----------
    def test_200_grade_scale_D_using_m12(self):
        """6/10 = 60% => D."""
        m = _fetch_mission("slides-m12")
        doc = copy.deepcopy(m["doc"])
        for t in m["tasks"][:6]:
            _apply_slides_check(doc, t["check"])
        d = requests.post(f"{API}/studio/slides/slides-m12/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 6 and d["total"] == 10
        assert d["score"] == 60 and d["grade"] == "D"
        assert d["mastery"] is False

    def test_210_grade_scale_lower_sticky_best(self):
        """3/10 = 30% (F). Response should carry sticky best (D/60), no new points."""
        m = _fetch_mission("slides-m12")
        doc = copy.deepcopy(m["doc"])
        for t in m["tasks"][:3]:
            _apply_slides_check(doc, t["check"])
        d = requests.post(f"{API}/studio/slides/slides-m12/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 3 and d["total"] == 10
        # sticky
        assert d["score"] == 60 and d["grade"] == "D"
        assert d["points_awarded"] == 0

    # ---------- Five-by-five fail paths (m4 - fresh explorer keeps best sticky, but current-submit passed must reflect fail) ----------
    def test_300_m4_starter_fails_five_by_five(self):
        """Starter has 6 long bullets — five_by_five should fail (0/1)."""
        m = _fetch_mission("slides-m4")
        d = requests.post(f"{API}/studio/slides/slides-m4/submit", headers=EH, json={"doc": copy.deepcopy(m["doc"])}).json()
        assert d["passed"] == 0 and d["total"] == 1
        # first submit for m4 so best == current
        assert d["score"] == 0 and d["grade"] == "F"

    def test_310_m4_more_than_five_bullets_fails(self):
        """6 bullets, each <=5 words -> still fails (>5 bullets)."""
        m = _fetch_mission("slides-m4")
        doc = copy.deepcopy(m["doc"])
        doc["slides"][0]["bullets"] = ["one two", "three four", "five six", "seven eight", "nine ten", "eleven twelve"]
        d = requests.post(f"{API}/studio/slides/slides-m4/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 0

    def test_320_m4_one_bullet_over_five_words_fails(self):
        """5 bullets but one has 6 words -> fails."""
        m = _fetch_mission("slides-m4")
        doc = copy.deepcopy(m["doc"])
        doc["slides"][0]["bullets"] = ["short one", "short two", "short three",
                                       "this bullet has exactly six words", "short five"]
        d = requests.post(f"{API}/studio/slides/slides-m4/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 0

    def test_330_m4_valid_five_by_five_passes(self):
        m = _fetch_mission("slides-m4")
        doc = copy.deepcopy(m["doc"])
        doc["slides"][0]["bullets"] = ["Save resources every day", "Recycle in the community",
                                       "Less waste in landfills", "Trees water minerals saved",
                                       "Reduce pollution overall"]
        d = requests.post(f"{API}/studio/slides/slides-m4/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 1 and d["total"] == 1
        assert d["score"] == 100 and d["grade"] == "A" and d["mastery"] is True
        assert d["points_awarded"] == 100

    def test_340_m4_empty_bullets_fails_five_by_five(self):
        """0 bullets -> fails (need >=1)."""
        m = _fetch_mission("slides-m4")
        doc = copy.deepcopy(m["doc"])
        doc["slides"][0]["bullets"] = []
        d = requests.post(f"{API}/studio/slides/slides-m4/submit", headers=EH, json={"doc": doc}).json()
        # current submit fails, but sticky best from prior perfect stays 100/A
        assert d["passed"] == 0
        assert d["score"] == 100 and d["grade"] == "A"
        assert d["points_awarded"] == 0

    # ---------- Per-mission perfect coverage ----------
    def test_400_m1_perfect_title_and_subtitle(self):
        m = _fetch_mission("slides-m1")
        d = requests.post(f"{API}/studio/slides/slides-m1/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100 and d["grade"] == "A" and d["mastery"] is True

    def test_410_m2_perfect_three_slides(self):
        m = _fetch_mission("slides-m2")
        d = requests.post(f"{API}/studio/slides/slides-m2/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["passed"] == 4 and d["total"] == 4
        assert d["score"] == 100 and d["grade"] == "A"

    def test_420_m3_perfect_bullets_min(self):
        m = _fetch_mission("slides-m3")
        d = requests.post(f"{API}/studio/slides/slides-m3/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100 and d["grade"] == "A"

    def test_430_m5_perfect_layouts(self):
        m = _fetch_mission("slides-m5")
        d = requests.post(f"{API}/studio/slides/slides-m5/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["passed"] == 3 and d["score"] == 100 and d["grade"] == "A"

    def test_440_m6_perfect_theme(self):
        m = _fetch_mission("slides-m6")
        d = requests.post(f"{API}/studio/slides/slides-m6/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100 and d["grade"] == "A"

    def test_450_m7_perfect_image(self):
        m = _fetch_mission("slides-m7")
        d = requests.post(f"{API}/studio/slides/slides-m7/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100

    def test_460_m8_perfect_chart(self):
        m = _fetch_mission("slides-m8")
        d = requests.post(f"{API}/studio/slides/slides-m8/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100

    def test_470_m9_perfect_animation(self):
        m = _fetch_mission("slides-m9")
        d = requests.post(f"{API}/studio/slides/slides-m9/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100

    def test_480_m10_perfect_transition(self):
        m = _fetch_mission("slides-m10")
        d = requests.post(f"{API}/studio/slides/slides-m10/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100

    def test_490_m11_perfect_notes(self):
        m = _fetch_mission("slides-m11")
        d = requests.post(f"{API}/studio/slides/slides-m11/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["score"] == 100

    def test_495_m11_notes_below_min_fails(self):
        """Notes with 7 words -> fails min 8."""
        m = _fetch_mission("slides-m11")
        doc = copy.deepcopy(m["doc"])
        doc["slides"][0]["notes"] = "one two three four five six seven"
        d = requests.post(f"{API}/studio/slides/slides-m11/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 0

    # ---------- Kind coverage spot checks ----------
    def test_600_slide_theme_wrong_value_fails(self):
        m = _fetch_mission("slides-m6")
        doc = copy.deepcopy(m["doc"])
        doc["slides"][0]["theme"] = "sunrise"  # required 'ocean'
        d = requests.post(f"{API}/studio/slides/slides-m6/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 0

    def test_610_slide_has_chart_type_mismatch_fails(self):
        m = _fetch_mission("slides-m8")  # requires bar
        doc = copy.deepcopy(m["doc"])
        doc["slides"][0]["chart"] = {"type": "pie"}
        d = requests.post(f"{API}/studio/slides/slides-m8/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 0

    def test_620_animation_none_fails(self):
        m = _fetch_mission("slides-m9")
        doc = copy.deepcopy(m["doc"])
        doc["slides"][0]["animation"] = "none"
        d = requests.post(f"{API}/studio/slides/slides-m9/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 0

    def test_630_transition_none_fails(self):
        m = _fetch_mission("slides-m10")
        doc = copy.deepcopy(m["doc"])
        doc["slides"][0]["transition"] = "none"
        d = requests.post(f"{API}/studio/slides/slides-m10/submit", headers=EH, json={"doc": doc}).json()
        assert d["passed"] == 0

    def test_640_slide_count_wrong_fails(self):
        m = _fetch_mission("slides-m2")
        doc = copy.deepcopy(m["doc"])
        # single slide, not 3 -> slide_count fails plus slides 2/3 title checks fail
        d = requests.post(f"{API}/studio/slides/slides-m2/submit", headers=EH, json={"doc": doc}).json()
        # only slide 1 could have title if we don't set it — starter has empty title -> 0
        assert d["passed"] <= 1

    # ---------- Capstone slides-m12 perfect ----------
    def test_700_m12_perfect_reaches_150_total(self):
        m = _fetch_mission("slides-m12")
        pre = requests.get(f"{API}/auth/me", headers=EH).json()["horizon_points"]
        d = requests.post(f"{API}/studio/slides/slides-m12/submit", headers=EH, json={"doc": _perfect_doc(m)}).json()
        assert d["passed"] == 10 and d["total"] == 10
        assert d["score"] == 100 and d["grade"] == "A" and d["mastery"] is True
        # points_awarded is the DELTA vs previously earned points (best-attempt sticky).
        # Prior best on m12 was D (60% -> 90 pts). Perfect: 150 - 90 = 60 delta.
        prev_best_pts = round(60 * 150 / 100)  # 90
        assert d["points_awarded"] == 150 - prev_best_pts  # 60
        assert d["compass_mark_earned"] is True

        db = _mongo()
        row = db.studio_progress.find_one({"user_id": EXP_UID, "mission_id": "slides-m12"})
        assert row is not None
        assert row["points_earned"] == 150
        assert row["score"] == 100
        assert row["mastery"] is True

        # HP delta = 150 - prev best pts (D/60 => 60% of 150 = 90)
        post = requests.get(f"{API}/auth/me", headers=EH).json()["horizon_points"]
        assert post - pre == 150 - prev_best_pts, f"delta {post - pre}"

    # ---------- Persisted progress ----------
    def test_900_points_event_written_for_m4(self):
        db = _mongo()
        ev = db.points_events.find_one({"user_id": EXP_UID, "mission_id": "slides-m4", "type": "studio"})
        assert ev is not None and ev["delta"] == 100 and ev["territory_id"] == "t2"

    def test_910_studio_progress_persisted(self):
        d = requests.get(f"{API}/studio/slides", headers=EH).json()
        prog = d["progress"]
        for mid in [f"slides-m{i}" for i in range(1, 13)]:
            assert mid in prog, f"missing progress for {mid}"
            assert prog[mid]["grade"] == "A", f"{mid} grade {prog[mid]['grade']}"
            assert prog[mid]["score"] == 100
            assert prog[mid]["mastery"] is True
