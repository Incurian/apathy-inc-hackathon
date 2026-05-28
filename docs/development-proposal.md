# Development Proposal — Three Human Leads Using Agent Swarms

## Purpose

This document turns the planning package into a practical execution plan for **three human team members**, each using agents heavily for implementation help.

The core idea is:
- agents do most of the narrow coding work
- humans own the product decisions
- humans own validation, testing, and merge decisions
- humans stop at the phase gates in the planning docs and decide whether to continue, cut scope, or redirect work

That matches the repo priorities in `AGENTS.md`: the simulation and observer experience are the product, while live agent play is an extension on top.

## Validation of the earlier draft

The earlier proposal had the right overall instinct: **interface-first parallel development** is the correct strategy.

However, it needed to be tightened in a few ways:
- it referenced stale SPEC section numbers
- it overloaded one lane with too much backend-critical work
- it did not clearly separate **human-owned validation/decision work** from **agent-owned implementation work**
- it did not define a strong enough checkpoint and integration cadence for a hackathon schedule

This revised version is aligned with:
- `SPEC.md` §11 replay requirements
- `SPEC.md` §14 agent player interface and MCP contract
- `SPEC.md` §15 spectator API and lifecycle semantics
- `docs/phases/phase-0-scope.md` through `phase-6-polish-and-demo.md`

## Non-negotiables from the current plan

This proposal does **not** change the product priorities already locked in the repo:
- the backend simulation remains authoritative
- the sim must be deterministic for a given seed and action sequence
- scripted bots must exist before live agent play becomes critical
- replay/history is an early requirement, not late polish
- the browser UI must be understandable to human observers
- MCP-facing agent play must stay behind a strict adapter boundary

The phase order still stands:
1. scope lock
2. simulation
3. scripted bots
4. observer API
5. observer UI
6. agent adapter
7. polish/demo prep

What changes here is **how three people can work in parallel without violating that order**.

## Recommended operating model

Use a **contract-first, three-lane execution plan**:

1. freeze shared contracts first
2. split into three owned lanes
3. let agents build inside those lanes
4. keep humans responsible for review, validation, and integration checkpoints
5. integrate before polishing

This gives all three people valuable work while keeping the risky product decisions in human hands.

## Shared contract freeze first (60–90 minutes)

Before parallel implementation starts, the humans should agree on these exact contracts and examples:

1. **`/api/state` spectator schema**
   - source of truth: `SPEC.md` §15 and `docs/phases/phase-3-api.md`
   - must include match metadata, factions, nodes/sites, missiles, recent events, and latest actions/summaries needed by the UI

2. **`/api/replay/latest` replay schema**
   - source of truth: `SPEC.md` §11 and `docs/phases/phase-3-api.md`
   - must include match metadata, ordered events, periodic snapshots, and final state

3. **Controller interface used by the simulation**
   - one clean boundary so scripted bots and MCP-backed agents plug in the same way
   - simulation asks for one action per decision window and receives either a valid action or a safe hold/no-op result

4. **MCP observation payload**
   - source of truth: `SPEC.md` §14
   - must reflect the no-fog MVP model and include legal actions

5. **MCP action response payload**
   - source of truth: `SPEC.md` §14
   - exactly one top-level `action`, plus optional `comment`

6. **Lifecycle semantics**
   - source of truth: `SPEC.md` §15
   - `idle`, `running`, `paused`, `finished`

7. **Ownership and merge rules**
   - who owns which directories
   - which files are shared seams
   - who approves contract changes

Humans should also check in or at least write down **example payloads** early. Those examples are what let the UI and agent-adapter lanes move before the full backend is finished.

## Recommended lane split

### Lane A — Simulation core and scripted controllers

**Human owner focus:** rules, deterministic behavior, core engine correctness

**Primary directories:**
- `src/sim/`
- `src/bots/`
- `tests/sim/`
- `data/scenarios/`

**Owns:**
- state models and scenario initialization
- tick stepping and action resolution
- missile travel and impact logic
- score and faction-status updates
- deterministic seeded match driver
- scripted bot policies
- canonical event emission from the engine
- snapshot generation hooks for replay

**Should deliver:**
- a headless match that runs from start to finish
- deterministic replay/event emission from the authoritative backend
- a controller hook that both scripted bots and agent adapters can plug into

**Should not own:**
- browser rendering
- UI interaction logic
- direct MCP transport/tooling
- presentation-only serializer choices unless they affect engine invariants

**Human validation focus:**
- same seed + same actions => same outcome
- invalid actions do not corrupt state
- impacts happen at the correct tick
- crippled vs eliminated rules match the spec
- replay events and snapshots are complete enough for later consumers

### Lane B — Spectator API and observer UI

**Human owner focus:** observer clarity, operator flow, API usability

**Primary directories:**
- `src/api/`
- `src/replay/` for replay serialization/exposure
- `web/`
- `tests/api/`
- `scripts/smoke/`

**Owns:**
- `/api/state` serialization layer
- lifecycle endpoints: start, pause, resume, reset
- `/api/replay/latest` exposure
- mock fixture generation for UI development
- browser page/layout
- strategic map rendering
- scoreboard, event log, and inspector
- operator controls and polling behavior

**Should deliver:**
- a UI that works first against agreed mock payloads, then against the real backend
- an API shape that can drive the whole observer experience without UI-side game logic
- a replay/history surface that supports post-match review

**Should not own:**
- core game rules
- engine-side mutation logic
- direct agent-decision logic

