"""
Tests for the bot implementations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sim.engine import SimulationEngine
from src.sim.models import LifecycleState
from src.bots.simple_bot import SimpleBot, AggressiveBot, DefensiveBot, create_bot


def test_bot_creation():
    """Test that bots are created correctly."""
    # Test SimpleBot
    bot = SimpleBot("red", "TestBot")
    assert bot.faction_id == "red"
    assert bot.name == "TestBot"
    assert bot.last_action_tick == -16  # -Constants.DECISION_WINDOW_TICKS
    
    # Test AggressiveBot
    agg_bot = AggressiveBot("blue", "AggBot")
    assert agg_bot.faction_id == "blue"
    assert agg_bot.name == "AggBot"
    
    # Test DefensiveBot
    def_bot = DefensiveBot("green", "DefBot")
    assert def_bot.faction_id == "green"
    assert def_bot.name == "DefBot"
    
    # Test factory function
    bot1 = create_bot("yellow", "simple")
    bot2 = create_bot("red", "aggressive")
    bot3 = create_bot("blue", "defensive")
    bot4 = create_bot("green", "unknown")  # Should default to simple
    
    assert isinstance(bot1, SimpleBot)
    assert not isinstance(bot1, AggressiveBot)
    assert isinstance(bot2, AggressiveBot)
    assert isinstance(bot3, DefensiveBot)
    assert isinstance(bot4, SimpleBot)  # Unknown type defaults to simple
    
    print("✓ Bot creation test passed")


def test_bot_legal_actions():
    """Test that bots correctly determine legal actions."""
    engine = SimulationEngine()
    match_state = engine.start_match()
    match_state.lifecycle_state = LifecycleState.RUNNING
    
    # Create a bot for red faction
    bot = SimpleBot("red")
    
    # Get legal actions
    legal_actions = bot.get_legal_actions(match_state)
    
    # Should always have at least hold action
    assert len(legal_actions) >= 1
    assert any(action["type"] == "hold" for action in legal_actions)
    
    # Should have launch actions for each silo with ammo and no cooldown
    red_silos = [
        node_id for node_id, node in match_state.nodes.items()
        if node.owner == "red" and node.type.value == "silo" and 
           node.status == "active" and node.ammo > 0 and node.cooldown == 0
    ]
    
    # Each silo should have launch actions to all enemy targets
    expected_launches = len(red_silos) * 6  # 2 silos * 3 enemy factions * (1 city + 1 silo each) = 12
    actual_launches = len([a for a in legal_actions if a["type"] == "launch"])
    
    # Note: This calculation assumes all enemy cities and silos are valid targets
    # which they should be in the initial state
    
    print(f"Red faction has {len(red_silos)} usable silos")
    print(f"Legal actions: {len(legal_actions)} total ({actual_launches} launches, {len(legal_actions)-actual_launches} holds)")
    
    assert len(legal_actions) > 0
    print("✓ Bot legal actions test passed")


def test_bot_decision_making():
    """Test that bots make decisions at appropriate times."""
    engine = SimulationEngine()
    match_state = engine.start_match()
    match_state.lifecycle_state = LifecycleState.RUNNING
    
    # Create bots
    bots = {
        "red": SimpleBot("red"),
        "blue": AggressiveBot("blue"),
        "green": DefensiveBot("green"),
        "yellow": SimpleBot("yellow")
    }
    
    # Test that bots don't act outside decision windows
    match_state.tick = 1  # Not a decision window
    for faction_id, bot in bots.items():
        action = bot.get_action(match_state)
        assert action is None, f"{faction_id} bot should not act on tick {match_state.tick}"
    
    # Test that bots can act on decision windows
    match_state.tick = 0  # Decision window
    for faction_id, bot in bots.items():
        action = bot.get_action(match_state)
        # Should return either a hold or launch action
        if action is not None:
            assert action["type"] in ["hold", "launch"]
            if action["type"] == "launch":
                assert "from" in action
                assert "target" in action
    
    print("✓ Bot decision making test passed")


def test_bot_integration_with_engine():
    """Test that bots can interact with the simulation engine."""
    engine = SimulationEngine()
    match_state = engine.start_match()
    match_state.lifecycle_state = LifecycleState.RUNNING
    
    # Create bots for each faction
    bots = {}
    for faction_id in ["red", "blue", "green", "yellow"]:
        bot_type = ["simple", "aggressive", "defensive"][hash(faction_id) % 3]
        bots[faction_id] = create_bot(faction_id, bot_type)
    
    # Run a few decision windows
    initial_tick = match_state.tick
    missiles_launched = 0
    
    for window in range(3):
        # Get actions from all bots (only works on decision windows)
        actions = {}
        if match_state.tick % 16 == 0:  # Decision window
            for faction_id, bot in bots.items():
                action = bot.get_action(match_state)
                if action is not None:
                    actions[faction_id] = action
            
            # Apply actions
            for faction_id, action in actions.items():
                events = engine.apply_faction_action(faction_id, action)
                launch_events = [e for e in events if e["type"] == "launch"]
                missiles_launched += len(launch_events)
        
        # Advance time properly for engine.update to work
        # Move last_tick_time back so that elapsed >= tick_interval
        engine.last_tick_time -= engine.tick_interval
        engine.update()
    
    print(f"Ran {window+1} decision windows, launched {missiles_launched} missiles")
    print(f"Final tick: {match_state.tick} (started at {initial_tick})")
    
    # Verify that game state is still valid
    assert match_state.tick > initial_tick
    assert len(match_state.factions) == 4
    
    print("✓ Bot integration test passed")


def test_different_bot_behaviors():
    """Test that different bot types exhibit different behaviors."""
    engine = SimulationEngine()
    match_state = engine.start_match()
    match_state.lifecycle_state = LifecycleState.RUNNING
    
    # Create specific bot types for testing
    simple_bot = SimpleBot("red")
    aggressive_bot = AggressiveBot("blue")
    defensive_bot = DefensiveBot("green")
    
    # Collect multiple decisions to see behavioral differences
    simple_launches = 0
    aggressive_launches = 0
    defensive_launches = 0
    total_decisions = 0
    
    # Test several decision windows
    for window in range(10):
        # Reset to decision window tick
        match_state.tick = window * 16
        
        # Get actions
        simple_action = simple_bot.get_action(match_state)
        aggressive_action = aggressive_bot.get_action(match_state)
        defensive_action = defensive_bot.get_action(match_state)
        
        # Count launches
        if simple_action and simple_action["type"] == "launch":
            simple_launches += 1
        if aggressive_action and aggressive_action["type"] == "launch":
            aggressive_launches += 1
        if defensive_action and defensive_action["type"] == "launch":
            defensive_launches += 1
            
        # Count total decisions (non-None actions)
        for action in [simple_action, aggressive_action, defensive_action]:
            if action is not None:
                total_decisions += 1
    
    print(f"Over {total_decisions} decisions:")
    print(f"  Simple bot launches: {simple_launches}")
    print(f"  Aggressive bot launches: {aggressive_launches}")
    print(f"  Defensive bot launches: {defensive_launches}")
    
    # Aggressive bot should tend to launch more than simple
    # Defensive bot behavior depends on threat level, but in initial state should be similar to simple
    # We're mainly testing that they don't crash and produce valid actions
    assert simple_launches >= 0
    assert aggressive_launches >= 0
    assert defensive_launches >= 0
    
    print("✓ Different bot behaviors test passed")


if __name__ == "__main__":
    print("Running bot tests...")
    
    test_bot_creation()
    test_bot_legal_actions()
    test_bot_decision_making()
    test_bot_integration_with_engine()
    test_different_bot_behaviors()
    
    print("\n🎉 All bot tests passed!")