"""
Simple scripted bot implementations for the DEFCON-inspired simulation.
"""

import random
from typing import Dict, List, Optional, Tuple
from ..sim.models import MatchState, LifecycleState
from ..sim.rules import Constants


class SimpleBot:
    """
    A simple scripted bot that makes random valid actions.
    """
    
    def __init__(self, faction_id: str, name: str = "SimpleBot"):
        self.faction_id = faction_id
        self.name = name
        self.last_action_tick = -Constants.DECISION_WINDOW_TICKS  # Allow action on tick 0
        
    def get_action(self, match_state: MatchState) -> Optional[Dict]:
        """
        Decide on an action for this faction.
        Returns action dict or None if no action should be taken.
        """
        # Only act on decision windows
        if match_state.tick % Constants.DECISION_WINDOW_TICKS != 0:
            return None
            
        # Check if we can act
        if self.faction_id not in match_state.factions:
            return None
            
        faction = match_state.factions[self.faction_id]
        if faction.status not in ["active"]:  # Only active factions can launch
            return {"type": "hold"}
        
        # Get legal actions
        legal_actions = self.get_legal_actions(match_state)
        if not legal_actions:
            return {"type": "hold"}
            
        # Choose random action (weighted slightly toward hold to reduce missile spam)
        weights = []
        for action in legal_actions:
            if action["type"] == "hold":
                weights.append(2)  # Hold is twice as likely
            else:
                weights.append(1)
                
        chosen_action = random.choices(legal_actions, weights=weights)[0]
        return chosen_action
    
    def get_legal_actions(self, match_state: MatchState) -> List[Dict]:
        """
        Get list of legal actions for this faction.
        """
        if self.faction_id not in match_state.factions:
            return []
            
        faction = match_state.factions[self.faction_id]
        if faction.status not in ["active"]:  # Only active factions can launch
            return [{"type": "hold"}] if match_state.lifecycle_state == LifecycleState.RUNNING else []
        
        legal_actions = [{"type": "hold"}]  # Hold is always legal if can act
        
        # Check for launch actions from each silo
        for node_id, node in match_state.nodes.items():
            if (node.owner == self.faction_id and 
                node.type.value == "silo" and 
                node.status == "active" and 
                node.ammo > 0 and 
                node.cooldown == 0):
                
                # For each possible target (enemy cities and silos)
                for target_id, target_node in match_state.nodes.items():
                    if (target_node.owner != self.faction_id and 
                        target_node.type.value in ["city", "silo"] and 
                        target_node.status == "active"):
                        
                        legal_actions.append({
                            "type": "launch",
                            "from": node_id,
                            "target": target_id
                        })
        
        return legal_actions


class AggressiveBot(SimpleBot):
    """
    An aggressive bot that prefers to launch missiles when possible.
    """
    
    def get_action(self, match_state: MatchState) -> Optional[Dict]:
        """
        Decide on an action for this faction - prefers launching.
        """
        # Only act on decision windows
        if match_state.tick % Constants.DECISION_WINDOW_TICKS != 0:
            return None
            
        # Check if we can act
        if self.faction_id not in match_state.factions:
            return None
            
        faction = match_state.factions[self.faction_id]
        if faction.status not in ["active"]:  # Only active factions can launch
            return {"type": "hold"}
        
        # Get legal actions
        legal_actions = self.get_legal_actions(match_state)
        if not legal_actions:
            return {"type": "hold"}
            
        # Separate launches and holds
        launches = [a for a in legal_actions if a["type"] == "launch"]
        holds = [a for a in legal_actions if a["type"] == "hold"]
        
        # Prefer launches, but sometimes hold
        if launches and random.random() < 0.8:  # 80% chance to launch if possible
            return random.choice(launches)
        elif holds:
            return random.choice(holds)
        elif launches:
            return random.choice(launches)
        else:
            return {"type": "hold"}


