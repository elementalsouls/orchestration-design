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

### Every node has a kind — record it

"Function or node" is too coarse. Three kinds behave differently enough that the
distinction has to be in the design, not discovered in production:

| Kind | What it is | Cost | Needs its own bounds? |
|---|---|---|---|
| **fixed** | Deterministic code. No model | ~0 | No |
| **model** | Exactly one model call in, one result out | Predictable, one call | No |
| **agent** | An open-ended run: the node loops with tools until *it* decides it is done | **Unbounded by default** | **Yes — always** |

A node can be a full agent run, not just code or a single call. That is useful —
it is how levels nest — and it is where runaways hide.

**The trap:** an `agent` node inside a bounded loop is *not* bounded by the outer
loop. Your attempt counter caps how many times the outer loop calls it; it says
nothing about how many tool calls happen inside. One outer attempt can burn the
entire budget. A design that passes the bounds checklist can still run away.

**The rule:** every `agent` node declares its own iteration cap and spend budget,
and the design records them separately from the outer loop's. If you cannot state
what stops it, it is not a node yet.

Write each node as one line: `name (kind) — job, in one sentence.`

## 2. Edges

Draw them before writing any code. Mermaid is fine; a napkin is fine.

Three edge shapes cover almost everything:

| Shape | Use |
|---|---|
| **Sequential** | `a → b` — b needs a's output. |
| **Fan-out / fan-in** | one branch per independent item, all rejoining at a barrier. |
| **Conditional** | a router function reads state and returns which node comes next. |

### Which cycles does your design need?

Real systems are almost never acyclic. Most designs assume the only loop-back is
"reviewer rejected, revise" — there are five, and **each is bounded differently**.
Walk the list and name the ones you need:

| Cycle | Fires when | Bounded by |
|---|---|---|
| **Retry** | A tool call or fetch failed transiently | Attempt cap **plus backoff** — a tight retry loop is a self-inflicted outage |
| **Revise** | A reviewer rejected the work | Attempt counter, then a deliberate exhaustion terminal |
| **Gather** | The agent does not yet have enough context | An explicit *sufficiency test* — "enough" must be a condition, not a vibe, or this never terminates |
| **Ask the user** | Required information is missing | A timeout **and** a default for when no answer comes |
| **Human pause** | Work needs approval before continuing | Persistence — the run must survive the wait, which usually means level 6 |

The last two are the ones people forget to bound at all, because a human is
"obviously" going to answer. They frequently do not.

**This is a menu, not a checklist.** It lists what a loop-back can be *for*, so
you can name the one you need and bound it correctly. It is not an invitation to
implement five. Most designs need one cycle; some need two. If you find yourself
wanting three, that is a signal the design is doing too much, not that you have
been thorough.

Rules:

- **Aim for as few conditional edges as the work needs — one is ideal.** Every branch point multiplies the paths you must test. Two conditionals with two outcomes each is four paths.
- **Every loop-back edge is a conditional edge**, and it must be bounded (see §4).
- **Every branch must be reachable.** A path that no test ever exercises is undemonstrated. If you document a "reject" edge, prove it fires.
- **Terminal choice matters.** When bounds are exhausted, decide deliberately: ship best-effort with a caveat, or route to a human/park node. Shipping unreviewed work is sometimes correct and sometimes a data-integrity bug. Choose on purpose.
- **If it does not fit on a napkin, simplify** — that is a real stopping rule, not a figure of speech.

### Check the premise of every loop-back before you draw it

Name the state the re-entry point reads, then name the node **inside** the cycle that writes
it. If no writer sits inside, the loop is decorative — it runs, consumes its bounds, and
terminates having changed nothing.

```
loop-back edge:   verify ──► map
map reads:        surface
who writes surface inside the loop?   grep -n 'add_surface' engine/*.py
  -> only recon(), which is OUTSIDE the loop   ==> DECORATIVE. Delete the edge.
```

It fails in both directions, and the two look nothing alike from outside:

- **A cycle whose re-entry has no writer.** Looks iterative, runs as a straight line with
  extra rounds. Symptom: round 2 onward does no work, and every run hits the dry condition
  immediately.
- **A straight line whose work is genuinely iterative.** Discovery feeds discovery — a
  finding reveals new inputs, a source reveals new sources — and one pass stops at the first
  layer. Symptom: the output looks complete and is shallow, and a human doing the same task
  by hand keeps going after your design has declared itself finished.

