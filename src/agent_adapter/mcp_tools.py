"""
MCP tool implementations for agent adapter.
Based on SPEC.md Section 14: Required MVP MCP tool surface.
"""

import asyncio
import logging
from typing import Dict, Optional
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

from .observation_builder import build_observation
from .action_parser import parse_and_validate_action
from .fallback import handle_agent_response
from .logging import log_decision
import time

# Configure logging
logger = logging.getLogger(__name__)

# Global references to simulation state (would be injected in real implementation)
_simulation_state = None
_faction_registry = {}  # faction_id -> faction object


def set_simulation_state(simulation_state):
    """Set the global simulation state reference."""
    global _simulation_state
    _simulation_state = simulation_state


def register_faction(faction_id: str, faction_obj):
    """Register a faction for MCP tool access."""
    global _faction_registry
    _faction_registry[faction_id] = faction_obj


def get_faction(faction_id: str):
    """Get faction object by ID."""
    return _faction_registry.get(faction_id)


# MCP Server setup
server = Server("defcon-agent-adapter")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available MCP tools."""
    return [
        types.Tool(
            name="get_faction_observation",
            description="Get the current observation for a faction",
            inputSchema={
                "type": "object",
                "properties": {
                    "faction_id": {
                        "type": "string",
                        "description": "ID of the faction to get observation for"
                    }
                },
                "required": ["faction_id"]
            }
        ),
        types.Tool(
            name="submit_faction_action",
            description="Submit an action for a faction",
            inputSchema={
                "type": "object",
                "properties": {
                    "faction_id": {
                        "type": "string",
                        "description": "ID of the faction submitting action"
                    },
                    "action": {
                        "type": "object",
                        "description": "Action object (hold or launch)"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Optional comment from agent"
                    }
                },
                "required": ["faction_id", "action"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle MCP tool calls."""
    
    if name == "get_faction_observation":
        return await get_faction_observation(arguments)
    elif name == "submit_faction_action":
        return await submit_faction_action(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def get_faction_observation(arguments: dict) -> list[types.TextContent]:
    """
    Get observation for a faction.
    MCP tool: get_faction_observation(faction_id)
    """
    faction_id = arguments.get("faction_id")
    if not faction_id:
        return [types.TextContent(
            type="text",
            text="Error: faction_id is required"
        )]
    
    faction = get_faction(faction_id)
    if not faction:
        return [types.TextContent(
            type="text",
            text=f"Error: Faction '{faction_id}' not found"
        )]
    
    if _simulation_state is None:
        return [types.TextContent(
            type="text",
            text="Error: Simulation state not available"
        )]
    
    try:
        # Build observation using current simulation state
        observation = build_observation(
            match_id=_simulation_state.match_id,
            tick=_simulation_state.tick,
            time_remaining_sec=_simulation_state.time_remaining_sec,
            factions=_simulation_state.factions,
            requesting_faction_id=faction_id,
            events=getattr(_simulation_state, 'recent_events', [])
        )
        
        return [types.TextContent(
            type="text",
            text=observation.json()
        )]
        
    except Exception as e:
        logger.error(f"Error building observation for faction {faction_id}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error building observation: {str(e)}"
        )]


async def submit_faction_action(arguments: dict) -> list[types.TextContent]:
    """
    Submit action for a faction.
    MCP tool: submit_faction_action(faction_id, action, comment?)
    """
    faction_id = arguments.get("faction_id")
    action = arguments.get("action")
    comment = arguments.get("comment")
    
    if not faction_id:
        return [types.TextContent(
            type="text",
            text="Error: faction_id is required"
        )]
    
    if action is None:
        return [types.TextContent(
            type="text",
            text="Error: action is required"
        )]
    
    faction = get_faction(faction_id)
    if not faction:
        return [types.TextContent(
            type="text",
            text=f"Error: Faction '{faction_id}' not found"
        )]
    
    if _simulation_state is None:
        return [types.TextContent(
            type="text",
            text="Error: Simulation state not available"
        )]
    
    try:
        # Record start time for latency measurement
        start_time = time.time()
        
        # Convert action dict to JSON string for parsing
        import json
        raw_response = json.dumps({
            "action": action,
            "comment": comment
        })
        
        # Parse and validate the action with fallback behavior
        parsed_action, error_reason = parse_and_validate_action(
            raw_response, faction, _simulation_state
        )
        
        # Apply fallback behavior (timeout, invalid actions, etc.)
        final_action, log_entry = handle_agent_response(
            faction_id=faction_id,
            tick=_simulation_state.tick,
            observation=build_observation(  # Build current observation for logging
                match_id=_simulation_state.match_id,
                tick=_simulation_state.tick,
                time_remaining_sec=_simulation_state.time_remaining_sec,
                factions=_simulation_state.factions,
                requesting_faction_id=faction_id,
                events=getattr(_simulation_state, 'recent_events', [])
            ),
            raw_response=raw_response,
            start_time=start_time,
            parser_func=lambda resp, fac, sim_state: parse_and_validate_action(resp, fac, sim_state)
        )
        
        # Log the decision attempt
        log_decision(
            faction_id=faction_id,
            tick=_simulation_state.tick,
            observation_summary=log_entry["observationSummary"],
            raw_response=raw_response,
            parsed_action_or_failure=log_entry["parsedActionOrFailure"],
            latency_ms=log_entry["latencyMs"]
        )
        
        # If we have a valid action (not hold due to error), apply it
        # In a real implementation, this would interface with the simulation controller
        if final_action.get("type") != "hold" or error_reason is None:
            # Action is valid, return success
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "action": final_action,
                    "message": "Action submitted successfully"
                })
            )]
        else:
            # Action resulted in hold (error case)
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "action": final_action,
                    "error": error_reason or "Invalid action",
                    "message": "Action rejected, fallback to hold applied"
                })
            )]
            
    except Exception as e:
        logger.error(f"Error processing action for faction {faction_id}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error processing action: {str(e)}"
        )]


async def serve():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="defcon-agent-adapter",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(serve())