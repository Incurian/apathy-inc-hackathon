# Phase 4 — Observer UI Vertical Slice

## Objective

Build the browser-based spectator experience that makes the simulation readable and demo-worthy.

This phase should produce a complete vertical slice even before LLM players are integrated.

## Deliverables

- one observer page or tightly scoped UI shell
- live strategic map
- scoreboard/faction summary
- recent event log
- click-to-inspect entities
- start/pause/resume/reset controls
- visual missile travel and impact feedback

## Preferred implementation approach

- plain HTML/CSS/JS
- SVG for map nodes, links, and trajectories
- optional Canvas overlay for missiles/explosions if needed
- polling current state from the backend

Avoid build tooling unless already justified.

## Suggested layout

### Center/left
- strategic map with cities, silos, missile paths, and impact effects

### Right sidebar
- faction scoreboard
- selected entity inspector
- recent actions/events

### Top or bottom controls
- start
- pause
- resume
- reset
- optional speed display/control

## Build sequence

### Step 4.1 — Static shell and layout
Build the page structure with panels and placeholders first.

### Step 4.2 — Live state polling
Connect to `/api/state` and render:
- match status
- faction summaries
- recent events

### Step 4.3 — Render map nodes
Render all cities and silos with:
- owner color
- labels or hover/inspect affordance
- status indicators for destroyed/disabled assets

### Step 4.4 — Render missiles and impacts
Show missiles in flight clearly enough for observers to track them.

Preferred simple options:
- moving dots
- line/arcs with animated progress
- short-lived flash or ring on impact

### Step 4.5 — Add inspector interaction
Clicking a faction/node/missile should populate a detail panel.

### Step 4.6 — Add operator controls
Wire start/pause/resume/reset to backend endpoints.

### Step 4.7 — Replay review affordance
If full replay controls are not ready, at minimum expose:
- latest match summary
- final event history
- or a post-match review panel

## Human validation gates

### Gate A — First readable live map
**Stop and show a human:**
- the map with live nodes and score updates
- no fancy animation required yet

**Human should verify:**
- they can tell who owns what
- they can tell whether the match is active
- they can understand the basic layout without explanation

### Gate B — First missile flight and impact
**Stop and show a human:**
- at least one visible launch and impact cycle
- the corresponding event log line and score change

**Human should verify:**
- the action is visually legible
- the event log matches what they saw
- the UI is exciting enough for a demo even before polish

### Gate C — Inspector usefulness
**Stop and show a human:**
- clicking a faction, city, silo, and if possible a missile
- the details panel contents

**Human should verify:**
- the inspector answers useful questions rather than just restating IDs
- observers can investigate what is happening in the match

### Gate D — Operator flow
**Stop and show a human:**
- start, pause, resume, reset flow
- what the UI does when a match ends

**Human should verify:**
- the app can be operated reliably in front of an audience

## Machine validation checklist

Validate at least:
- page loads without fatal console errors
- polling updates data over time
- controls trigger the correct backend endpoints
- clicking selectable entities always updates the inspector safely
- destroyed assets render distinctly from active ones

## Exit criteria

Phase 4 is complete when:
- a human can watch a full match in the browser
- launches and impacts are visible
- faction score/event state is understandable
- at least core entity types are inspectable
- the product is demoable even with scripted bots only

## If behind schedule

Prioritize in this order:
1. readable map nodes
2. visible missiles and impacts
3. scoreboard
4. event log
5. inspector
6. cosmetics

Cut visual sophistication before cutting inspectability.