The test is the same for both: *does any node in the loop write the state the loop re-reads?*
Answer it from the code or the process. Intuition gets this wrong in both directions, which
is why this is a grep and not a judgement call.

### How to draw it — the styling carries information

An unstyled diagram makes every node look equally cheap and equally safe. They are not.
Shape and colour here encode **what a node costs and what can go wrong with it**, so the
reader sees the expensive and unbounded parts *before* anyone builds them. That is the whole
job of Phase 2.5, and a diagram that hides it has failed at the gate.

| Node | Shape | Fill | Means |
|---|---|---|---|
| `([terminal])` | stadium | green | start, done |
| `[fixed]` | rectangle | grey | deterministic code — free, predictable |
| `(model)` | rounded | blue | exactly one model call — one bill, one latency |
| `[[agent]]` | subroutine | **amber, thick border** | loops with tools until *it* decides. **Unbounded by default** |
| `{router}` | diamond | grey | a branch — every one doubles the paths to test |
| `[/park/]` | parallelogram | red | the exhaustion terminal: bounds hit, work shipped unreviewed or held |

Amber is doing real work. It is the only fill that means *this node can run away inside a
design that looks bounded from outside* — the trap in §1. If a reader's eye goes straight to
the amber box and asks "what stops that?", the diagram has done its job.

Copy this block; change only the `class` lines:

```
classDef fixed fill:#e8eef2,stroke:#5b7183,color:#1d2b36
classDef model fill:#dbeafe,stroke:#2563eb,color:#12244a
classDef agent fill:#fef3c7,stroke:#b45309,stroke-width:2px,color:#3a2708
classDef term  fill:#dcfce7,stroke:#15803d,color:#0a2e15
classDef halt  fill:#fee2e2,stroke:#b91c1c,color:#3f0d0d
class load,digest fixed
class triage,review model
class S,E term
class park halt
```

Light fills with dark text, deliberately: it renders the same on a white README and a dark
editor, and nobody has to guess which theme the reader is on.

**Label every conditional edge with its bound**, not just its outcome — `FAIL · attempts < 3`,
not `FAIL`. The bound is the thing a reviewer is checking for, and putting it on the arrow
means they can check it without reading the tables.

### Node ids are the names in the code

One rule makes the diagram checkable instead of decorative:

> **Every node id in the diagram is a callable in the implementation, and every callable
> that owns state is a node in the diagram.**

`load` in the diagram is `def load(...)`. `triage` is `def triage(...)`. Not a comment, not
an inline `.invoke()` buried in a loop body — a named thing you can grep for.

This is what lets a reader believe the picture describes the program. It is also what makes
Phase 4 possible at every level: at levels 4–6 the framework emits the topology and you
assert edge-set equality; at levels 1–3 there is no emitted diagram, so this naming rule is
the only correspondence there is. Break it and the diagram becomes a drawing of something
that does not exist.

The worked example carries it: `examples/ticket-triage/` has four nodes in its diagram and
four functions of the same names. It did not always — `triage` and `review` were inline model
calls, and the diagram promised two nodes the code did not have.

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

**`counter` and `sum` are both ints and they are not the same reducer.** A counter is
owned by one node and *replaces* (`attempts + 1`); a sum is written by every model-calling
node and *accumulates*. In code they look identical until they don't: `+` implements two of
the four — **append for lists, sum for ints** — so a spend field left out of the append set,
or declared as a bare `int` in a TypedDict, is silently replaced with the cost of the last
call. It never climbs, and the budget router that reads it can never fire. Declare it.

That failure is invisible to every other test, because the attempt cap fires first at any
normal budget — see the bound-masking rule in §4.

### The three state rules

1. **One writer per field.** A field written by two nodes needs a reducer or it is a state-drift bug waiting to happen. The symptom is outputs that change depending on execution order — a bug that reproduces intermittently and eats days.
2. **Never mutate in place.** Nodes *return updates*. In-place mutation defeats checkpointing, breaks replay, and makes parallel branches non-deterministic.
3. **Append-reduced fields cannot be cleared by replacing them.** This surprises people. If reviewers append to `reviews` every round, you cannot empty it between rounds. **Tag each entry with its round number and filter on read.** This is the correct fix; trying to reset the field is the common wrong one.

### Payload discipline in fan-out

