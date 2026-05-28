# Detailed Specification

## 1. Product summary

Build a local spectator application for a DEFCON-inspired autonomous strategy game.

- AI agents play as rival factions
- The backend runs a deterministic strategic war simulation
- Human observers watch a live match in a browser
- Human observers can inspect factions, cities, silos, missiles, and recent events
- Finished matches can be replayed or at least reviewed through recorded state/events

The project is intended to be hackathon-practical: simple enough to finish, strong enough to demo.

---

## 2. Product goals

### Primary goals
- Create a compelling agent-vs-agent spectacle
- Make the battle readable to a human audience
- Allow humans to inspect what happened and why
- Preserve demo value even if live LLM play is unstable

### Secondary goals
- Show recent agent decisions or reasoning snippets
- Support replay of completed matches
- Allow speed control, pause/resume, and reset

### Non-goals for MVP
- full DEFCON feature parity
- realistic geopolitics
- sophisticated diplomacy
- high-fidelity military simulation
- advanced multiplayer networking
- complex 3D world rendering

---

## 3. Target users

### Primary user: human observer
Wants to:
- watch the game unfold live
- understand who is winning
- inspect actors and recent actions
- replay a completed match

### Secondary user: hackathon operator
Wants to:
- start, pause, reset, and rerun matches
- swap between scripted and agent-controlled players
- inspect raw agent outputs and invalid actions

### Tertiary user: AI player agent
Needs to:
- receive a compact structured view of the current game state
- output simple legal actions in strict JSON
- fail safely if confused or timed out

---

## 4. Core product loop

1. A new match starts with a fixed map and several factions
2. The simulation advances on ticks
3. Each faction periodically chooses an action
4. Launches create missiles that visibly travel toward targets
5. Impacts damage or destroy cities/silos
6. Score and remaining population shift over time
7. The observer watches, inspects, and reviews events
8. The match ends on timer expiry or effective elimination
9. Replay/history remains available for inspection

---

## 5. Game structure

### Recommended MVP match setup
- 4 factions
- 2 cities per faction
- 1 silo per faction
- optional 1 defense site per faction only if time allows
- match duration: 5 to 8 minutes
- simulation tick: 250ms to 500ms
- decision cadence: one decision per faction every 3 to 5 seconds

### Win condition
At match end, the winner is the faction with the highest final score.

### Recommended MVP score model
- surviving population contributes the largest share
- destroying enemy cities/silos adds smaller bonus points
- a faction may also be considered defeated if it has no surviving cities or no launch capability

---

## 6. World model

Use a fixed stylized strategic map rather than a realistic geographic simulation.

### Node-based map
Represent key locations as named map nodes with known screen/world coordinates.

### Required node types
- `city`
- `silo`

### Optional node type
- `defense_site`

### Node fields
```json
{
  "id": "red-city-1",
  "name": "Red Capital",
  "owner": "red",
  "type": "city",
  "x": 420,
  "y": 280,
  "hp": 100,
  "population": 120,
  "status": "active"
}
```

---

## 7. Factions

Each faction must have:
- `id`
- display name
- color
- remaining population
- score
- status (`active`, `crippled`, `eliminated`)
- list of owned sites
- last action / last valid order
- control mode (`scripted`, `agent`, optionally `human-debug`)

Example:
```json
{
  "id": "red",
  "name": "Red Directorate",
  "color": "#ff4d5a",
  "population": 240,
  "score": 180,
  "status": "active",
  "controlMode": "agent",
  "lastAction": {"type": "launch", "from": "red-silo-1", "target": "blue-city-2"}
}
```

---

## 8. Entity types

### 8.1 City
Purpose:
- source of population/value
- high-priority target

Fields:
- hp
- population/value
- incoming missile count
- last hit tick/time

### 8.2 Silo
Purpose:
- launches missiles

Fields:
- ammo
- cooldown
- hp
- active/destroyed state

### 8.3 Missile
Purpose:
- transient moving attack entity

