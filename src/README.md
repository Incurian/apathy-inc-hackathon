# src/

Implementation code belongs here.

This folder is intentionally scaffold-only right now.
Do not treat the existence of these folders as implemented functionality.

## Intended layout
- `sim/` — deterministic simulation engine, models, rules, scoring
- `bots/` — scripted controllers and controller-selection logic
- `api/` — HTTP endpoints and serialization layer for spectator state and lifecycle controls
- `replay/` — event log, snapshots, and replay export/load helpers
- `agent_adapter/` — observation building, action parsing, timeout/fallback behavior for AI players
