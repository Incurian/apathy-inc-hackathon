"""
Pydantic models for agent adapter observation and action schemas.
Based on SPEC.md Section 14: Agent Player Interface.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class Site(BaseModel):
    """Represents a city, silo, or defense site."""
    id: str
    type: Literal["city", "silo", "defense_site"]
    owner: str
    x: int
    y: int
    hp: int
    population: Optional[int] = None  # For cities
    ammo: Optional[int] = None        # For silos
    cooldown: Optional[int] = None    # For silos
    active: bool = True
    status: Optional[str] = None      # For MVP, can be "active"/"destroyed"


class FactionState(BaseModel):
    """State of a single faction."""
    id: str
    population: int
    score: int
    status: Literal["active", "crippled", "eliminated"]
    sites: List[Site]


class WorldFaction(BaseModel):
    """Minimal faction info for world view."""
    id: str
    status: Literal["active", "crippled", "eliminated"]
    population: int
    score: int


class Target(BaseModel):
    """A target that can be attacked (city or silo)."""
    id: str
    owner: str
    type: Literal["city", "silo"]
    hp: int
    value: int


class Missile(BaseModel):
    """A missile in flight."""
    id: str
    owner: str
    source: str  # silo ID
    target: str  # city or silo ID
    etaSec: int  # seconds until impact


class Event(BaseModel):
    """A game event."""
    tick: int
    type: Literal["launch", "impact", "destruction", "invalid_action"]
    target: str
    damage: Optional[int] = None
    factionId: Optional[str] = None
    action: Optional[dict] = None  # For invalid actions
    errorReason: Optional[str] = None  # For invalid actions


class LegalAction(BaseModel):
    """A legal action available to the faction."""
    type: Literal["hold", "launch"]
    from_: Optional[str] = Field(None, alias="from")  # silo ID for launch
    allowedTargets: Optional[List[str]] = None  # For launch actions

    class Config:
        populate_by_name = True


class Observation(BaseModel):
    """
    The observation payload provided to an agent for its turn.
    Based on SPEC.md lines 423-458.
    """
    match: dict = Field(..., example={
        "matchId": "match-001",
        "tick": 120,
        "timeRemainingSec": 214
    })
    self: FactionState
    world: dict = Field(..., example={
        "factions": [
            {"id": "blue", "status": "active", "population": 180, "score": 120}
        ],
        "targets": [
            {"id": "blue-city-1", "owner": "blue", "type": "city", "hp": 100, "value": 100},
            {"id": "blue-silo-1", "owner": "blue", "type": "silo", "hp": 100, "value": 25}
        ],
        "missiles": [
            {"id": "m-14", "owner": "green", "target": "red-city-2", "etaSec": 4}
        ]
    })
    recentEvents: List[Event]
    legalActions: List[LegalAction]


class Action(BaseModel):
    """
    The action payload returned by an agent.
    MVP has exactly one top-level `action`, not an array.
    Based on SPEC.md action response shape.
    """
    action: dict
    comment: Optional[str] = None

    @field_validator('action')
    @classmethod
    def validate_action_structure(cls, v):
        """Ensure action has correct structure."""
        if not isinstance(v, dict):
            raise ValueError("Action must be a dictionary")
        if "type" not in v:
            raise ValueError("Action must have a 'type' field")
        if v["type"] == "hold":
            if len(v) != 1:
                raise ValueError("Hold action must only contain 'type' field")
        elif v["type"] == "launch":
            required_fields = {"type", "from", "target"}
            if set(v.keys()) != required_fields:
                raise ValueError(f"Launch action must contain exactly {required_fields}")
            if not isinstance(v["from"], str) or not isinstance(v["target"], str):
                raise ValueError("Launch 'from' and 'target' must be strings")
        else:
            raise ValueError("Action type must be 'hold' or 'launch'")
        return v