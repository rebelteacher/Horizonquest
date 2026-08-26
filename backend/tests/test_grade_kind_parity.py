"""Guard test: every deterministic grading `kind` used in the backend curriculum
must also be implemented in the frontend live-checker (studioGrade.js). This class
of bug ("Your Tasks stuck at 0/N because the client can't evaluate the kind") has
recurred, so we fail fast if the two ever drift apart.

'ai' is intentionally excluded — it is graded server-side on submit only.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend" / "skillstudio.py"
FRONTEND = ROOT / "frontend" / "src" / "lib" / "studioGrade.js"

SERVER_ONLY = {"ai"}


def _backend_kinds():
    src = BACKEND.read_text()
    return set(re.findall(r'"kind":\s*"([a-z_]+)"', src))


def _frontend_kinds():
    src = FRONTEND.read_text()
    kinds = set(re.findall(r'k === "([a-z_]+)"', src))
    for grp in re.findall(r'\[([^\]]*)\]\.includes\(k\)', src):
        kinds |= set(re.findall(r'"([a-z_]+)"', grp))
    return kinds


def test_frontend_mirror_covers_all_backend_kinds():
    missing = _backend_kinds() - _frontend_kinds() - SERVER_ONLY
    assert not missing, (
        f"studioGrade.js is missing check kinds: {sorted(missing)}. "
        "Add them to frontend/src/lib/studioGrade.js (mirror skillstudio._check_one) "
        "or the 'Your Tasks' checklist will never tick for those tasks."
    )
