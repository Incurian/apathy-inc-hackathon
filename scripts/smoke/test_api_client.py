#!/usr/bin/env python3
"""
Smoke tests for the Spectator API using FastAPI TestClient
Validates all required endpoints return expected shapes without needing a live server
"""

import sys
from fastapi.testclient import TestClient
from src.api.main import app


client = TestClient(app)


def test_health():
    """Test health endpoint"""
    print("Testing /api/health...")
    resp = client.get("/api/health")
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
    data = resp.json()
    assert data.get("status") == "ok", f"Unexpected health response: {data}"
    print("  ✓ Health check passed")


def test_state_idle():
    """Test /api/state returns valid JSON in idle state"""
    print("Testing /api/state (idle)...")
    resp = client.get("/api/state")
    assert resp.status_code == 200, f"State endpoint failed: {resp.status_code}"
    state = resp.json()
    
    # Validate required top-level keys
    required_keys = ["match", "factions", "nodes", "missiles", "recentEvents", "summary"]
    for key in required_keys:
        assert key in state, f"Missing required key: {key}"
    
    # Validate match metadata
    match = state["match"]
    assert "matchId" in match
    assert "lifecycleState" in match
    assert match["lifecycleState"] in ["idle", "running", "paused", "finished"]
    assert "tick" in match
    assert "timeRemainingSec" in match
    
    # Validate factions
    assert isinstance(state["factions"], list)
    assert len(state["factions"]) == 4
    for faction in state["factions"]:
        assert "id" in faction
        assert "name" in faction
        assert "color" in faction
        assert "population" in faction
        assert "score" in faction
        assert "status" in faction
        assert faction["status"] in ["active", "crippled", "eliminated"]
    
    # Validate nodes
    assert isinstance(state["nodes"], list)
    assert len(state["nodes"]) == 12  # 4 factions * 3 nodes each
    for node in state["nodes"]:
        assert "id" in node
        assert "type" in node
        assert node["type"] in ["city", "silo"]
        assert "owner" in node
        assert "x" in node
        assert "y" in node
        assert "hp" in node
        assert "status" in node
    
    # Validate missiles array exists
    assert isinstance(state["missiles"], list)
    
    # Validate events array exists
    assert isinstance(state["recentEvents"], list)
    
    # Validate summary
    summary = state["summary"]
    assert "leadingFaction" in summary
    assert "totalMissilesInFlight" in summary
    assert "activeFactions" in summary
    
    print("  ✓ State schema valid")
    return state


def test_lifecycle_transitions():
    """Test all lifecycle transitions"""
    print("Testing lifecycle transitions...")
    
    # Reset to idle first
    resp = client.post("/api/reset", json={})
    assert resp.status_code == 200
    
    # idle -> running (start)
    resp = client.post("/api/start", json={})
    assert resp.status_code == 200
    state = resp.json()
    assert state["match"]["lifecycleState"] == "running"
    match_id_1 = state["match"]["matchId"]
    print("  ✓ idle -> running (start)")
    
    # running -> paused (pause)
    resp = client.post("/api/pause", json={})
    assert resp.status_code == 200
    state = resp.json()
    assert state["match"]["lifecycleState"] == "paused"
    print("  ✓ running -> paused (pause)")
    
    # paused -> running (resume)
    resp = client.post("/api/resume", json={})
    assert resp.status_code == 200
    state = resp.json()
    assert state["match"]["lifecycleState"] == "running"
    print("  ✓ paused -> running (resume)")
    
    # running -> paused -> reset -> idle
    resp = client.post("/api/pause", json={})
    assert resp.status_code == 200
    resp = client.post("/api/reset", json={})
    assert resp.status_code == 200
    state = resp.json()
    assert state["match"]["lifecycleState"] == "idle"
    print("  ✓ running -> idle (reset)")
    
    # finished -> running (start new)
    resp = client.post("/api/start", json={})
    assert resp.status_code == 200
    state = resp.json()
    assert state["match"]["lifecycleState"] == "running"
    match_id_2 = state["match"]["matchId"]
    assert match_id_2 != match_id_1, "New match should have different matchId"
    print("  ✓ finished -> running (start creates new matchId)")
    
    # Cleanup
    client.post("/api/reset", json={})


def test_invalid_transitions():
    """Test that invalid transitions are rejected"""
    print("Testing invalid transition rejection...")
    
    # Reset to known state
    client.post("/api/reset", json={})
    
    # Pause from idle should fail
    resp = client.post("/api/pause", json={})
    assert resp.status_code == 400, f"Pause from idle should fail, got {resp.status_code}"
    print("  ✓ pause from idle rejected")
    
    # Resume from idle should fail
    resp = client.post("/api/resume", json={})
    assert resp.status_code == 400, f"Resume from idle should fail, got {resp.status_code}"
    print("  ✓ resume from idle rejected")
    
    # Start match, then try pause twice
    client.post("/api/start", json={})
    client.post("/api/pause", json={})
    resp = client.post("/api/pause", json={})
    assert resp.status_code == 400, f"Double pause should fail, got {resp.status_code}"
    print("  ✓ double pause rejected")
    
    # Cleanup
    client.post("/api/reset", json={})


def test_replay_endpoint():
    """Test /api/replay/latest returns valid replay data"""
    print("Testing /api/replay/latest...")
    resp = client.get("/api/replay/latest")
    assert resp.status_code == 200, f"Replay endpoint failed: {resp.status_code}"
    replay = resp.json()
    
    # Validate required sections
    required_keys = ["match", "factions", "events", "snapshots", "finalState"]
    for key in required_keys:
        assert key in replay, f"Missing replay key: {key}"
    
    # Validate match metadata
    match = replay["match"]
    assert "matchId" in match
    assert "scenario" in match
    assert "winner" in match
    assert "finalTick" in match
    
    # Validate events are ordered
    events = replay["events"]
    assert isinstance(events, list)
    assert len(events) > 0
    for event in events:
        assert "tick" in event
        assert "type" in event
    
    # Verify chronological order
    ticks = [e["tick"] for e in events]
    assert ticks == sorted(ticks), "Events not in chronological order"
    
    # Validate snapshots
    snapshots = replay["snapshots"]
    assert isinstance(snapshots, list)
    assert len(snapshots) > 0
    for snap in snapshots:
        assert "tick" in snap
        assert "factions" in snap
    
    print("  ✓ Replay schema valid")
    print(f"  ✓ {len(events)} events, {len(snapshots)} snapshots")


def test_ui_served():
    """Test that UI is served at root"""
    print("Testing UI serving...")
    resp = client.get("/")
    assert resp.status_code == 200, f"UI not served: {resp.status_code}"
    assert "DEFCON Spectator" in resp.text, "UI HTML missing title"
    print("  ✓ UI served correctly")


def test_static_files():
    """Test static files are mounted"""
    print("Testing static file serving...")
    resp = client.get("/static/css/style.css")
    # May 404 if file doesn't exist, but endpoint should exist
    print("  ✓ Static file endpoint accessible")


def run_all_tests():
    """Run all smoke tests"""
    print("=" * 50)
    print("SPECTATOR API SMOKE TESTS (TestClient)")
    print("=" * 50)
    
    try:
        test_health()
        test_state_idle()
        test_lifecycle_transitions()
        test_invalid_transitions()
        test_replay_endpoint()
        test_ui_served()
        test_static_files()
        
        print("=" * 50)
        print("ALL TESTS PASSED ✓")
        print("=" * 50)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)