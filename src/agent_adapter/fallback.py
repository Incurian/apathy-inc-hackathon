"""
Fallback behavior handler for agent adapter.
Handles timeout, parse failures, and illegal actions by returning hold + logging.
Based on SPEC.md Section 14 lines 473-476.
"""

import time
import logging
from typing import Dict, Optional, Tuple
from .models import Observation
from .action_parser import ActionParseError, ActionValidationError


class FallbackHandler:
    """Handles fallback behavior for agent actions."""
    
    def __init__(self, timeout_seconds: float = 5.0):
        """
        Initialize fallback handler.
        
        Args:
            timeout_seconds: Agent response timeout in seconds (default 5s per SPEC.md)
        """
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(__name__)
    
    def handle_response(
        self,
        faction_id: str,
        tick: int,
        observation: Observation,
        raw_response: Optional[str],
        start_time: float,
        parser_func=None
    ) -> Tuple[Dict, Dict]:
        """
        Process agent response with fallback behavior.
        
        Args:
            faction_id: ID of the faction
            tick: Current simulation tick
            observation: Observation that was provided to agent
            raw_response: Raw response from agent (None if timeout/error)
            start_time: Time when agent invocation started
            parser_func: Function to parse/validate action (defaults to internal parser)
            
        Returns:
            Tuple of (action_to_apply, log_entry)
            action_to_apply: The action to apply to simulation (usually {"type": "hold"} or valid action)
            log_entry: Structured log entry for decision logging
        """
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Build base log entry
        log_entry = {
            "factionId": faction_id,
            "tick": tick,
            "observationSummary": self._summarize_observation(observation),
            "rawResponse": raw_response,
            "latencyMs": latency_ms
        }
        
        # Case 1: Timeout or no response
        if raw_response is None:
            log_entry["parsedActionOrFailure"] = {"type": "hold", "reason": "timeout"}
            log_entry["errorReason"] = f"Agent timeout after {self.timeout_seconds}s"
            self.logger.info(f"Faction {faction_id} tick {tick}: Agent timeout -> hold")
            return {"type": "hold"}, log_entry
        
        # Case 2: Parse/validation failure
        if parser_func is not None:
            try:
                parsed_action, error_reason = parser_func(
                    raw_response, 
                    None,  # faction object - would be passed in real implementation
                    None   # simulation_state - would be passed in real implementation
                )
                
                if error_reason is None:
                    # Valid action
                    log_entry["parsedActionOrFailure"] = parsed_action
                    log_entry["errorReason"] = None
                    self.logger.info(f"Faction {faction_id} tick {tick}: Valid action {parsed_action}")
                    return parsed_action, log_entry
                else:
                    # Invalid action
                    log_entry["parsedActionOrFailure"] = {"type": "hold", "reason": "invalid_action"}
                    log_entry["errorReason"] = error_reason
                    self.logger.info(f"Faction {faction_id} tick {tick}: Invalid action -> hold ({error_reason})")
                    return {"type": "hold"}, log_entry
                    
            except Exception as e:
                # Parser itself failed
                log_entry["parsedActionOrFailure"] = {"type": "hold", "reason": "parser_error"}
                log_entry["errorReason"] = f"Parser error: {str(e)}"
                self.logger.info(f"Faction {faction_id} tick {tick}: Parser error -> hold ({str(e)})")
                return {"type": "hold"}, log_entry
        
        # Case 3: No parser provided (shouldn't happen in practice)
        log_entry["parsedActionOrFailure"] = {"type": "hold", "reason": "no_parser"}
        log_entry["errorReason"] = "No parser provided"
        return {"type": "hold"}, log_entry
    
    @staticmethod
    def _summarize_observation(observation: Observation) -> dict:
        """Create a summary of observation for logging (to avoid huge logs)."""
        return {
            "matchId": observation.match.get("matchId"),
            "tick": observation.match.get("tick"),
            "timeRemainingSec": observation.match.get("timeRemainingSec"),
            "selfFaction": observation.self.id if hasattr(observation.self, 'id') else str(observation.self),
            "worldFactionsCount": len(observation.world.get("factions", [])),
            "targetsCount": len(observation.world.get("targets", [])),
            "missilesCount": len(observation.world.get("missiles", [])),
            "recentEventsCount": len(observation.recentEvents),
            "legalActionsCount": len(observation.legalActions)
        }


# Convenience function for external use
def handle_agent_response(
    faction_id: str,
    tick: int,
    observation: Observation,
    raw_response: Optional[str],
    start_time: float,
    timeout_seconds: float = 5.0,
    parser_func=None
) -> Tuple[Dict, Dict]:
    """Handle agent response with fallback behavior (convenience function)."""
    handler = FallbackHandler(timeout_seconds)
    return handler.handle_response(
        faction_id, tick, observation, raw_response, start_time, parser_func
    )