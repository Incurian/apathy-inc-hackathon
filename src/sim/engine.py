"""
Deterministic simulation engine for DEFCON Spectator.
"""

import time
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from enum import Enum


class LifecycleState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


class NodeType(str, Enum):
    CITY = "city"
    SILO = "silo"


class NodeStatus(str, Enum):
    ACTIVE = "active"
    DAMAGED = "damaged"
    DESTROYED = "destroyed"


class FactionStatus(str, Enum):
    ACTIVE = "active"
    CRIPPLED = "crippled"
    ELIMINATED = "eliminated"


class ControlMode(str, Enum):
    AGENT = "agent"
    SCRIPTED = "scripted"


class MissileStatus(str, Enum):
    FLYING = "flying"
    IMPACT = "impact"


@dataclass
class Faction:
    id: str
    name: str
    color: str
    population: int = 200
    score: int = 150
    status: FactionStatus = FactionStatus.ACTIVE
    control_mode: ControlMode = ControlMode.SCRIPTED
    sites: list[str] = field(default_factory=list)
    last_action: dict | None = None
    invalid_action_count: int = 0


@dataclass
class Node:
    id: str
    name: str
    owner: str
    type: NodeType
    x: float
    y: float
    hp: int = 100
    population: int = 0
    ammo: int = 0
    cooldown: int = 0
    status: NodeStatus = NodeStatus.ACTIVE
    last_launch_tick: int | None = None
    incoming_missiles: int = 0


@dataclass
class Missile:
    id: str
    owner: str
    source: str
    target: str
    launch_tick: int
    impact_tick: int
    current_tick: int
    progress: float
    status: MissileStatus
    x: float
    y: float


@dataclass
class Event:
    tick: int
    time: str
    type: str
    data: dict = field(default_factory=dict)


@dataclass
class Match:
    match_id: str | None = None
    lifecycle_state: LifecycleState = LifecycleState.IDLE
    tick: int = 0
    time_remaining_sec: float = 300.0
    started_at: str | None = None
    scenario: str = "canonical-4-faction"


@dataclass
class Summary:
    leading_faction: str | None = None
    total_missiles_in_flight: int = 0
    active_factions: int = 4
    crippled_factions: int = 0
    eliminated_factions: int = 0


@dataclass
class SimulationState:
    match: Match = field(default_factory=Match)
    factions: list[Faction] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)
    missiles: list[Missile] = field(default_factory=list)
    recent_events: list[dict] = field(default_factory=list)
    summary: Summary = field(default_factory=Summary)


TICK_RATE = 4
MATCH_DURATION_TICKS = 1200
MISSILE_FLIGHT_TICKS = 32


def create_initial_state() -> SimulationState:
    factions = [
        Faction("red", "Red Directorate", "#ff4d5a", control_mode=ControlMode.AGENT,
                sites=["red-city-1", "red-city-2", "red-silo-1"]),
        Faction("blue", "Blue Alliance", "#4d8cff", control_mode=ControlMode.SCRIPTED,
                sites=["blue-city-1", "blue-city-2", "blue-silo-1"]),
        Faction("green", "Green Collective", "#4dcc5a", control_mode=ControlMode.SCRIPTED,
                sites=["green-city-1", "green-city-2", "green-silo-1"]),
        Faction("yellow", "Yellow Dominion", "#ffcc00", control_mode=ControlMode.SCRIPTED,
                sites=["yellow-city-1", "yellow-city-2", "yellow-silo-1"]),
    ]

    nodes = [
        Node("red-city-1", "Red Capital", "red", NodeType.CITY, 150, 200, population=100),
        Node("red-city-2", "Red Industrial", "red", NodeType.CITY, 200, 300, population=100),
        Node("red-silo-1", "Red Silo Alpha", "red", NodeType.SILO, 175, 250, ammo=6),
        Node("blue-city-1", "Blue Capital", "blue", NodeType.CITY, 650, 200, population=100),
        Node("blue-city-2", "Blue Industrial", "blue", NodeType.CITY, 700, 300, population=100),
        Node("blue-silo-1", "Blue Silo Alpha", "blue", NodeType.SILO, 675, 250, ammo=6),
        Node("green-city-1", "Green Capital", "green", NodeType.CITY, 400, 100, population=100),
        Node("green-city-2", "Green Industrial", "green", NodeType.CITY, 450, 180, population=100),
        Node("green-silo-1", "Green Silo Alpha", "green", NodeType.SILO, 425, 140, ammo=6),
        Node("yellow-city-1", "Yellow Capital", "yellow", NodeType.CITY, 400, 400, population=100),
        Node("yellow-city-2", "Yellow Industrial", "yellow", NodeType.CITY, 450, 480, population=100),
        Node("yellow-silo-1", "Yellow Silo Alpha", "yellow", NodeType.SILO, 425, 440, ammo=6),
    ]

    return SimulationState(
        match=Match(),
        factions=factions,
        nodes=nodes,
        missiles=[],
        recent_events=[{
            "tick": 0,
            "time": datetime.utcnow().isoformat() + "Z",
            "type": "match_created",
            "message": "Match created, waiting to start"
        }],
        summary=Summary()
    )


