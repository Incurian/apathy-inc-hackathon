#!/usr/bin/env python3
"""Test harness to initialize simulation state and run MCP server."""

import sys
sys.path.insert(0, 'src')

from agent_adapter.mcp_tools import set_simulation_state, register_faction, server
from sim.models import MatchState, Faction, Node, EntityType, Position, Constants, FactionStatus, LifecycleState


def create_test_simulation_state():
    """Create minimal test simulation state with two factions."""
    # Create nodes (cities and silos)
    city_a1 = Node(
        id="city_a1",
        name="Alpha City",
        owner="faction_a",
        type=EntityType.CITY,
        position=Position(x=0, y=0),
        hp=100,
        population=1000000
    )
    silo_a1 = Node(
        id="silo_a1",
        name="Alpha Silo",
        owner="faction_a",
        type=EntityType.SILO,
        position=Position(x=10, y=10),
        hp=100,
        ammo=10
    )
    city_b1 = Node(
        id="city_b1",
        name="Beta City",
        owner="faction_b",
        type=EntityType.CITY,
        position=Position(x=100, y=100),
        hp=100,
        population=1000000
    )
    silo_b1 = Node(
        id="silo_b1",
        name="Beta Silo",
        owner="faction_b",
        type=EntityType.SILO,
        position=Position(x=110, y=110),
        hp=100,
        ammo=10
    )

    # Create factions
    faction_a = Faction(
        id="faction_a",
        name="Alpha",
        color="#FF0000",
        population=1000000,
        score=0,
        status=FactionStatus.ACTIVE,
        control_mode="agent",
        owned_sites=["city_a1", "silo_a1"]
    )
    faction_b = Faction(
        id="faction_b",
        name="Beta",
        color="#0000FF",
        population=1000000,
        score=0,
        status=FactionStatus.ACTIVE,
        control_mode="agent",
        owned_sites=["city_b1", "silo_b1"]
    )

# Create match state with nodes
    match_state = MatchState(
        match_id="test_match_001",
        tick=0,
        time_remaining_sec=300,
        lifecycle_state=LifecycleState.RUNNING,
        factions={"faction_a": faction_a, "faction_b": faction_b},
        nodes={"city_a1": city_a1, "silo_a1": silo_a1, "city_b1": city_b1, "silo_b1": silo_b1},
        events=[],
        missiles={}
    )
    return match_state


# Initialize simulation state at module load
sim_state = create_test_simulation_state()
set_simulation_state(sim_state)

# Register factions
register_faction("faction_a", sim_state.factions["faction_a"])
register_faction("faction_b", sim_state.factions["faction_b"])

print("MCP server initialized with test state")
print("Factions registered: faction_a, faction_b")
print("Server object: server")

# Expose server for MCP Inspector
app = server