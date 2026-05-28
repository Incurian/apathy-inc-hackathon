# Phase 3 — Observer API and Replay Surface

## Objective

Expose the simulation to the browser UI and preserve enough data for replay and inspection.

This phase turns the headless game into a product platform.

## Deliverables

- backend service exposing current state
- start/pause/resume/reset endpoints
- replay/event endpoint
- serialized state shape suitable for the UI
- state snapshots and/or replay history representation

## Recommended minimal endpoints

- `GET /api/state`
- `POST /api/start`
- `POST /api/pause`
- `POST /api/resume`
- `POST /api/reset`
- `GET /api/replay/latest`

Optional later:
- `GET /api/entity/<id>`
- `GET /api/faction/<id>`
- `POST /api/speed`

## Build sequence

### Step 3.1 — Define spectator state schema
Decide exactly what the UI needs on each poll.

Suggested sections:
- match metadata
- factions summary
- nodes/sites
- missiles in flight
- recent events
- current leader / summary metrics
- latest actions per faction

### Step 3.2 — Serialize current state cleanly
Create one clear serialization layer rather than leaking internal model objects directly.

### Step 3.3 — Add match lifecycle endpoints
Support:
- start new match
- pause ticking
- resume ticking
- reset to initial or fresh scenario

### Step 3.4 — Add replay/history endpoint
At minimum, expose:
- latest match event list
- enough snapshots or current/final state to reconstruct the match meaningfully

### Step 3.5 — Add smoke scripts
Write a script or small tests to hit all required endpoints and confirm expected shapes.

## Human validation gates

### Gate A — `/api/state` review
**Stop and show a human:**
- one actual JSON sample from a running match
- field names and nesting
- confirmation that map, score, log, and inspector can all be driven from this shape

**Human should verify:**
- the API is understandable
- the frontend will not need weird extra endpoints just to render basics

### Gate B — Replay review
**Stop and show a human:**
- one replay payload or event history sample
- enough information to tell a match story after the fact

**Human should verify:**
- the replay payload is rich enough for post-match explanation
- if live play fails, this still supports a demo

### Gate C — Lifecycle controls review
**Stop and show a human:**
- start/pause/resume/reset flow
- how a new match ID or replay state is handled

**Human should verify:**
- the operator experience is simple enough for live demo use

## Machine validation checklist

Validate at least:
- `/api/state` returns valid JSON during a running match
- `/api/state` changes over time while running and stops changing when paused
- lifecycle endpoints do not corrupt the match state
- replay endpoint returns data after a completed match
- serialization does not expose unserializable internal objects

## Exit criteria

Phase 3 is complete when:
- the backend exposes a stable spectator API
- a separate UI could be built using only these endpoints
- replay/history data exists and is retrievable
- operator controls work reliably

## If behind schedule

Keep the API small. If necessary:
- fold entity-detail lookups into `/api/state`
- use polling only
- expose latest replay only, not full replay management

Do not postpone replay/history entirely.
