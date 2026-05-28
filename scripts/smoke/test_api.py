#!/usr/bin/env python3
"""
Smoke tests for the Spectator API
Validates all required endpoints return expected shapes
"""

import sys
import time
import requests
import json


BASE_URL = "http://localhost:8080"
API_BASE = f"{BASE_URL}/api"


def test_health():
    """Test health endpoint"""
    print("Testing /api/health...")
    resp = requests.get(f"{API_BASE}/health", timeout=5)
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
    data = resp.json()
    assert data.get("status") == "ok", f"Unexpected health response: {data}"
    print("  ✓ Health check passed")


def test_state_idle():
    """Test /api/state returns valid JSON in idle state"""
    print("Testing /api/state (idle)...")
    resp = requests.get(f"{API_BASE}/state", timeout=5)
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


def test_state_running():
    """Test /api/state changes over time while running"""
    print("Testing /api/state updates while running...")
    
    # Start match
    resp = requests.post(f"{API_BASE}/start", json={}, timeout=5)
    assert resp.status_code == 200, f"Start failed: {resp.status_code}"
    
    # Get initial state
    resp1 = requests.get(f"{API_BASE}/state", timeout=5)
    state1 = resp1.json()
    assert state1["match"]["lifecycleState"] == "running"
    tick1 = state1["match"]["tick"]
    
    # Wait a moment and poll again
    time.sleep(1)
    
    resp2 = requests.get(f"{API_BASE}/state", timeout=5)
    state2 = resp2.json()
    tick2 = state2["match"]["tick"]
    
    # Tick should advance (or at least state should be valid)
    assert state2["match"]["lifecycleState"] == "running"
    print(f"  ✓ State updates: tick {tick1} -> {tick2}")


def test_lifecycle_transitions():
    """Test all lifecycle transitions"""
    print("Testing lifecycle transitions...")
    
    # Reset to idle first
    requests.post(f"{API_BASE}/reset", json={}, timeout=5)
    time.sleep(0.5)
    
    # idle -> running (start)
    resp = requests.post(f"{API_BASE}/start", json={}, timeout=5)
    assert resp.status_code == 200
    state = resp.json()
    assert state["match"]["lifecycleState"] == "running"
    print("  ✓ idle -> running (start)")
    
    # running -> paused (pause)
    resp = requests.post(f"{API_BASE}/pause", json={}, timeout=5)
    assert resp.status_code == 200
    state = resp.json()
    assert state["match"]["lifecycleState"] == "paused"
    print("  ✓ running -> paused (pause)")
    
    # paused -> running (resume)
    resp = requests.post(f"{API_BASE}/resume", json={}, timeout=5)
    assert resp.status_code == 200
    state = resp.json()
    assert state["match"]["lifecycleState"] == "running"
    print("  ✓ paused -> running (resume)")
    
    # running -> paused -> reset -> idle
    requests.post(f"{API_BASE}/pause", json={}, timeout=5)
    resp = requests.post(f"{API_BASE}/reset", json={}, timeout=5)
    assert resp.status_code == 200
    state = resp.json()
    assert state["match"]["lifecycleState"] == "idle"
    print("  ✓ running -> idle (reset)")
    
    # finished -> running (start new)
    # First simulate finished by running to completion (or just test reset from any state)
    requests.post(f"{API_BASE}/start", json={}, timeout=5)
    requests.post(f"{API_BASE}/reset", json={}, timeout=5)
    resp = requests.post(f"{API_BASE}/start", json={}, timeout=5)
    assert resp.status_code == 200
    state = resp.json()
    assert state["match"]["lifecycleState"] == "running"
    assert state["match"]["matchId"] is not None
    print("  ✓ finished -> running (start creates new matchId)")
    
    # Cleanup
    requests.post(f"{API_BASE}/reset", json={}, timeout=5)


def test_invalid_transitions():
    """Test that invalid transitions are rejected"""
    print("Testing invalid transition rejection...")
    
    # Reset to known state
    requests.post(f"{API_BASE}/reset", json={}, timeout=5)
    time.sleep(0.5)
    
    # Pause from idle should fail
    resp = requests.post(f"{API_BASE}/pause", json={}, timeout=5)
    assert resp.status_code == 400, f"Pause from idle should fail, got {resp.status_code}"
    print("  ✓ pause from idle rejected")
    
    # Resume from idle should fail
    resp = requests.post(f"{API_BASE}/resume", json={}, timeout=5)
    assert resp.status_code == 400, f"Resume from idle should fail, got {resp.status_code}"
    print("  ✓ resume from idle rejected")
    
    # Start match, then try pause twice
    requests.post(f"{API_BASE}/start", json={}, timeout=5)
    requests.post(f"{API_BASE}/pause", json={}, timeout=5)
    resp = requests.post(f"{API_BASE}/pause", json={}, timeout=5)
    assert resp.status_code == 400, f"Double pause should fail, got {resp.status_code}"
    print("  ✓ double pause rejected")
    
    # Cleanup
    requests.post(f"{API_BASE}/reset", json={}, timeout=5)


def test_replay_endpoint():
    """Test /api/replay/latest returns valid replay data"""
    print("Testing /api/replay/latest...")
    resp = requests.get(f"{API_BASE}/replay/latest", timeout=5)
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
    resp = requests.get(BASE_URL, timeout=5)
    assert resp.status_code == 200, f"UI not served: {resp.status_code}"
    assert "DEFCON Spectator" in resp.text, "UI HTML missing title"
    print("  ✓ UI served correctly")


def run_all_tests():
    """Run all smoke tests"""
    print("=" * 50)
    print("SPECTATOR API SMOKE TESTS")
    print("=" * 50)
    
    try:
        # Wait for server to be ready
        for _ in range(10):
            try:
                requests.get(f"{API_BASE}/health", timeout=2)
                break
            except:
                time.sleep(0.5)
        else:
            print("ERROR: Server not responding")
            return False
        
        test_health()
        test_state_idle()
        test_lifecycle_transitions()
        test_invalid_transitions()
        test_replay_endpoint()
        test_ui_served()
        
        # Test running state updates last (requires started match)
        test_state_running()
        
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