def serialize_state(state: SimulationState) -> dict[str, Any]:
    return {
        "match": {
            "matchId": state.match.match_id,
            "lifecycleState": state.match.lifecycle_state.value,
            "tick": state.match.tick,
            "timeRemainingSec": state.match.time_remaining_sec,
            "startedAt": state.match.started_at,
            "scenario": state.match.scenario,
        },
        "factions": [{
            "id": f.id,
            "name": f.name,
            "color": f.color,
            "population": f.population,
            "score": f.score,
            "status": f.status.value,
            "controlMode": f.control_mode.value,
            "sites": f.sites,
            "lastAction": f.last_action,
            "invalidActionCount": f.invalid_action_count,
        } for f in state.factions],
        "nodes": [{
            "id": n.id,
            "name": n.name,
            "owner": n.owner,
            "type": n.type.value,
            "x": n.x,
            "y": n.y,
            "hp": n.hp,
            "population": n.population,
            "ammo": n.ammo,
            "cooldown": n.cooldown,
            "status": n.status.value,
            "lastLaunchTick": n.last_launch_tick,
            "incomingMissiles": n.incoming_missiles,
        } for n in state.nodes],
        "missiles": [{
            "id": m.id,
            "owner": m.owner,
            "source": m.source,
            "target": m.target,
            "launchTick": m.launch_tick,
            "impactTick": m.impact_tick,
            "currentTick": m.current_tick,
            "progress": m.progress,
            "status": m.status.value,
            "x": m.x,
            "y": m.y,
        } for m in state.missiles],
        "recentEvents": state.recent_events[-50:],
        "summary": {
            "leadingFaction": state.summary.leading_faction,
            "totalMissilesInFlight": state.summary.total_missiles_in_flight,
            "activeFactions": state.summary.active_factions,
            "crippledFactions": state.summary.crippled_factions,
            "eliminatedFactions": state.summary.eliminated_factions,
        }
    }


