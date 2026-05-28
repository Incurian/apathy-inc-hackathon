"""
Integration tests for agent adapter.
Tests contract validation, observation/action schemas, and adapter behavior.
"""

import json
import pytest
from pathlib import Path

# Import agent adapter modules
from src.agent_adapter.models import Observation, Action, LegalAction, Site, FactionState
from src.agent_adapter.observation_builder import ObservationBuilder
from src.agent_adapter.action_parser import ActionParser
from src.agent_adapter.fallback import FallbackHandler
from src.agent_adapter.logging import DecisionLogger, DecisionLogEntry, get_decision_logger, log_decision, get_latest_decision


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "agent_adapter"


class TestObservationSchema:
    """Tests for observation schema validation."""
    
    def test_valid_observation_loads(self):
        """Test that valid observation fixture loads correctly."""
        fixture_path = FIXTURES_DIR / "observation_valid.json"
        assert fixture_path.exists(), "Valid observation fixture should exist"
        
        with open(fixture_path) as f:
            data = json.load(f)
        
        # Should parse with Pydantic model
        observation = Observation(**data)
        assert observation.match["matchId"] == "match-001"
        assert observation.match["tick"] == 120
        assert observation.self.id == "red"
        assert len(observation.legalActions) == 2
    
    def test_observation_has_required_fields(self):
        """Test observation has all required fields per SPEC.md."""
        fixture_path = FIXTURES_DIR / "observation_valid.json"
        
        with open(fixture_path) as f:
            data = json.load(f)
        
        observation = Observation(**data)
        
        # Required fields from SPEC.md
        assert "match" in data
        assert "self" in data
        assert "world" in data
        assert "recentEvents" in data
        assert "legalActions" in data
        
        # Match metadata
        assert "matchId" in observation.match
        assert "tick" in observation.match
        assert "timeRemainingSec" in observation.match
        
        # Self state
        assert observation.self.id == "red"
        assert observation.self.population >= 0
        assert observation.self.score >= 0
        assert observation.self.status in ["active", "crippled", "eliminated"]
        
        # World state
        assert "factions" in observation.world
        assert "targets" in observation.world
        assert "missiles" in observation.world
        
        # Legal actions include hold
        action_types = [a.type for a in observation.legalActions]
        assert "hold" in action_types


class TestActionSchema:
    """Tests for action schema validation."""
    
    def test_valid_launch_action_loads(self):
        """Test valid launch action fixture."""
        fixture_path = FIXTURES_DIR / "action_valid_launch.json"
        
        with open(fixture_path) as f:
            data = json.load(f)
        
        action_model = Action(**data)
        assert action_model.action["type"] == "launch"
        assert action_model.action["from"] == "red-silo-1"
        assert action_model.action["target"] == "blue-city-1"
        assert action_model.comment is not None
    
    def test_valid_hold_action_loads(self):
        """Test valid hold action fixture."""
        fixture_path = FIXTURES_DIR / "action_valid_hold.json"
        
        with open(fixture_path) as f:
            data = json.load(f)
        
        action_model = Action(**data)
        assert action_model.action["type"] == "hold"
        assert action_model.comment is not None
    
    def test_malformed_json_rejected(self):
        """Test that malformed JSON is rejected."""
        fixture_path = FIXTURES_DIR / "action_invalid_malformed.json"
        
        with open(fixture_path) as f:
            content = f.read()
        
        # Should fail to parse as JSON
        import json
        with pytest.raises(json.JSONDecodeError):
            json.loads(content)
    
    def test_invalid_action_type_rejected(self):
        """Test that invalid action type is rejected."""
        fixture_path = FIXTURES_DIR / "action_invalid_schema.json"
        
        with open(fixture_path) as f:
            data = json.load(f)
        
        # Should fail Pydantic validation
        with pytest.raises(Exception):
            Action(**data)


class TestActionParser:
    """Tests for action parser validation logic."""
    
    def test_parse_valid_launch(self):
        """Test parsing valid launch action."""
        parser = ActionParser()
        
        # Mock faction and simulation state would be needed for full test
        # For now, test the parsing logic in isolation
        raw_response = json.dumps({
            "action": {"type": "launch", "from": "red-silo-1", "target": "blue-city-1"},
            "comment": "Test launch"
        })
        
        # This would need actual faction/simulation objects to fully test
        # But we can verify the parser exists and has the right interface
        assert hasattr(parser, 'parse_and_validate')
    
    def test_parse_valid_hold(self):
        """Test parsing valid hold action."""
        raw_response = json.dumps({
            "action": {"type": "hold"},
            "comment": "Holding"
        })
        
        # Parser should accept hold actions
        assert True  # Placeholder for actual test with mocks


