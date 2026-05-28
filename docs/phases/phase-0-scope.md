# Phase 0 — Scope Lock and Architecture Alignment

## Objective

Lock the MVP scope, core rules, data model, and team workflow before implementation begins.

This phase exists to prevent the common hackathon failure mode of starting with flashy UI or agent integration before the game loop is stable.

## Deliverables

- agreed MVP ruleset
- agreed list of in-scope entities
- agreed list of out-of-scope features
- high-level architecture sketch
- initial file/module plan
- ranked backlog: MVP / should-have / stretch
- named owner for each early subsystem
- agreed three-lane execution plan with human validation checkpoints

## Required outputs

By the end of this phase, the team should have a written answer for all of the following:

1. What entities exist in MVP?
2. What actions can a faction take?
3. How does the game end?
4. What exact MVP constants are frozen?
5. What must the observer be able to see?
6. What will be recorded for replay?
7. What is the lifecycle state model?
8. What MCP tools will agent players use?
9. What are the first three stretch goals to cut if time slips?
10. What are the exact shared contracts that let the three work lanes proceed in parallel?
11. Which human owns each lane, and what are the required integration checkpoints?

## Recommended work sequence

### Step 0.1 — Confirm the fantasy and observer story
Decide the exact demo framing:
- autonomous strategic war game
- humans are spectators/operators, not players
- observers can inspect actors and recent actions

### Step 0.2 — Freeze the MVP rules
Choose the smallest real version and lock the canonical constants:
- 4 factions
- 2 cities + 1 silo per faction
- only `hold` and `launch` actions
- no defense sites in MVP
- 5-minute match timer
- 250ms simulation tick
- 4-second decision cadence
- 8-second missile flight time
- score based mainly on surviving population plus a small silo-destruction bonus
- one-hit destruction for cities and silos in MVP

### Step 0.3 — Freeze the MVP map approach
Choose one:
- stylized fixed map with hand-placed coordinates
- or very simple abstract strategic map

Do **not** attempt dynamic world generation in MVP.

### Step 0.4 — Freeze the architecture
Recommended:
- Python backend
- deterministic simulation module
- simple HTTP API
- plain HTML/CSS/JS observer UI
- SVG-first rendering

### Step 0.5 — Freeze replay strategy
Lock the MVP replay contract early:
- event log is always recorded in chronological order
- snapshots are stored every 4 ticks (once per second)
- latest replay should expose match metadata, ordered events, snapshots, and final state

### Step 0.6 — Freeze lifecycle, API, replay, and MCP contracts
Lock:
- lifecycle states: `idle`, `running`, `paused`, `finished`
- spectator API baseline: `/api/state`, lifecycle endpoints, and `/api/replay/latest`
- agent-player MCP tools: `get_faction_observation(faction_id)` and `submit_faction_action(faction_id, action, comment?)`
- MVP information model: no fog of war; all factions receive the same public strategic state

Then sort everything into:
- MVP
- post-MVP nice-to-have
- stretch/cut-first

### Step 0.7 — Assign the three human work lanes and validation cadence
Before implementation begins, name the three primary human owners and make the split explicit.
Recommended lane split:
- simulation core + scripted bots
- spectator API + observer UI
- agent adapter + integration/failure-path validation

Also lock:
- who owns each directory or subsystem seam
- which shared contracts require human approval before changing
- what evidence each lane must show at the next checkpoint
- how often humans stop to review agent-generated work
## Human validation gates

### Gate A — Fantasy alignment
**Stop and show a human:**
- the one-sentence pitch
- the exact audience experience
- 3 screenshots or rough wireframe notes if available

**Human should answer:**
- “Would this still be interesting if the AI behavior is mediocre?”
- “Can I explain this game in under 30 seconds?”

Do not continue until the answer is yes.

### Gate B — Rules lock
**Stop and show a human:**
- the final list of entity types
- allowed actions
- win condition and elimination semantics
- exact MVP constants
- what is explicitly out of scope

**Human should answer:**
- “Is this small enough to finish today?”
- “Does this still feel like a real product?”

### Gate C — Architecture lock
**Stop and show a human:**
- backend/frontend split
- replay approach
- no-build-tooling decision unless overridden
- validation plan for Phases 1–2

**Human should answer:**
- “Can we validate the core loop before touching fancy UI?”

## Validation checklist

Before exiting Phase 0, verify that:
- `SPEC.md` or equivalent is coherent and current
- there are no unresolved debates about core entity types
- the team agrees on one rendering baseline for MVP
- the backlog has a clearly marked cut line
- there is a single stated definition of done for MVP

## Exit criteria

Phase 0 is complete when:
- all MVP rules are written and agreed
- every team member can describe the MVP similarly
- risky features have been explicitly pushed right
- the team is ready to begin a headless simulation without further debate

## If behind schedule during Phase 0

Cut discussion time, not product clarity. If necessary:
- pick the simpler rule
- choose the simpler API
- choose the simpler UI layout
- defer realism immediately
