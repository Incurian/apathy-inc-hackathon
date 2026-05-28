# CHANGELOG.md

This file is a running record of meaningful project changes.

Use it for:
- completed feature slices
- architecture/API changes
- scope or MVP changes
- important bug fixes
- validation milestones

## Entry template

```md
## YYYY-MM-DD HH:MM - Short title
- Summary:
- Files/subsystems:
- Validation:
- Remaining limitation/risk:
```

---

## 2026-05-28 08:50 - Planning doc set established
- Summary: Created the initial planning package for the DEFCON-inspired hackathon project, including the project overview, detailed specification, and phase-by-phase execution plans.
- Files/subsystems: `README.md`, `AGENTS.md`, `SPEC.md`, `docs/phases/phase-0-scope.md`, `docs/phases/phase-1-simulation.md`, `docs/phases/phase-2-bots.md`, `docs/phases/phase-3-api.md`, `docs/phases/phase-4-observer-ui.md`, `docs/phases/phase-5-agent-adapter.md`, `docs/phases/phase-6-polish-and-demo.md`
- Validation: Verified file creation and reviewed the generated doc set for structure; corrected an obvious typo in Phase 6.
- Remaining limitation/risk: This is still a planning package only; no implementation scaffold or code has been built yet.

## 2026-05-28 08:50 - AGENTS.md promoted to repo front door
- Summary: Reworked `AGENTS.md` so it now serves as the operational entry point for the repo, including document ownership, reading order, workflow rules, history-tracking expectations, and commit guidance.
- Files/subsystems: `AGENTS.md`, `CHANGELOG.md`, `notes/lessonslearned.md`
- Validation: Read the existing repo docs first, then rewrote instructions to reference the actual file layout and project workflow.
- Remaining limitation/risk: The repo still depends on team discipline to keep the changelog, lessons learned, and commits current.

## 2026-05-28 08:55 - Repo scaffold created without implementation
- Summary: Added a phase-aligned implementation scaffold for upcoming work without starting the actual simulation, API, UI, or agent integration.
- Files/subsystems: `.gitignore`, `src/`, `web/`, `tests/`, `scripts/`, `data/`, root and folder `README.md` placeholders, `AGENTS.md`, `README.md`
- Validation: Verified the new directories and placeholder files exist; updated the front-door docs so the scaffold is documented and clearly marked as non-implementation.
- Remaining limitation/risk: The scaffold helps organization only; all code-bearing subsystems are still empty and future work must respect the phase plan.

## 2026-05-28 08:57 - MCP-first agent integration clarified
- Summary: Updated the product spec and the Phase 5 adapter plan so agent-controlled factions are explicitly expected to connect through MCP-facing tooling or a thin MCP-compatible adapter rather than touching simulation internals directly.
- Files/subsystems: `SPEC.md`, `docs/phases/phase-5-agent-adapter.md`
- Validation: Reviewed the agent-interface section of the spec and the Phase 5 plan, then aligned both documents around the same MCP-first integration model.
- Remaining limitation/risk: This is still a planning-level decision; the actual MCP tool surface and adapter implementation remain future work.

## 2026-05-28 12:47 - Development parallelization proposal added
- Summary: Added a proposal for splitting work among three team members using agent swarms, including interface-first parallel development approach and alternative schemes.
- Files/subsystems: `docs/development-proposal.md`
- Validation: Reviewed the proposal for clarity and completeness; verified it addresses the team's parallelization question.
- Remaining limitation/risk: This is a planning document; actual implementation would require agreeing on interface contracts first.

## 2026-05-28 09:02 - Core MVP design decisions locked in docs
- Summary: Tightened the planning package by resolving the major open ambiguities before implementation: exact MVP constants, single-action turn schema, no-fog information model, explicit crippled vs eliminated semantics, concrete lifecycle semantics, concrete replay minimums, and a real MCP tool contract for agent players.
- Files/subsystems: `SPEC.md`, `docs/phases/phase-0-scope.md`, `docs/phases/phase-1-simulation.md`, `docs/phases/phase-3-api.md`, `docs/phases/phase-5-agent-adapter.md`, `AGENTS.md`
- Validation: Reviewed the spec and phase docs for contradictions, then re-scanned for stale ranged constants, action-list wording, soft MCP wording, and old elimination language.
- Remaining limitation/risk: The planning package is much tighter now, but actual scenario coordinates/content and exact implementation file boundaries still remain future work.
