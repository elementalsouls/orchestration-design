# Graph Design — the runtime-free method

Everything here is independent of language and framework. A design produced by this file can be implemented in LangGraph, in LangGraph.js, in a workflow engine, or in eighty lines of `asyncio`. Pick the runtime *after* the design exists (Phase 3a), never before.

The output is five artifacts: **nodes, edges, state, bounds, cost.**

---

## 1. Nodes

A node is a unit of work with one job. The test for whether something deserves to be a node:

> Could a single loop hold this job alongside its neighbour?

If yes, it is a step, not a node — inline it. A node earns its existence through one of:

- **Different model** — a cheap classifier and an expensive reasoner are different nodes.
- **Different toolset** — a node with database write access should not be the node that talks to the public internet.
- **Read-only reviewer role** — the highest-value node in most designs.
- **Different failure semantics** — a step that may fail and must not take its neighbours down.
- **Different scaling shape** — one thing that runs once, another that runs 400 times.

**Merge test:** if two adjacent nodes use the same model, the same tools and the same prompt style, they are one node wearing two hats.

**Determinism test:** a node that does not call a model should be a plain function. Parsing, chunking, formatting, arithmetic, and validation-by-schema are not agent work. Many designs shrink by half on this test alone.

Write each node as one line: `name — job, in one sentence.`

## 2. Edges

Draw them before writing any code. Mermaid is fine; a napkin is fine.

Three edge shapes cover almost everything:

| Shape | Use |
|---|---|
| **Sequential** | `a → b` — b needs a's output. |
| **Fan-out / fan-in** | one branch per independent item, all rejoining at a barrier. |
| **Conditional** | a router function reads state and returns which node comes next. |

Rules:

- **Aim for one conditional edge.** Every branch point multiplies the paths you must test. Two conditionals with two outcomes each is four paths.
- **Every loop-back edge is a conditional edge**, and it must be bounded (see §4).
- **Every branch must be reachable.** A path that no test ever exercises is undemonstrated. If you document a "reject" edge, prove it fires.
- **Terminal choice matters.** When bounds are exhausted, decide deliberately: ship best-effort with a caveat, or route to a human/park node. Shipping unreviewed work is sometimes correct and sometimes a data-integrity bug. Choose on purpose.
- **If it does not fit on a napkin, simplify** — that is a real stopping rule, not a figure of speech.

## 3. State

The shared object that travels along the edges. This is where graphs rot.

For **every** field record four things:

| Field | Type | Owner (the one node that writes it) | Reducer |
|---|---|---|---|

**Reducer** means: how do two writes merge?

- **replace** — last write wins. Correct for single-owner scalars: `draft`, `verdict`, `plan`.
- **append** — writes accumulate. **Mandatory** for any field written by parallel branches. Without it, concurrent writes collide and results vanish silently.
- **counter** — a scalar the owner increments; used by bounds.
- **sum** — accumulates across every writer; how spend tracking works.

### The three state rules

1. **One writer per field.** A field written by two nodes needs a reducer or it is a state-drift bug waiting to happen. The symptom is outputs that change depending on execution order — a bug that reproduces intermittently and eats days.
2. **Never mutate in place.** Nodes *return updates*. In-place mutation defeats checkpointing, breaks replay, and makes parallel branches non-deterministic.
3. **Append-reduced fields cannot be cleared by replacing them.** This surprises people. If reviewers append to `reviews` every round, you cannot empty it between rounds. **Tag each entry with its round number and filter on read.** This is the correct fix; trying to reset the field is the common wrong one.

### Payload discipline in fan-out

A fanned-out branch receives a payload, not the whole state. Send only what that branch needs. Branches must never read sibling-branch state — they run concurrently, so anything a sibling wrote may or may not be there yet. That is a race, and it will pass in testing and fail in production.

Related: decide per node whether it is **resident** (accumulates history across iterations — right for a producer receiving feedback) or **ephemeral** (sees only the current artifact — right for a reviewer, who should arrive with fresh eyes and no sunk-cost attachment).

## 4. Bounds

A graph is many loops, sometimes running in parallel. A weak verifier now burns budget concurrently. Bound it **three independent ways**, so no single missed check produces a runaway:

1. **Attempt counter** — in state, incremented by the owner, checked by the router on every loop-back edge.
2. **Global step limit** — a hard cap on total node executions for the whole run. The backstop for a counter you forgot.
3. **Spend budget** — a `tokens_spent`-style field accumulated by every model-calling node, checked by at least one router, which routes to a terminal when exceeded.

Then decide the **exhaustion terminal** explicitly (see §2) and make sure the run tells you it happened. A result that silently shipped without passing review is worse than a loud failure.

## 5. Cost — as a comparison, never a bare number

Produce this in Phase 2, before anyone builds:

```
worst case ≈ items × attempts × nodes_per_item × tokens_per_call
```

**One number is nearly useless.** "This design costs 8k tokens" tells the reader
nothing — 8k compared to what? The decision it has to inform is *which level*, so
cost the level you chose **and the levels either side of it**:

| Option | Arithmetic | Worst case | Buys you |
|---|---|---|---|
| Level below | 1 × 2.5k | ~2.5k | — |
| **Chosen** | 2 rounds × (2.5k + 1.5k) | **~8k** | the reviewer catches the thing that hurts |
| Level above | 12 items × 2 × (400 + 300) | ~17k | *nothing here* — items fit in one context |

Read it two ways, and say the answer out loud:

- **Is the level below nearly as cheap?** Then you climbed too far, unless you can
  name what the extra spend buys.
- **Does the level above cost more and buy nothing?** Say so explicitly. That
  sentence is the single most useful line in a design review, and it is the one
  people skip.

Note the third row: fan-out often costs *more* than a loop with a reviewer,
because per-item overhead is paid N times. "More parallel" is not "cheaper".

If the chosen number is shocking, **the design is wrong** — reduce attempts,
route cheap work to a cheap model, or triage so only hard items take the
expensive path. Do not treat the budget as the thing that needs adjusting.

Two levers that usually help more than they look:

- **Triage node.** A cheap classifier routing items to a cheap path or an expensive path often cuts cost by most of it, because the majority of items are usually easy.
- **Fewer attempts.** Going from 3 to 2 attempts on a 400-item fan-out is a third of the worst-case bill.

---

## The five-layer check

Graph engineering sits on top of layers that must already work:

**prompt** (am I asking well?) → **context** (is the right information present?) → **harness** (tools, memory, retrieval) → **loop** (does it verify and stop?) → **graph** (who does what, in what order)

If a lower layer is broken, fixing it beats adding nodes. Orchestration does not repair a bad prompt or absent retrieval — it hides them behind more moving parts and makes the eventual debugging harder.

## Design smells

| Smell | What it usually means |
|---|---|
| More than ~7 nodes | Several are steps, not nodes. Run the merge test. |
| Node names that are verbs of one action (`chunk`, `parse`, `format`) | These are functions. Inline them. |
| Two conditional edges early in the design | The routing is doing work the state should do. |
| No node without a model call | The deterministic work is hiding inside prompts. |
| A field with no obvious owner | The design is not finished. |
| Reviewer and producer are the same model with a different prompt | Not an independent check. Rubber stamp. |
| Bounds "to be added later" | They will not be. They are load-bearing. |