Fields:
- owner
- source node id
- target node id
- launch tick/time
- impact tick/time or ETA
- current interpolated position
- status (`flying`, `intercepted`, `impact`, `expired`)

### 8.4 Defense site (optional MVP+)
Purpose:
- automatic interception chance within a radius or against incoming missiles

Fields:
- radius
- intercept chance
- ammo or charges if desired

---

## 9. Allowed actions

Keep the MVP action space very small.

### Required MVP actions
- `hold`
- `launch`

### Launch action
```json
{
  "type": "launch",
  "from": "red-silo-1",
  "target": "blue-city-2"
}
```

### Hold action
```json
{
  "type": "hold"
}
```

### MVP rules
- each faction may issue at most one action per decision window
- invalid actions are ignored and logged
- actions from destroyed or cooling-down silos are invalid
- if an agent times out or emits invalid JSON, the faction holds for that turn

---

## 10. Simulation rules

### Tick model
- The simulation advances on fixed ticks
- Missile travel is resolved incrementally over time
- Decision windows happen every N ticks

### Launch resolution
When a launch action is accepted:
- check legality
- consume silo ammo
- start cooldown if used
- create a missile entity with source, target, launch tick, and arrival tick
- append a launch event

### Travel resolution
Each tick:
- move missiles along their path by interpolation or recomputed progress
- update incoming threat counts if needed

### Impact resolution
On impact:
- damage the target
- destroy the target if hp <= 0
- reduce city population/value if applicable
- update faction score/population
- emit impact and destruction events

### Elimination
A faction may become `crippled` or `eliminated` when:
- all cities are destroyed, or
- all strategic capacity is gone, depending on final rules chosen

---

## 11. Replay and event recording

Replay is an early requirement, not end-stage polish.

### Minimum replay requirement
Record enough information to reconstruct or review a match:
- event log for all launches, impacts, destructions, invalid actions, and match transitions
- periodic snapshots or a full tick-state history

### Recommended approach
- append events continuously
- store full snapshots every N ticks
- keep a final replay artifact in memory or on disk for the latest match

### Observer benefit
Replay provides:
- a fallback demo if live play is unstable
- debugging support
- explainability for human observers

---

## 12. Observer UI requirements

### Main page layout
The observer UI should include:
- central strategic map
- faction scoreboard
- recent event log
- selected entity inspector
- match controls

### Map view must show
- cities and silos as nodes
- faction ownership by color
- missiles in flight
- visible impact/explosion feedback
- optional targeting lines or arcs

### Sidebar / panels should show
- faction score/population/status
- incoming threats or top active missiles
- recent actions/events
- selected entity details

### Required interactions
- click faction to inspect
- click city/silo to inspect
- click missile if feasible
- click event to highlight relevant entities if feasible

### Match controls
- start new match
- pause
- resume
- reset
- optional speed control (1x/2x)

---

## 13. Inspector requirements

### Faction inspector
Show:
- name, color, status
- control mode
- score
- surviving population
- available ammo / surviving assets
- last action
- invalid action count if useful

### City inspector
Show:
- owner
- hp/status
- population/value
- incoming missiles
- recent damage

### Silo inspector
Show:
- owner
- ammo
- cooldown
- hp/status
- last launch

### Missile inspector
Show:
- owner
- source
- target
- ETA or progress
- launched at tick/time

---

## 14. Agent player interface

Agent players should not manipulate internal game state directly.
They should connect to the game **via MCP-facing tooling or an MCP-compatible adapter layer**, not by directly importing or mutating the simulation internals.
They receive an observation object and return structured actions.

### MCP integration requirement

The intended integration model is:
- the game exposes a small MCP tool surface or an equivalent local adapter that is designed for MCP-connected agents
- agent players connect through that MCP layer to read current faction observations and submit actions
- the simulation remains backend-authoritative at all times
- agents must never bypass validation by writing directly into engine state

