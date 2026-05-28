"""
Decision-attempt logging for agent adapter.
Persists agent decisions for debugging and inspection.
Based on SPEC.md Section 14 and Phase 5.5.
"""

import json
import time
import threading
from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class DecisionLogEntry:
    """Single decision attempt log entry."""
    factionId: str
    tick: int
    observationSummary: dict
    rawResponse: Optional[str]
    parsedActionOrFailure: dict
    latencyMs: int
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class DecisionLogger:
    """Logs agent decision attempts for debugging and inspection."""
    
    def __init__(self, max_entries: int = 1000, log_file: Optional[str] = None):
        """
        Initialize decision logger.
        
        Args:
            max_entries: Maximum number of entries to keep in memory
            log_file: Optional file path to persist logs
        """
        self.max_entries = max_entries
        self.log_file = Path(log_file) if log_file else None
        self._entries: deque = deque(maxlen=max_entries)
        self._lock = threading.Lock()
        
        # Ensure log directory exists
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_decision(self, entry: DecisionLogEntry) -> None:
        """
        Log a decision attempt.
        
        Args:
            entry: Decision log entry to record
        """
        with self._lock:
            self._entries.append(entry)
            
            # Persist to file if configured
            if self.log_file:
                try:
                    with open(self.log_file, 'a') as f:
                        f.write(json.dumps(asdict(entry)) + '\n')
                except Exception:
                    # Don't let logging failures break the simulation
                    pass
    
    def get_recent_decisions(self, faction_id: Optional[str] = None, limit: int = 10) -> List[DecisionLogEntry]:
        """
        Get recent decision entries.
        
        Args:
            faction_id: If provided, only return entries for this faction
            limit: Maximum number of entries to return
            
        Returns:
            List of decision log entries (most recent first)
        """
        with self._lock:
            entries = list(self._entries)
            
            if faction_id:
                entries = [e for e in entries if e.factionId == faction_id]
            
            # Return most recent first
            return list(reversed(entries[-limit:]))
    
    def get_latest_decision(self, faction_id: str) -> Optional[DecisionLogEntry]:
        """
        Get the most recent decision for a faction.
        
        Args:
            faction_id: Faction ID to check
            
        Returns:
            Most recent decision log entry or None if no decisions
        """
        recent = self.get_recent_decisions(faction_id=faction_id, limit=1)
        return recent[0] if recent else None
    
    def clear(self) -> None:
        """Clear all logged entries."""
        with self._lock:
            self._entries.clear()
            
            # Clear log file if configured
            if self.log_file and self.log_file.exists():
                try:
                    self.log_file.unlink()
                except Exception:
                    pass


# Global logger instance (can be replaced with dependency injection)
_decision_logger: Optional[DecisionLogger] = None


def get_decision_logger() -> DecisionLogger:
    """Get the global decision logger instance."""
    global _decision_logger
    if _decision_logger is None:
        _decision_logger = DecisionLogger()
    return _decision_logger


def set_decision_logger(logger: DecisionLogger) -> None:
    """Set the global decision logger instance."""
    global _decision_logger
    _decision_logger = logger


def log_decision(
    faction_id: str,
    tick: int,
    observation_summary: dict,
    raw_response: Optional[str],
    parsed_action_or_failure: dict,
    latency_ms: int
) -> None:
    """
    Convenience function to log a decision attempt.
    
    Args:
        faction_id: ID of the faction
        tick: Current simulation tick
        observation_summary: Summary of observation provided to agent
        raw_response: Raw response from agent
        parsed_action_or_failure: Parsed action or failure information
        latency_ms: Latency in milliseconds
    """
    logger = get_decision_logger()
    entry = DecisionLogEntry(
        factionId=faction_id,
        tick=tick,
        observationSummary=observation_summary,
        rawResponse=raw_response,
        parsedActionOrFailure=parsed_action_or_failure,
        latencyMs=latency_ms
    )
    logger.log_decision(entry)


# Convenience function for external use
def get_recent_decisions(faction_id: Optional[str] = None, limit: int = 10) -> List[DecisionLogEntry]:
    """Get recent decision entries (convenience function)."""
    return get_decision_logger().get_recent_decisions(faction_id, limit)


def get_latest_decision(faction_id: str) -> Optional[DecisionLogEntry]:
    """Get latest decision for faction (convenience function)."""
    return get_decision_logger().get_latest_decision(faction_id)