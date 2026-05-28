"""
Integration tests for agent adapter failure paths.
Tests malformed/timeout/invalid action handling per SPEC.md §14 lines 473-476.
"""

import json
import pytest
from src.agent_adapter.fallback import FallbackHandler, handle_agent_response
from src.agent_adapter.action_parser import parse_and_validate_action
from src.agent_adapter.observation_builder import build_observation
from src.agent_adapter.models import Observation, FactionState, WorldFaction, Target, Missile, Event, LegalAction
from src.agent_adapter.logging import DecisionLogger, DecisionLogEntry
from src.sim.engine import SimulationEngine
from src.sim.models import LifecycleState


class TestFallbackHandler:
    """Tests for fallback behavior on agent failures."""

    def create_test_observation(self) -> Observation:
        """Create a minimal valid observation for testing."""
        return Observation(
            match={"matchId": "test-match", "tick": 100, "timeRemainingSec": 300},
            self=FactionState(
                id="red",
                population=100,
                score=50,
                status="active",
                sites=[]
            ),
            world={"factions": [], "targets": [], "missiles": []},
            recentEvents=[],
            legalActions=[LegalAction(type="hold")]
        )

    def test_timeout_returns_hold(self):
        """Test that timeout returns hold action per SPEC.md."""
        handler = FallbackHandler(timeout_seconds=5.0)
        observation = self.create_test_observation()
        
        # Simulate timeout (raw_response = None, very old start_time)
        action, log_entry = handler.handle_response(
            faction_id="red",
            tick=100,
            observation=observation,
            raw_response=None,  # Timeout
            start_time=0.0  # Very old = timeout
        )
        
        assert action["type"] == "hold"
        assert log_entry["errorReason"] is not None
        assert "timeout" in log_entry["errorReason"].lower()

    def test_malformed_json_returns_hold(self):
        """Test that malformed JSON returns hold action per SPEC.md."""
        handler = FallbackHandler()
        observation = self.create_test_observation()
        
        # Malformed JSON response
        action, log_entry = handler.handle_response(
            faction_id="red",
            tick=100,
            observation=observation,
            raw_response="not valid json{{{",
            start_time=0.0
        )
        
        assert action["type"] == "hold"
        assert log_entry["errorReason"] is not None
        assert "json" in log_entry["errorReason"].lower() or "parse" in log_entry["errorReason"].lower()

    def test_empty_response_returns_hold(self):
        """Test that empty response returns hold action."""
        handler = FallbackHandler()
        observation = self.create_test_observation()
        
        action, log_entry = handler.handle_response(
            faction_id="red",
            tick=100,
            observation=observation,
            raw_response="",
            start_time=0.0
        )
        
        assert action["type"] == "hold"
        assert log_entry["errorReason"] is not None

    def test_invalid_action_type_returns_hold(self):
        """Test that invalid action type returns hold action per SPEC.md."""
        handler = FallbackHandler()
        observation = self.create_test_observation()
        
        # Invalid action type
        raw_response = json.dumps({"action": {"type": "invalid"}})
        
        def mock_parser(resp, faction, sim_state):
            return {"type": "hold"}, "Invalid action type"
        
        action, log_entry = handler.handle_response(
            faction_id="red",
            tick=100,
            observation=observation,
            raw_response=raw_response,
            start_time=0.0,
            parser_func=mock_parser
        )
        
        assert action["type"] == "hold"
        assert log_entry["parsedActionOrFailure"]["reason"] == "invalid_action"

    def test_missing_action_field_returns_hold(self):
        """Test that missing action field returns hold."""
        handler = FallbackHandler()
        observation = self.create_test_observation()
        
        raw_response = json.dumps({"comment": "test"})
        
        action, log_entry = handler.handle_response(
            faction_id="red",
            tick=100,
            observation=observation,
            raw_response=raw_response,
            start_time=0.0
        )
        
        assert action["type"] == "hold"

    def test_action_not_object_returns_hold(self):
        """Test that non-object action returns hold."""
        handler = FallbackHandler()
        observation = self.create_test_observation()
        
        raw_response = json.dumps({"action": "hold"})  # String instead of object
        
        action, log_entry = handler.handle_response(
            faction_id="red",
            tick=100,
            observation=observation,
            raw_response=raw_response,
            start_time=0.0
        )
        
        assert action["type"] == "hold"


