# AGENTS.md

This is the **front door** for the project.

If you are a human or coding agent joining this repo, start here before making changes.

This file explains:
- what the project is
- which docs exist and which one owns what
- how to choose the current phase
- how to work safely during a hackathon
- how to keep project history, lessons, and commits up to date

---

## 1. Project mission

Build a **local, browser-based spectator game** inspired by DEFCON where AI agents act as rival strategic factions and human observers can watch, inspect, and replay the match.

The project is intentionally structured so that:
- the **simulation and observer experience are the product**
- LLM/agent players are an extension on top of that product
- the demo remains valuable even if live agent play is imperfect

That means the priority order is:
1. real deterministic simulation
2. clear observer experience
3. reliable replay/history
4. scripted bots
5. live agent players
6. polish and stretch goals

---

## 2. How to use this repo

### Start here
When beginning any task:
1. read this `AGENTS.md`
2. read `SPEC.md`
3. identify the current phase
4. read the matching phase doc in `docs/phases/`
5. check `CHANGELOG.md` for the latest state of work
6. check `notes/lessonslearned.md` for known pitfalls, strategy updates, and model behavior lessons

Do **not** jump straight into implementation without locating the current phase and constraints first.

---

## 3. Document map and ownership

These files do different jobs. Use the right one as the source of truth.

### `AGENTS.md`
Purpose:
- the operational front door
- repo workflow, priorities, document usage, and working rules

Use it for:
- onboarding
- deciding how to work
- deciding what to read next
- understanding logging/changelog/commit expectations

### `README.md`
Purpose:
- short project overview for humans
- quick explanation of the concept and document layout

Use it for:
- quick orientation
- sharing the project at a glance

### `SPEC.md`
Purpose:
- detailed product, gameplay, API, UX, and acceptance specification

Use it for:
- entity definitions
- action rules
- observer requirements
- replay requirements
- MVP boundaries

If there is ambiguity about what the product should do, **trust `SPEC.md` over README-level summaries**.

### `docs/phases/phase-0-scope.md`
Use for:
- scope locking
- architecture alignment
- deciding what is in/out of MVP

### `docs/phases/phase-1-simulation.md`
Use for:
- deterministic headless simulation work
- game engine/state/rules implementation

### `docs/phases/phase-2-bots.md`
Use for:
- scripted controller policies
- proving the sim is playable before LLM integration

### `docs/phases/phase-3-api.md`
Use for:
- spectator API design
- replay/history exposure
- backend lifecycle controls

### `docs/phases/phase-4-observer-ui.md`
Use for:
- browser UI
- live map rendering
- scoreboard/log/inspector
- operator control surface

### `docs/phases/phase-5-agent-adapter.md`
Use for:
- LLM/agent observations
- strict action schema
- parsing, fallback, timeout, and logging behavior

### `docs/phases/phase-6-polish-and-demo.md`
Use for:
- demo hardening
- polish
- fallback planning
- rehearsal and cut-line decisions

### `CHANGELOG.md`
Purpose:
- durable running record of meaningful project changes

Use it to record:
- new completed capabilities
- scope changes
- architecture decisions that affect future work
- validation milestones
- major bug fixes

### `notes/lessonslearned.md`
Purpose:
- capture tactical lessons, mistakes, model capability findings, prompt lessons, and demo advice

Use it to record:
- what failed and why
- which model types handled which tasks well or badly
- API or framework pitfalls
- workflow changes the team should remember later in the day
- demo/operator lessons discovered during testing

---

## 4. Implementation scaffold layout

The repo now includes an **implementation scaffold only**. These folders are placeholders to organize upcoming work. Their existence does **not** mean those subsystems are implemented yet.

### `src/`
Primary application code goes here.

- `src/sim/` — deterministic simulation engine, state models, rules, scoring
- `src/bots/` — scripted bot players and controller-selection logic
- `src/api/` — HTTP endpoints, state serialization, and lifecycle handlers
- `src/replay/` — event logging, snapshots, replay loading/export helpers
- `src/agent_adapter/` — observation building, action parsing, timeout/fallback behavior for AI players

### `web/`
Observer UI assets go here.

