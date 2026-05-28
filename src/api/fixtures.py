"""
State fixtures for different lifecycle states.
Used for testing and UI development before simulation is integrated.
"""

from typing import Any


def create_base_factions() -> list[dict[str, Any]]:
    """Create the four canonical factions."""
    return [
        {
            "id": "red",
            "name": "Red Directorate",
            "color": "#ff4d5a",
            "population": 200,
            "score": 150,
            "status": "active",
            "controlMode": "agent",
            "sites": ["red-city-1", "red-city-2", "red-silo-1"],
            "lastAction": None,
            "invalidActionCount": 0,
        },
        {
            "id": "blue",
            "name": "Blue Alliance",
            "color": "#4d8cff",
            "population": 200,
            "score": 150,
            "status": "active",
            "controlMode": "scripted",
            "sites": ["blue-city-1", "blue-city-2", "blue-silo-1"],
            "lastAction": None,
            "invalidActionCount": 0,
        },
        {
            "id": "green",
            "name": "Green Collective",
            "color": "#4dcc5a",
            "population": 200,
            "score": 150,
            "status": "active",
            "controlMode": "scripted",
            "sites": ["green-city-1", "green-city-2", "green-silo-1"],
            "lastAction": None,
            "invalidActionCount": 0,
        },
        {
            "id": "yellow",
            "name": "Yellow Dominion",
            "color": "#ffcc00",
            "population": 200,
            "score": 150,
            "status": "active",
            "controlMode": "scripted",
            "sites": ["yellow-city-1", "yellow-city-2", "yellow-silo-1"],
            "lastAction": None,
            "invalidActionCount": 0,
        },
    ]


def create_base_nodes() -> list[dict[str, Any]]:
    """Create the canonical map nodes (4 factions × 2 cities + 1 silo = 12 nodes)."""
    return [
        # Red faction (top-left)
        {"id": "red-city-1", "name": "Red Capital", "owner": "red", "type": "city", "x": 150, "y": 200, "hp": 100, "population": 100, "status": "active", "incomingMissiles": 0},
        {"id": "red-city-2", "name": "Red Industrial", "owner": "red", "type": "city", "x": 200, "y": 300, "hp": 100, "population": 100, "status": "active", "incomingMissiles": 0},
        {"id": "red-silo-1", "name": "Red Silo Alpha", "owner": "red", "type": "silo", "x": 175, "y": 250, "hp": 100, "ammo": 6, "cooldown": 0, "status": "active", "lastLaunchTick": None},
        # Blue faction (top-right)
        {"id": "blue-city-1", "name": "Blue Capital", "owner": "blue", "type": "city", "x": 650, "y": 200, "hp": 100, "population": 100, "status": "active", "incomingMissiles": 0},
        {"id": "blue-city-2", "name": "Blue Industrial", "owner": "blue", "type": "city", "x": 700, "y": 300, "hp": 100, "population": 100, "status": "active", "incomingMissiles": 0},
        {"id": "blue-silo-1", "name": "Blue Silo Alpha", "owner": "blue", "type": "silo", "x": 675, "y": 250, "hp": 100, "ammo": 6, "cooldown": 0, "status": "active", "lastLaunchTick": None},
        # Green faction (middle-top)
        {"id": "green-city-1", "name": "Green Capital", "owner": "green", "type": "city", "x": 400, "y": 100, "hp": 100, "population": 100, "status": "active", "incomingMissiles": 0},
        {"id": "green-city-2", "name": "Green Industrial", "owner": "green", "type": "city", "x": 450, "y": 180, "hp": 100, "population": 100, "status": "active", "incomingMissiles": 0},
        {"id": "green-silo-1", "name": "Green Silo Alpha", "owner": "green", "type": "silo", "x": 425, "y": 140, "hp": 100, "ammo": 6, "cooldown": 0, "status": "active", "lastLaunchTick": None},
        # Yellow faction (middle-bottom)
        {"id": "yellow-city-1", "name": "Yellow Capital", "owner": "yellow", "type": "city", "x": 400, "y": 400, "hp": 100, "population": 100, "status": "active", "incomingMissiles": 0},
        {"id": "yellow-city-2", "name": "Yellow Industrial", "owner": "yellow", "type": "city", "x": 450, "y": 480, "hp": 100, "population": 100, "status": "active", "incomingMissiles": 0},
        {"id": "yellow-silo-1", "name": "Yellow Silo Alpha", "owner": "yellow", "type": "silo", "x": 425, "y": 440, "hp": 100, "ammo": 6, "cooldown": 0, "status": "active", "lastLaunchTick": None},
    ]