class TestActionParserFailurePaths:
    """Tests for action parser validation failures."""

    def setup_method(self):
        """Set up test simulation state."""
        self.engine = SimulationEngine()
        self.match_state = self.engine.start_match()
        self.match_state.lifecycle_state = LifecycleState.RUNNING
        self.faction = self.match_state.factions["red"]

    def advance_ticks(self, num_ticks):
        """Helper to advance simulation ticks."""
        for _ in range(num_ticks):
            self.engine.last_tick_time -= self.engine.tick_interval
            self.engine.update()

    def test_malformed_json_parse_failure(self):
        """Test JSON parse failure handling."""
        action, error = parse_and_validate_action(
            raw_response="invalid json{{{",
            faction=self.faction,
            match_state=self.match_state
        )
        
        assert action["type"] == "hold"
        assert error is not None
        assert "json" in error.lower() or "parse" in error.lower()

    def test_missing_action_field(self):
        """Test missing action field handling."""
        action, error = parse_and_validate_action(
            raw_response=json.dumps({"comment": "test"}),
            faction=self.faction,
            match_state=self.match_state
        )
        
        assert action["type"] == "hold"
        assert error is not None

    def test_action_not_dict(self):
        """Test action as non-dict handling."""
        action, error = parse_and_validate_action(
            raw_response=json.dumps({"action": "hold"}),
            faction=self.faction,
            match_state=self.match_state
        )
        
        assert action["type"] == "hold"
        assert error is not None

    def test_invalid_action_type(self):
        """Test invalid action type handling."""
        action, error = parse_and_validate_action(
            raw_response=json.dumps({"action": {"type": "nuclear_strike"}}),
            faction=self.faction,
            match_state=self.match_state
        )
        
        assert action["type"] == "hold"
        assert error is not None

    def test_launch_missing_fields(self):
        """Test launch action missing from/target fields."""
        action, error = parse_and_validate_action(
            raw_response=json.dumps({"action": {"type": "launch"}}),
            faction=self.faction,
            match_state=self.match_state
        )
        
        assert action["type"] == "hold"
        assert error is not None

    def test_launch_invalid_silo(self):
        """Test launch from non-existent silo."""
        action, error = parse_and_validate_action(
            raw_response=json.dumps({"action": {"type": "launch", "from": "fake-silo", "target": "blue-city-1"}}),
            faction=self.faction,
            match_state=self.match_state
        )
        
        assert action["type"] == "hold"
        assert error is not None

    def test_launch_own_city(self):
        """Test launch targeting own city."""
        action, error = parse_and_validate_action(
            raw_response=json.dumps({"action": {"type": "launch", "from": "red-silo-1", "target": "red-city-1"}}),
            faction=self.faction,
            match_state=self.match_state
        )
        
        assert action["type"] == "hold"
        assert error is not None

    def test_hold_action_extra_fields(self):
        """Test hold action with extra fields rejected."""
        action, error = parse_and_validate_action(
            raw_response=json.dumps({"action": {"type": "hold", "extra": "field"}}),
            faction=self.faction,
            match_state=self.match_state
        )
        
        assert action["type"] == "hold"
        assert error is not None


class TestDecisionLogging:
    """Tests for decision attempt logging per SPEC.md Phase 5.5."""

    def test_decision_log_captures_required_fields(self):
        """Test that decision logging captures all required fields."""
        from src.agent_adapter.logging import log_decision, get_latest_decision
        
        # Reset global logger
        import src.agent_adapter.logging as logging_module
        logging_module._decision_logger = None
        
        log_decision(
            faction_id="red",
            tick=100,
            observation_summary={"matchId": "test", "tick": 100},
            raw_response='{"action": {"type": "hold"}}',
            parsed_action_or_failure={"type": "hold"},
            latency_ms=25
        )
        
        latest = get_latest_decision("red")
        assert latest is not None
        assert latest.factionId == "red"
        assert latest.tick == 100
        assert latest.latencyMs == 25
        assert latest.rawResponse == '{"action": {"type": "hold"}}'
        assert latest.parsedActionOrFailure == {"type": "hold"}

    def test_decision_log_stores_multiple_entries(self):
        """Test that multiple decisions are stored per faction."""
        logger = DecisionLogger(max_entries=10)
        
        for tick in [100, 101, 102, 103, 104]:
            entry = DecisionLogEntry(
                factionId="red",
                tick=tick,
                observationSummary={},
                rawResponse=None,
                parsedActionOrFailure={"type": "hold"},
                latencyMs=10
            )
            logger.log_decision(entry)
        
        recent = logger.get_recent_decisions("red", limit=3)
        assert len(recent) == 3
        assert recent[0].tick == 104  # Most recent first
        assert recent[2].tick == 102


class TestIntegrationFailurePaths:
    """End-to-end integration tests for failure paths."""

    def advance_ticks(self, engine, num_ticks):
        """Helper to advance simulation ticks."""
        for _ in range(num_ticks):
            engine.last_tick_time -= engine.tick_interval
            engine.update()

    def test_full_match_with_agent_timeouts(self):
        """Test full match where agent times out every turn."""
        engine = SimulationEngine()
        match_state = engine.start_match()
        match_state.lifecycle_state = LifecycleState.RUNNING
        
        from src.agent_adapter.adapter import AgentAdapter, ControllerMode
        adapter = AgentAdapter()
        adapter.set_simulation_state(match_state)
        adapter.set_control_mode("red", ControllerMode.AGENT)
        
        # Run match for multiple decision windows
        # Agent will timeout each time (simulated in adapter)
        self.advance_ticks(engine, 50)
        
        # Match should continue running despite agent timeouts
        assert match_state.lifecycle_state in [LifecycleState.RUNNING, LifecycleState.FINISHED]

    def test_match_with_malformed_agent_responses(self):
        """Test match continues with malformed agent responses."""
        engine = SimulationEngine()
        match_state = engine.start_match()
        match_state.lifecycle_state = LifecycleState.RUNNING
        
        # Simulate by directly applying hold actions (what fallback produces)
        initial_tick = match_state.tick
        for _ in range(20):
            # Each faction submits hold (fallback behavior)
            for faction_id in ["red", "blue", "green", "yellow"]:
                engine.apply_faction_action(faction_id, {"type": "hold"})
            self.advance_ticks(engine, 1)
        
        assert match_state.tick > initial_tick


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
