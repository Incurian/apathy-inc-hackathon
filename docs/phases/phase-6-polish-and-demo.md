# Phase 6 — Polish, Demo Choreography, and Contingency Prep

## Objective

Turn the finished vertical slice into a strong, resilient hackathon demo.

This phase is where presentation improves, but only after the real product already works.

## Deliverables

- improved visual clarity and dramatic pacing
- stable demo controls
- chosen demo script and fallback path
- seeded or replay-based backup plan
- final bug triage and cut decisions

## Good polish candidates

- better faction colors and labels
- clearer missile trails and impact flashes
- threat highlighting for selected entities
- summary banner for major events
- match timer and leader display
- simple replay controls or post-match summary panel
- latest agent action display

## Dangerous polish traps

Avoid late-stage work on:
- 3D globe
- new entity classes
- diplomacy or negotiation systems
- major architectural rewrites
- replacing a working UI framework
- complex animation systems that could destabilize the demo

## Build sequence

### Step 6.1 — Demo-path hardening
Pick the primary live demo path:
- start match
- watch live launches and impacts
- inspect actors
- point out agent decisions
- show replay or match summary

Then define the fallback path:
- replay a known-good recorded match
- or run scripted bots with one agent faction disabled

### Step 6.2 — Bug triage
Classify open issues:
- demo blocker
- visible but tolerable
- post-demo cleanup

### Step 6.3 — Improve observer legibility
Polish only features that improve:
- readability
- inspectability
- confidence during live narration

### Step 6.4 — Record a known-good scenario
Capture at least one seed/replay that is safe to show if live agent play is unreliable.

### Step 6.5 — Prepare narration cues
Write a short live script:
- what the audience is looking at
- what each faction is
- what decisions matter
- how to interpret the inspector and event log

## Human validation gates

### Gate A — Demo rehearsal
**Stop and show a human:**
- the exact intended 2 to 5 minute demo flow
- who clicks what
- where the strongest visual moment is

**Human should verify:**
- the story is understandable to a cold audience
- the strongest moment happens early enough

### Gate B — Contingency rehearsal
**Stop and show a human:**
- what happens if the live agent stalls
- what happens if the UI is slow
- what replay or scripted fallback will be shown

**Human should verify:**
- there is no single-point-of-failure demo dependency

### Gate C — Final cut line
**Stop and show a human:**
- all remaining possible polish tasks
- time remaining
- recommendation on what not to touch

**Human should explicitly approve:**
- stopping feature work and shifting to stabilization

## Machine validation checklist

Before the demo, verify at least:
- known-good start/pause/resume/reset flow
- seeded or replay fallback works
- no fatal errors on page load during a full match
- a complete match still finishes after latest polish
- agent timeouts or invalid actions remain safe

## Exit criteria

Phase 6 is complete when:
- the team can confidently demo the product live
- a fallback demonstration path exists
- the app is stable enough to survive operator mistakes
- remaining issues are non-blocking

## Final recommendation

In the last stretch, choose confidence over novelty.
A simpler demo that runs smoothly is better than an ambitious one that might fail mid-presentation.