class SimulationEngine:
    def __init__(self):
        self.state = create_initial_state()
        self._lock = threading.RLock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._tick_accumulator = 0.0
        self._last_update = time.time()

    def start_match(self) -> dict[str, Any]:
        with self._lock:
            if self.state.match.lifecycle_state in (LifecycleState.RUNNING,):
                return serialize_state(self.state)

            self.state = create_initial_state()
            self.state.match.match_id = f"match-{uuid.uuid4().hex[:6]}"
            self.state.match.lifecycle_state = LifecycleState.RUNNING
            self.state.match.tick = 0
            self.state.match.time_remaining_sec = 300.0
            self.state.match.started_at = datetime.utcnow().isoformat() + "Z"
            self.state.recent_events.append({
                "tick": 0,
                "time": datetime.utcnow().isoformat() + "Z",
                "type": "match_start",
                "matchId": self.state.match.match_id,
            })
            self._running = True
            self._last_update = time.time()
            if not self._thread or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()
            return serialize_state(self.state)

    def pause_match(self) -> dict[str, Any]:
        with self._lock:
            if self.state.match.lifecycle_state != LifecycleState.RUNNING:
                raise ValueError("Can only pause a running match")
            self.state.match.lifecycle_state = LifecycleState.PAUSED
            self.state.recent_events.append({
                "tick": self.state.match.tick,
                "time": datetime.utcnow().isoformat() + "Z",
                "type": "match_paused",
                "message": "Match paused by operator",
            })
            self._running = False
            return serialize_state(self.state)

    def resume_match(self) -> dict[str, Any]:
        with self._lock:
            if self.state.match.lifecycle_state != LifecycleState.PAUSED:
                raise ValueError("Can only resume a paused match")
            self.state.match.lifecycle_state = LifecycleState.RUNNING
            self._running = True
            self._last_update = time.time()
            return serialize_state(self.state)

    def reset_match(self) -> dict[str, Any]:
        with self._lock:
            self.state = create_initial_state()
            self._running = False
            return serialize_state(self.state)

    def get_state(self) -> dict[str, Any]:
        with self._lock:
            return serialize_state(self.state)

    def _run_loop(self):
        while self._running:
            now = time.time()
            dt = now - self._last_update
            self._last_update = now
            self._tick_accumulator += dt * TICK_RATE

            ticks_to_process = int(self._tick_accumulator)
            if ticks_to_process > 0:
                self._tick_accumulator -= ticks_to_process
                with self._lock:
                    for _ in range(ticks_to_process):
                        self._step()

            time.sleep(0.05)

    def _step(self):
        if self.state.match.lifecycle_state != LifecycleState.RUNNING:
            return

        self.state.match.tick += 1
        self.state.match.time_remaining_sec = max(0, 300.0 - (self.state.match.tick / TICK_RATE))

        self._update_missiles()
        self._update_nodes()
        self._update_factions()
        self._update_summary()

        if self.state.match.tick >= MATCH_DURATION_TICKS or self.state.summary.active_factions <= 1:
            self._end_match()

    def _update_missiles(self):
        new_missiles = []
        for missile in self.state.missiles:
            missile.current_tick = self.state.match.tick
            missile.progress = (missile.current_tick - missile.launch_tick) / MISSILE_FLIGHT_TICKS

            if missile.current_tick >= missile.impact_tick:
                missile.status = MissileStatus.IMPACT
                self._process_impact(missile)
            else:
                source_node = next((n for n in self.state.nodes if n.id == missile.source), None)
                target_node = next((n for n in self.state.nodes if n.id == missile.target), None)
                if source_node and target_node:
                    missile.x = source_node.x + (target_node.x - source_node.x) * missile.progress
                    missile.y = source_node.y + (target_node.y - source_node.y) * missile.progress
                new_missiles.append(missile)

        self.state.missiles = new_missiles

    def _process_impact(self, missile: Missile):
        target_node = next((n for n in self.state.nodes if n.id == missile.target), None)
        if not target_node:
            return

        damage = 100
        target_node.hp = max(0, target_node.hp - damage)
        target_node.incoming_missiles = max(0, target_node.incoming_missiles - 1)

        faction = next((f for f in self.state.factions if f.id == target_node.owner), None)

        self.state.recent_events.append({
            "tick": self.state.match.tick,
            "time": datetime.utcnow().isoformat() + "Z",
            "type": "impact",
            "faction": missile.owner,
            "target": missile.target,
            "damage": damage,
            "destroyed": target_node.hp <= 0,
            "missileId": missile.id,
        })

        if target_node.hp <= 0:
            target_node.status = NodeStatus.DESTROYED
            if target_node.type == NodeType.CITY:
                target_node.population = 0
                if faction:
                    faction.population = max(0, faction.population - 100)
            self.state.recent_events.append({
                "tick": self.state.match.tick,
                "time": datetime.utcnow().isoformat() + "Z",
                "type": "destruction",
                "faction": target_node.owner,
                "target": missile.target,
                "targetType": target_node.type.value,
            })

    def _update_nodes(self):
        for node in self.state.nodes:
            node.incoming_missiles = sum(1 for m in self.state.missiles if m.target == node.id and m.status == MissileStatus.FLYING)
            if node.hp <= 0:
                node.status = NodeStatus.DESTROYED
            elif node.hp < 100:
                node.status = NodeStatus.DAMAGED
            else:
                node.status = NodeStatus.ACTIVE

            if node.type == NodeType.SILO and node.cooldown > 0:
                node.cooldown -= 1

    def _update_factions(self):
        for faction in self.state.factions:
            faction_sites = [n for n in self.state.nodes if n.id in faction.sites]
            active_silos = [n for n in faction_sites if n.type == NodeType.SILO and n.status != NodeStatus.DESTROYED]
            active_cities = [n for n in faction_sites if n.type == NodeType.CITY and n.status != NodeStatus.DESTROYED]

            faction.sites = [n.id for n in faction_sites if n.status != NodeStatus.DESTROYED]

            if len(active_cities) == 0:
                faction.status = FactionStatus.ELIMINATED
            elif len(active_silos) == 0:
                faction.status = FactionStatus.CRIPPLED
            else:
                faction.status = FactionStatus.ACTIVE

    def _update_summary(self):
        active = sum(1 for f in self.state.factions if f.status == FactionStatus.ACTIVE)
        crippled = sum(1 for f in self.state.factions if f.status == FactionStatus.CRIPPLED)
        eliminated = sum(1 for f in self.state.factions if f.status == FactionStatus.ELIMINATED)

        leading = max(self.state.factions, key=lambda f: f.score, default=None)

        self.state.summary = Summary(
            leading_faction=leading.id if leading else None,
            total_missiles_in_flight=len([m for m in self.state.missiles if m.status == MissileStatus.FLYING]),
            active_factions=active,
            crippled_factions=crippled,
            eliminated_factions=eliminated,
        )

    def _end_match(self):
        self.state.match.lifecycle_state = LifecycleState.FINISHED
        self.state.match.time_remaining_sec = 0
        winner = max(self.state.factions, key=lambda f: f.score, default=None)
        self.state.recent_events.append({
            "tick": self.state.match.tick,
            "time": datetime.utcnow().isoformat() + "Z",
            "type": "match_end",
            "winner": winner.id if winner else None,
            "message": f"Match complete - {winner.name if winner else 'No one'} wins",
        })
        self._running = False


_simulation_engine: SimulationEngine | None = None


def get_engine() -> SimulationEngine:
    global _simulation_engine
    if _simulation_engine is None:
        _simulation_engine = SimulationEngine()
    return _simulation_engine