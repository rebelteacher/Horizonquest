"""Seed one completed email-cp1 checkpoint attempt for em-exp so Checkpoint% has a number."""
import os
import requests
from dotenv import dotenv_values

BASE = (os.environ.get("REACT_APP_BACKEND_URL") or dotenv_values("/app/frontend/.env")["REACT_APP_BACKEND_URL"]).rstrip("/") + "/api"
H = {"Authorization": "Bearer em_exp_tok"}

r = requests.post(f"{BASE}/assessments/email-cp1/start", headers=H, timeout=60)
print("start", r.status_code, r.text[:300])
if r.status_code == 200:
    d = r.json()
    answers = {q["qid"]: 0 for q in d["questions"]}
    s = requests.post(f"{BASE}/assessments/attempts/{d['attempt_id']}/submit", headers=H, json={"answers": answers}, timeout=60)
    print("submit", s.status_code, {k: v for k, v in s.json().items() if k != "review"} if s.status_code == 200 else s.text[:300])