For MVP, it is acceptable for the actual implementation to use a thin local adapter around the backend as long as that adapter is explicitly shaped for MCP-style request/response interaction and can be surfaced as MCP tools cleanly.

### Observation shape

This observation should be what the MCP-facing adapter hands to the agent for its turn.

```json
{
  "match": {
    "matchId": "match-001",
    "tick": 120,
    "timeRemainingSec": 214
  },
  "self": {
    "factionId": "red",
    "population": 240,
    "score": 180,
    "status": "active",
    "sites": [
      {"id": "red-silo-1", "type": "silo", "ammo": 2, "cooldown": 0, "active": true}
    ]
  },
  "world": {
    "factions": [
      {"id": "blue", "status": "active", "population": 180, "score": 120}
    ],
    "targets": [
      {"id": "blue-city-1", "owner": "blue", "type": "city", "hp": 100, "value": 120},
      {"id": "blue-silo-1", "owner": "blue", "type": "silo", "hp": 80, "value": 60}
    ],
    "missiles": [
      {"id": "m-14", "owner": "green", "target": "red-city-2", "etaSec": 4}
    ]
  },
  "recentEvents": [
    {"tick": 116, "type": "impact", "target": "red-city-1", "damage": 40}
  ],
  "legalActions": [
    {"type": "hold"},
    {"type": "launch", "from": "red-silo-1", "allowedTargets": ["blue-city-1", "blue-silo-1"]}
  ]
}
```

### Action response shape

This action payload should be what the agent returns through the MCP-facing adapter back to the authoritative backend.

```json
{
  "actions": [
    {"type": "launch", "from": "red-silo-1", "target": "blue-city-1"}
  ],
  "comment": "Attempting to reduce enemy population while preserving ammo efficiency."
}
```

### Safe failure behavior
- parse failure => `hold`
- timeout => `hold`
- invalid action => ignored, logged, and treated as `hold`

---

## 15. Suggested API surface

### Required MVP endpoints
- `GET /api/state` — full current spectator state
- `POST /api/start` — initialize and start a new match
- `POST /api/pause`
- `POST /api/resume`
- `POST /api/reset`
- `GET /api/replay/latest` — latest replay artifact or event log

### Optional endpoints
- `GET /api/entity/<id>`
- `GET /api/faction/<id>`
- `GET /api/config`
- `POST /api/speed` — set playback speed

### `/api/state` should include
- match metadata
- factions
- nodes/sites
- missiles
- recent events
- selected summary metrics
- optionally latest raw agent action summaries

---

## 16. MVP acceptance criteria

The MVP is complete when:
- a match can run from start to finish with scripted bots
- `/api/state` exposes enough data for a spectator UI
- the spectator UI shows a live strategic map and changing score/event data
- a human can click at least factions, cities, and silos to inspect details
- the game records enough history for replay or post-match review
- one agent-controlled faction can participate without crashing the sim

---

## 17. Stretch goals

### Good stretch goals
- automated defense/interception sites
- speed controls and replay scrubber
- agent reasoning snippets in the UI
- threat highlighting and filters
- match presets or scenario selection
- commentator panel summarizing big events

### High-risk stretch goals
- 3D globe
- submarines/mobile launchers
- fog of war
- diplomacy/alliances
- multi-turn planning negotiations
- complex asset pathfinding

These should only be attempted after MVP is stable and demo-ready.

---

## 18. Out of scope for the first finished version

- realistic world map projection concerns
- realistic missile physics
- networked multiplayer observers
- production authentication/security
- large-scale content authoring tools
- polished mobile support

---

## 19. Demo success definition

A successful demo looks like this:
- the operator starts a match locally
- the map immediately becomes active and readable
- factions visibly launch missiles at one another
- score/population and event log change in a legible way
- a human clicks actors and sees useful details
- at least one AI agent faction participates or its decisions are shown from a recorded match
- if live agents fail, the team can still replay a completed match and explain what happened