def create_idle_state() -> dict[str, Any]:
    """Create initial idle state - no match running yet."""
    return {
        "match": {
            "matchId": None,
            "lifecycleState": "idle",
            "tick": 0,
            "timeRemainingSec": 300,
            "startedAt": None,
            "scenario": "canonical-4-faction",
        },
        "factions": create_base_factions(),
        "nodes": create_base_nodes(),
        "missiles": [],
        "recentEvents": [
            {
                "tick": 0,
                "time": datetime.utcnow().isoformat() + "Z",
                "type": "match_created",
                "message": "Match created, waiting to start",
            }
        ],
        "summary": {
            "leadingFaction": None,
            "totalMissilesInFlight": 0,
            "activeFactions": 4,
            "crippledFactions": 0,
            "eliminatedFactions": 0,
        },
    }


def create_running_state(tick: int = 0) -> dict[str, Any]:
    """Create a running match state."""
    factions = create_base_factions()
    nodes = create_base_nodes()
    
    return {
        "match": {
            "matchId": f"match-{tick:03d}",
            "lifecycleState": "running",
            "tick": tick,
            "timeRemainingSec": max(0, 300 - (tick * 0.25)),
            "startedAt": datetime.utcnow().isoformat() + "Z",
            "scenario": "canonical-4-faction",
        },
        "factions": factions,
        "nodes": nodes,
        "missiles": [],
        "recentEvents": [
            {
                "tick": 0,
                "time": datetime.utcnow().isoformat() + "Z",
                "type": "match_start",
                "matchId": f"match-{tick:03d}",
            }
        ],
        "summary": {
            "leadingFaction": "red",
            "totalMissilesInFlight": 0,
            "activeFactions": 4,
            "crippledFactions": 0,
            "eliminatedFactions": 0,
        },
    }


def create_paused_state() -> dict[str, Any]:
    """Create a paused match state."""
    state = create_running_state(120)
    state["match"]["lifecycleState"] = "paused"
    state["recentEvents"].append({
        "tick": 120,
        "time": datetime.utcnow().isoformat() + "Z",
        "type": "match_paused",
        "message": "Match paused by operator",
    })
    return state


