#!/usr/bin/env python3
"""
Agent adapter smoke test for demo validation.
Quick validation that agent integration works correctly.
Run with: python scripts/demo/agent_smoke.py
"""

import json
import sys
import traceback
from src.sim.engine import SimulationEngine
from src.sim.models import LifecycleState
from src.agent_adapter.adapter import AgentAdapter, ControllerMode
from src.agent_adapter.observation_builder import build_observation
from src.agent_adapter.action_parser import parse_and_validate_action
from src.agent_adapter.fallback import handle_agent_response
from src.agent_adapter.logging import log_decision, get_latest_decision
from src.agent_adapter.models import Observation


def advance_ticks(engine, num_ticks):
    """Helper to advance simulation ticks by manipulating time."""
    for _ in range(num_ticks):
        engine.last_tick_time -= engine.tick_interval
        engine.update()


def test_observation_build():
    """Test building observation from simulation state."""
    print("Test 1: Building observation from simulation state...")
    engine = SimulationEngine()
    match_state = engine.start_match()
    match_state.lifecycle_state = LifecycleState.RUNNING
    
    observation = build_observation(match_state, "red", recent_events=[])
    
    assert isinstance(observation, Observation)
    assert observation.match["matchId"] == match_state.match_id
    assert observation.match["tick"] == match_state.tick
    assert observation.self.id == "red"
    assert "hold" in [a.type for a in observation.legalActions]
    print("  ✓ Observation builds correctly")
    print(f"  ✓ Match ID: {observation.match['matchId']}")
    print(f"  ✓ Tick: {observation.match['tick']}")
    print(f"  ✓ Faction: {observation.self.id}")
    print(f"  ✓ Legal actions: {[a.type for a in observation.legalActions]}")
    print(f"  ✓ Observation size: {len(observation.model_dump_json()) / 1024:.2f} KB")
    return True


def test_action_parser_valid():
    """Test parsing valid agent actions."""
    print("\nTest 2: Parsing valid agent actions...")
    engine = SimulationEngine()
    match_state = engine.start_match()
    match_state.lifecycle_state = LifecycleState.RUNNING
    faction = match_state.factions["red"]
    
    # Test hold action
    hold_response = json.dumps({"action": {"type": "hold"}, "comment": "Waiting"})
    action, error = parse_and_validate_action(hold_response, faction, match_state)
    assert error is None, f"Hold action failed: {error}"
    assert action["type"] == "hold"
    print("  ✓ Hold action parses correctly")
    
    # Test launch action
    launch_response = json.dumps({
        "action": {"type": "launch", "from": "red-silo-1", "target": "blue-city-1"},
        "comment": "Attack blue capital"
    })
    action, error = parse_and_validate_action(launch_response, faction, match_state)
    assert error is None, f"Launch action failed: {error}"
    assert action["type"] == "launch"
    assert action["from"] == "red-silo-1"
    assert action["target"] == "blue-city-1"
    print("  ✓ Launch action parses correctly")
    return True


def test_action_parser_invalid():
    """Test that invalid actions are rejected with hold fallback."""
    print("\nTest 3: Invalid action rejection...")
    engine = SimulationEngine()
    match_state = engine.start_match()
    match_state.lifecycle_state = LifecycleState.RUNNING
    faction = match_state.factions["red"]
    
    test_cases = [
        ('{"action": {"type": "invalid"}}', "invalid action type"),
        ('{"action": {"type": "launch"}}', "missing launch fields"),
        ('{"action": "hold"}', "action not object"),
        ('{"comment": "test"}', "missing action field"),
        ('not json', "malformed JSON"),
        ('', "empty response"),
    ]
    
    for response, description in test_cases:
        action, error = parse_and_validate_action(response, faction, match_state)
        assert action["type"] == "hold", f"Expected hold for {description}"
        assert error is not None, f"Expected error for {description}"
        print(f"  ✓ Rejected: {description}")
    return True


