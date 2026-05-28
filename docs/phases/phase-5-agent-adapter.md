# Phase 5 — Agent Player Adapter

## Objective

Integrate one or more AI-controlled factions without destabilizing the simulation.

This phase should treat LLM/agent players as replaceable controllers behind a strict interface, not as privileged parts of the engine.
The intended connection model is **MCP-first**: agents should interact with the game through MCP tools or a thin MCP-compatible local adapter, not by reaching into engine internals directly.

## Deliverables

- actual MVP MCP tool contract for agent-controlled factions
- observation builder for a faction
- single-action parser/validator
- timeout-safe agent invocation path
- action/error logging
- control-mode assignment per faction
- at least one successful agent-controlled match participant

## Design principles

- backend remains authoritative
- agents never mutate simulation state directly
- invalid output never crashes the match
- every agent decision attempt is inspectable
- one agent-controlled faction is enough for MVP proof

## Build sequence

### Step 5.1 — Freeze MCP-facing observation schema
Build one compact observation object for a faction.
This is the payload the MCP tool should provide to the agent on its turn.

It should include:
- current match metadata
- faction self-state
- full public strategic target summaries for MVP (no fog of war)
- recent events
- legal actions

### Step 5.2 — Freeze action schema
Require strict JSON with a very small action surface.

For MVP this should remain:
- `hold`
- `launch`

The returned payload should contain exactly one top-level `action`, not an action list.

### Step 5.3 — Build parser and fallback behavior
Handle these cases safely:
- invalid JSON
- empty response
- timeout
- illegal action
- references to nonexistent targets

Fallback behavior should be `hold` plus logging.

### Step 5.4 — Build MCP tool interface and internal adapter boundary
Support control modes such as:
- scripted bot
- agent/LLM player via MCP
- maybe debug/manual controller

The required MVP MCP tools should be:
- `get_faction_observation(faction_id)`
- `submit_faction_action(faction_id, action, comment?)`

### Step 5.5 — Log decision attempts
Store for each agent turn:
- faction id
- prompt/observation summary or reference
- raw response
- parsed action or failure reason
- time taken

### Step 5.6 — Surface latest actions to the observer UI
If time permits, expose:
- latest valid action per faction
- latest invalid response summary
- optional reasoning/comment text

## Human validation gates

### Gate A — Observation and action review
**Stop and show a human:**
- one actual observation payload
- one expected valid single-action payload
- the MCP tool names and their request/response shapes
- the invalid-output fallback behavior

**Human should verify:**
- the schema is small enough for weaker models
- the agent does not need hidden engine knowledge

### Gate B — First successful agent turn
**Stop and show a human:**
- one real agent decision cycle
- raw response
- parsed action
- resulting state/event change

**Human should verify:**
- the integration feels real, not mocked
- the fallback behavior is safe and understandable

### Gate C — One mixed-control match
**Stop and show a human:**
- a match with at least one agent-controlled faction and the rest scripted
- action logs for both valid and invalid cases if possible

**Human should verify:**
- the system remains stable when the agent behaves badly
- the project can still be demoed even if only one agent works reliably

## Machine validation checklist

Validate at least:
- malformed agent output does not crash the engine
- timeout leads to hold/no-op behavior
- invalid actions are logged and rejected
- a valid parsed single action is applied exactly once
- the MCP-facing adapter exposes the required tool contract cleanly
- mixed controller modes can coexist in one match

## Exit criteria

Phase 5 is complete when:
- one or more factions can be controlled by an AI agent via the adapter
- failures degrade safely
- decision attempts are logged for debugging/inspection
- the observer can at least indirectly tell what the agent attempted

## If behind schedule

Reduce scope to:
- one agent-controlled faction
- one simple strict action schema
- no fancy reasoning UI

Do not loosen validation just to make the agent seem more capable.