def create_finished_state() -> dict[str, Any]:
    """Create a finished match state."""
    factions = [
        {"id": "red", "name": "Red Directorate", "color": "#ff4d5a", "population": 180, "score": 205, "status": "active", "controlMode": "agent", "sites": ["red-city-1", "red-city-2", "red-silo-1"], "lastAction": {"type": "hold"}, "invalidActionCount": 0},
        {"id": "blue", "name": "Blue Alliance", "color": "#4d8cff", "population": 60, "score": 85, "status": "crippled", "controlMode": "scripted", "sites": ["blue-city-1"], "lastAction": {"type": "hold"}, "invalidActionCount": 0},
        {"id": "green", "name": "Green Collective", "color": "#4dcc5a", "population": 0, "score": 25, "status": "eliminated", "controlMode": "scripted", "sites": [], "lastAction": None, "invalidActionCount": 1},
        {"id": "yellow", "name": "Yellow Dominion", "color": "#ffcc00", "population": 0, "score": 25, "status": "eliminated", "controlMode": "scripted", "sites": [], "lastAction": None, "invalidActionCount": 0},
    ]
    
    nodes = [
        {"id": "red-city-1", "name": "Red Capital", "owner": "red", "type": "city", "x": 150, "y": 200, "hp": 100, "population": 100, "status": "active", "incomingMissiles": 0},
        {"id": "red-city-2", "name": "Red Industrial", "owner": "red", "type": "city", "x": 200, "y": 300, "hp": 100, "population": 80, "status": "damaged", "incomingMissiles": 0},
        {"id": "red-silo-1", "name": "Red Silo Alpha", "owner": "red", "type": "silo", "x": 175, "y": 250, "hp": 100, "ammo": 2, "cooldown": 0, "status": "active", "lastLaunchTick": 1180},
        {"id": "blue-city-1", "name": "Blue Capital", "owner": "blue", "type": "city", "x": 650, "y": 200, "hp": 60, "population": 60, "status": "damaged", "incomingMissiles": 0},
        {"id": "blue-city-2", "name": "Blue Industrial", "owner": "blue", "type": "city", "x": 700, "y": 300, "hp": 0, "population": 0, "status": "destroyed", "incomingMissiles": 0},
        {"id": "blue-silo-1", "name": "Blue Silo Alpha", "owner": "blue", "type": "silo", "x": 675, "y": 250, "hp": 0, "ammo": 0, "cooldown": 0, "status": "destroyed", "lastLaunchTick": 1100},
        {"id": "green-city-1", "name": "Green Capital", "owner": "green", "type": "city", "x": 400, "y": 100, "hp": 0, "population": 0, "status": "destroyed", "incomingMissiles": 0},
        {"id": "green-city-2", "name": "Green Industrial", "owner": "green", "type": "city", "x": 450, "y": 180, "hp": 0, "population": 0, "status": "destroyed", "incomingMissiles": 0},
        {"id": "green-silo-1", "name": "Green Silo Alpha", "owner": "green", "type": "silo", "x": 425, "y": 140, "hp": 0, "ammo": 0, "cooldown": 0, "status": "destroyed", "lastLaunchTick": 800},
        {"id": "yellow-city-1", "name": "Yellow Capital", "owner": "yellow", "type": "city", "x": 400, "y": 400, "hp": 0, "population": 0, "status": "destroyed", "incomingMissiles": 0},
        {"id": "yellow-city-2", "name": "Yellow Industrial", "owner": "yellow", "type": "city", "x": 450, "y": 480, "hp": 0, "population": 0, "status": "destroyed", "incomingMissiles": 0},
        {"id": "yellow-silo-1", "name": "Yellow Silo Alpha", "owner": "yellow", "type": "silo", "x": 425, "y": 440, "hp": 0, "ammo": 0, "cooldown": 0, "status": "destroyed", "lastLaunchTick": 500},
    ]
    
    return {
        "match": {
            "matchId": "match-001",
            "lifecycleState": "finished",
            "tick": 1200,
            "timeRemainingSec": 0,
            "startedAt": "2026-05-28T12:00:00Z",
            "scenario": "canonical-4-faction",
        },
        "factions": factions,
        "nodes": nodes,
        "missiles": [],
        "recentEvents": [
            {"tick": 1198, "time": "2026-05-28T12:04:59.5Z", "type": "match_end", "winner": "red", "message": "Match complete - Red Directorate wins"},
        ],
        "summary": {
            "leadingFaction": "red",
            "totalMissilesInFlight": 0,
            "activeFactions": 1,
            "crippledFactions": 1,
            "eliminatedFactions": 2,
        },
    }


