"""
Strict action parser and validator for agent adapter.
Based on SPEC.md Section 14: Agent Player Interface.
"""

from typing import Dict, List, Optional, Tuple
from .models import Action
from ..sim.models import Faction, SimulationState  # Assuming these exist or will be created


class ActionParseError(Exception):
    """Raised when action parsing fails."""
    pass


class ActionValidationError(Exception):
    """Raised when action validation fails."""
    pass


class ActionParser:
    """Parses and validates agent actions according to SPEC.md §14."""
    
    @staticmethod
    def parse_and_validate(
        raw_response: str,
        faction: 'Faction',
        simulation_state: 'SimulationState'
    ) -> Tuple[Dict, Optional[str]]:
        """
        Parse and validate agent action response.
        
        Args:
            raw_response: Raw string response from agent
            faction: The faction attempting the action
            simulation_state: Current simulation state for validation
            
        Returns:
            Tuple of (parsed_action_dict, error_reason)
            If successful, error_reason is None and parsed_action_dict contains the action
            If failed, parsed_action_dict is {"type": "hold"} and error_reason contains the reason
        """
        # Step 1: Parse JSON
        try:
            import json
            parsed = json.loads(raw_response.strip())
        except (json.JSONDecodeError, ValueError) as e:
            return {"type": "hold"}, f"JSON parse error: {str(e)}"
        
        # Step 2: Check for exactly one top-level "action" field
        if not isinstance(parsed, dict) or "action" not in parsed:
            return {"type": "hold"}, "Missing or invalid 'action' field"
        
        action_data = parsed["action"]
        if not isinstance(action_data, dict):
            return {"type": "hold"}, "'action' must be an object"
        
        # Step 3: Validate action structure using Pydantic model
        try:
            action_model = Action(action=action_data, comment=parsed.get("comment"))
            validated_action = action_model.action
        except Exception as e:
            return {"type": "hold"}, f"Action validation error: {str(e)}"
        
        # Step 4: Validate action content against game state
        try:
            ActionParser._validate_action_content(validated_action, faction, simulation_state)
            return validated_action, None
        except ActionValidationError as e:
            return {"type": "hold"}, str(e)
        except Exception as e:
            return {"type": "hold"}, f"Unexpected validation error: {str(e)}"
    
    @staticmethod
    def _validate_action_content(
        action: Dict,
        faction: 'Faction',
        simulation_state: 'SimulationState'
    ) -> None:
        """
        Validate action content against current game state.
        Raises ActionValidationError if invalid.
        """
        action_type = action["type"]
        
        if action_type == "hold":
            # Hold action is always valid
            return
        
        elif action_type == "launch":
            # Validate launch action
            from_silo_id = action.get("from")
            target_id = action.get("target")
            
            if not from_silo_id or not target_id:
                raise ActionValidationError("Launch action missing 'from' or 'target' field")
            
            # Find the silo
            silo = None
            for site in faction.sites:
                if site.id == from_silo_id and site.type == "silo":
                    silo = site
                    break
            
            if not silo:
                raise ActionValidationError(f"Silo '{from_silo_id}' not found or not owned by faction")
            
            if silo.destroyed:
                raise ActionValidationError(f"Silo '{from_silo_id}' is destroyed")
            
            if silo.ammo <= 0:
                raise ActionValidationError(f"Silo '{from_silo_id}' has no ammo")
            
            if silo.cooldown > 0:
                raise ActionValidationError(f"Silo '{from_silo_id}' is on cooldown")
            
            # Validate target exists and is enemy-owned
            target_site = None
            all_factions = {faction.id: faction for faction in simulation_state.factions.values()}
            
            for fid, fac in all_factions.items():
                for site in fac.sites:
                    if site.id == target_id and site.type in ["city", "silo"]:
                        target_site = site
                        break
                if target_site:
                    break
            
            if not target_site:
                raise ActionValidationError(f"Target '{target_id}' not found")
            
            if target_site.destroyed:
                raise ActionValidationError(f"Target '{target_id}' is destroyed")
            
            if target_site.owner == faction.id:
                raise ActionValidationError(f"Cannot target own site '{target_id}'")
            
        else:
            raise ActionValidationError(f"Invalid action type: {action_type}. Must be 'hold' or 'launch'")


# Convenience function for external use
def parse_and_validate_action(
    raw_response: str,
    faction: 'Faction',
    simulation_state: 'SimulationState'
) -> Tuple[Dict, Optional[str]]:
    """Parse and validate agent action (convenience function)."""
    return ActionParser.parse_and_validate_action(raw_response, faction, simulation_state)