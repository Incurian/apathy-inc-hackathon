"""
Main agent adapter class.
Plugs into simulation controller hook for mixed-control integration.
Based on development proposal and Phase 5 requirements.
"""

import asyncio
import logging
from typing import Dict, Optional, Tuple
from .models import Observation
from .observation_builder import build_observation
from .action_parser import parse_and_validate_action
from .fallback import handle_agent_response
from .logging import log_decision
from sim.models import MatchState
import time

logger = logging.getLogger(__name__)


class ControllerMode:
    """Control modes for factions."""
    SCRIPTED = "scripted"
    AGENT = "agent"
    HUMAN_DEBUG = "human-debug"


class AgentAdapter:
    """
    Main adapter for agent-controlled factions.
    Interfaces with simulation through controller hook.
    """
    
    def __init__(self):
        """Initialize agent adapter."""
        # faction_id -> control mode
        self._control_modes: Dict[str, str] = {}
        # faction_id -> last decision timestamp (for timeout tracking)
        self._last_decision_time: Dict[str, float] = {}
        # Reference to simulation state (set externally)
        self._simulation_state = None
        # MCP client for agent communication (would be initialized with actual MCP client)
        self._mcp_client = None
        
    def set_simulation_state(self, simulation_state):
        """Set the simulation state reference."""
        self._simulation_state = simulation_state
    
    def set_control_mode(self, faction_id: str, mode: str):
        """
        Set control mode for a faction.
        
        Args:
            faction_id: ID of the faction
            mode: One of ControllerMode.SCRIPTED, ControllerMode.AGENT, ControllerMode.HUMAN_DEBUG
        """
        if mode not in [ControllerMode.SCRIPTED, ControllerMode.AGENT, ControllerMode.HUMAN_DEBUG]:
            raise ValueError(f"Invalid control mode: {mode}")
        
        self._control_modes[faction_id] = mode
        logger.info(f"Set control mode for faction {faction_id} to {mode}")
    
    def get_control_mode(self, faction_id: str) -> str:
        """
        Get control mode for a faction.
        
        Args:
            faction_id: ID of the faction
            
        Returns:
            Control mode string (defaults to SCRIPTED)
        """
        return self._control_modes.get(faction_id, ControllerMode.SCRIPTED)
    
    def is_agent_controlled(self, faction_id: str) -> bool:
        """
        Check if faction is agent-controlled.
        
        Args:
            faction_id: ID of the faction
            
        Returns:
            True if faction is agent-controlled
        """
        return self.get_control_mode(faction_id) == ControllerMode.AGENT
    
    def get_faction_action(
        self,
        faction_id: str,
        tick: int,
        time_remaining_sec: int
    ) -> Tuple[Dict, Optional[str]]:
        """
        Get action for a faction based on its control mode.
        
        This is the main interface that the simulation controller hook calls.
        
        Args:
            faction_id: ID of the faction needing an action
            tick: Current simulation tick
            time_remaining_sec: Seconds remaining in match
            
        Returns:
            Tuple of (action_dict, error_reason)
            action_dict: Action to apply to simulation (e.g., {"type": "hold"} or {"type": "launch", "from": "...", "target": "..."})
            error_reason: None if successful, error message if fallback occurred
        """
        # Get control mode for this faction
        control_mode = self.get_control_mode(faction_id)
        
        # Scripted or human-debug factions use their normal controllers
        if control_mode != ControllerMode.AGENT:
            # Delegate to faction's normal controller (would be implemented in faction class)
            # For now, return hold as placeholder
            return {"type": "hold"}, None
        
        # Agent-controlled faction - use MCP agent
        return self._get_agent_action(faction_id, tick, time_remaining_sec)
    
    def _get_agent_action(
        self,
        faction_id: str,
        tick: int,
        time_remaining_sec: int
    ) -> Tuple[Dict, Optional[str]]:
        """
        Get action from agent-controlled faction via MCP.
        
        Args:
            faction_id: ID of the faction
            tick: Current simulation tick
            time_remaining_sec: Seconds remaining in match
            
        Returns:
            Tuple of (action_dict, error_reason)
        """
        if self._simulation_state is None:
            logger.warning("Simulation state not available, returning hold")
            return {"type": "hold"}, "Simulation state not available"
        
        # Ensure simulation state is a MatchState
        if not isinstance(self._simulation_state, MatchState):
            logger.warning("Simulation state is not MatchState, returning hold")
            return {"type": "hold"}, "Invalid simulation state type"
        
        # Get the faction object
        faction = self._get_faction_object(faction_id)
        if not faction:
            logger.warning(f"Faction {faction_id} not found, returning hold")
            return {"type": "hold"}, f"Faction {faction_id} not found"
        
        try:
            # Build observation for the agent using new interface
            observation = build_observation(
                match_state=self._simulation_state,
                requesting_faction_id=faction_id,
                recent_events=[e.to_dict() for e in self._simulation_state.events[-10:]]
            )
            
            # Record start time for timeout handling
            start_time = time.time()
            
            # Get observation JSON for agent
            observation_json = observation.json()
            
            # In a real implementation, we would:
            # 1. Send observation_json to the agent via MCP
            # 2. Wait for response with timeout
            # 3. Process the response
            
            # For now, we'll simulate by returning a hold action
            # This would be replaced with actual MCP communication
            raw_response = None  # Simulate no response/timeout for now
            
            # Apply fallback behavior
            final_action, log_entry = handle_agent_response(
                faction_id=faction_id,
                tick=tick,
                observation=observation,
                raw_response=raw_response,
                start_time=start_time,
                parser_func=lambda resp, fac, sim_state: parse_and_validate_action(resp, fac, sim_state)
            )
            
            # Log the decision attempt
            log_decision(
                faction_id=faction_id,
                tick=tick,
                observation_summary=log_entry["observationSummary"],
                raw_response=raw_response,
                parsed_action_or_failure=log_entry["parsedActionOrFailure"],
                latency_ms=log_entry["latencyMs"]
            )
            
            # Determine if this was a fallback
            error_reason = log_entry.get("errorReason")
            
            return final_action, error_reason
            
        except Exception as e:
            logger.error(f"Error getting agent action for faction {faction_id}: {e}")
            return {"type": "hold"}, f"Internal error: {str(e)}"
    
    def _get_faction_object(self, faction_id: str):
        """
        Get faction object from simulation state.
        
        Args:
            faction_id: ID of the faction
            
        Returns:
            Faction object or None if not found
        """
        if self._simulation_state is None:
            return None
            
        if not isinstance(self._simulation_state, MatchState):
            return None
            
        return self._simulation_state.factions.get(faction_id)
    
    # Methods for integration with actual MCP client (to be implemented when MCP client is available)
    async def _get_agent_action_async(
        self,
        faction_id: str,
        tick: int,
        time_remaining_sec: int
    ) -> Tuple[Dict, Optional[str]]:
        """
        Async version for actual MCP communication.
        Placeholder for future implementation.
        """
        # This would be implemented when we have an actual MCP client
        # For now, fall back to synchronous version
        return self._get_agent_action(faction_id, tick, time_remaining_sec)


# Convenience function for external use
def get_agent_action(
    adapter: AgentAdapter,
    faction_id: str,
    tick: int,
    time_remaining_sec: int
) -> Tuple[Dict, Optional[str]]:
    """
    Get faction action using agent adapter (convenience function).
    
    Args:
        adapter: AgentAdapter instance
        faction_id: ID of the faction
        tick: Current simulation tick
        time_remaining_sec: Seconds remaining in match
        
    Returns:
        Tuple of (action_dict, error_reason)
    """
    return adapter.get_faction_action(faction_id, tick, time_remaining_sec)