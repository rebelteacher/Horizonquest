from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
import logging
import string
import random
import re
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
import httpx
from datetime import datetime, timezone, timedelta

import curriculum
import skillstudio
import assessments
import objstore

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
AUTH_SESSION_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"

FLEETS = ["North Star", "Dawn Treaders", "Sea Wolves", "Trade Winds"]


def rank_tier(points):
    if points >= 800:
        return "Conqueror"
    if points >= 300:
        return "Voyager"
    return "Navigator"

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ---------------- Helpers ----------------
def now_utc():
    return datetime.now(timezone.utc)


def gen_join_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


async def get_current_user(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now_utc():
        raise HTTPException(status_code=401, detail="Session expired")

    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def require_guide(user=Depends(get_current_user)):
    if user.get("role") != "guide":
        raise HTTPException(status_code=403, detail="Guides only")
    return user


async def require_explorer(user=Depends(get_current_user)):
    if user.get("role") != "explorer":
        raise HTTPException(status_code=403, detail="Explorers only")
    return user


# ---------------- Models ----------------
class RoleUpdate(BaseModel):
    role: str


class ExpeditionCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class ExpeditionRename(BaseModel):
    name: str
    description: Optional[str] = None


class AdminRoleUpdate(BaseModel):
    role: str


class JoinRequest(BaseModel):
    join_code: str


class TrialSubmit(BaseModel):
    answers: Dict[str, str]
    reflection: Optional[str] = ""


class CopilotRequest(BaseModel):
    message: str
    quest_id: Optional[str] = None
    session_id: Optional[str] = None


# ---------------- Auth ----------------
@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        body = await request.json()
        session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session id")

    sid_dbg = f"len={len(session_id)}" if session_id else "none"
    logger.info(f"[AUTH] /auth/session exchange start · session_id {sid_dbg}")
    async with httpx.AsyncClient(timeout=20.0) as hc:
        r = await hc.get(AUTH_SESSION_URL, headers={"X-Session-ID": session_id})
    if r.status_code != 200:
        logger.error(f"[AUTH] session-data exchange FAILED · status={r.status_code} body={r.text[:300]}")
        raise HTTPException(status_code=401, detail="Invalid session id")
    logger.info(f"[AUTH] session-data exchange OK · status=200")
    data = r.json()

    email = data["email"]
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one({"user_id": user_id}, {"$set": {"name": data.get("name"), "picture": data.get("picture")}})
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user = {
            "user_id": user_id,
            "email": email,
            "name": data.get("name"),
            "picture": data.get("picture"),
            "role": None,
            "horizon_points": 0,
            "compass_marks": 0,
            "fleet": None,
            "expedition_ids": [],
            "created_at": now_utc().isoformat(),
        }
        await db.users.insert_one(user)
        user.pop("_id", None)

    session_token = data.get("session_token") or f"st_{uuid.uuid4().hex}"
    expires_at = now_utc() + timedelta(days=7)
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": now_utc().isoformat(),
    })

    response.set_cookie(
        key="session_token", value=session_token, httponly=True,
        secure=True, samesite="none", path="/", max_age=7 * 24 * 60 * 60,
    )
    return {"user": _public_user(user)}


def _public_user(u):
    return {
        "user_id": u["user_id"],
        "email": u["email"],
        "name": u.get("name"),
        "picture": u.get("picture"),
        "role": u.get("role"),
        "horizon_points": u.get("horizon_points", 0),
        "compass_marks": u.get("compass_marks", 0),
        "fleet": u.get("fleet"),
        "expedition_ids": u.get("expedition_ids", []),
    }


@api_router.get("/auth/me")
async def auth_me(user=Depends(get_current_user)):
    return _public_user(user)


@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_many({"session_token": token})
    response.delete_cookie("session_token", path="/")
    return {"ok": True}


@api_router.post("/auth/role")
async def set_role(payload: RoleUpdate, user=Depends(get_current_user)):
    if payload.role not in ("explorer", "guide"):
        raise HTTPException(status_code=400, detail="Invalid role")
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"role": payload.role}})
    updated = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return _public_user(updated)


# ---------------- Curriculum ----------------
@api_router.get("/curriculum")
async def get_curriculum():
    return curriculum.public_curriculum()


# ---------------- Expeditions (Guide) ----------------
@api_router.post("/expeditions")
async def create_expedition(payload: ExpeditionCreate, guide=Depends(require_guide)):
    for _ in range(10):
        code = gen_join_code()
        if not await db.expeditions.find_one({"join_code": code}):
            break
    exp = {
        "expedition_id": f"exp_{uuid.uuid4().hex[:12]}",
        "name": payload.name,
        "description": payload.description or "",
        "join_code": code,
        "guide_id": guide["user_id"],
        "guide_name": guide.get("name"),
        "leaderboard_visible": True,
        "member_count": 0,
        "created_at": now_utc().isoformat(),
    }
    await db.expeditions.insert_one(exp)
    exp.pop("_id", None)
    return exp