class DefensiveBot(SimpleBot):
    """
    A defensive bot that only launches when under immediate threat.
    """
    
    def get_action(self, match_state: MatchState) -> Optional[Dict]:
        """
        Decide on an action for this faction - defensive posture.
        """
        # Only act on decision windows
        if match_state.tick % Constants.DECISION_WINDOW_TICKS != 0:
            return None
            
        # Check if we can act
        if self.faction_id not in match_state.factions:
            return None
            
        faction = match_state.factions[self.faction_id]
        if faction.status not in ["active"]:  # Only active factions can launch
            return {"type": "hold"}
        
        # Get legal actions
        legal_actions = self.get_legal_actions(match_state)
        if not legal_actions:
            return {"type": "hold"}
            
        # Count incoming missiles to our cities/silos
        incoming_threat = self.count_incoming_threats(match_state)
        
        # If under threat, be more likely to launch
        if incoming_threat > 0:
            launches = [a for a in legal_actions if a["type"] == "launch"]
            holds = [a for a in legal_actions if a["type"] == "hold"]
            
            if launches and random.random() < 0.7:  # 70% chance to launch when threatened
                return random.choice(launches)
            elif holds:
                return random.choice(holds)
            elif launches:
                return random.choice(launches)
            else:
                return {"type": "hold"}
        else:
            # No immediate threat - mostly hold
            launches = [a for a in legal_actions if a["type"] == "launch"]
            holds = [a for a in legal_actions if a["type"] == "hold"]
            
            if holds and random.random() < 0.9:  # 90% chance to hold when safe
                return random.choice(holds)
            elif launches:
                return random.choice(launches)
            else:
                return {"type": "hold"}
    
    def count_incoming_threats(self, match_state: MatchState) -> int:
        """
        Count missiles incoming to our faction's cities and silos.
        """
        threat_count = 0
        for missile_id, missile in match_state.missiles.items():
            if missile.status.value == "flying":
                target_node = match_state.nodes.get(missile.target_node_id)
                if target_node and target_node.owner == self.faction_id:
                    threat_count += 1
        return threat_count


def create_bot(faction_id: str, bot_type: str = "simple", name: Optional[str] = None) -> SimpleBot:
    """
    Factory function to create bot instances.
    """
    if name is None:
        name = f"{bot_type.capitalize()}Bot-{faction_id}"
        
    if bot_type == "aggressive":
        return AggressiveBot(faction_id, name)
    elif bot_type == "defensive":
        return DefensiveBot(faction_id, name)
    else:  # default to simple
        return SimpleBot(faction_id, name)


# Example usage and testing
if __name__ == "__main__":
    # Simple test of the bots
    from ..sim.engine import SimulationEngine
    
    engine = SimulationEngine()
    match_state = engine.start_match()
    match_state.lifecycle_state = match_state.lifecycle_state  # Keep as RUNNING
    
    # Create bots for each faction
    bots = {}
    for faction_id in ["red", "blue", "green", "yellow"]:
        bot_type = ["simple", "aggressive", "defensive"][hash(faction_id) % 3]
        bots[faction_id] = create_bot(faction_id, bot_type)
        print(f"Created {bots[faction_id].name} for {faction_id}")
    
    # Simulate a few decision windows
    print("\\nSimulating decision windows...")
    for window in range(5):
        print(f"\\n--- Decision Window {window} (Tick {match_state.tick}) ---")
        
        # Get actions from all bots
        actions = {}
        for faction_id, bot in bots.items():
            action = bot.get_action(match_state)
            if action:
                actions[faction_id] = action
                print(f"{faction_id}: {action['type']}", end="")
                if action['type'] == 'launch':
                    print(f" from {action['from']} to {action['target']}")
                else:
                    print()
        
        # Apply actions
        for faction_id, action in actions.items():
            events = engine.apply_faction_action(faction_id, action)
            launch_events = [e for e in events if e["type"] == "launch"]
            if launch_events:
                print(f"  {faction_id} launched missile!")
        
        # Advance to next decision window
        for _ in range(Constants.DECISION_WINDOW_TICKS):
            engine.update()
        
        print(f"Tick: {match_state.tick}, Time left: {match_state.time_remaining_sec:.1f}s")
        
        # Show faction statuses
        for faction_id, faction in match_state.factions.items():
            print(f"  {faction_id}: {faction.status.value} (pop: {faction.population})")