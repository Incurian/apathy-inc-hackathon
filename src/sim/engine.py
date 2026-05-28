"""
Main simulation engine that orchestrates the game loop.
"""

from typing import List, Dict, Optional
from .models import MatchState, LifecycleState
from .rules import (
    apply_action, advance_tick, initialize_match, 
    validate_hold_action, validate_launch_action
)
import time


class SimulationEngine:
    def __init__(self):
        self.match_state: Optional[MatchState] = None
        self.is_running = False
        self.last_tick_time = 0
        self.tick_interval = 0.25  # 250ms in seconds
        
    def start_match(self, scenario_name: str = "default") -> MatchState:
        """Start a new match."""
        self.match_state = initialize_match(scenario_name)
        self.match_state.lifecycle_state = LifecycleState.RUNNING
        self.is_running = True
        self.last_tick_time = time.time()
        return self.match_state
    
    def pause_match(self) -> None:
        """Pause the current match."""
        if self.match_state and self.match_state.lifecycle_state == LifecycleState.RUNNING:
            self.match_state.lifecycle_state = LifecycleState.PAUSED
            self.is_running = False
    
    def resume_match(self) -> None:
        """Resume a paused match."""
        if self.match_state and self.match_state.lifecycle_state == LifecycleState.PAUSED:
            self.match_state.lifecycle_state = LifecycleState.RUNNING
            self.is_running = True
            self.last_tick_time = time.time()
    
    def reset_match(self) -> MatchState:
        """Reset the match to initial state."""
        self.is_running = False
        if self.match_state:
            return self.initialize_match()
        return MatchState(
            match_id="",
            tick=0,
            time_remaining_sec=0,
            lifecycle_state=LifecycleState.IDLE
        )
    
    def update(self) -> List[Dict]:
        """
        Update the simulation by one tick if enough time has passed.
        Returns list of events generated during this update.
        """
        if not self.match_state or not self.is_running:
            return []
        
        current_time = time.time()
        elapsed = current_time - self.last_tick_time
        
        # Only advance if we've passed the tick interval
        if elapsed >= self.tick_interval:
            # Apply any pending actions (in a real implementation, these would come from a queue)
            # For now, we'll just advance the tick
            
            events = advance_tick(self.match_state)
            
            # Update last tick time (account for possible multiple ticks if game is behind)
            ticks_to_advance = int(elapsed / self.tick_interval)
            self.last_tick_time += ticks_to_advance * self.tick_interval
            
            # Convert events to dictionaries for easier consumption
            return [event.to_dict() for event in events]
        
        return []
    
    def apply_faction_action(self, faction_id: str, action: dict) -> List[Dict]:
        """
        Apply an action from a faction.
        Returns list of events generated.
        """
        if not self.match_state:
            return []
        
        events = apply_action(self.match_state, faction_id, action)
        return [event.to_dict() for event in events]
    
    def get_state(self) -> Optional[Dict]:
        """Get current match state."""
        if self.match_state:
            return self.match_state.to_dict()
        return None
    
    def is_match_running(self) -> bool:
        """Check if match is currently running."""
        return (self.match_state and 
                self.match_state.lifecycle_state == LifecycleState.RUNNING)
    
    def get_legal_actions(self, faction_id: str) -> List[Dict]:
        """
        Get list of legal actions for a faction.
        Returns list of action dictionaries.
        """
        if not self.match_state or faction_id not in self.match_state.factions:
            return []
        
        faction = self.match_state.factions[faction_id]
        if faction.status not in [self.match_state.factions[faction_id].status]:  # ACTIVE or CRIPPLED with ammo
            return []
        
        legal_actions = [{"type": "hold"}]  # Hold is always legal if can act
        
        # Check for launch actions from each silo
        for node_id, node in self.match_state.nodes.items():
            if (node.owner == faction_id and 
                node.type == "silo" and 
                node.status == "active" and 
                node.ammo > 0 and 
                node.cooldown == 0):
                
                # For each possible target (enemy cities and silos)
                for target_id, target_node in self.match_state.nodes.items():
                    if (target_node.owner != faction_id and 
                        target_node.type in ["city", "silo"] and 
                        target_node.status == "active"):
                        
                        legal_actions.append({
                            "type": "launch",
                            "from": node_id,
                            "target": target_id
                        })
        
        return legal_actions


# Example usage and testing
if __name__ == "__main__":
    # Simple test of the engine
    engine = SimulationEngine()
    match_state = engine.start_match()
    
    print(f"Started match: {match_state.match_id}")
    print(f"Factions: {list(match_state.factions.keys())}")
    print(f"Red faction population: {match_state.factions['red'].population}")
    print(f"Red faction silos: {[nid for nid, node in match_state.nodes.items() if node.owner == 'red' and node.type == 'silo']}")
    
    # Test applying a hold action
    events = engine.apply_faction_action("red", {"type": "hold"})
    print(f"Hold action generated {len(events)} events")
    
    # Test getting legal actions
    legal_actions = engine.get_legal_actions("red")
    print(f"Red faction has {len(legal_actions)} legal actions")
    if legal_actions:
        print(f"First few legal actions: {legal_actions[:3]}")
    
    # Advance a few ticks
    for i in range(5):
        events = engine.update()
        if events:
            print(f"Tick {match_state.tick}: {len(events)} events")
    
    print(f"Match state after updates: {engine.get_state()['lifecycle_state']}")