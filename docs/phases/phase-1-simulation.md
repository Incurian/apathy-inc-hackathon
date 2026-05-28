# Phase 1 — Deterministic Headless Simulation

## Objective

Build the core game loop with no dependency on the final observer UI.

This is the heart of the product. If this phase works, the project already has a meaningful core.

## Deliverables

- match initialization
- fixed map/state model
- tick advancement
- legal action application
- missile travel and impact resolution
- score/population updates
- faction elimination state
- deterministic seeded runs
- simulation smoke tests

## Suggested module boundaries

Recommended modules or equivalents:
- `sim/models.py` — entities and state shapes
- `sim/rules.py` — rule constants and validation
- `sim/engine.py` — tick stepping and resolution
- `sim/scenario.py` — initial map/faction setup
- `sim/scoring.py` — score/win logic
- `tests/` or `scripts/` for deterministic validation

## Build sequence

### Step 1.1 — Define state structures
Create explicit structures for:
- match state
- faction state
- node/site state
- missile state
- event records

Keep them serializable to JSON.

### Step 1.2 — Build scenario initialization
Create a fixed map and initial faction loadout.

Required initial data:
- factions
- nodes/sites with coordinates and hp/population
- initial ammo and cooldown values
- match timer/tick settings

### Step 1.3 — Implement legal action validation
Build a pure function or equivalent that checks:
- faction can act
- source silo exists and belongs to actor
- silo is alive
- silo has ammo
- silo is off cooldown
- target exists and is legal

### Step 1.4 — Implement launch creation
A valid launch should:
- decrement ammo
- create missile entity
- emit launch event
- set cooldown

### Step 1.5 — Implement tick stepping
Every tick should:
- advance simulation time
- move missiles or update their progress
- resolve impacts at arrival
- reduce HP / population
- emit impact/destruction events
- update faction status
- update score

### Step 1.6 — Implement match end detection
End the match when:
- timer expires, or
- a faction is the only credible survivor according to chosen rules

### Step 1.7 — Determinism and smoke tests
Add a small test or script that runs a match with scripted actions and verifies repeatability.

## Human validation gates

### Gate A — First legal launch
**Stop and show a human:**
- a printed or serialized state before launch
- the accepted action
- the resulting state after launch
- created missile entity and event record

**Human should verify:**
- ammo dropped correctly
- launch event is understandable
- missile metadata is sufficient for UI and replay

### Gate B — First visible impact in logs
**Stop and show a human:**
- a short run from launch through impact
- the state delta at impact
- updated score/population
- destruction handling if applicable

**Human should verify:**
- the consequences feel legible and game-like
- the rules are simple enough to explain in the demo

### Gate C — Full seeded match
**Stop and show a human:**
- a full match summary
- winner output
- event counts
- sample replay data or event history

**Human should verify:**
- the match has a beginning, middle, and end
- the result feels believable enough for a demo
- no extra mechanics are required to make it interesting

## Machine validation checklist

Required validation examples:
- same seed + same actions => same outcome
- invalid launch does not mutate state except for logged error/invalid event if designed
- a missile launched at tick T impacts at the expected future tick
- destroyed targets remain destroyed
- eliminated factions do not continue launching

## Exit criteria

Phase 1 is complete when:
- a full match can run headlessly to completion
- deterministic runs work
- events and state are serializable
- the outcome can be summarized without a UI

## If behind schedule

Cut complexity in this order:
1. defense/interception
2. partial damage complexity
3. advanced score modifiers
4. nuanced elimination states

Keep:
- launch
- missile travel
- impact
- score
- end condition