def create_mock_match_state() -> dict[str, Any]:
    """Create a realistic mid-match state for UI development."""
    return {
        "match": {
            "matchId": "match-001",
            "lifecycleState": "running",
            "tick": 120,
            "timeRemainingSec": 214,
            "startedAt": "2026-05-28T12:00:00Z",
            "scenario": "canonical-4-faction",
        },
        "factions": [
            {
                "id": "red",
                "name": "Red Directorate",
                "color": "#ff4d5a",
                "population": 240,
                "score": 180,
                "status": "active",
                "controlMode": "agent",
                "sites": ["red-city-1", "red-city-2", "red-silo-1"],
                "lastAction": {"type": "launch", "from": "red-silo-1", "target": "blue-city-2"},
                "invalidActionCount": 0,
            },
            {
                "id": "blue",
                "name": "Blue Alliance",
                "color": "#4d8cff",
                "population": 180,
                "score": 120,
                "status": "active",
                "controlMode": "scripted",
                "sites": ["blue-city-1", "blue-city-2", "blue-silo-1"],
                "lastAction": {"type": "hold"},
                "invalidActionCount": 0,
            },
            {
                "id": "green",
                "name": "Green Collective",
                "color": "#4dcc5a",
                "population": 160,
                "score": 95,
                "status": "crippled",
                "controlMode": "scripted",
                "sites": ["green-city-1", "green-city-2"],
                "lastAction": {"type": "hold"},
                "invalidActionCount": 1,
            },
            {
                "id": "yellow",
                "name": "Yellow Dominion",
                "color": "#ffcc00",
                "population": 0,
                "score": 25,
                "status": "eliminated",
                "controlMode": "scripted",
                "sites": [],
                "lastAction": None,
                "invalidActionCount": 0,
            },
        ],
        "nodes": [
            {"id": "red-city-1", "name": "Red Capital", "owner": "red", "type": "city", "x": 150, "y": 200, "hp": 100, "population": 100, "status": "active", "incomingMissiles": 1},
            {"id": "red-city-2", "name": "Red Industrial", "owner": "red", "type": "city", "x": 200, "y": 300, "hp": 100, "population": 100, "status": "active", "incomingMissiles": 0},
            {"id": "red-silo-1", "name": "Red Silo Alpha", "owner": "red", "type": "silo", "x": 175, "y": 250, "hp": 100, "ammo": 4, "cooldown": 0, "status": "active", "lastLaunchTick": 116},
            {"id": "blue-city-1", "name": "Blue Capital", "owner": "blue", "type": "city", "x": 650, "y": 200, "hp": 100, "population": 100, "status": "active", "incomingMissiles": 0},
            {"id": "blue-city-2", "name": "Blue Industrial", "owner": "blue", "type": "city", "x": 700, "y": 300, "hp": 60, "population": 60, "status": "damaged", "incomingMissiles": 1},
            {"id": "blue-silo-1", "name": "Blue Silo Alpha", "owner": "blue", "type": "silo", "x": 675, "y": 250, "hp": 100, "ammo": 5, "cooldown": 2, "status": "active", "lastLaunchTick": 110},
            {"id": "green-city-1", "name": "Green Capital", "owner": "green", "type": "city", "x": 400, "y": 100, "hp": 100, "population": 100, "status": "active", "incomingMissiles": 0},
            {"id": "green-city-2", "name": "Green Industrial", "owner": "green", "type": "city", "x": 450, "y": 180, "hp": 100, "population": 60, "status": "damaged", "incomingMissiles": 0},
            {"id": "green-silo-1", "name": "Green Silo Alpha", "owner": "green", "type": "silo", "x": 425, "y": 140, "hp": 0, "ammo": 0, "cooldown": 0, "status": "destroyed", "lastLaunchTick": 80},
            {"id": "yellow-city-1", "name": "Yellow Capital", "owner": "yellow", "type": "city", "x": 400, "y": 400, "hp": 0, "population": 0, "status": "destroyed", "incomingMissiles": 0},
            {"id": "yellow-city-2", "name": "Yellow Industrial", "owner": "yellow", "type": "city", "x": 450, "y": 480, "hp": 0, "population": 0, "status": "destroyed", "incomingMissiles": 0},
            {"id": "yellow-silo-1", "name": "Yellow Silo Alpha", "owner": "yellow", "type": "silo", "x": 425, "y": 440, "hp": 0, "ammo": 0, "cooldown": 0, "status": "destroyed", "lastLaunchTick": 50},
        ],
        "missiles": [
            {
                "id": "missile-001",
                "owner": "red",
                "source": "red-silo-1",
                "target": "blue-city-2",
                "launchTick": 116,
                "impactTick": 148,
                "currentTick": 120,
                "progress": 0.125,
                "status": "flying",
                "x": 185,
                "y": 255,
            },
            {
                "id": "missile-002",
                "owner": "blue",
                "source": "blue-silo-1",
                "target": "red-city-1",
                "launchTick": 110,
                "impactTick": 142,
                "currentTick": 120,
                "progress": 0.3125,
                "status": "flying",
                "x": 580,
                "y": 235,
            },
            {
                "id": "missile-003",
                "owner": "green",
                "source": "green-silo-1",
                "target": "yellow-city-1",
                "launchTick": 80,
                "impactTick": 112,
                "currentTick": 120,
                "progress": 1.0,
                "status": "impact",
                "x": 400,
                "y": 400,
            },
        ],
        "recentEvents": [
            {
                "tick": 118,
                "time": "2026-05-28T12:01:58Z",
                "type": "launch",
                "faction": "red",
                "source": "red-silo-1",
                "target": "blue-city-2",
                "missileId": "missile-001",
            },
            {
                "tick": 116,
                "time": "2026-05-28T12:01:56Z",
                "type": "impact",
                "faction": "blue",
                "target": "blue-city-2",
                "damage": 40,
                "destroyed": False,
                "missileId": "missile-000",
            },
            {
                "tick": 112,
                "time": "2026-05-28T12:01:52Z",
                "type": "destruction",
                "faction": "yellow",
                "target": "yellow-city-1",
                "targetType": "city",
            },
            {
                "tick": 110,
                "time": "2026-05-28T12:01:50Z",
                "type": "launch",
                "faction": "blue",
                "source": "blue-silo-1",
                "target": "red-city-1",
                "missileId": "missile-002",
            },
            {
                "tick": 108,
                "time": "2026-05-28T12:01:48Z",
                "type": "invalid_action",
                "faction": "green",
                "reason": "silo_destroyed",
            },
        ],
        "summary": {
            "leadingFaction": "red",
            "totalMissilesInFlight": 2,
            "activeFactions": 2,
            "crippledFactions": 1,
            "eliminatedFactions": 1,
        },
    }