@api_router.get("/expeditions")
async def list_expeditions(guide=Depends(require_guide)):
    exps = await db.expeditions.find({"guide_id": guide["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return exps


@api_router.patch("/expeditions/{expedition_id}")
async def rename_expedition(expedition_id: str, payload: ExpeditionRename, guide=Depends(require_guide)):
    exp = await db.expeditions.find_one({"expedition_id": expedition_id, "guide_id": guide["user_id"]})
    if not exp:
        raise HTTPException(status_code=404, detail="Expedition not found")
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Class name cannot be empty.")
    updates = {"name": name}
    if payload.description is not None:
        updates["description"] = payload.description.strip()
    await db.expeditions.update_one({"expedition_id": expedition_id}, {"$set": updates})
    updated = await db.expeditions.find_one({"expedition_id": expedition_id}, {"_id": 0})
    return updated


# ---------------- Account role admin (Guides/Teachers can fix mis-signups) ----------------
@api_router.get("/admin/users")
async def admin_search_users(q: str, guide=Depends(require_guide)):
    q = (q or "").strip()
    if len(q) < 3:
        raise HTTPException(status_code=400, detail="Enter at least 3 characters of the email or name.")
    rx = {"$regex": re.escape(q), "$options": "i"}
    users = await db.users.find(
        {"$or": [{"email": rx}, {"name": rx}]},
        {"_id": 0, "user_id": 1, "email": 1, "name": 1, "role": 1, "picture": 1},
    ).limit(20).to_list(20)
    return {"users": users}


@api_router.post("/admin/users/{user_id}/role")
async def admin_set_user_role(user_id: str, payload: AdminRoleUpdate, guide=Depends(require_guide)):
    if payload.role not in ("explorer", "guide"):
        raise HTTPException(status_code=400, detail="Invalid role")
    if user_id == guide["user_id"]:
        raise HTTPException(status_code=400, detail="You can't change your own role here.")
    target = await db.users.find_one({"user_id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    await db.users.update_one({"user_id": user_id}, {"$set": {"role": payload.role}})
    updated = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return _public_user(updated)


@api_router.get("/expeditions/{expedition_id}")
async def get_expedition(expedition_id: str, user=Depends(get_current_user)):
    exp = await db.expeditions.find_one({"expedition_id": expedition_id}, {"_id": 0})
    if not exp:
        raise HTTPException(status_code=404, detail="Expedition not found")
    members = await db.users.find({"expedition_ids": expedition_id}, {"_id": 0, "user_id": 1, "email": 1, "name": 1, "picture": 1, "role": 1, "horizon_points": 1, "compass_marks": 1, "fleet": 1, "expedition_ids": 1}).to_list(500)
    return {"expedition": exp, "members": [_public_user(m) for m in members]}


@api_router.patch("/expeditions/{expedition_id}/leaderboard")
async def toggle_leaderboard(expedition_id: str, guide=Depends(require_guide)):
    exp = await db.expeditions.find_one({"expedition_id": expedition_id}, {"_id": 0})
    if not exp or exp["guide_id"] != guide["user_id"]:
        raise HTTPException(status_code=404, detail="Not found")
    new_val = not exp.get("leaderboard_visible", True)
    await db.expeditions.update_one({"expedition_id": expedition_id}, {"$set": {"leaderboard_visible": new_val}})
    return {"leaderboard_visible": new_val}


# ---------------- Join (Explorer) ----------------
@api_router.post("/expeditions/join")
async def join_expedition(payload: JoinRequest, explorer=Depends(require_explorer)):
    code = payload.join_code.strip().upper()
    exp = await db.expeditions.find_one({"join_code": code}, {"_id": 0})
    if not exp:
        raise HTTPException(status_code=404, detail="Invalid join code")
    if exp["expedition_id"] in explorer.get("expedition_ids", []):
        return {"expedition": exp, "already_member": True}

    # assign fleet by round-robin within this expedition
    current = await db.users.count_documents({"expedition_ids": exp["expedition_id"]})
    fleet = explorer.get("fleet") or FLEETS[current % len(FLEETS)]

    await db.users.update_one(
        {"user_id": explorer["user_id"]},
        {"$addToSet": {"expedition_ids": exp["expedition_id"]}, "$set": {"fleet": fleet}},
    )
    await db.expeditions.update_one({"expedition_id": exp["expedition_id"]}, {"$inc": {"member_count": 1}})
    return {"expedition": exp, "fleet": fleet, "already_member": False}


@api_router.get("/me/expeditions")
async def my_expeditions(user=Depends(get_current_user)):
    ids = user.get("expedition_ids", [])
    if not ids:
        return []
    exps = await db.expeditions.find({"expedition_id": {"$in": ids}}, {"_id": 0}).to_list(200)
    return exps


# ---------------- Progress & Trials ----------------
@api_router.get("/me/progress")
async def my_progress(user=Depends(get_current_user)):
    rows = await db.progress.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(1000)
    return {
        "progress": rows,
        "horizon_points": user.get("horizon_points", 0),
        "compass_marks": user.get("compass_marks", 0),
    }


@api_router.post("/trials/{quest_id}/submit")
async def submit_trial(quest_id: str, payload: TrialSubmit, explorer=Depends(require_explorer)):
    quest = curriculum.QUEST_INDEX.get(quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    result = curriculum.grade(quest_id, payload.answers)
    score, correct, total, per_question = result
    threshold = quest["trial"]["pass_threshold"]
    mastery = score >= threshold
    points_awarded = quest["points"] if mastery else round(quest["points"] * score / 100)

    prev = await db.progress.find_one({"user_id": explorer["user_id"], "quest_id": quest_id}, {"_id": 0})
    prev_points = prev["points_earned"] if prev else 0
    prev_mastery = prev["mastery"] if prev else False

    # only keep the best attempt's points
    final_points = max(points_awarded, prev_points)
    delta = final_points - prev_points

    progress_doc = {
        "user_id": explorer["user_id"],
        "quest_id": quest_id,
        "territory_id": quest["territory_id"],
        "standard_code": quest["standard"]["code"],
        "score": max(score, prev["score"]) if prev else score,
        "last_score": score,
        "points_earned": final_points,
        "mastery": mastery or prev_mastery,
        "reflection": payload.reflection or (prev.get("reflection") if prev else ""),
        "updated_at": now_utc().isoformat(),
    }
    await db.progress.update_one(
        {"user_id": explorer["user_id"], "quest_id": quest_id},
        {"$set": progress_doc}, upsert=True,
    )

    inc = {"horizon_points": delta}
    if mastery and not prev_mastery:
        inc["compass_marks"] = 1
    await db.users.update_one({"user_id": explorer["user_id"]}, {"$inc": inc})

    if delta > 0:
        await db.points_events.insert_one({
            "user_id": explorer["user_id"],
            "delta": delta,
            "quest_id": quest_id,
            "territory_id": quest["territory_id"],
            "type": "trial",
            "created_at": now_utc().isoformat(),
        })

    updated_user = await db.users.find_one({"user_id": explorer["user_id"]}, {"_id": 0})
    return {
        "score": score,
        "correct": correct,
        "total": total,
        "mastery": mastery,
        "points_awarded": max(delta, 0),
        "compass_mark_earned": mastery and not prev_mastery,
        "per_question": per_question,
        "horizon_points": updated_user.get("horizon_points", 0),
        "compass_marks": updated_user.get("compass_marks", 0),
    }


# ---------------- Hands-On Labs ----------------
LAB_BONUS = 75
LAB_QUESTS = {"t1-q8", "t2-q1", "t2-q2", "t2-q4", "t3-q5", "t3-q6"}  # quests that have a hands-on lab
CHALLENGE_BONUSES = {"cipher-pigpen": 50}  # optional extra-XP mini challenges


@api_router.post("/labs/{quest_id}/complete")
async def complete_lab(quest_id: str, explorer=Depends(require_explorer)):
    quest = curriculum.QUEST_INDEX.get(quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    if quest_id not in LAB_QUESTS:
        raise HTTPException(status_code=400, detail="This quest has no hands-on lab")
    existing = await db.lab_completions.find_one(
        {"user_id": explorer["user_id"], "quest_id": quest_id}, {"_id": 0}
    )
    if existing:
        u = await db.users.find_one({"user_id": explorer["user_id"]}, {"_id": 0})
        return {"already_completed": True, "bonus": 0, "horizon_points": u.get("horizon_points", 0)}
    await db.lab_completions.insert_one({
        "user_id": explorer["user_id"],
        "quest_id": quest_id,
        "territory_id": quest["territory_id"],
        "bonus": LAB_BONUS,
        "created_at": now_utc().isoformat(),
    })
    await db.users.update_one({"user_id": explorer["user_id"]}, {"$inc": {"horizon_points": LAB_BONUS}})
    await db.points_events.insert_one({
        "user_id": explorer["user_id"],
        "delta": LAB_BONUS,
        "quest_id": quest_id,
        "territory_id": quest["territory_id"],
        "type": "lab",
        "created_at": now_utc().isoformat(),
    })
    u = await db.users.find_one({"user_id": explorer["user_id"]}, {"_id": 0})
    return {"already_completed": False, "bonus": LAB_BONUS, "horizon_points": u.get("horizon_points", 0)}


@api_router.get("/labs/completions")
async def my_lab_completions(user=Depends(get_current_user)):
    rows = await db.lab_completions.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(200)
    return [r["quest_id"] for r in rows]


@api_router.post("/challenges/{challenge_id}/complete")
async def complete_challenge(challenge_id: str, explorer=Depends(require_explorer)):
    bonus = CHALLENGE_BONUSES.get(challenge_id)
    if bonus is None:
        raise HTTPException(status_code=404, detail="Unknown challenge")
    existing = await db.challenge_completions.find_one(
        {"user_id": explorer["user_id"], "challenge_id": challenge_id}, {"_id": 0}
    )
    if existing:
        u = await db.users.find_one({"user_id": explorer["user_id"]}, {"_id": 0})
        return {"already_completed": True, "bonus": 0, "horizon_points": u.get("horizon_points", 0)}
    await db.challenge_completions.insert_one({
        "user_id": explorer["user_id"],
        "challenge_id": challenge_id,
        "bonus": bonus,
        "created_at": now_utc().isoformat(),
    })
    await db.users.update_one({"user_id": explorer["user_id"]}, {"$inc": {"horizon_points": bonus}})
    await db.points_events.insert_one({
        "user_id": explorer["user_id"],
        "delta": bonus,
        "challenge_id": challenge_id,
        "territory_id": "t3",
        "type": "challenge",
        "created_at": now_utc().isoformat(),
    })
    u = await db.users.find_one({"user_id": explorer["user_id"]}, {"_id": 0})
    return {"already_completed": False, "bonus": bonus, "horizon_points": u.get("horizon_points", 0)}


class MissionSubmit(BaseModel):
    doc: Dict


async def grade_email_ai(mission, doc):
    """Grade the AI dimensions (tone/etiquette/grammar) of the student's email via Claude.
    Returns (results_list, feedback_str, rating_str)."""
    ai_tasks = [t for t in mission["tasks"] if t["check"].get("kind") == "ai"]
    if not ai_tasks:
        return [], "", ""
    target = mission.get("ai_target", {})
    msgs = [m for m in (doc.get("messages") or []) if m.get("folder") == "sent" and m.get("kind") == target.get("sentKind")]
    email = msgs[-1] if msgs else None
    if not email or not (email.get("body") or "").strip():
        # Nothing written yet — all AI dims fail with guidance.
        return ([{"id": t["id"], "passed": False} for t in ai_tasks],
                "Write and send the email first, then the AI Coach can grade your tone, etiquette, and grammar.", "Not yet")
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    system_message = (
        "You are an email-writing coach for middle-school CTE students. Evaluate a student's email for a "
        f"{target.get('register','professional')} message to {target.get('recipient','the recipient')}. "
        "Return STRICT JSON only, no prose, with keys: tone_ok (bool), etiquette_ok (bool), grammar_ok (bool), "
        "rating (one of 'Excellent','Good','Needs work'), feedback (2-3 short, warm, specific sentences of advice). "
        "Judge tone_ok = tone matches the register and reader; etiquette_ok = has proper greeting+closing, is respectful, "
        "no slang/ALL CAPS, clear purpose; grammar_ok = no notable grammar/spelling errors. Be encouraging but honest."
    )
    prompt = f"Subject: {email.get('subject','')}\nTo: {', '.join(email.get('to', []))}\n\n{email.get('body','')}"
    try:
        chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=f"emailgrade_{mission['id']}", system_message=system_message).with_model("anthropic", "claude-sonnet-4-6")
        raw = await chat.send_message(UserMessage(text=prompt))
        txt = raw[raw.find("{"): raw.rfind("}") + 1]
        data = json.loads(txt)
    except Exception as e:
        logger.error(f"Email AI grade error: {e}")
        # Fail-open: give credit so a Claude hiccup never blocks a student, with a note.
        return ([{"id": t["id"], "passed": True} for t in ai_tasks],
                "The AI Coach was unavailable, so your writing tasks were credited. Ask your teacher for feedback too!", "Unrated")
    dim_map = {"tone": bool(data.get("tone_ok")), "etiquette": bool(data.get("etiquette_ok")), "grammar": bool(data.get("grammar_ok"))}
    results = [{"id": t["id"], "passed": dim_map.get(t["check"]["dim"], False)} for t in ai_tasks]
    return results, str(data.get("feedback", "")), str(data.get("rating", ""))


# ---------------- Skill Studio (guided, auto-graded missions) ----------------
@api_router.get("/studio/{track_id}")
async def studio_track(track_id: str, user=Depends(get_current_user)):
    data = skillstudio.public_track(track_id)
    if not data:
        raise HTTPException(status_code=404, detail="Track not found")
    rows = await db.studio_progress.find(
        {"user_id": user["user_id"], "track": track_id}, {"_id": 0}
    ).to_list(200)
    progress = {r["mission_id"]: {"score": r.get("score", 0), "grade": r.get("grade", "F"), "mastery": r.get("mastery", False)} for r in rows}
    return {**data, "progress": progress}


@api_router.get("/studio/reports/all")
async def studio_reports(guide=Depends(get_current_user)):
    if guide.get("role") != "guide":
        raise HTTPException(status_code=403, detail="Guides only")
    tracks = ["docs", "sheets", "slides", "email"]
    totals = {t: len(skillstudio.MISSIONS.get(t, [])) for t in tracks}
    explorers = await db.users.find({"role": "explorer"}, {"_id": 0, "user_id": 1, "name": 1, "email": 1}).to_list(1000)
    rows = []
    for ex in explorers:
        prog = await db.studio_progress.find({"user_id": ex["user_id"]}, {"_id": 0}).to_list(500)
        if not prog:
            continue
        by_track = {}
        for t in tracks:
            tp = [p for p in prog if p.get("track") == t]
            if tp:
                by_track[t] = {
                    "attempted": len(tp),
                    "total": totals[t],
                    "mastered": sum(1 for p in tp if p.get("mastery")),
                    "avg": round(sum(p.get("score", 0) for p in tp) / len(tp)),
                    "missions": {p["mission_id"]: {"score": p.get("score", 0), "grade": p.get("grade", "F"), "mastery": p.get("mastery", False)} for p in tp},
                }
        last = max((p.get("updated_at", "") for p in prog), default="")
        rows.append({"user_id": ex["user_id"], "name": ex.get("name", ""), "email": ex.get("email", ""), "tracks": by_track, "last_active": last})
    rows.sort(key=lambda r: r["name"].lower())
    return {"totals": totals, "students": rows}


# ---------------- Skill Studio: Drafts (save an unfinished email) ----------------
class DraftsSave(BaseModel):
    drafts: List[Dict]


@api_router.get("/studio/{track_id}/{mission_id}/drafts")
async def get_drafts(track_id: str, mission_id: str, user=Depends(get_current_user)):
    row = await db.studio_drafts.find_one({"user_id": user["user_id"], "mission_id": mission_id}, {"_id": 0})
    return {"drafts": (row.get("drafts", []) if row else [])}


@api_router.put("/studio/{track_id}/{mission_id}/drafts")
async def save_drafts(track_id: str, mission_id: str, payload: DraftsSave, user=Depends(get_current_user)):
    if user.get("role") != "explorer":
        return {"ok": True, "skipped": True}
    await db.studio_drafts.update_one(
        {"user_id": user["user_id"], "mission_id": mission_id},
        {"$set": {"user_id": user["user_id"], "track": track_id, "mission_id": mission_id,
                  "drafts": payload.drafts, "updated_at": now_utc().isoformat()}},
        upsert=True,
    )
    return {"ok": True}


# ---------------- Skill Studio: Assignments (Guides assign missions to a class) ----------------
class AssignmentCreate(BaseModel):
    expedition_id: str
    track: str
    mission_ids: List[str]
    note: Optional[str] = ""


PASS_SCORE = 60  # a mission counts as "finished" when the best score is a passing 60%+


@api_router.post("/assignments")
async def create_assignment(payload: AssignmentCreate, guide=Depends(require_guide)):
    exp = await db.expeditions.find_one({"expedition_id": payload.expedition_id, "guide_id": guide["user_id"]}, {"_id": 0})
    if not exp:
        raise HTTPException(status_code=404, detail="Expedition not found")
    valid = {m["id"] for m in skillstudio.MISSIONS.get(payload.track, [])}
    mids = [m for m in payload.mission_ids if m in valid]
    if not mids:
        raise HTTPException(status_code=400, detail="No valid missions selected")
    a = {
        "assignment_id": f"asg_{uuid.uuid4().hex[:12]}", "guide_id": guide["user_id"],
        "expedition_id": payload.expedition_id, "track": payload.track, "mission_ids": mids,
        "note": payload.note or "", "created_at": now_utc().isoformat(),
    }
    await db.assignments.insert_one(a)
    a.pop("_id", None)
    return a


@api_router.get("/assignments")
async def list_assignments(guide=Depends(require_guide)):
    asgs = await db.assignments.find({"guide_id": guide["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(300)
    result = []
    for a in asgs:
        exp = await db.expeditions.find_one({"expedition_id": a["expedition_id"]}, {"_id": 0, "name": 1})
        members = await db.users.find({"expedition_ids": a["expedition_id"], "role": "explorer"},
                                      {"_id": 0, "user_id": 1, "name": 1, "email": 1}).to_list(500)
        titles = {m["id"]: m["title"] for m in skillstudio.MISSIONS.get(a["track"], []) if m["id"] in a["mission_ids"]}
        students = []
        for mem in members:
            prog = await db.studio_progress.find(
                {"user_id": mem["user_id"], "mission_id": {"$in": a["mission_ids"]}}, {"_id": 0}
            ).to_list(200)
            pm = {p["mission_id"]: p for p in prog}
            done = {mid: bool(pm.get(mid, {}).get("score", 0) >= PASS_SCORE) for mid in a["mission_ids"]}
            students.append({
                "user_id": mem["user_id"], "name": mem.get("name", ""), "email": mem.get("email", ""),
                "done": done, "done_count": sum(1 for v in done.values() if v),
            })
        students.sort(key=lambda s: (s["name"] or s["email"]).lower())
        result.append({
            **a, "expedition_name": exp["name"] if exp else "—",
            "mission_titles": titles, "students": students, "member_count": len(members),
        })
    return result


@api_router.delete("/assignments/{assignment_id}")
async def delete_assignment(assignment_id: str, guide=Depends(require_guide)):
    await db.assignments.delete_one({"assignment_id": assignment_id, "guide_id": guide["user_id"]})
    return {"ok": True}


@api_router.get("/me/assignments")
async def my_assignments(user=Depends(get_current_user)):
    ids = user.get("expedition_ids", [])
    if not ids:
        return []
    asgs = await db.assignments.find({"expedition_id": {"$in": ids}}, {"_id": 0}).sort("created_at", -1).to_list(300)
    return asgs


# ---------------- Assessments: checkpoint tests + comprehensive final ----------------
class AttemptSubmit(BaseModel):
    answers: Dict[str, int]


async def _assessment_summary(user_id, assessment_id):
    attempts = await db.assessment_attempts.find(
        {"user_id": user_id, "assessment_id": assessment_id, "status": "completed"}, {"_id": 0}
    ).to_list(50)
    best = max([a["score"] for a in attempts], default=None)
    return {
        "best_score": best,
        "attempts_used": len(attempts),
        "passed": any(a.get("passed") for a in attempts),
    }


@api_router.get("/assessments/track/{track_id}")
async def get_track_assessments(track_id: str, user=Depends(get_current_user)):
    metas = assessments.track_checkpoint_metas(track_id)
    if not metas:
        return {"checkpoints": []}
    prog = await db.studio_progress.find({"user_id": user["user_id"]}, {"_id": 0, "mission_id": 1, "score": 1}).to_list(500)
    passed_missions = {p["mission_id"] for p in prog if p.get("score", 0) >= 60}
    out = []
    for m in metas:
        summ = await _assessment_summary(user["user_id"], m["id"])
        missing = [mid for mid in m["covers"] if mid not in passed_missions]
        unlocked = len(missing) == 0 or user.get("role") != "explorer"
        out.append({**m, **summ,
                    "unlocked": unlocked,
                    "locked_reason": None if unlocked else f"Finish the {len(m['covers'])} lessons in this block first"})
    return {"checkpoints": out}


@api_router.get("/assessments/final/meta")
async def get_final_meta(user=Depends(get_current_user)):
    m = assessments.assessment_meta(assessments.FINAL_ID)
    summ = await _assessment_summary(user["user_id"], assessments.FINAL_ID)
    return {**m, **summ, "unlocked": True}


@api_router.post("/assessments/{assessment_id}/start")
async def start_assessment(assessment_id: str, user=Depends(get_current_user)):
    meta = assessments.assessment_meta(assessment_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if user.get("role") == "explorer":
        if meta["kind"] == "checkpoint":
            prog = await db.studio_progress.find({"user_id": user["user_id"]}, {"_id": 0, "mission_id": 1, "score": 1}).to_list(500)
            passed_missions = {p["mission_id"] for p in prog if p.get("score", 0) >= 60}
            if any(mid not in passed_missions for mid in meta["covers"]):
                raise HTTPException(status_code=403, detail="Finish the lessons in this block before taking the checkpoint")
        completed = await db.assessment_attempts.count_documents(
            {"user_id": user["user_id"], "assessment_id": assessment_id, "status": "completed"})
        if completed >= meta["max_attempts"]:
            raise HTTPException(status_code=403, detail="No attempts remaining")
    public, key = assessments.build_attempt_questions(assessment_id)
    # Reuse an unsubmitted attempt instead of drawing a new one — prevents orphan rows and question-mining.
    existing = await db.assessment_attempts.find_one(
        {"user_id": user["user_id"], "assessment_id": assessment_id, "status": "in_progress"}, {"_id": 0})
    if existing:
        return {"attempt_id": existing["attempt_id"], "assessment_id": assessment_id, "kind": meta["kind"],
                "title": meta["title"], "pass": meta["pass"], "questions": existing["questions"]}
    attempt = {
        "attempt_id": f"att_{uuid.uuid4().hex[:14]}", "user_id": user["user_id"],
        "assessment_id": assessment_id, "kind": meta["kind"], "track": meta.get("track"),
        "answer_key": key, "questions": public, "status": "in_progress",
        "score": None, "passed": None, "started_at": now_utc().isoformat(),
    }
    await db.assessment_attempts.insert_one(dict(attempt))
    return {"attempt_id": attempt["attempt_id"], "assessment_id": assessment_id, "kind": meta["kind"],
            "title": meta["title"], "pass": meta["pass"], "questions": public}


@api_router.post("/assessments/attempts/{attempt_id}/submit")
async def submit_assessment(attempt_id: str, payload: AttemptSubmit, user=Depends(get_current_user)):
    attempt = await db.assessment_attempts.find_one({"attempt_id": attempt_id, "user_id": user["user_id"]}, {"_id": 0})
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt["status"] == "completed":
        raise HTTPException(status_code=400, detail="Attempt already submitted")
    meta = assessments.assessment_meta(attempt["assessment_id"])
    score, correct, total = assessments.grade_attempt(attempt["answer_key"], payload.answers)
    passed = score >= meta["pass"]

    is_explorer = user.get("role") == "explorer"
    prior_passed = False
    points_awarded = 0
    if is_explorer:
        prior = await db.assessment_attempts.find(
            {"user_id": user["user_id"], "assessment_id": attempt["assessment_id"], "status": "completed"},
            {"_id": 0, "passed": 1}).to_list(50)
        prior_passed = any(p.get("passed") for p in prior)
        if meta["kind"] == "checkpoint" and passed and not prior_passed:
            points_awarded = assessments.CHECKPOINT_POINTS
    completed_count = 0
    if is_explorer:
        completed_count = await db.assessment_attempts.count_documents(
            {"user_id": user["user_id"], "assessment_id": attempt["assessment_id"], "status": "completed"})

    review = [{"question": q["question"], "options": q["options"],
               "correct": attempt["answer_key"][q["qid"]], "chosen": payload.answers.get(q["qid"], -1)}
              for q in attempt["questions"]]

    if is_explorer:
        await db.assessment_attempts.update_one(
            {"attempt_id": attempt_id},
            {"$set": {"status": "completed", "score": score, "correct": correct, "total": total,
                      "passed": passed, "attempt_number": completed_count + 1,
                      "points_awarded": points_awarded, "completed_at": now_utc().isoformat()}})
        if points_awarded > 0:
            await db.users.update_one({"user_id": user["user_id"]}, {"$inc": {"horizon_points": points_awarded}})
            await db.points_events.insert_one({"user_id": user["user_id"], "delta": points_awarded,
                                               "mission_id": attempt["assessment_id"], "territory_id": "t2",
                                               "type": "assessment", "created_at": now_utc().isoformat()})
    else:
        await db.assessment_attempts.delete_one({"attempt_id": attempt_id})  # guides: preview, don't persist

    attempts_used = (completed_count + 1) if is_explorer else 0
    return {"score": score, "correct": correct, "total": total, "passed": passed,
            "points_awarded": points_awarded, "attempts_used": attempts_used,
            "attempts_remaining": max(0, meta["max_attempts"] - attempts_used),
            "preview": not is_explorer, "review": review}


@api_router.get("/me/assessments")
async def my_assessments(user=Depends(get_current_user)):
    out = []
    for track, cids in assessments.TRACK_CHECKPOINTS.items():
        for cid in cids:
            m = assessments.assessment_meta(cid)
            summ = await _assessment_summary(user["user_id"], cid)
            out.append({**m, **summ})
    fm = assessments.assessment_meta(assessments.FINAL_ID)
    out.append({**fm, **(await _assessment_summary(user["user_id"], assessments.FINAL_ID))})
    return out


@api_router.get("/assessments/reports")
async def assessment_reports(guide=Depends(require_guide)):
    exps = await db.expeditions.find({"guide_id": guide["user_id"]}, {"_id": 0, "expedition_id": 1}).to_list(100)
    exp_ids = [e["expedition_id"] for e in exps]
    members = await db.users.find({"expedition_ids": {"$in": exp_ids}, "role": "explorer"},
                                  {"_id": 0, "user_id": 1, "name": 1, "email": 1}).to_list(1000) if exp_ids else []
    all_ids = [cid for cids in assessments.TRACK_CHECKPOINTS.values() for cid in cids] + [assessments.FINAL_ID]
    columns = [{"id": cid, "title": assessments.assessment_meta(cid)["title"]} for cid in all_ids]
    member_ids = [m["user_id"] for m in members]
    best = {}
    if member_ids:
        atts = await db.assessment_attempts.find(
            {"user_id": {"$in": member_ids}, "status": "completed"},
            {"_id": 0, "user_id": 1, "assessment_id": 1, "score": 1}).to_list(20000)
        for a in atts:
            k = (a["user_id"], a["assessment_id"])
            if a.get("score") is not None and (k not in best or a["score"] > best[k]):
                best[k] = a["score"]
    rows = []
    for mem in members:
        rows.append({"user_id": mem["user_id"], "name": mem.get("name", ""), "email": mem.get("email", ""),
                     "scores": {cid: best.get((mem["user_id"], cid)) for cid in all_ids}})
    rows.sort(key=lambda r: (r["name"] or r["email"]).lower())
    return {"columns": columns, "students": rows}


@api_router.get("/assessments/bank")
async def get_assessment_bank(guide=Depends(require_guide)):
    return assessments.full_bank()


# ---------------- Teaching slides embedded before each lesson block ----------------
class BlockSlides(BaseModel):
    embed_url: str

PPTX_CT = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
_PPTX_EXTS = (".pptx", ".ppt")


def _block_slide_public(r):
    """Shape a db.block_slides row for the frontend."""
    pptx = r.get("pptx")
    return {
        "embed_url": r.get("embed_url", ""),
        "pptx": {"filename": pptx["filename"], "version": pptx["version"]} if pptx else None,
    }


@api_router.get("/block-slides/{track_id}")
async def get_block_slides(track_id: str, user=Depends(get_current_user)):
    block_ids = assessments.TRACK_CHECKPOINTS.get(track_id, [])
    rows = await db.block_slides.find({"block_id": {"$in": block_ids}}, {"_id": 0}).to_list(50)
    return {r["block_id"]: _block_slide_public(r) for r in rows}


@api_router.put("/block-slides/{block_id}")
async def set_block_slides(block_id: str, payload: BlockSlides, guide=Depends(require_guide)):
    if not assessments.assessment_meta(block_id):
        raise HTTPException(status_code=404, detail="Unknown block")
    url = (payload.embed_url or "").strip()
    if url and not url.startswith("https://docs.google.com/"):
        raise HTTPException(status_code=400, detail="Please paste a Google Slides 'Publish to web' embed link (https://docs.google.com/...)")
    await db.block_slides.update_one(
        {"block_id": block_id},
        {"$set": {"block_id": block_id, "embed_url": url, "updated_by": guide["user_id"], "updated_at": now_utc().isoformat()}},
        upsert=True,
    )
    return {"ok": True, "block_id": block_id, "embed_url": url}


@api_router.post("/block-slides/{block_id}/upload-pptx")
async def upload_block_pptx(block_id: str, file: UploadFile = File(...), guide=Depends(require_guide)):
    if not assessments.assessment_meta(block_id):
        raise HTTPException(status_code=404, detail="Unknown block")
    fname = (file.filename or "deck.pptx").strip()
    if not fname.lower().endswith(_PPTX_EXTS):
        raise HTTPException(status_code=400, detail="Please upload a PowerPoint file (.pptx or .ppt).")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The file is empty.")
    if len(data) > 40 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File is too large (max 40 MB).")
    version = uuid.uuid4().hex[:12]
    storage_path = f"horizonquest/decks/{block_id}/{version}.pptx"
    await run_in_threadpool(objstore.put_object, storage_path, data, PPTX_CT)
    await db.block_slides.update_one(
        {"block_id": block_id},
        {"$set": {"block_id": block_id,
                  "pptx": {"storage_path": storage_path, "filename": fname, "version": version,
                           "uploaded_at": now_utc().isoformat(), "uploaded_by": guide["user_id"]}}},
        upsert=True,
    )
    return {"ok": True, "block_id": block_id, "pptx": {"filename": fname, "version": version}}


@api_router.delete("/block-slides/{block_id}/pptx")
async def delete_block_pptx(block_id: str, guide=Depends(require_guide)):
    await db.block_slides.update_one({"block_id": block_id}, {"$unset": {"pptx": ""}})
    return {"ok": True}


@api_router.get("/decks/pptx/{fname}")
async def serve_block_pptx(fname: str):
    """Public: serves an uploaded PowerPoint so the Office viewer + download link can fetch it.
    fname is '<block_id>.pptx' so the URL ends in a real extension."""
    block_id = fname.rsplit(".", 1)[0]
    row = await db.block_slides.find_one({"block_id": block_id})
    if not row or not row.get("pptx"):
        raise HTTPException(status_code=404, detail="No PowerPoint uploaded for this block")
    pptx = row["pptx"]
    data, ct = await run_in_threadpool(objstore.get_object, pptx["storage_path"])
    return Response(
        content=data, media_type=PPTX_CT,
        headers={
            "Content-Disposition": f'inline; filename="{pptx.get("filename", "deck.pptx")}"',
            "Cache-Control": "public, max-age=3600",
        },
    )


TRACK_NAMES = {"docs": "Word Processing", "sheets": "Spreadsheets", "slides": "Presentations", "email": "Email & Communication"}


@api_router.get("/reports/student/{user_id}")
async def student_report(user_id: str, guide=Depends(require_guide)):
    student = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Explorer not found")
    guide_exps = await db.expeditions.find({"guide_id": guide["user_id"]}, {"_id": 0, "expedition_id": 1, "name": 1}).to_list(200)
    guide_exp_ids = {e["expedition_id"] for e in guide_exps}
    student_exp_ids = set(student.get("expedition_ids", []))
    shared = guide_exp_ids & student_exp_ids
    if not shared:
        raise HTTPException(status_code=403, detail="This Explorer is not in your classes")
    classes = [e["name"] for e in guide_exps if e["expedition_id"] in shared]

    prog = await db.studio_progress.find({"user_id": user_id}, {"_id": 0}).to_list(500)
    pm = {p["mission_id"]: p for p in prog}
    studio = []
    for track in ["docs", "sheets", "slides", "email"]:
        missions = skillstudio.MISSIONS.get(track, [])
        done = [pm[m["id"]] for m in missions if m["id"] in pm]
        mastered = sum(1 for p in done if p.get("score", 0) >= 90)
        avg = round(sum(p.get("score", 0) for p in done) / len(done)) if done else None
        studio.append({"track": track, "name": TRACK_NAMES[track], "total": len(missions),
                       "attempted": len(done), "mastered": mastered, "avg": avg})

    atts = await db.assessment_attempts.find({"user_id": user_id, "status": "completed"},
                                             {"_id": 0, "assessment_id": 1, "score": 1}).to_list(500)
    best = {}
    for a in atts:
        if a.get("score") is not None:
            best[a["assessment_id"]] = max(best.get(a["assessment_id"], 0), a["score"])
    checkpoints = []
    for track in ["docs", "sheets", "slides", "email"]:
        for cid in assessments.TRACK_CHECKPOINTS.get(track, []):
            m = assessments.assessment_meta(cid)
            checkpoints.append({"id": cid, "track_name": TRACK_NAMES[track], "title": m["title"],
                                "best": best.get(cid), "pass": m["pass"]})
    fmeta = assessments.assessment_meta(assessments.FINAL_ID)
    final = {"title": fmeta["title"], "best": best.get(assessments.FINAL_ID), "pass": fmeta["pass"]}

    return {
        "student": {"name": student.get("name", ""), "email": student.get("email", ""),
                    "level": student.get("level", 1), "horizon_points": student.get("horizon_points", 0),
                    "compass_marks": student.get("compass_marks", 0), "fleet": student.get("fleet", ""),
                    "tier": student.get("tier", "")},
        "classes": classes, "guide_name": guide.get("name", ""),
        "studio": studio, "checkpoints": checkpoints, "final": final,
        "generated_at": now_utc().isoformat(),
    }



@api_router.post("/studio/{track_id}/{mission_id}/submit")
async def studio_submit(track_id: str, mission_id: str, payload: MissionSubmit, user=Depends(get_current_user)):
    mission = skillstudio.MISSION_INDEX.get(mission_id)
    if not mission or mission.get("track") != track_id:
        raise HTTPException(status_code=404, detail="Mission not found")

    graded = skillstudio.grade_mission(mission_id, payload.doc)
    ai_feedback, ai_rating = "", ""
    if track_id == "email":
        ai_results, ai_feedback, ai_rating = await grade_email_ai(mission, payload.doc)
        if ai_results:
            graded["results"] = graded["results"] + ai_results
            graded["passed"] += sum(1 for r in ai_results if r["passed"])
            graded["total"] += len(ai_results)
            graded["score"] = round(graded["passed"] / graded["total"] * 100) if graded["total"] else 0
    score = graded["score"]
    points_awarded = round(graded["points"] * score / 100)

    # No credit for a blank email: if a message was sent but the student wrote essentially nothing, award 0 points.
    sent_msgs = [m for m in (payload.doc.get("messages") or [])
                 if m.get("folder") == "sent" and m.get("kind") in ("reply", "replyall", "forward", "new")]
    blank_send = False
    if sent_msgs:
        latest = sent_msgs[-1]
        sb = latest.get("bodyStudent")
        sb = sb if sb is not None else (latest.get("body") or "")
        if len(sb.split()) < 5:
            blank_send = True
            points_awarded = 0
    # Guides (and any non-explorer) can grade-preview missions as a teaching tool.
    # Nothing is persisted and no points are awarded.
    if user.get("role") != "explorer":
        return {
            "results": graded["results"], "passed": graded["passed"], "total": graded["total"],
            "score": score, "grade": skillstudio.letter_grade(score), "mastery": score >= 90,
            "points_awarded": 0, "compass_mark_earned": False,
            "horizon_points": user.get("horizon_points", 0), "compass_marks": user.get("compass_marks", 0),
            "ai_feedback": ai_feedback, "ai_rating": ai_rating, "preview": True, "blank_send": blank_send,
        }

    prev = await db.studio_progress.find_one({"user_id": user["user_id"], "mission_id": mission_id}, {"_id": 0})
    prev_points = prev["points_earned"] if prev else 0
    prev_score = prev["score"] if prev else 0
    prev_mastery = prev.get("mastery", False) if prev else False

    best_score = max(score, prev_score)
    best_grade = skillstudio.letter_grade(best_score)
    sticky_mastery = (score >= 90) or prev_mastery
    final_points = max(points_awarded, prev_points)
    delta = final_points - prev_points

    await db.studio_progress.update_one(
        {"user_id": user["user_id"], "mission_id": mission_id},
        {"$set": {
            "user_id": user["user_id"], "track": track_id, "mission_id": mission_id,
            "score": best_score, "last_score": score,
            "grade": best_grade, "points_earned": final_points, "mastery": sticky_mastery,
            "updated_at": now_utc().isoformat(),
        }}, upsert=True,
    )

    inc = {"horizon_points": delta}
    newly_mastered = (score >= 90) and not prev_mastery
    if newly_mastered:
        inc["compass_marks"] = 1
    await db.users.update_one({"user_id": user["user_id"]}, {"$inc": inc})
    if delta > 0:
        await db.points_events.insert_one({
            "user_id": user["user_id"], "delta": delta, "mission_id": mission_id,
            "territory_id": "t2", "type": "studio", "created_at": now_utc().isoformat(),
        })

    updated = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return {
        "results": graded["results"], "passed": graded["passed"], "total": graded["total"],
        "score": best_score, "grade": best_grade, "mastery": sticky_mastery,
        "points_awarded": max(delta, 0), "compass_mark_earned": newly_mastered,
        "horizon_points": updated.get("horizon_points", 0), "compass_marks": updated.get("compass_marks", 0),
        "ai_feedback": ai_feedback, "ai_rating": ai_rating, "blank_send": blank_send,
    }


# ---------------- Leaderboard ----------------
@api_router.get("/leaderboard")
async def leaderboard(
    expedition_id: Optional[str] = None,
    territory_id: Optional[str] = None,
    period: Optional[str] = None,
    user=Depends(get_current_user),
):
    query = {"role": "explorer"}
    if expedition_id:
        exp = await db.expeditions.find_one({"expedition_id": expedition_id}, {"_id": 0})
        if not exp:
            raise HTTPException(status_code=404, detail="Expedition not found")
        query["expedition_ids"] = expedition_id
    explorers = await db.users.find(query, {"_id": 0, "user_id": 1, "name": 1, "picture": 1, "fleet": 1, "horizon_points": 1, "compass_marks": 1, "expedition_ids": 1}).to_list(1000)
    ids = [u["user_id"] for u in explorers]

    score_map = {}
    if territory_id:
        metric = "territory"
        prog = await db.progress.find({"user_id": {"$in": ids}, "territory_id": territory_id}, {"_id": 0, "user_id": 1, "points_earned": 1}).to_list(10000)
        for p in prog:
            score_map[p["user_id"]] = score_map.get(p["user_id"], 0) + p.get("points_earned", 0)
        labs = await db.lab_completions.find({"user_id": {"$in": ids}, "territory_id": territory_id}, {"_id": 0, "user_id": 1, "bonus": 1}).to_list(10000)
        for l in labs:
            score_map[l["user_id"]] = score_map.get(l["user_id"], 0) + l.get("bonus", 0)
    elif period == "week":
        metric = "week"
        cutoff = (now_utc() - timedelta(days=7)).isoformat()
        evs = await db.points_events.find({"user_id": {"$in": ids}, "created_at": {"$gte": cutoff}}, {"_id": 0, "user_id": 1, "delta": 1}).to_list(50000)
        for e in evs:
            score_map[e["user_id"]] = score_map.get(e["user_id"], 0) + e.get("delta", 0)
    else:
        metric = "overall"
        for u in explorers:
            score_map[u["user_id"]] = u.get("horizon_points", 0)

    ranked = sorted(explorers, key=lambda u: (-score_map.get(u["user_id"], 0), u.get("name") or ""))

    entries = []
    for i, u in enumerate(ranked):
        entries.append({
            "rank": i + 1,
            "user_id": u["user_id"],
            "name": u.get("name"),
            "picture": u.get("picture"),
            "fleet": u.get("fleet"),
            "tier": rank_tier(u.get("horizon_points", 0)),
            "score": score_map.get(u["user_id"], 0),
            "horizon_points": u.get("horizon_points", 0),
            "compass_marks": u.get("compass_marks", 0),
            "is_me": u["user_id"] == user["user_id"],
        })

    fleet_totals = {}
    for u in ranked:
        f = u.get("fleet") or "Unaligned"
        fleet_totals[f] = fleet_totals.get(f, 0) + score_map.get(u["user_id"], 0)
    fleets = [{"fleet": k, "points": v} for k, v in sorted(fleet_totals.items(), key=lambda x: -x[1])]

    return {"entries": entries, "fleets": fleets, "metric": metric}


# ---------------- Guide: Review Queue & Mastery ----------------
@api_router.get("/guide/reviews")
async def guide_reviews(guide=Depends(require_guide)):
    exps = await db.expeditions.find({"guide_id": guide["user_id"]}, {"_id": 0}).to_list(200)
    exp_ids = [e["expedition_id"] for e in exps]
    reviews = await db.reviews.find(
        {"expedition_ids": {"$in": exp_ids}, "status": "pending"}, {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    return reviews


@api_router.post("/guide/reviews/{review_id}/approve")
async def approve_review(review_id: str, guide=Depends(require_guide)):
    review = await db.reviews.find_one({"review_id": review_id}, {"_id": 0})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    await db.reviews.update_one({"review_id": review_id}, {"$set": {"status": "approved", "reviewed_by": guide["user_id"]}})
    # bonus points for approved reflection
    await db.users.update_one({"user_id": review["user_id"]}, {"$inc": {"horizon_points": 25}})
    return {"ok": True, "bonus": 25}


@api_router.get("/guide/mastery/{expedition_id}")
async def guide_mastery(expedition_id: str, guide=Depends(require_guide)):
    exp = await db.expeditions.find_one({"expedition_id": expedition_id}, {"_id": 0})
    if not exp or exp["guide_id"] != guide["user_id"]:
        raise HTTPException(status_code=404, detail="Not found")
    members = await db.users.find({"expedition_ids": expedition_id, "role": "explorer"}, {"_id": 0, "user_id": 1}).to_list(500)
    member_ids = [m["user_id"] for m in members]
    total_members = len(member_ids) or 1

    # aggregate per-standard mastery
    standards = {}
    for q in curriculum.QUESTS:
        code = q["standard"]["code"]
        standards.setdefault(code, {"code": code, "description": q["standard"]["description"], "territory_id": q["territory_id"], "mastered": 0, "attempted": 0})

    progress = await db.progress.find({"user_id": {"$in": member_ids}}, {"_id": 0, "user_id": 1, "standard_code": 1, "mastery": 1}).to_list(5000)
    for p in progress:
        code = p.get("standard_code")
        if code in standards:
            standards[code]["attempted"] += 1
            if p.get("mastery"):
                standards[code]["mastered"] += 1

    rows = []
    for code, s in standards.items():
        rows.append({
            **s,
            "mastery_pct": round((s["mastered"] / total_members) * 100),
        })
    rows.sort(key=lambda r: (r["territory_id"], r["code"]))

    # per-territory summary for chart
    territory_summary = []
    for t in curriculum.TERRITORIES:
        trows = [r for r in rows if r["territory_id"] == t["id"]]
        avg = round(sum(r["mastery_pct"] for r in trows) / len(trows)) if trows else 0
        territory_summary.append({"territory": t["name"], "mastery": avg, "color": t["color"]})

    return {"standards": rows, "territory_summary": territory_summary, "member_count": len(member_ids)}


# ---------------- AI Copilot (Claude, streaming) ----------------
@api_router.post("/ai/copilot")
async def ai_copilot(payload: CopilotRequest, explorer=Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

    quest = curriculum.QUEST_INDEX.get(payload.quest_id) if payload.quest_id else None
    context = ""
    if quest:
        context = (f" The Explorer is working on the quest '{quest['title']}' "
                   f"({quest['standard']['description']}).")

    system_message = (
        "You are the HorizonQuest Copilot, a friendly learning guide for young Explorers on an "
        "epic educational adventure. Give encouraging HINTS and ask guiding questions to help them "
        "think — NEVER give the direct final answer to a trial question. Keep replies short (2-4 sentences), "
        "warm, and use nautical/exploration language occasionally." + context
    )

    session_id = payload.session_id or f"{explorer['user_id']}_{payload.quest_id or 'general'}"

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=system_message,
    ).with_model("anthropic", "claude-sonnet-4-6")

    await db.ai_messages.insert_one({
        "user_id": explorer["user_id"], "session_id": session_id, "role": "user",
        "content": payload.message, "created_at": now_utc().isoformat(),
    })

    async def event_generator():
        collected = []
        try:
            async for event in chat.stream_message(UserMessage(text=payload.message)):
                if isinstance(event, TextDelta):
                    collected.append(event.content)
                    yield event.content
                elif isinstance(event, StreamDone):
                    break
        except Exception as e:
            logger.error(f"Copilot error: {e}")
            yield "\n[The Copilot lost the signal for a moment. Try again, Explorer.]"
        finally:
            await db.ai_messages.insert_one({
                "user_id": explorer["user_id"], "session_id": session_id, "role": "assistant",
                "content": "".join(collected), "created_at": now_utc().isoformat(),
            })

    return StreamingResponse(
        event_generator(), media_type="text/plain",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@api_router.get("/")
async def root():
    return {"message": "HorizonQuest API ⛵"}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
