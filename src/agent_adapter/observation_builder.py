"""
Observation builder for agent adapter.
Builds SPEC-compliant observation payload from simulation state.
Based on SPEC.md Section 14: Agent Player Interface (lines 423-458).
"""

from typing import Dict, List, Optional
from .models import Observation, Site, FactionState, WorldFaction, Target, Missile, Event, LegalAction
from sim.models import MatchState, Faction, Node, Missile as SimMissile, EntityType, Constants


class ObservationBuilder:
    """Builds agent observations from simulation state."""
    
    @staticmethod
    def build_observation(
        match_state: MatchState,
        requesting_faction_id: str,
        recent_events: Optional[List[Dict]] = None
    ) -> Observation:
        """
        Build SPEC-compliant observation for a faction.
        
        Args:
            match_state: Current match state
            requesting_faction_id: ID of faction requesting observation
            recent_events: Recent game events (defaults to last 10 from match_state)
            
        Returns:
            Observation: SPEC-compliant observation payload
        """
        if recent_events is None:
            recent_events = [e.to_dict() for e in match_state.events[-10:]]
            
        # Get requesting faction (self)
        self_faction = match_state.factions.get(requesting_faction_id)
        if not self_faction:
            raise ValueError(f"Faction {requesting_faction_id} not found")
        
        # Build self state
        self_state = ObservationBuilder._build_faction_state(match_state, self_faction)
        
        # Build world state (all other factions + targets + missiles)
        world_state = ObservationBuilder._build_world_state(match_state, requesting_faction_id)
        
        # Build recent events - filter to only agent-relevant event types
        # Agent adapter Event model only supports: launch, impact, destruction, invalid_action
        agent_event_types = {"launch", "impact", "destruction", "invalid_action"}
        recent_events_parsed = []
        for event in recent_events:
            event_dict = event if isinstance(event, dict) else event.to_dict()
            if event_dict.get("type") in agent_event_types:
                # Convert to agent adapter Event format
                agent_event = {
                    "tick": event_dict["tick"],
                    "type": event_dict["type"],
                    "target": event_dict.get("target_node_id") or event_dict.get("source_node_id") or "unknown",
                    "damage": event_dict.get("damage"),
                    "factionId": event_dict.get("faction_id"),
                    "action": event_dict.get("details", {}).get("attempted_action"),
                    "errorReason": event_dict.get("details", {}).get("reason")
                }
                recent_events_parsed.append(Event(**agent_event))
        
        # Build legal actions
        legal_actions = ObservationBuilder._build_legal_actions(match_state, self_faction)
        
        return Observation(
            match={
                "matchId": match_state.match_id,
                "tick": match_state.tick,
                "timeRemainingSec": int(match_state.time_remaining_sec)
            },
            self=self_state,
            world=world_state,
            recentEvents=recent_events_parsed,
            legalActions=legal_actions
        )
    
    @staticmethod
    def _build_faction_state(match_state: MatchState, faction: Faction) -> FactionState:
        """Build faction state for observation."""
        sites = []
        
        # Get faction's owned nodes from match_state.nodes
        for node_id in faction.owned_sites:
            node = match_state.nodes.get(node_id)
            if not node:
                continue
                
            site_data = {
                "id": node.id,
                "type": node.type.value,  # "city" or "silo"
                "owner": faction.id,
                "x": node.position.x,
                "y": node.position.y,
                "hp": node.hp,
                "active": node.status == "active"
            }
            
            # Add type-specific fields
            if node.type == EntityType.CITY:
                site_data["population"] = node.population
            elif node.type == EntityType.SILO:
                site_data["ammo"] = node.ammo
                site_data["cooldown"] = node.cooldown
                
            sites.append(Site(**site_data))
        
        return FactionState(
            id=faction.id,
            population=faction.population,
            score=faction.score,
            status=faction.status.value,
            sites=sites
        )
    
    @staticmethod
    def _build_world_state(match_state: MatchState, requesting_faction_id: str) -> dict:
        """Build world state (public information visible to all factions)."""
        world_factions = []
        targets = []
        missiles = []
        
        for faction_id, faction in match_state.factions.items():
            # Skip if this is the requesting faction (already in 'self')
            if faction_id == requesting_faction_id:
                continue
                
            # Add to world factions list
            world_factions.append(WorldFaction(
                id=faction.id,
                status=faction.status.value,
                population=faction.population,
                score=faction.score
            ))
            
            # Add faction's nodes as targets (cities and silos can be attacked)
            for node_id in faction.owned_sites:
                node = match_state.nodes.get(node_id)
                if not node:
                    continue
                if node.type in [EntityType.CITY, EntityType.SILO] and node.status == "active":
                    target_data = {
                        "id": node.id,
                        "owner": faction.id,
                        "type": node.type.value,
                        "hp": node.hp,
                        "value": node.population if node.type == EntityType.CITY else 25  # Cities worth population, silos worth 25
                    }
                    targets.append(Target(**target_data))
            
            # Add missiles in flight owned by this faction
            for missile in match_state.missiles.values():
                if missile.owner == faction_id and missile.status == SimMissile.FLYING:
                    # Calculate ETA in seconds
                    ticks_remaining = max(0, missile.impact_tick - match_state.tick)
                    eta_sec = ticks_remaining * (Constants.TICK_MS / 1000.0)
                    
                    missile_data = {
                        "id": missile.id,
                        "owner": missile.owner,
                        "source": missile.source_node_id,
                        "target": missile.target_node_id,
                        "etaSec": int(eta_sec)
                    }
                    missiles.append(Missile(**missile_data))
        
        return {
            "factions": [f.dict() for f in world_factions],
            "targets": [t.dict() for t in targets],
            "missiles": [m.dict() for m in missiles]
        }
    
    @staticmethod
    def _build_legal_actions(match_state: MatchState, faction: Faction) -> List[LegalAction]:
        """Build list of legal actions for the faction."""
        legal_actions = []
        
        # Hold action is always legal
        legal_actions.append(LegalAction(type="hold"))
        
        # Launch actions for each ready silo owned by this faction
        for node_id in faction.owned_sites:
            node = match_state.nodes.get(node_id)
            if not node:
                continue
                
            if (node.type == EntityType.SILO and 
                node.status == "active" and 
                node.ammo > 0 and 
                node.cooldown == 0):
                
                # Determine valid targets (enemy cities and silos that are active)
                allowed_targets = []
                for target_id, target_node in match_state.nodes.items():
                    if (target_node.owner != faction.id and 
                        target_node.type in [EntityType.CITY, EntityType.SILO] and 
                        target_node.status == "active"):
                        allowed_targets.append(target_id)
                
                legal_actions.append(LegalAction(
                    type="launch",
                    from_=node.id,
                    allowedTargets=allowed_targets if allowed_targets else []
                ))
        
        return legal_actions


# Convenience function for external use
def build_observation(
    match_state: MatchState,
    requesting_faction_id: str,
    recent_events: Optional[List[Dict]] = None
) -> Observation:
    """Build observation for agent (convenience function)."""
    return ObservationBuilder.build_observation(
        match_state, requesting_faction_id, recent_events
    )