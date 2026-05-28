"""
Spectator API - Backend service exposing simulation state to the observer UI.
"""

import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .fixtures import (
    create_finished_state,
    create_idle_state,
    create_mock_match_state,
    create_mock_replay,
    create_paused_state,
)


class LifecycleAction(BaseModel):
    """Request model for lifecycle actions."""


match_state = create_idle_state()
match_history: list[dict[str, Any]] = []
_match_counter = 0


def serialize_state() -> dict[str, Any]:
    """Return current match state serialized for spectators."""
    return match_state


def transition_to_running() -> dict[str, Any]:
    """Start a new match from idle or finished state."""
    global match_state, match_history, _match_counter
    _match_counter += 1
    match_state = create_mock_match_state()
    match_state["match"]["matchId"] = f"match-{_match_counter:03d}"
    match_state["match"]["startedAt"] = datetime.utcnow().isoformat() + "Z"
    match_history = []
    return match_state


def transition_to_paused() -> dict[str, Any]:
    """Pause a running match."""
    global match_state
    if match_state["match"]["lifecycleState"] != "running":
        raise HTTPException(status_code=400, detail="Can only pause a running match")
    match_state = create_paused_state()
    return match_state


def transition_to_resumed() -> dict[str, Any]:
    """Resume a paused match."""
    global match_state
    if match_state["match"]["lifecycleState"] != "paused":
        raise HTTPException(status_code=400, detail="Can only resume a paused match")
    match_state = create_mock_match_state()
    return match_state


def transition_to_idle() -> dict[str, Any]:
    """Reset to idle state from any state."""
    global match_state, match_history
    match_state = create_idle_state()
    match_history = []
    return match_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global match_state
    match_state = create_idle_state()
    yield


app = FastAPI(title="DEFCON Spectator API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/state")
async def get_state() -> dict[str, Any]:
    """
    Get current spectator state.
    
    Returns complete match state including:
    - match metadata (id, lifecycle, tick, time remaining)
    - factions (population, score, status, control mode)
    - nodes (cities, silos with positions and status)
    - missiles in flight
    - recent events
    - summary metrics
    """
    return serialize_state()


@app.post("/api/start")
async def start_match(action: LifecycleAction) -> dict[str, Any]:
    """
    Start a new match.
    
    Valid from: idle, finished
    Creates new match with new matchId.
    """
    return transition_to_running()


@app.post("/api/pause")
async def pause_match(action: LifecycleAction) -> dict[str, Any]:
    """
    Pause the current match.
    
    Valid from: running only
    """
    return transition_to_paused()


@app.post("/api/resume")
async def resume_match(action: LifecycleAction) -> dict[str, Any]:
    """
    Resume a paused match.
    
    Valid from: paused only
    """
    return transition_to_resumed()


@app.post("/api/reset")
async def reset_match(action: LifecycleAction) -> dict[str, Any]:
    """
    Reset to fresh idle match.
    
    Valid from: any state
    Creates fresh match using default scenario.
    """
    return transition_to_idle()


@app.get("/api/replay/latest")
async def get_latest_replay() -> dict[str, Any]:
    """
    Get latest match replay.
    
    Returns:
    - match metadata
    - ordered event log
    - periodic snapshots (every 4 ticks)
    - final state
    """
    return create_mock_replay()


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def serve_ui() -> FileResponse:
    """Serve the observer UI."""
    return FileResponse("web/index.html")


app.mount("/static", StaticFiles(directory="web"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)