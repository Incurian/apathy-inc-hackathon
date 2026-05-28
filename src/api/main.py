"""
Spectator API - Backend service exposing simulation state to the observer UI.
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.sim.engine import get_engine


class LifecycleAction(BaseModel):
    """Request model for lifecycle actions."""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    engine = get_engine()
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
    engine = get_engine()
    return engine.get_state()


@app.post("/api/start")
async def start_match(action: LifecycleAction) -> dict[str, Any]:
    """
    Start a new match.
    
    Valid from: idle, finished
    Creates new match with new matchId.
    """
    engine = get_engine()
    return engine.start_match()


@app.post("/api/pause")
async def pause_match(action: LifecycleAction) -> dict[str, Any]:
    """
    Pause the current match.
    
    Valid from: running only
    """
    engine = get_engine()
    try:
        return engine.pause_match()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/resume")
async def resume_match(action: LifecycleAction) -> dict[str, Any]:
    """
    Resume a paused match.
    
    Valid from: paused only
    """
    engine = get_engine()
    try:
        return engine.resume_match()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/reset")
async def reset_match(action: LifecycleAction) -> dict[str, Any]:
    """
    Reset to fresh idle match.
    
    Valid from: any state
    Creates fresh match using default scenario.
    """
    engine = get_engine()
    return engine.reset_match()


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
    from src.api.fixtures import create_mock_replay
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