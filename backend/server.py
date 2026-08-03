from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import string
import random
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
import httpx
from datetime import datetime, timezone, timedelta

import curriculum

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

    async with httpx.AsyncClient(timeout=20.0) as hc:
        r = await hc.get(AUTH_SESSION_URL, headers={"X-Session-ID": session_id})
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session id")
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