- `web/css/` — stylesheets
- `web/js/` — browser scripts
- `web/assets/` — icons, map art, and static visual assets

### `tests/`
Validation and automated testing go here.

- `tests/sim/` — deterministic simulation tests
- `tests/api/` — endpoint and serialization tests
- `tests/integration/` — end-to-end tests across match, replay, and controller integration

### `scripts/`
Operator and validation helpers go here.

- `scripts/smoke/` — fast smoke checks
- `scripts/demo/` — demo helper scripts and operator conveniences

### `data/`
Non-code project data goes here.

- `data/scenarios/` — fixed scenario definitions and map/loadout data
- `data/replays/` — generated replay artifacts or known-good demo recordings

When starting implementation, respect the phase plan. Do not fill these folders opportunistically with unrelated code.

---

## 5. Reading order by task type

### If you are planning or scoping
Read:
1. `AGENTS.md`
2. `SPEC.md`
3. `docs/phases/phase-0-scope.md`
4. `CHANGELOG.md`
5. `notes/lessonslearned.md`

### If you are implementing simulation/backend logic
Read:
1. `AGENTS.md`
2. `SPEC.md`
3. current phase doc, usually `phase-1-simulation.md`, `phase-2-bots.md`, or `phase-3-api.md`
4. `CHANGELOG.md`
5. relevant code

### If you are implementing UI/observer features
Read:
1. `AGENTS.md`
2. `SPEC.md`
3. `phase-4-observer-ui.md`
4. `CHANGELOG.md`
5. `notes/lessonslearned.md`
6. relevant code

### If you are integrating LLM/agent players
Read:
1. `AGENTS.md`
2. `SPEC.md`
3. `phase-5-agent-adapter.md`
4. `CHANGELOG.md`
5. `notes/lessonslearned.md`
6. relevant backend code

---

## 6. Non-negotiable project priorities

1. **The simulation must be real**
   - a full match must run from start to finish
   - the backend must be the source of truth
   - outcomes must be deterministic for a given seed and action sequence

2. **The observer experience must be understandable**
   - humans must be able to tell who is winning, what is happening, and why
   - the UI must expose map state, score, and recent actions/events
   - click-to-inspect entities is a core feature, not optional polish

3. **The project must remain demoable even if LLM players are flaky**
   - scripted bots are required before live agent players
   - invalid/late agent outputs must degrade safely to no-op/hold
   - replay/event recording should exist early

4. **Risky stretch goals must stay to the right**
   - fancy graphics come after the vertical slice works
   - diplomacy, fog of war, mobile units, and elaborate 3D are stretch work

---

## 7. Product guardrails

### Build this first
- server-authoritative simulation
- small fixed map with named cities and silos
- missiles with visible travel and impacts
- observer API
- browser UI with map, score, log, and inspector
- scripted bots
- one LLM/agent integration after the above works

### Do not lead with these
- React/Vite/build tooling unless clearly necessary
- 3D globe or high-complexity rendering
- natural-language-only command parsing
- complicated unit movement/pathfinding
- diplomacy/alliance systems
- freeform world generation

---

## 8. Preferred technical defaults

### Backend
- Python is preferred for speed of implementation
- keep the simulation deterministic and testable
- favor plain modules and simple HTTP over elaborate frameworks
- polling is acceptable for the UI; WebSockets are optional polish

### Frontend
- plain HTML/CSS/JS is preferred
- SVG is the default rendering choice for the strategic map
- Canvas is acceptable for animated missile/explosion layers if helpful
- keep the UI local-first and hackathon-simple

### Data flow
- backend owns simulation state
- frontend consumes `/api/state` or equivalent current-state endpoint
- replay data should be generated by the backend, not inferred by the client

---

## 9. Phase discipline

Work phase-by-phase. Do not skip ahead because a later phase sounds more exciting.

### Required order
1. Phase 0 — scope lock and architecture alignment
2. Phase 1 — headless simulation
3. Phase 2 — scripted bots
4. Phase 3 — observer API and replay shape
5. Phase 4 — observer UI
6. Phase 5 — agent player adapter
7. Phase 6 — polish and demo prep