def create_mock_replay() -> dict[str, Any]:
    """Create a complete mock replay for UI development."""
    return {
        "match": {
            "matchId": "match-001",
            "scenario": "canonical-4-faction",
            "startedAt": "2026-05-28T12:00:00Z",
            "endedAt": "2026-05-28T12:05:00Z",
            "durationSec": 300,
            "finalTick": 1200,
            "winner": "red",
            "seed": 12345,
        },
        "factions": [
            {"id": "red", "name": "Red Directorate", "color": "#ff4d5a"},
            {"id": "blue", "name": "Blue Alliance", "color": "#4d8cff"},
            {"id": "green", "name": "Green Collective", "color": "#4dcc5a"},
            {"id": "yellow", "name": "Yellow Dominion", "color": "#ffcc00"},
        ],
        "events": [
            {"tick": 0, "time": "2026-05-28T12:00:00Z", "type": "match_start", "matchId": "match-001"},
            {"tick": 16, "time": "2026-05-28T12:00:04Z", "type": "launch", "faction": "red", "source": "red-silo-1", "target": "blue-city-1", "missileId": "m-1"},
            {"tick": 16, "time": "2026-05-28T12:00:04Z", "type": "launch", "faction": "blue", "source": "blue-silo-1", "target": "red-city-1", "missileId": "m-2"},
            {"tick": 16, "time": "2026-05-28T12:00:04Z", "type": "launch", "faction": "green", "source": "green-silo-1", "target": "yellow-city-1", "missileId": "m-3"},
            {"tick": 16, "time": "2026-05-28T12:00:04Z", "type": "hold", "faction": "yellow"},
            {"tick": 48, "time": "2026-05-28T12:00:12Z", "type": "impact", "faction": "blue", "target": "blue-city-1", "damage": 100, "destroyed": True, "missileId": "m-1"},
            {"tick": 48, "time": "2026-05-28T12:00:12Z", "type": "destruction", "faction": "blue", "target": "blue-city-1", "targetType": "city"},
            {"tick": 50, "time": "2026-05-28T12:00:12.5Z", "type": "launch", "faction": "red", "source": "red-silo-1", "target": "blue-silo-1", "missileId": "m-4"},
            {"tick": 80, "time": "2026-05-28T12:00:20Z", "type": "impact", "faction": "red", "target": "red-city-1", "damage": 100, "destroyed": True, "missileId": "m-2"},
            {"tick": 80, "time": "2026-05-28T12:00:20Z", "type": "destruction", "faction": "red", "target": "red-city-1", "targetType": "city"},
            {"tick": 82, "time": "2026-05-28T12:00:20.5Z", "type": "launch", "faction": "blue", "source": "blue-silo-1", "target": "red-city-2", "missileId": "m-5"},
            {"tick": 112, "time": "2026-05-28T12:00:28Z", "type": "impact", "faction": "yellow", "target": "yellow-city-1", "damage": 100, "destroyed": True, "missileId": "m-3"},
            {"tick": 112, "time": "2026-05-28T12:00:28Z", "type": "destruction", "faction": "yellow", "target": "yellow-city-1", "targetType": "city"},
            {"tick": 144, "time": "2026-05-28T12:00:36Z", "type": "impact", "faction": "blue", "target": "blue-silo-1", "damage": 100, "destroyed": True, "missileId": "m-4"},
            {"tick": 144, "time": "2026-05-28T12:00:36Z", "type": "destruction", "faction": "blue", "target": "blue-silo-1", "targetType": "silo"},
            {"tick": 1198, "time": "2026-05-28T12:04:59.5Z", "type": "match_end", "winner": "red", "message": "Match complete - Red Directorate wins"},
        ],
        "snapshots": [
            {"tick": 0, "time": "2026-05-28T12:00:00Z", "factions": [{"id": "red", "population": 200, "score": 150}, {"id": "blue", "population": 200, "score": 150}, {"id": "green", "population": 200, "score": 150}, {"id": "yellow", "population": 200, "score": 150}]},
            {"tick": 300, "time": "2026-05-28T12:01:15Z", "factions": [{"id": "red", "population": 180, "score": 175}, {"id": "blue", "population": 100, "score": 100}, {"id": "green", "population": 200, "score": 150}, {"id": "yellow", "population": 100, "score": 75}]},
            {"tick": 600, "time": "2026-05-28T12:02:30Z", "factions": [{"id": "red", "population": 180, "score": 200}, {"id": "blue", "population": 60, "score": 85}, {"id": "green", "population": 100, "score": 100}, {"id": "yellow", "population": 0, "score": 25}]},
            {"tick": 900, "time": "2026-05-28T12:03:45Z", "factions": [{"id": "red", "population": 180, "score": 205}, {"id": "blue", "population": 60, "score": 85}, {"id": "green", "population": 0, "score": 25}, {"id": "yellow", "population": 0, "score": 25}]},
            {"tick": 1200, "time": "2026-05-28T12:05:00Z", "factions": [{"id": "red", "population": 180, "score": 205}, {"id": "blue", "population": 60, "score": 85}, {"id": "green", "population": 0, "score": 25}, {"id": "yellow", "population": 0, "score": 25}]},
        ],
        "finalState": {
            "factions": [
                {"id": "red", "population": 180, "score": 205, "status": "active", "survivingCities": 2, "survivingSilos": 1},
                {"id": "blue", "population": 60, "score": 85, "status": "crippled", "survivingCities": 1, "survivingSilos": 0},
                {"id": "green", "population": 0, "score": 25, "status": "eliminated", "survivingCities": 0, "survivingSilos": 0},
                {"id": "yellow", "population": 0, "score": 25, "status": "eliminated", "survivingCities": 0, "survivingSilos": 0},
            ]
        },
    }


from datetime import datetime