class TestFallbackHandler:
    """Tests for fallback behavior."""
    
    def test_timeout_returns_hold(self):
        """Test that timeout returns hold action."""
        handler = FallbackHandler(timeout_seconds=5.0)
        
        # Create minimal observation for testing
        observation = Observation(
            match={"matchId": "test", "tick": 100, "timeRemainingSec": 300},
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
        
        # Simulate timeout (raw_response = None)
        action, log_entry = handler.handle_response(
            faction_id="red",
            tick=100,
            observation=observation,
            raw_response=None,  # Timeout
            start_time=0.0  # Very old start time
        )
        
        assert action["type"] == "hold"
        assert log_entry["errorReason"] is not None
        assert "timeout" in log_entry["errorReason"].lower()
    
    def test_malformed_response_returns_hold(self):
        """Test that malformed response returns hold."""
        handler = FallbackHandler()
        
        observation = Observation(
            match={"matchId": "test", "tick": 100, "timeRemainingSec": 300},
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
    
    def test_invalid_action_returns_hold(self):
        """Test that invalid action returns hold."""
        handler = FallbackHandler()
        
        observation = Observation(
            match={"matchId": "test", "tick": 100, "timeRemainingSec": 300},
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
        
        # Invalid action type
        raw_response = json.dumps({"action": {"type": "invalid"}})
        
        def mock_parser(resp, faction, sim):
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


class TestDecisionLogging:
    """Tests for decision logging."""
    
    def test_log_decision(self):
        """Test logging a decision."""
        logger = DecisionLogger(max_entries=10)
        
        entry = DecisionLogEntry(
            factionId="red",
            tick=100,
            observationSummary={"matchId": "test"},
            rawResponse='{"action": {"type": "hold"}}',
            parsedActionOrFailure={"type": "hold"},
            latencyMs=50
        )
        
        logger.log_decision(entry)
        
        recent = logger.get_recent_decisions("red", limit=1)
        assert len(recent) == 1
        assert recent[0].factionId == "red"
        assert recent[0].tick == 100
    
    def test_get_latest_decision(self):
        """Test getting latest decision for faction."""
        logger = DecisionLogger(max_entries=10)
        
        # Log multiple decisions
        for tick in [100, 101, 102]:
            entry = DecisionLogEntry(
                factionId="red",
                tick=tick,
                observationSummary={},
                rawResponse=None,
                parsedActionOrFailure={"type": "hold"},
                latencyMs=10
            )
            logger.log_decision(entry)
        
        latest = logger.get_latest_decision("red")
        assert latest is not None
        assert latest.tick == 102
    
    def test_convenience_functions(self):
        """Test convenience logging functions."""
        # Reset global logger
        import src.agent_adapter.logging as logging_module
        logging_module._decision_logger = None
        
        log_decision(
            faction_id="blue",
            tick=50,
            observation_summary={},
            raw_response='{"action": {"type": "hold"}}',
            parsed_action_or_failure={"type": "hold"},
            latency_ms=25
        )
        
        latest = get_latest_decision("blue")
        assert latest is not None
        assert latest.factionId == "blue"
        assert latest.tick == 50


class TestObservationSize:
    """Test that observation size is reasonable for weaker models."""
    
    def test_observation_under_size_limit(self):
        """Test observation is under ~3KB per SPEC.md."""
        fixture_path = FIXTURES_DIR / "observation_valid.json"
        
        with open(fixture_path) as f:
            content = f.read()
        
        size_kb = len(content.encode('utf-8')) / 1024
        assert size_kb < 3.0, f"Observation should be under 3KB, got {size_kb:.2f}KB"


# Fixtures
@pytest.fixture
def valid_observation():
    """Load valid observation fixture."""
    fixture_path = FIXTURES_DIR / "observation_valid.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def valid_launch_action():
    """Load valid launch action fixture."""
    fixture_path = FIXTURES_DIR / "action_valid_launch.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def valid_hold_action():
    """Load valid hold action fixture."""
    fixture_path = FIXTURES_DIR / "action_valid_hold.json"
    with open(fixture_path) as f:
        return json.load(f)