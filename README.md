# Agent DEFCON Hackathon

A planning-and-execution package for a hackathon project: a **DEFCON-inspired autonomous war simulation** where AI agents act as rival factions and human observers watch, inspect, and replay the match in a local browser UI.

## Core idea

- Multiple AI-controlled factions compete in a stylized nuclear standoff
- A server-authoritative simulation resolves launches, travel, impacts, score, and elimination
- Human observers watch the battle unfold in a browser-based spectator interface
- The observer can inspect factions, cities, silos, missiles, and recent decisions/events
- Replay support is built in early so the project remains demoable even if live agent behavior is unreliable

## Why this structure

The project is intentionally organized so that **the simulation and observer experience are the product**, and the LLM-player layer is an extension on top of it.

That means if the team runs out of time, you can still demo:

- a functioning strategic simulation
- a live or replayable observer UI
- scripted or partially agent-driven players

## Document map

- `AGENTS.md` — the front door for the repo: workflow, priorities, reading order, and operating rules
- `SPEC.md` — detailed game, product, API, and UX specification
- `docs/phases/phase-0-scope.md` — scope lock and architecture alignment
- `docs/phases/phase-1-simulation.md` — deterministic headless simulation
- `docs/phases/phase-2-bots.md` — scripted bot players
- `docs/phases/phase-3-api.md` — observer API and replay surface
- `docs/phases/phase-4-observer-ui.md` — browser spectator UI
- `docs/phases/phase-5-agent-adapter.md` — LLM/agent player integration
- `docs/phases/phase-6-polish-and-demo.md` — final polish, demo choreography, and contingency prep
- `docs/development-proposal.md` — recommended three-person execution split: human-owned decisions/validation with agent-heavy implementation lanes
- `CHANGELOG.md` — running record of meaningful project changes
- `notes/lessonslearned.md` — tactical team memory: pitfalls, model lessons, and demo observations
- `src/`, `web/`, `tests/`, `scripts/`, `data/` — implementation scaffold only; these are placeholders for upcoming work

## Implementation scaffold

The repo now includes a non-code scaffold for the future implementation:

- `src/` — backend/simulation/controller/replay/adapter code
- `web/` — observer UI assets
- `tests/` — validation and automated test locations
- `scripts/` — smoke and demo helper scripts
- `data/` — scenarios and replay artifacts

These folders are intentionally placeholders only. No implementation has been started in them yet.

## Delivery philosophy

1. Finish a vertical slice early
2. Validate with humans constantly
3. Push risky graphics and complex agent behavior to the right
4. Prefer a simple, legible 2D map over ambitious 3D
5. Record replay/logging data from early phases onward

## Definition of real product

The project counts as a real product once all of the following are true:

- a match can run from start to finish without human intervention
- a human can watch the match in a browser
- a human can inspect actors and recent events
- the winner and match outcome are understandable
- a completed match can be replayed or reviewed through recorded events/state

Everything beyond that is polish or stretch.
