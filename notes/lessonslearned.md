# lessonslearned.md

This file captures practical lessons, mistakes, prompt insights, model capability observations, and demo/operator notes.

Use it for:
- things that wasted time
- frameworks/models that proved unreliable
- prompt structures that worked or failed
- validation gaps that let bad work slip through
- demo observations from humans watching the product

This is not polished release documentation. It is tactical team memory.

## Entry template

```md
## YYYY-MM-DD HH:MM - Short lesson
- Context:
- Observation:
- Why it mattered:
- Adjustment going forward:
```

---

## 2026-05-28 14:30 - FastAPI TestClient enables reliable API testing without live server
- Context: Running uvicorn in background in CI/automated environments was unreliable - server would start then immediately shut down due to stdin/EOF issues in non-interactive shells.
- Observation: FastAPI's TestClient (using httpx) allows full API testing including lifecycle transitions, schema validation, and error cases without needing a live server process.
- Why it mattered: Enables reliable smoke tests in any environment, critical for CI/CD and validation gates.
- Adjustment going forward: Use TestClient for all API validation; only run live server for manual UI testing.

## 2026-05-28 12:55 - Three-human parallelism works best when humans own the checkpoints
- Context: The repo needed a concrete proposal for how three teammates should work in parallel when agents are doing most of the implementation.
- Observation: The highest-value split is not three arbitrary coding buckets. It is one human protecting the deterministic sim, one protecting the observer product, and one protecting the agent boundary and integration quality, while all contract changes and validation gates stay human-owned.
- Why it mattered: Without that division, one lane becomes overloaded, schema drift shows up late, and teams over-delegate product decisions to agents.
- Adjustment going forward: Use contract-first parallelization, freeze example payloads early, assign clear lane ownership, and treat humans as the decision/test/integration layer rather than just extra prompt operators.

## 2026-05-28 08:50 - Smaller models struggled badly with graphics-library front ends
- Context: A separate bakeoff repo was used to test a weaker model on five browser demos using Vanilla SVG, p5.js, PixiJS, three.js, and A-Frame.
- Observation: The only version that even reliably rendered a visible picture was the plain JS/SVG-style implementation. The library-driven demos failed substantially due to bad API usage, invented features, weak validation, and not truly reading the backend contract.
- Why it mattered: This strongly suggests the hackathon project should not depend on weaker models inventing complex graphics integrations from scratch.
- Adjustment going forward: Prefer plain HTML/CSS/JS and SVG for the main observer UI, keep 3D and non-native graphics as stretch goals, and give weaker models narrow, scaffolded tasks only.

## 2026-05-28 08:50 - The product should be the sim plus observer, not the LLM layer alone
- Context: Planning for the hackathon emphasized demo resilience under time pressure and model unreliability.
- Observation: If the simulation, spectator UI, and replay exist, the project is still real and demoable even when live agent play is flaky.
- Why it mattered: This changes architecture and schedule priorities. Scripted bots and replay become core requirements rather than backups.
- Adjustment going forward: Build in this order: deterministic sim -> scripted bots -> observer API -> observer UI -> agent adapter -> polish.

## 2026-05-28 08:55 - Scaffolding without code is worth doing explicitly
- Context: The goal was to prepare the repo for a hackathon build without accidentally “cheating” by pre-implementing core systems.
- Observation: A clear folder layout plus front-door documentation meaningfully lowers startup friction while still keeping the actual implementation work fair game for the hackathon.
- Why it mattered: Without this, later agents or humans are more likely to waste time debating folder structure, mixing phases, or starting code in the wrong place.
- Adjustment going forward: It is worth doing early repo structure, phase-aligned placeholders, and workflow docs before implementation starts, as long as those placeholders are explicitly marked as non-code scaffolding.

## 2026-05-28 08:57 - Keep agent integration behind MCP-shaped boundaries
- Context: The project needs AI-controlled factions, but direct engine coupling would make the simulation harder to validate and easier to destabilize.
- Observation: Framing the agent-player interface as MCP-first forces a cleaner separation between the authoritative backend and agent controllers.
- Why it mattered: This improves safety, inspectability, and swapability, and it matches the larger agent-tooling theme of the hackathon.
- Adjustment going forward: Treat agent players as clients of a small MCP-facing tool surface or thin MCP-compatible adapter, never as code that reaches directly into engine state.

## 2026-05-28 09:02 - Planning docs need exact constants before small teams start coding
- Context: A review of the planning package found that most of the architecture was solid, but several key rules still existed as ranges or soft suggestions.
- Observation: The biggest implementation risks were not high-level concept problems; they were unresolved details like single-action vs multi-action turns, elimination semantics, lifecycle states, and whether agent integration was truly MCP-backed.
- Why it mattered: Small teams and smaller models lose time fast when they have to invent missing rules mid-implementation.
- Adjustment going forward: Before coding starts, freeze exact MVP constants, exact API/lifecycle semantics, exact replay minimums, and an exact agent-tool contract. Treat soft ranges as planning debt.