**Human validation focus:**
- can a spectator tell who is winning quickly?
- are launches, impacts, and destroyed assets readable?
- does the inspector answer useful questions?
- do lifecycle controls behave correctly in all states?
- can the demo still work from replay data if live play is shaky?

### Lane C — Agent adapter, mixed-control integration, and failure-path testing

**Human owner focus:** safe agent integration, contract enforcement, cross-lane validation

**Primary directories:**
- `src/agent_adapter/`
- `tests/integration/`
- `scripts/demo/` for agent/demo helpers if needed

**Owns:**
- MCP-facing observation builder
- strict action parser and validator
- timeout/parse/illegal-action fallback behavior
- decision-attempt logging
- mixed-controller integration path
- regression tests for valid and invalid agent behavior
- fixtures and harnesses for observation/action contract validation

**Should deliver:**
- an agent control path that cannot bypass engine validation
- safe degradation to hold/no-op on malformed output or timeouts
- mixed-control matches where scripted and agent-backed factions coexist cleanly
- integration tests that prove the adapter does not destabilize the simulation

**Should not own:**
- authority over simulation rules
- UI rendering decisions except where agent activity needs exposure in the observer
- ad hoc schema changes without human approval from the contract owners

**Human validation focus:**
- malformed output never crashes the match
- legal actions are applied exactly once
- invalid actions are rejected and logged clearly
- observation payloads are small enough for weaker models
- the adapter remains a boundary, not a backdoor into the engine

## Why this split is better than the original version

This version is better for the current repo because it avoids giving one person the entire backend critical path.

In particular:
- **Lane A** owns the authoritative engine and bots
- **Lane B** owns the spectator-facing product slice and can start from mocks immediately
- **Lane C** owns the high-risk integration and failure-path work that would otherwise be neglected until too late

That means all three people have work that is both meaningful and demo-relevant:
- one protects game correctness
- one protects observer value
- one protects agent safety and integration quality

## Human responsibilities vs. agent responsibilities

### Humans should own
- product and scope decisions
- contract freeze and contract changes
- phase-gate approvals
- manual validation and demo-readability checks
- deterministic test review
- risky integration decisions
- merge/conflict resolution
- changelog and lessons-learned updates
- final cut-line decisions when time slips

### Agents should own
- implementing narrow modules inside a lane
- generating fixtures and serializers from frozen contracts
- writing targeted tests
- wiring straightforward UI panels or API handlers
- producing draft docs or smoke scripts for human review

### Humans should not delegate blindly
Do **not** let agents silently decide:
- new gameplay rules
- schema-breaking contract changes
- how to cut scope
- whether validation is “good enough”
- whether a risky demo path is acceptable

## Checkpoint cadence

Use short, human-led checkpoints rather than waiting for a giant merge.

### Checkpoint 0 — Contract freeze
Humans agree on:
- schemas
- controller interface
- ownership boundaries
- first integration sequence

### Checkpoint 1 — Mocked lane starts
Expected outputs:
- Lane A: engine model/rule skeleton and deterministic test plan
- Lane B: checked-in mock `/api/state` and `/api/replay/latest` fixtures plus UI shell
- Lane C: checked-in mock observation/action examples plus validation harness outline

### Checkpoint 2 — Isolated lane demos
Expected outputs:
- Lane A: one headless seeded match run with events
- Lane B: one UI view driven entirely from mock data
- Lane C: one successful valid action and one invalid/timeout fallback trace

### Checkpoint 3 — Pairwise integration
Integrate in this order:
1. Lane A + Lane B on real `/api/state`
2. Lane A + Lane C on real controller hook and agent adapter
3. replay exposure and decision-log visibility across all lanes

### Checkpoint 4 — Full-system rehearsal
Show:
- one full match in the browser
- event/replay review
- one safe agent-participant flow
- one fallback demo path if live agent behavior fails

## Recommended merge and ownership rules

- Prefer one human owner per lane for final review and merge approval.
- Treat shared contracts as explicit approval points, not casual edits.
- If a lane needs a contract change, stop and get human agreement first.
- Keep commits small and lane-local where possible.
- Do not mix broad cleanup into a checkpoint merge.
- Re-run focused validation after each real integration step.

## If the schedule slips

Cut scope differently per lane rather than stalling all three people.

### Lane A cuts last
Keep:
- deterministic full match
- missiles, impacts, score, end conditions
- scripted bots

Cut first:
- any non-MVP combat nuance
- extra replay sophistication beyond the required event/snapshot contract

### Lane B cuts by reducing polish
Keep:
- readable map
- scoreboard
- event log
- inspector
- start/pause/resume/reset

Cut first:
- fancy animation
- advanced replay controls
- visual extras that do not improve readability

### Lane C cuts by shrinking live-agent ambition
Keep:
- one safe agent-controlled faction path
- strict schema validation
- timeout/invalid fallback

Cut first:
- reasoning display
- multi-agent commentary
- anything that loosens validation in exchange for demo flash

## Bottom line

Yes, the project can be parallelized across three people **without inventing fake work**.

The best split is not “three people each writing random pieces of code.”
It is:
- one human protecting the deterministic core
- one human protecting the observer product
- one human protecting the agent boundary and integration quality

Agents can do most of the coding inside those lanes.
Humans should spend their scarce time on:
- decisions
- validation
- testing
- integration
- demo readiness

That is the highest-value use of the three-person team for this repo.
