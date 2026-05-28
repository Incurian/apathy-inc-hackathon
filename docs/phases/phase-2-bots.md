# Phase 2 — Scripted Bot Players

## Objective

Prove the game is playable and interesting before introducing live LLM agents.

Scripted bots are not a fallback afterthought. They are the first reliable players.

## Deliverables

- bot interface / policy hook
- at least 3 simple bot policies
- autonomous full-match play with no human decisions
- bot-vs-bot simulation runs
- logged action history per faction

## Minimum required bots

### 1. Random bot
- picks any legal target at random
- holds if no legal launch exists

### 2. City-priority bot
- prefers enemy cities
- may choose highest population/value first

### 3. Silo-priority bot
- prefers enemy launch capacity
- targets enemy silos first

Optional fourth bot if easy:
- retaliation bot that targets the most recent aggressor

## Build sequence

### Step 2.1 — Define player adapter interface
The simulation should ask a controller for an action using a clean function or protocol, e.g.:
- input: current observation or state slice
- output: one action or hold

### Step 2.2 — Implement pure bot policies
Keep policies simple and deterministic where useful.

Bots should avoid side effects so they are easy to test.

### Step 2.3 — Add match driver with controller assignment
Allow a match to assign each faction a control mode:
- scripted random
- scripted city-priority
- scripted silo-priority
- later: agent-backed

### Step 2.4 — Log chosen actions
For each decision window, record:
- faction id
- chosen action
- timestamp/tick
- controller type
- optional rationale string for scripted bots

### Step 2.5 — Run repeated match samples
Run multiple seeded matches to ensure:
- matches finish
- bots don’t crash
- outcomes vary enough to be interesting

## Human validation gates

### Gate A — First autonomous match
**Stop and show a human:**
- one full bot-vs-bot match summary
- winner
- launch counts
- event highlights

**Human should verify:**
- the game remains watchable even without LLMs
- the bot behavior is simple but not completely lifeless

### Gate B — Strategy differentiation
**Stop and show a human:**
- side-by-side summaries of at least two bot policy matchups
- examples showing city-priority vs silo-priority differences

**Human should verify:**
- factions feel meaningfully distinct enough for a demo narrative

### Gate C — Controller abstraction sanity check
**Stop and show a human:**
- the interface the future LLM adapter will use
- how bot and agent controllers share that interface

**Human should verify:**
- agent integration can be added without rewriting the sim

## Machine validation checklist

Validate at least the following:
- every controller returns a valid action or a safe no-op
- no bot can crash the engine by returning malformed state
- repeated seeded bot matches are deterministic where expected
- the action log contains enough info for later UI display

## Exit criteria

Phase 2 is complete when:
- the game can run from start to finish with only scripted bots
- at least three policies exist
- their action histories are logged
- the simulation is already demoable without LLMs

## If behind schedule

Reduce bot sophistication, not bot existence.

It is better to have:
- 2 very simple stable bots
than:
- 5 partially implemented smart bots