A fanned-out branch receives a payload, not the whole state. Send only what that branch needs. Branches must never read sibling-branch state — they run concurrently, so anything a sibling wrote may or may not be there yet. That is a race, and it will pass in testing and fail in production.

Related: decide per node whether it is **resident** (accumulates history across iterations — right for a producer receiving feedback) or **ephemeral** (sees only the current artifact — right for a reviewer, who should arrive with fresh eyes and no sunk-cost attachment).

## 4. Bounds

A graph is many loops, sometimes running in parallel. A weak verifier now burns budget concurrently. Bound it **four independent ways**, so no single missed check produces a runaway:

1. **Attempt counter** — in state, incremented by the owner, checked by the router on every loop-back edge.
2. **Global step limit** — a hard cap on total node executions for the whole run. The backstop for a counter you forgot.
3. **Spend budget** — a `tokens_spent`-style field accumulated by every model-calling node, checked by at least one router, which routes to a terminal when exceeded. **Where nothing costs tokens, bound whatever does cost**: HTTP requests, pages fetched, rows written, wall clock. A design with no models is not a design that cannot run away — it just runs away on someone else's rate limit instead of your bill.

4. **Per-agent-node bounds.** Any node of kind `agent` (see §1) carries its own iteration cap and spend budget. The outer three do **not** constrain what happens inside it — this is the most common way a design that passes this checklist still runs away.

**Bounds mask each other, so prove them one at a time.** Where two bounds guard the same
loop, the tighter one always fires first and the looser one is never exercised — a spend
budget that silently fails to accumulate (§3) passes every test in a suite whose attempt cap
stops the run first. Assert **each bound separately as the thing that stops the run**, with
the others slackened: force the reviewer to never pass *and* set the budget below one round,
then assert the run stopped on spend and that the attempt cap did **not** get there first.
A bound you have never seen fire is a bound you have not tested.

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

### Count tokens, then price them — they are not the same question

The arithmetic above yields a **token count**. The decision needs a **bill**, and on
any provider with prompt caching those two diverge by roughly an order of magnitude
in exactly the place this skill is most reluctant to approve.

Fan-out is the case. Two hundred branches sharing one system prompt, one instruction
block and one schema pay for that prefix **once at write, then at cache-read rates for
every branch after**. Cache reads are priced far below fresh input — an order of
magnitude on Anthropic's published pricing. So a raw token multiplier systematically
overstates what level 5 actually costs, and a cost table that ignores it will push a
design down the ladder for a reason that is not true.

Split the estimate rather than inflating one number:

```
cached_prefix   × 1              -> written once, at the cache-write rate
cached_prefix   × (branches - 1) -> read back, at the cache-read rate
unique_input    × branches       -> full input rate
output          × branches       -> full output rate, never cached
```

Three things worth holding on to:

- **Output tokens never cache.** A reviewer that writes a long verdict, or an agent
  node that reasons at length, costs full rate on every branch. Where the bill is
  dominated by output, caching changes nothing and the raw multiplier is honest.
- **This does not soften rule 2.** *Structure does not buy intelligence* rests on
  Tran & Kiela, who matched **thinking tokens** — output, uncacheable. Caching makes
  multi-agent **cheaper**, never **smarter**. A design that was wrong on accuracy
  grounds is still wrong at half the price.
- **Caching needs a stable prefix.** Per-branch preamble that varies (an item id, a
  timestamp, a shuffled context) invalidates the cache. If you are costing a fan-out
  on cache-read rates, say in the design that the prefix is fixed — otherwise the
  estimate is fiction.

If the chosen number is still shocking, **the design is wrong** — reduce attempts,
route cheap work to a cheap model, or triage so only hard items take the
expensive path. Do not treat the budget as the thing that needs adjusting.

Three levers that usually help more than they look:

- **Model tier per node.** This is the first lever, not the last. Node kinds already
  distinguish `fixed` / `model` / `agent`; assign a model per `model` node the same
  way. A cheap model on the mechanical nodes routinely saves more than a whole rung
  of ladder discipline, and it is a one-line change rather than a redesign.
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
| **Every** node calls a model | Deterministic work is hiding inside prompts. Note the direction: a design where **no** node calls a model is not a smell at all — that is level 1, and it is the most reliable thing you can ship. |
| A field with no obvious owner | The design is not finished. |
| Reviewer and producer are the same model with a different prompt | Not an independent check. Rubber stamp. |
| Bounds "to be added later" | They will not be. They are load-bearing. |
