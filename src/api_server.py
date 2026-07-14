"""
Lightweight read-mostly API for the dashboard frontend.

This is intentionally a SEPARATE service from agent-server: agent-server only
speaks the Unix Domain Socket protocol used by agent-watcher, and shouldn't be
made to also juggle HTTP concerns. This process only reads from the same
bind-mounted volumes (categories/, snapshots/, run/mempalace_db/) and shells
out to the mempalace CLI exactly like query.py does — it never writes to the
ingestion pipeline's state.

Run with:
    uvicorn api_server:app --host 0.0.0.0 --port 8420
"""

import json
import os
import re
import subprocess
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from ollama import AsyncClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CATEGORIES_DIR = os.path.join(PROJECT_ROOT, "categories")
SNAPSHOTS_DIR = os.path.join(PROJECT_ROOT, "snapshots")
PALACE_DIR = os.path.join(PROJECT_ROOT, "run/mempalace_db")
MODEL_NAME = "gemma4:e4b"

app = FastAPI(title="Field Log API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the frontend's real origin before exposing this beyond localhost
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

async_client = AsyncClient()


# --------------------------------------------------------------------------
# Helpers — all read-only, mirroring the conventions server.py/query.py use
# --------------------------------------------------------------------------

def _wing_dir(wing: str) -> str:
    path = os.path.join(CATEGORIES_DIR, wing)
    if not os.path.isdir(path):
        raise HTTPException(status_code=404, detail=f"No such wing: {wing}")
    return path


def _find_baseline(wing: str) -> Optional[str]:
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        candidate = os.path.join(CATEGORIES_DIR, wing, f"baseline{ext}")
        if os.path.exists(candidate):
            return candidate
    return None


def _find_processed(wing: str) -> Optional[str]:
    candidate = os.path.join(CATEGORIES_DIR, wing, "processed.jpg")
    return candidate if os.path.exists(candidate) else None


def _latest_snapshot_analysis(wing: str) -> Optional[dict]:
    """Returns the most recent snapshot's analytics_conclusion.json content, if any."""
    wing_snap_dir = os.path.join(SNAPSHOTS_DIR, wing)
    if not os.path.isdir(wing_snap_dir):
        return None
    dates = sorted(os.listdir(wing_snap_dir), reverse=True)
    for date in dates:
        date_dir = os.path.join(wing_snap_dir, date)
        if not os.path.isdir(date_dir):
            continue
        times = sorted(os.listdir(date_dir), reverse=True)
        for time_str in times:
            time_dir = os.path.join(date_dir, time_str)
            conclusion_path = os.path.join(time_dir, "analytics_conclusion.json")
            if os.path.exists(conclusion_path):
                with open(conclusion_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["_date"] = date
                data["_time"] = time_str
                return data
    return None


def _parse_history(wing: str, max_entries: int = 100):
    """Splits categories/<wing>/history.md into {timestamp, text} entries."""
    history_path = os.path.join(CATEGORIES_DIR, wing, "history.md")
    if not os.path.exists(history_path):
        return []
    with open(history_path, "r", encoding="utf-8") as f:
        content = f.read()

    entries = []
    for match in re.finditer(
        r"^## (.+?)\n\n(.+?)(?=\n## |\Z)", content, re.DOTALL | re.MULTILINE
    ):
        timestamp, text = match.group(1).strip(), match.group(2).strip()
        entries.append({"timestamp": timestamp, "text": text})
    return list(reversed(entries))[:max_entries]


def _run_mempalace(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["mempalace"] + args,
            cwd=PALACE_DIR,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=502, detail=f"mempalace error: {e.stderr.strip() if e.stderr else str(e)}"
        )


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@app.get("/api/wings")
def list_wings():
    if not os.path.isdir(CATEGORIES_DIR):
        return []
    wings = []
    for name in sorted(os.listdir(CATEGORIES_DIR)):
        wing_path = os.path.join(CATEGORIES_DIR, name)
        if not os.path.isdir(wing_path):
            continue
        processed = _find_processed(name)
        latest = _latest_snapshot_analysis(name)
        wings.append(
            {
                "wing": name,
                "has_baseline": _find_baseline(name) is not None,
                "last_processed_at": (
                    datetime.fromtimestamp(os.path.getmtime(processed)).isoformat()
                    if processed
                    else None
                ),
                "drift_detected": (
                    latest.get("environmental_drift_detected") if latest else None
                ),
            }
        )
    return wings


@app.get("/api/wings/{wing}/summary")
def wing_summary(wing: str):
    _wing_dir(wing)
    latest = _latest_snapshot_analysis(wing)
    return {
        "wing": wing,
        "has_baseline": _find_baseline(wing) is not None,
        "has_processed": _find_processed(wing) is not None,
        "latest_analysis": latest,
    }


@app.get("/api/wings/{wing}/timeline")
def wing_timeline(wing: str, limit: int = 50):
    _wing_dir(wing)
    wing_snap_dir = os.path.join(SNAPSHOTS_DIR, wing)
    if not os.path.isdir(wing_snap_dir):
        return []

    entries = []
    for date in sorted(os.listdir(wing_snap_dir), reverse=True):
        date_dir = os.path.join(wing_snap_dir, date)
        if not os.path.isdir(date_dir):
            continue
        for time_str in sorted(os.listdir(date_dir), reverse=True):
            time_dir = os.path.join(date_dir, time_str)
            conclusion_path = os.path.join(time_dir, "analytics_conclusion.json")
            if not os.path.exists(conclusion_path):
                continue
            with open(conclusion_path, "r", encoding="utf-8") as f:
                analysis = json.load(f)
            image_files = [
                fn for fn in os.listdir(time_dir) if fn.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
            entries.append(
                {
                    "date": date,
                    "time": time_str,
                    "drift_detected": analysis.get("environmental_drift_detected", False),
                    "detailed_log": analysis.get("detailed_log", ""),
                    "human_count": analysis.get("metrics", {}).get("human_density_count", 0),
                    "image_url": (
                        f"/api/wings/{wing}/snapshot/{date}/{time_str}/{image_files[0]}"
                        if image_files
                        else None
                    ),
                }
            )
            if len(entries) >= limit:
                return entries
    return entries


@app.get("/api/wings/{wing}/history")
def wing_history(wing: str):
    _wing_dir(wing)
    return _parse_history(wing)


@app.get("/api/wings/{wing}/image/baseline")
def wing_baseline_image(wing: str):
    path = _find_baseline(wing)
    if not path:
        raise HTTPException(status_code=404, detail="No baseline image set for this wing")
    return FileResponse(path)


@app.get("/api/wings/{wing}/image/processed")
def wing_processed_image(wing: str):
    path = _find_processed(wing)
    if not path:
        raise HTTPException(status_code=404, detail="No processed frame recorded yet")
    return FileResponse(path)


@app.get("/api/wings/{wing}/snapshot/{date}/{time}/{filename}")
def wing_snapshot_image(wing: str, date: str, time: str, filename: str):
    path = os.path.join(SNAPSHOTS_DIR, wing, date, time, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return FileResponse(path)


class QueryRequest(BaseModel):
    wing: str
    room: Optional[str] = None
    question: str


@app.post("/api/query")
async def query(req: QueryRequest):
    _wing_dir(req.wing)
    cmd = ["search", req.question, "--wing", req.wing]
    if req.room:
        cmd += ["--room", req.room]
    context_str = _run_mempalace(cmd)

    prompt = f"""
    You are answering a quick factual question about historical camera logs.

    LOG MEMORIES RECOVERED:
    {context_str}

    QUESTION:
    {req.question}

    Answer in 2-4 plain, everyday sentences. No headers, no markdown, no
    bullet points, no filler phrases like "based on the analysis." If the
    recovered memories don't answer the question, say so in one sentence.
    """
    response = await async_client.generate(model=MODEL_NAME, prompt=prompt)
    return {"answer": response["response"].strip()}


@app.get("/api/status")
def status():
    raw = _run_mempalace(["status"])
    drawer_counts = dict(re.findall(r"^\s*(\S+)\s+(\d+) files\s*$", raw, re.MULTILINE))
    return {"raw": raw, "by_room": drawer_counts}


@app.get("/api/health")
def health():
    return {
        "categories_dir_exists": os.path.isdir(CATEGORIES_DIR),
        "palace_dir_exists": os.path.isdir(PALACE_DIR),
    }
