"""
Integration tests for mixed-control matches.
Tests scripted + agent faction coexistence in same match.
"""

import pytest
from src.sim.engine import SimulationEngine
from src.sim.models import LifecycleState
from src.agent_adapter.adapter import AgentAdapter, ControllerMode
from src.agent_adapter.observation_builder import build_observation


class TestMixedControl:
    """Tests for mixed-control match scenarios."""

    def advance_ticks(self, engine, num_ticks):
        """Helper to advance simulation ticks."""
        for _ in range(num_ticks):
            engine.last_tick_time -= engine.tick_interval
            engine.update()

    def test_scripted_factions_only(self):
        """Test match runs with all scripted factions."""
        engine = SimulationEngine()
        match_state = engine.start_match()
        match_state.lifecycle_state = LifecycleState.RUNNING
        
        adapter = AgentAdapter()
        adapter.set_simulation_state(match_state)
        
        # Run a few ticks
        self.advance_ticks(engine, 10)
        
        assert match_state.tick > 0
        assert match_state.lifecycle_state == LifecycleState.RUNNING

    def test_single_agent_faction(self):
        """Test match with one agent-controlled faction."""
        engine = SimulationEngine()
        match_state = engine.start_match()
        match_state.lifecycle_state = LifecycleState.RUNNING
        
        adapter = AgentAdapter()
        adapter.set_simulation_state(match_state)
        adapter.set_control_mode("red", ControllerMode.AGENT)
        
        # Other factions remain scripted
        assert adapter.get_control_mode("red") == ControllerMode.AGENT
        assert adapter.get_control_mode("blue") == ControllerMode.SCRIPTED
        assert adapter.get_control_mode("green") == ControllerMode.SCRIPTED
        assert adapter.get_control_mode("yellow") == ControllerMode.SCRIPTED
        
        # Run a few ticks
        self.advance_ticks(engine, 10)
        
        assert match_state.tick > 0

    def test_multiple_agent_factions(self):
        """Test match with multiple agent-controlled factions."""
        engine = SimulationEngine()
        match_state = engine.start_match()
        match_state.lifecycle_state = LifecycleState.RUNNING
        
        adapter = AgentAdapter()
        adapter.set_simulation_state(match_state)
        adapter.set_control_mode("red", ControllerMode.AGENT)
        adapter.set_control_mode("blue", ControllerMode.AGENT)
        
        assert adapter.is_agent_controlled("red")
        assert adapter.is_agent_controlled("blue")
        assert not adapter.is_agent_controlled("green")
        assert not adapter.is_agent_controlled("yellow")
        
        # Run a few ticks
        self.advance_ticks(engine, 10)
        
        assert match_state.tick > 0

    def test_all_agent_factions(self):
        """Test match with all factions agent-controlled."""
        engine = SimulationEngine()
        match_state = engine.start_match()
        match_state.lifecycle_state = LifecycleState.RUNNING
        
        adapter = AgentAdapter()
        adapter.set_simulation_state(match_state)
        
        for faction_id in ["red", "blue", "green", "yellow"]:
            adapter.set_control_mode(faction_id, ControllerMode.AGENT)
            assert adapter.is_agent_controlled(faction_id)
        
        # Run a few ticks
        self.advance_ticks(engine, 10)
        
        assert match_state.tick > 0

    def test_control_mode_switching(self):
        """Test switching control modes mid-match."""
        engine = SimulationEngine()
        match_state = engine.start_match()
        match_state.lifecycle_state = LifecycleState.RUNNING
        
        adapter = AgentAdapter()
        adapter.set_simulation_state(match_state)
        
        # Start as scripted
        assert adapter.get_control_mode("red") == ControllerMode.SCRIPTED
        
        # Switch to agent
        adapter.set_control_mode("red", ControllerMode.AGENT)
        assert adapter.get_control_mode("red") == ControllerMode.AGENT
        
        # Switch back to scripted
        adapter.set_control_mode("red", ControllerMode.SCRIPTED)
        assert adapter.get_control_mode("red") == ControllerMode.SCRIPTED

    def test_agent_observation_build(self):
        """Test building observation for agent-controlled faction."""
        engine = SimulationEngine()
        match_state = engine.start_match()
        match_state.lifecycle_state = LifecycleState.RUNNING
        
        # Build observation for red faction
        observation = build_observation(match_state, "red", recent_events=[])
        
        # Verify observation structure per SPEC.md
        assert observation.match["matchId"] == match_state.match_id
        assert observation.match["tick"] == match_state.tick
        assert observation.self.id == "red"
        assert observation.self.status in ["active", "crippled", "eliminated"]
        assert "factions" in observation.world
        assert "targets" in observation.world
        assert "missiles" in observation.world
        assert isinstance(observation.recentEvents, list)
        assert isinstance(observation.legalActions, list)
        
        # Should have hold action at minimum
        action_types = [a.type for a in observation.legalActions]
        assert "hold" in action_types

    def test_scripted_and_agent_coexist(self):
        """Test scripted and agent factions coexist and simulate correctly."""
        engine = SimulationEngine()
        match_state = engine.start_match()
        match_state.lifecycle_state = LifecycleState.RUNNING
        
        adapter = AgentAdapter()
        adapter.set_simulation_state(match_state)
        
        # Red and blue agent-controlled, green and yellow scripted
        adapter.set_control_mode("red", ControllerMode.AGENT)
        adapter.set_control_mode("blue", ControllerMode.AGENT)
        # green, yellow remain SCRIPTED (default)
        
        # Run simulation for multiple ticks
        initial_tick = match_state.tick
        self.advance_ticks(engine, 20)
        
        # Match should progress
        assert match_state.tick > initial_tick
        # All factions should still exist
        assert len(match_state.factions) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