If a phase is incomplete, finish it or formally de-scope it before moving on.

### Human validation gates
Every phase doc contains explicit human validation gates.

Agents should stop and request human confirmation at those gates unless the human has already said to continue automatically.

When pausing for a gate, show the human:
- the current build status
- what now works
- what remains risky
- what validation actually ran
- what the proposed next step is

---

## 10. Working rules for coding agents

### Always do this
- read the relevant existing code and docs before editing
- make the smallest coherent change that advances the current phase
- validate immediately after any meaningful change
- keep notes about what was verified vs. what was assumed
- preserve the current architecture unless the human explicitly re-scopes it
- update project history docs when the work materially changes the state of the project

### Never do this casually
- introduce a build pipeline without approval
- replace a working simple system with a more clever system
- mix broad refactors into a phase-focused task
- claim “done” without naming what was actually validated
- silently change product scope without updating the docs

---

## 11. Change tracking requirements

### Update `CHANGELOG.md`
Update `CHANGELOG.md` whenever you make a meaningful change such as:
- completing a feature slice
- changing architecture or API shape
- changing the MVP/scope/cut line
- fixing a meaningful bug
- adding a validation milestone worth preserving

Recommended entry contents:
- date/time if useful
- short title
- summary of change
- files or subsystem touched
- validation performed
- any known limitation left behind

### Update `notes/lessonslearned.md`
Update `notes/lessonslearned.md` whenever you learn something the team should remember later, such as:
- a model repeatedly failing with a certain framework
- a prompt style that worked well or badly
- a bug pattern that wasted time
- a UI idea that observers found confusing
- a demo or operator lesson discovered during rehearsal

This file is for **practical team memory**, not polished release notes.

### When to update both
If a change both:
- advances the product, and
- taught the team something,

then update both files.

---

## 12. Git and commit expectations

This repo should be in git, and work should be committed frequently.

### Preferred cadence
Commit after each stable checkpoint such as:
- end of a phase slice
- after a human validation gate passes
- after a meaningful bug fix plus validation
- before a risky experiment

### Good commit behavior
- keep commits small and coherent
- prefer one logical change per commit
- include a message that says what changed and why
- do not bundle unrelated cleanup with core work

### If git has not been initialized yet
- recommend initializing it early
- until then, keep `CHANGELOG.md` and `notes/lessonslearned.md` especially up to date so project history is not lost

---

## 13. Time management rules

This is a hackathon. Optimize for a strong demo, not a perfect system.

### If behind schedule, cut scope in this order
1. fancy graphics
2. defense/interception complexity
3. multiple missile types
4. advanced replay controls
5. multi-agent commentary/personality
6. extra unit classes

### Do **not** cut
- deterministic simulation
- spectator map
- event log
- inspector
- scripted bots
- safe agent fallback behavior

---

## 14. Acceptance heuristics

A feature is worth keeping if it improves at least one of:
- observer clarity
- match stability
- demo reliability
- agent inspectability

A feature is suspect if it mostly adds complexity while helping none of the above.

---

## 15. Recommended task split

### Good tasks for smaller/weaker coding agents
- render scoreboard and event log
- render SVG map nodes and links
- add inspector panels
- write JSON serializers and simple bot policies
- add deterministic tests and smoke scripts
- implement static UI scaffolding
- update changelog/notes after focused work is complete

### Good tasks for stronger agents or humans
- simulation architecture
- replay/event model design
- agent adapter and validation/fallback logic
- cross-cutting state model changes
- performance-sensitive rendering or animation decisions
- scope/cut-line decisions under time pressure

---

## 16. Required reporting format for agents

When completing a task, report:
1. what changed
2. what files changed
3. how it was validated
4. what remains unverified
5. whether the project is still within the current phase scope
6. whether `CHANGELOG.md` and `notes/lessonslearned.md` were updated
7. whether the work is at a good commit point

---

## 17. Final demo principle

At any moment, the team should be able to stop and still have something real:
- first a sim,
- then a replayable sim,
- then an observable sim,
- then an agent-driven observable sim.

When in doubt, choose the simpler option that preserves this ladder.
