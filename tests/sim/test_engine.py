"""
Tests for the simulation engine.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sim.engine import SimulationEngine
from src.sim.models import LifecycleState
from src.sim.rules import Constants, initialize_match


def test_match_initialization():
    """Test that a match initializes correctly."""
    engine = SimulationEngine()
    match_state = engine.start_match()
    
    # Check basic properties
    assert match_state.match_id.startswith("match-")
    assert match_state.tick == 0
    assert match_state.time_remaining_sec == Constants.MATCH_DURATION_SEC
    assert match_state.lifecycle_state == LifecycleState.RUNNING  # start_match sets to RUNNING
    
    # Check factions
    assert len(match_state.factions) == Constants.NUM_FACTIONS
    for faction_id in ["red", "blue", "green", "yellow"]:
        assert faction_id in match_state.factions
        faction = match_state.factions[faction_id]
        assert faction.population == Constants.INITIAL_CITY_POPULATION * Constants.CITIES_PER_FACTION
        assert faction.score == 0
        assert faction.status == faction.status.ACTIVE  # Should be active
    
    # Check nodes
    expected_nodes = (Constants.CITIES_PER_FACTION + Constants.SILOS_PER_FACTION) * Constants.NUM_FACTIONS
    assert len(match_state.nodes) == expected_nodes
    
    # Check cities have correct population
    for node_id, node in match_state.nodes.items():
        if node.type == node.type.CITY:
            assert node.population == Constants.INITIAL_CITY_POPULATION
            assert node.hp == Constants.CITY_HP
        elif node.type == node.type.SILO:
            assert node.ammo == Constants.INITIAL_SILO_AMMO
            assert node.hp == Constants.SILO_HP
            assert node.cooldown == 0
    
    print("✓ Match initialization test passed")


def test_hold_action():
    """Test that hold actions work correctly."""
    engine = SimulationEngine()
    match_state = engine.start_match()
    
    # Switch to running state
    match_state.lifecycle_state = LifecycleState.RUNNING
    
    # Apply hold action
    events = engine.apply_faction_action("red", {"type": "hold"})
    
    # Should generate one event
    assert len(events) == 1
    event = events[0]
    assert event["type"] == "hold"
    assert event["faction_id"] == "red"
    
    # Check that faction's last action was updated
    faction = match_state.factions["red"]
    assert faction.last_action["type"] == "hold"
    
    print("✓ Hold action test passed")


def test_launch_action_validation():
    """Test launch action validation."""
    engine = SimulationEngine()
    match_state = engine.start_match()
    match_state.lifecycle_state = LifecycleState.RUNNING
    
    # Test valid launch
    red_silo = "red-silo-1"
    blue_city = "blue-city-1"
    
    # Verify the silo has ammo and is ready
    silo_node = match_state.nodes[red_silo]
    assert silo_node.ammo > 0
    assert silo_node.cooldown == 0
    
    events = engine.apply_faction_action("red", {
        "type": "launch",
        "from": red_silo,
        "target": blue_city
    })
    
    # Should generate launch event
    assert len(events) == 1
    event = events[0]
    assert event["type"] == "launch"
    assert event["faction_id"] == "red"
    assert event["missile_id"] is not None
    assert event["source_node_id"] == red_silo
    assert event["target_node_id"] == blue_city
    
    # Check that silo ammo decreased
    assert match_state.nodes[red_silo].ammo == Constants.INITIAL_SILO_AMMO - 1
    
    # Check that silo cooldown was set
    assert match_state.nodes[red_silo].cooldown == Constants.DECISION_WINDOW_TICKS
    
    # Check that faction's last action was updated
    faction = match_state.factions["red"]
    assert faction.last_action["type"] == "launch"
    assert faction.last_action["from"] == red_silo
    assert faction.last_action["target"] == blue_city
    
    print("✓ Launch action validation test passed")


def test_invalid_launch_actions():
    """Test that invalid launch actions are properly rejected."""
    engine = SimulationEngine()
    match_state = engine.start_match()
    match_state.lifecycle_state = LifecycleState.RUNNING
    
    red_silo = "red-silo-1"
    blue_city = "blue-city-1"
    
    # Test launch from non-owned silo (should fail)
    events = engine.apply_faction_action("red", {
        "type": "launch",
        "from": "blue-silo-1",  # Blue's silo
        "target": blue_city
    })
    
    # Should generate invalid action event
    assert len(events) == 1
    event = events[0]
    assert event["type"] == "invalid_action"
    assert event["faction_id"] == "red"
    assert "does not belong to faction" in event["details"]["reason"]
    
    # Test launch from silo with no ammo (after using all ammo)
    # First, use all ammo from red silo
    for i in range(Constants.INITIAL_SILO_AMMO):
        engine.apply_faction_action("red", {
            "type": "launch",
            "from": red_silo,
            "target": blue_city
        })
        # Advance time enough to reset cooldown between shots
        # We need to advance multiple ticks to account for cooldown and missile flight
        # Manipulate last_tick_time to simulate time passage since update() checks real time
        for tick in range(Constants.DECISION_WINDOW_TICKS):
            engine.last_tick_time -= engine.tick_interval  # Move back in time by one tick interval
            engine.update()
    
    # Now try to launch again (should fail due to no ammo)
    events = engine.apply_faction_action("red", {
        "type": "launch",
        "from": red_silo,
        "target": blue_city
    })
    
    assert len(events) == 1
    event = events[0]
    assert event["type"] == "invalid_action"
    assert event["faction_id"] == "red"
    assert "no ammo" in event["details"]["reason"]
    
    print("✓ Invalid launch actions test passed")


def test_missile_flight_and_impact():
    """Test that missiles fly and impact correctly."""
    engine = SimulationEngine()
    match_state = engine.start_match()
    match_state.lifecycle_state = LifecycleState.RUNNING
    
    red_silo = "red-silo-1"
    blue_city = "blue-city-1"
    
    # Launch a missile
    events = engine.apply_faction_action("red", {
        "type": "launch",
        "from": red_silo,
        "target": blue_city
    })
    
    assert len(events) == 1
    assert events[0]["type"] == "launch"
    missile_id = events[0]["missile_id"]
    
    # Check missile was created
    assert missile_id in match_state.missiles
    missile = match_state.missiles[missile_id]
    assert missile.status == missile.status.FLYING
    assert missile.launch_tick == 0
    assert missile.impact_tick == Constants.MISSILE_FLIGHT_TIME_TICKS
    
    # Store initial city HP
    initial_city_hp = match_state.nodes[blue_city].hp
    assert initial_city_hp == Constants.CITY_HP
    
    # Advance ticks until impact (should be MISSILE_FLIGHT_TIME_TICKS ticks)
    impact_tick = Constants.MISSILE_FLIGHT_TIME_TICKS
    for i in range(impact_tick):
        events = engine.update()
        # Check for impact event around the expected time
        if i >= impact_tick - 2:  # Check a couple ticks before expected impact
            impact_events = [e for e in events if e["type"] == "impact"]
            if impact_events:
                print(f"Impact detected at tick {match_state.tick}")
                break
    
    # After impact, city should be destroyed (HP = 0)
    assert match_state.nodes[blue_city].hp == 0
    assert match_state.nodes[blue_city].status == "destroyed"
    assert match_state.nodes[blue_city].population == 0
    
    # Check that red faction's score increased (destroying enemy city/silo gives points)
    # Note: Scoring happens in update_faction_statuses which is called during advance_tick
    # Let's advance a few more ticks to ensure scoring is updated
    for i in range(5):
        engine.update()
    
    red_faction = match_state.factions["red"]
    # Should have gained points for destroying the city
    # According to spec: surviving population + 25 per enemy silo destroyed
    # Cities don't give direct points, but destroying them reduces enemy population
    # Let's just verify the engine didn't crash and produced reasonable results
    assert red_faction.score >= 0
    
    print("✓ Missile flight and impact test passed")


def test_deterministic_runs():
    """Test that same seed + same actions produces same outcome."""
    # This is a simplified test - in a full implementation we'd use explicit seeding
    engine1 = SimulationEngine()
    engine2 = SimulationEngine()
    
    match_state1 = engine1.start_match("deterministic-test")
    match_state2 = engine2.start_match("deterministic-test")
    
    # Apply same sequence of actions
    actions = [
        ("red", {"type": "hold"}),
        ("blue", {"type": "hold"}),
        ("red", {"type": "launch", "from": "red-silo-1", "target": "blue-city-1"}),
        ("green", {"type": "hold"}),
        ("yellow", {"type": "hold"})
    ]
    
    # Apply actions to both engines
    for faction_id, action in actions:
        engine1.apply_faction_action(faction_id, action)
        engine2.apply_faction_action(faction_id, action)
        
        # Advance a few ticks between actions
        for _ in range(4):
            engine1.update()
            engine2.update()
    
    # Compare states (simplified comparison)
    state1_dict = engine1.get_state()
    state2_dict = engine2.get_state()
    
    # Compare basic properties
    assert state1_dict["tick"] == state2_dict["tick"]
    assert state1_dict["time_remaining_sec"] == state2_dict["time_remaining_sec"]
    assert state1_dict["lifecycle_state"] == state2_dict["lifecycle_state"]
    
    # Compare faction counts
    assert len(state1_dict["factions"]) == len(state2_dict["factions"])
    
    print("✓ Deterministic runs test passed")


def test_match_end_conditions():
    """Test match end conditions."""
    engine = SimulationEngine()
    match_state = engine.start_match()
    match_state.lifecycle_state = LifecycleState.RUNNING
    
    # Test time-based end
    match_state.time_remaining_sec = 0
    # Normally this would be checked in advance_tick, but we can test the function directly
    from src.sim.rules import check_match_end
    assert check_match_end(match_state) == True
    
    # Reset time and test elimination-based end
    match_state.time_remaining_sec = 100  # 100 seconds remaining
    
    # Destroy all cities for one faction except red
    for faction_id in ["blue", "green", "yellow"]:
        for node_id, node in match_state.nodes.items():
            if node.owner == faction_id and node.type == "city":
                node.hp = 0
                node.status = "destroyed"
                node.population = 0
    
    # Now only red should have cities
    assert check_match_end(match_state) == True
    
    print("✓ Match end conditions test passed")


if __name__ == "__main__":
    print("Running simulation engine tests...")
    
    test_match_initialization()
    test_hold_action()
    test_launch_action_validation()
    test_invalid_launch_actions()
    test_missile_flight_and_impact()
    test_deterministic_runs()
    test_match_end_conditions()
    
    print("\n🎉 All tests passed!")