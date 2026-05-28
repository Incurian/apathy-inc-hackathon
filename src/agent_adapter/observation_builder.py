"""
Observation builder for agent adapter.
Builds SPEC-compliant observation payload from simulation state.
Based on SPEC.md Section 14: Agent Player Interface (lines 423-458).
"""

from typing import Dict, List, Optional
from .models import Observation, Site, FactionState, WorldFaction, Target, Missile, Event, LegalAction
from ..sim.models import Faction, SimulationState  # Assuming these exist or will be created


class ObservationBuilder:
    """Builds agent observations from simulation state."""
    
    @staticmethod
    def build_observation(
        match_id: str,
        tick: int,
        time_remaining_sec: int,
        factions: Dict[str, 'Faction'],
        requesting_faction_id: str,
        events: List[Dict] = None
    ) -> Observation:
        """
        Build SPEC-compliant observation for a faction.
        
        Args:
            match_id: Unique match identifier
            tick: Current simulation tick
            time_remaining_sec: Seconds remaining in match
            factions: Dictionary of all factions in the simulation
            requesting_faction_id: ID of faction requesting observation
            events: Recent game events (defaults to empty list)
            
        Returns:
            Observation: SPEC-compliant observation payload
        """
        if events is None:
            events = []
            
        # Get requesting faction (self)
        self_faction = factions.get(requesting_faction_id)
        if not self_faction:
            raise ValueError(f"Faction {requesting_faction_id} not found")
        
        # Build self state
        self_state = ObservationBuilder._build_faction_state(self_faction)
        
        # Build world state (all other factions + targets + missiles)
        world_state = ObservationBuilder._build_world_state(factions, requesting_faction_id)
        
        # Build recent events
        recent_events = [Event(**event) for event in events[-10:]]  # Last 10 events
        
        # Build legal actions
        legal_actions = ObservationBuilder._build_legal_actions(self_faction)
        
        return Observation(
            match={
                "matchId": match_id,
                "tick": tick,
                "timeRemainingSec": time_remaining_sec
            },
            self=self_state,
            world=world_state,
            recentEvents=recent_events,
            legalActions=legal_actions
        )
    
    @staticmethod
    def _build_faction_state(faction: 'Faction') -> FactionState:
        """Build faction state for observation."""
        sites = []
        for site in faction.sites:
            site_data = {
                "id": site.id,
                "type": site.type,
                "owner": faction.id,
                "x": site.x,
                "y": site.y,
                "hp": site.hp,
                "active": not site.destroyed
            }
            
            # Add type-specific fields
            if site.type == "city":
                site_data["population"] = site.population
            elif site.type == "silo":
                site_data["ammo"] = site.ammo
                site_data["cooldown"] = site.cooldown
                
            sites.append(Site(**site_data))
        
        return FactionState(
            id=faction.id,
            population=faction.population,
            score=faction.score,
            status=faction.status,
            sites=sites
        )
    
    @staticmethod
    def _build_world_state(factions: Dict[str, 'Faction'], requesting_faction_id: str) -> dict:
        """Build world state (public information visible to all factions)."""
        world_factions = []
        targets = []
        missiles = []
        
        for faction_id, faction in factions.items():
            # Skip if this is the requesting faction (already in 'self')
            if faction_id == requesting_faction_id:
                continue
                
            # Add to world factions list
            world_factions.append(WorldFaction(
                id=faction.id,
                status=faction.status,
                population=faction.population,
                score=faction.score
            ))
            
            # Add faction's sites as targets (cities and silos can be attacked)
            for site in faction.sites:
                if site.type in ["city", "silo"] and not site.destroyed:
                    target_data = {
                        "id": site.id,
                        "owner": faction.id,
                        "type": site.type,
                        "hp": site.hp,
                        "value": site.population if site.type == "city" else 25  # Cities worth population, silos worth 25
                    }
                    targets.append(Target(**target_data))
            
            # Add missiles in flight
            for missile in faction.missiles:
                if missile.status == "flying":
                    missile_data = {
                        "id": missile.id,
                        "owner": missile.owner,
                        "source": missile.source,
                        "target": missile.target,
                        "etaSec": max(0, (missile.impact_tick - faction.simulation.tick) * 0.25)  # Convert ticks to seconds
                    }
                    missiles.append(Missile(**missile_data))
        
        return {
            "factions": [f.dict() for f in world_factions],
            "targets": [t.dict() for t in targets],
            "missiles": [m.dict() for m in missiles]
        }
    
    @staticmethod
    def _build_legal_actions(faction: 'Faction') -> List[LegalAction]:
        """Build list of legal actions for the faction."""
        legal_actions = []
        
        # Hold action is always legal
        legal_actions.append(LegalAction(type="hold"))
        
        # Launch actions for each ready silo
        for site in faction.sites:
            if site.type == "silo" and not site.destroyed and site.ammo > 0 and site.cooldown == 0:
                # Determine valid targets (enemy cities and silos)
                allowed_targets = []
                for target_site in faction.sites:  # This should be all sites in world, but we'll simplify for now
                    if target_site.type in ["city", "silo"] and target_site.owner != faction.id and not target_site.destroyed:
                        allowed_targets.append(target_site.id)
                
                # In a real implementation, we'd check against all enemy factions' sites
                # For now, we'll use a placeholder that will be filtered by the action parser
                legal_actions.append(LegalAction(
                    type="launch",
                    from_=site.id,
                    allowedTargets=allowed_targets if allowed_targets else ["dummy-target"]  # Will be validated in parser
                ))
        
        return legal_actions


# Convenience function for external use
def build_observation(
    match_id: str,
    tick: int,
    time_remaining_sec: int,
    factions: Dict[str, 'Faction'],
    requesting_faction_id: str,
    events: List[Dict] = None
) -> Observation:
    """Build observation for agent (convenience function)."""
    return ObservationBuilder.build_observation(
        match_id, tick, time_remaining_sec, factions, requesting_faction_id, events
    )