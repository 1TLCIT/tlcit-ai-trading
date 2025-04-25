import os
import requests
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI(title="TLCIT Engine")

# ── Configuration ─────────────────────────────────────────────────────────────

PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER  = os.getenv("PUSHOVER_USER")
if not PUSHOVER_TOKEN or not PUSHOVER_USER:
    raise RuntimeError("Environment variables PUSHOVER_TOKEN and PUSHOVER_USER must be set")

# ── Pushover helper ────────────────────────────────────────────────────────────

def send_pushover(message: str, title: str = "tlcit Bot", priority: int = 0):
    """
    Send a message via Pushover.
    """
    payload = {
        "token":   PUSHOVER_TOKEN,
        "user":    PUSHOVER_USER,
        "message": message,
        "title":   title,
        "priority": priority,
    }
    r = requests.post("https://api.pushover.net/1/messages.json", data=payload, timeout=10)
    r.raise_for_status()

# ── Request models ─────────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    url: str = Field(..., example="https://example.com/image.png")
    threshold: float = Field(0.5, ge=0.0, le=1.0, description="Detection threshold 0–1")

class SignalRequest(BaseModel):
    level: Literal["info", "warn", "error"] = Field(..., example="error")
    detail: str = Field(..., example="Something noteworthy happened")

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "tlcit-engine up and running"}

@app.post("/scan")
async def scan(payload: ScanRequest, background_tasks: BackgroundTasks):
    """
    Stubbed scan: in reality you'd call your model here.
    """
    # TODO: call your tlcit model on payload.url with payload.threshold
    result = f"Scanned {payload.url!r} at threshold {payload.threshold}"
    background_tasks.add_task(send_pushover, result, title="Scan Complete")
    return {"status": "queued", "detail": result}

@app.post("/signal")
async def signal(payload: SignalRequest, background_tasks: BackgroundTasks):
    """
    Send a one-off alert signal.
    """
    msg = f"[{payload.level.upper()}] {payload.detail}"
    prio = {"info": 0, "warn": 1, "error": 2}[payload.level]
    background_tasks.add_task(send_pushover, msg, title="Signal Alert", priority=prio)
    return {"status": "notified", "detail": msg}

# ── App entrypoint ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