def test_fallback_behavior():
    """Test fallback handler behavior."""
    print("\nTest 4: Fallback handler behavior...")
    from src.agent_adapter.fallback import FallbackHandler
    from src.agent_adapter.models import Observation, FactionState, LegalAction
    
    handler = FallbackHandler(timeout_seconds=5.0)
    observation = Observation(
        match={"matchId": "test", "tick": 100, "timeRemainingSec": 300},
        self=FactionState(id="red", population=100, score=50, status="active", sites=[]),
        world={"factions": [], "targets": [], "missiles": []},
        recentEvents=[],
        legalActions=[LegalAction(type="hold")]
    )
    
    # Test timeout
    action, log = handle_agent_response(
        faction_id="red", tick=100, observation=observation,
        raw_response=None, start_time=0.0  # Ancient start = timeout
    )
    assert action["type"] == "hold"
    assert "timeout" in log["errorReason"].lower()
    print("  ✓ Timeout returns hold")
    
    # Test malformed JSON
    action, log = handle_agent_response(
        faction_id="red", tick=100, observation=observation,
        raw_response="bad json{{{", start_time=1000.0
    )
    assert action["type"] == "hold"
    print("  ✓ Malformed JSON returns hold")
    
    # Test invalid action
    def mock_parser(resp, fac, state):
        return {"type": "hold"}, "invalid_action"
    
    action, log = handle_agent_response(
        faction_id="red", tick=100, observation=observation,
        raw_response=json.dumps({"action": {"type": "bad"}}),
        start_time=1000.0,
        parser_func=mock_parser
    )
    assert action["type"] == "hold"
    assert log["parsedActionOrFailure"]["reason"] == "invalid_action"
    print("  ✓ Invalid action returns hold")
    return True


def test_decision_logging():
    """Test decision attempt logging."""
    print("\nTest 5: Decision logging...")
    import src.agent_adapter.logging as logging_module
    logging_module._decision_logger = None  # Reset
    
    log_decision(
        faction_id="red",
        tick=100,
        observation_summary={"matchId": "test"},
        raw_response='{"action": {"type": "hold"}}',
        parsed_action_or_failure={"type": "hold"},
        latency_ms=25
    )
    
    latest = get_latest_decision("red")
    assert latest is not None
    assert latest.factionId == "red"
    assert latest.tick == 100
    assert latest.latencyMs == 25
    print("  ✓ Decision logged correctly")
    print(f"  ✓ Logged: faction={latest.factionId}, tick={latest.tick}, latency={latest.latencyMs}ms")
    return True


def test_mixed_control():
    """Test mixed scripted/agent control."""
    print("\nTest 6: Mixed control (scripted + agent)...")
    engine = SimulationEngine()
    match_state = engine.start_match()
    match_state.lifecycle_state = LifecycleState.RUNNING
    
    adapter = AgentAdapter()
    adapter.set_simulation_state(match_state)
    
    # Red and blue agent-controlled
    adapter.set_control_mode("red", ControllerMode.AGENT)
    adapter.set_control_mode("blue", ControllerMode.AGENT)
    # Green and yellow remain scripted
    
    assert adapter.is_agent_controlled("red")
    assert adapter.is_agent_controlled("blue")
    assert not adapter.is_agent_controlled("green")
    assert not adapter.is_agent_controlled("yellow")
    print("  ✓ Control modes set correctly")
    
    # Run simulation - need to advance ticks manually
    initial_tick = match_state.tick
    advance_ticks(engine, 20)
    
    assert match_state.tick > initial_tick
    print(f"  ✓ Simulation advanced from tick {initial_tick} to {match_state.tick}")
    return True


def test_full_integration():
    """Test full agent integration in match."""
    print("\nTest 7: Full integration test...")
    engine = SimulationEngine()
    match_state = engine.start_match()
    match_state.lifecycle_state = LifecycleState.RUNNING
    
    adapter = AgentAdapter()
    adapter.set_simulation_state(match_state)
    adapter.set_control_mode("red", ControllerMode.AGENT)
    
    # Get action for agent faction
    action, error = adapter.get_faction_action("red", match_state.tick, int(match_state.time_remaining_sec))
    
    # Should get hold (fallback due to no MCP client)
    assert action["type"] == "hold"
    print("  ✓ Agent adapter returns fallback action")
    
    # Apply action to simulation
    events = engine.apply_faction_action("red", action)
    assert len(events) >= 1
    assert events[0]["type"] == "hold"
    print("  ✓ Fallback action applied to simulation")
    return True


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 60)
    print("AGENT ADAPTER SMOKE TEST")
    print("=" * 60)
    
    tests = [
        test_observation_build,
        test_action_parser_valid,
        test_action_parser_invalid,
        test_fallback_behavior,
        test_decision_logging,
        test_mixed_control,
        test_full_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  ✗ FAILED: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
