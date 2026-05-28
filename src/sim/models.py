"""
Data models for the DEFCON-inspired simulation.
Defines the state structures for factions, cities, silos, missiles, and match state.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from enum import Enum
import json


class FactionStatus(Enum):
    ACTIVE = "active"
    CRIPPLED = "crippled"
    ELIMINATED = "eliminated"


class LifecycleState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


class ActionType(Enum):
    HOLD = "hold"
    LAUNCH = "launch"


class EntityType(Enum):
    CITY = "city"
    SILO = "silo"


class MissileStatus(Enum):
    FLYING = "flying"
    IMPACT = "impact"
    EXPIRED = "expired"


@dataclass
class Position:
    x: int
    y: int


@dataclass
class Node:
    id: str
    name: str
    owner: str  # faction ID
    type: EntityType
    position: Position
    hp: int
    # For cities: population, for silos: ammo
    population: int = 0
    ammo: int = 0
    cooldown: int = 0
    status: str = "active"  # active/destroyed

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "owner": self.owner,
            "type": self.type.value,
            "x": self.position.x,
            "y": self.position.y,
            "hp": self.hp,
            "population": self.population,
            "ammo": self.ammo,
            "cooldown": self.cooldown,
            "status": self.status
        }


@dataclass
class Missile:
    id: str
    owner: str  # faction ID
    source_node_id: str
    target_node_id: str
    launch_tick: int
    impact_tick: int
    current_position: Position
    status: MissileStatus = MissileStatus.FLYING

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner": self.owner,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "launch_tick": self.launch_tick,
            "impact_tick": self.impact_tick,
            "current_position": {
                "x": self.current_position.x,
                "y": self.current_position.y
            },
            "status": self.status.value
        }


@dataclass
class Faction:
    id: str
    name: str
    color: str
    population: int
    score: int
    status: FactionStatus
    control_mode: str  # scripted, agent, human-debug
    last_action: Optional[dict] = None
    owned_sites: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "population": self.population,
            "score": self.score,
            "status": self.status.value,
            "control_mode": self.control_mode,
            "last_action": self.last_action,
            "owned_sites": self.owned_sites
        }


@dataclass
class Event:
    tick: int
    type: str  # launch, impact, destruction, invalid_action, match_start, match_end, etc.
    faction_id: Optional[str] = None
    missile_id: Optional[str] = None
    source_node_id: Optional[str] = None
    target_node_id: Optional[str] = None
    damage: int = 0
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "tick": self.tick,
            "type": self.type,
            "faction_id": self.faction_id,
            "missile_id": self.missile_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "damage": self.damage,
            "details": self.details
        }


@dataclass
class MatchState:
    match_id: str
    tick: int
    time_remaining_sec: int
    lifecycle_state: LifecycleState
    factions: Dict[str, Faction] = field(default_factory=dict)
    nodes: Dict[str, Node] = field(default_factory=dict)
    missiles: Dict[str, Missile] = field(default_factory=dict)
    events: List[Event] = field(default_factory=list)
    snapshot_tick: int = 0  # for replay snapshots

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "tick": self.tick,
            "time_remaining_sec": self.time_remaining_sec,
            "lifecycle_state": self.lifecycle_state.value,
            "factions": {fid: faction.to_dict() for fid, faction in self.factions.items()},
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "missiles": {mid: missile.to_dict() for mid, missile in self.missiles.items()},
            "events": [event.to_dict() for event in self.events],
            "snapshot_tick": self.snapshot_tick
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MatchState':
        # Simplified deserialization - in practice would need proper enum handling
        match_state = cls(
            match_id=data["match_id"],
            tick=data["tick"],
            time_remaining_sec=data["time_remaining_sec"],
            lifecycle_state=LifecycleState(data["lifecycle_state"]),
            snapshot_tick=data.get("snapshot_tick", 0)
        )
        
        # Reconstruct factions
        for fid, faction_data in data["factions"].items():
            match_state.factions[fid] = Faction(
                id=faction_data["id"],
                name=faction_data["name"],
                color=faction_data["color"],
                population=faction_data["population"],
                score=faction_data["score"],
                status=FactionStatus(faction_data["status"]),
                control_mode=faction_data["control_mode"],
                last_action=faction_data.get("last_action"),
                owned_sites=faction_data.get("owned_sites", [])
            )
        
        # Reconstruct nodes
        for nid, node_data in data["nodes"].items():
            match_state.nodes[nid] = Node(
                id=node_data["id"],
                name=node_data["name"],
                owner=node_data["owner"],
                type=EntityType(node_data["type"]),
                position=Position(x=node_data["x"], y=node_data["y"]),
                hp=node_data["hp"],
                population=node_data.get("population", 0),
                ammo=node_data.get("ammo", 0),
                cooldown=node_data.get("cooldown", 0),
                status=node_data.get("status", "active")
            )
        
        # Reconstruct missiles
        for mid, missile_data in data["missiles"].items():
            match_state.missiles[mid] = Missile(
                id=missile_data["id"],
                owner=missile_data["owner"],
                source_node_id=missile_data["source_node_id"],
                target_node_id=missile_data["target_node_id"],
                launch_tick=missile_data["launch_tick"],
                impact_tick=missile_data["impact_tick"],
                current_position=Position(
                    x=missile_data["current_position"]["x"],
                    y=missile_data["current_position"]["y"]
                ),
                status=MissileStatus(missile_data["status"])
            )
        
        # Reconstruct events
        for event_data in data["events"]:
            match_state.events.append(Event(
                tick=event_data["tick"],
                type=event_data["type"],
                faction_id=event_data.get("faction_id"),
                missile_id=event_data.get("missile_id"),
                source_node_id=event_data.get("source_node_id"),
                target_node_id=event_data.get("target_node_id"),
                damage=event_data.get("damage", 0),
                details=event_data.get("details", {})
            ))
        
        return match_state


# MVP Constants - frozen per SPEC.md and phase-0-scope.md
class Constants:
    # Match timing
    MATCH_DURATION_SEC = 300  # 5 minutes
    TICK_MS = 250  # 250ms per tick
    TICKS_PER_SEC = 1000 // TICK_MS  # 4 ticks per second
    DECISION_WINDOW_TICKS = 16  # every 16 ticks (4 seconds)
    MISSILE_FLIGHT_TIME_TICKS = 32  # 8 seconds at 250ms/tick
    
    # Combat values
    CITY_HP = 100
    SILO_HP = 100
    MISSILE_DAMAGE = 100  # one-hit destruction
    
    # Initial values
    INITIAL_CITY_POPULATION = 100
    INITIAL_SILO_AMMO = 6
    
    # Faction setup
    NUM_FACTIONS = 4
    CITIES_PER_FACTION = 2
    SILOS_PER_FACTION = 1
    
    # Faction IDs and colors
    FACTION_CONFIGS = [
        {"id": "red", "name": "Red Directorate", "color": "#ff4d5a"},
        {"id": "blue", "name": "Blue Confederation", "color": "#4d79ff"},
        {"id": "green", "name": "Green Collective", "color": "#4dff88"},
        {"id": "yellow", "name": "Yellow Republic", "color": "#ffeb4d"}
    ]
    
    # Map coordinates (stylized fixed positions)
    MAP_COORDINATES = {
        # Red faction
        "red-city-1": {"name": "Red Capital", "x": 200, "y": 200},
        "red-city-2": {"name": "Red Industrial", "x": 250, "y": 350},
        "red-silo-1": {"name": "Red Silo", "x": 150, "y": 300},
        
        # Blue faction
        "blue-city-1": {"name": "Blue Capital", "x": 600, "y": 200},
        "blue-city-2": {"name": "Blue Industrial", "x": 550, "y": 350},
        "blue-silo-1": {"name": "Blue Silo", "x": 650, "y": 300},
        
        # Green faction
        "green-city-1": {"name": "Green Capital", "x": 400, "y": 500},
        "green-city-2": {"name": "Green Industrial", "x": 450, "y": 350},
        "green-silo-1": {"name": "Green Silo", "x": 350, "y": 400},
        
        # Yellow faction
        "yellow-city-1": {"name": "Yellow Capital", "x": 200, "y": 400},
        "yellow-city-2": {"name": "Yellow Industrial", "x": 250, "y": 250},
        "yellow-silo-1": {"name": "Yellow Silo", "x": 150, "y": 350}
    }