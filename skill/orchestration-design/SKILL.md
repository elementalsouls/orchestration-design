---
name: orchestration-design
description: Decide how much orchestration a piece of work actually needs, design it, implement it on any runtime — or none — and verify what was built matches what was designed. Use for multi-step work of any kind, whether the output is software or a process. SOFTWARE: multi-agent system, agent workflow, pipeline, batch job, ETL, RAG ingestion, CI/CD, LangGraph, StateGraph, fan-out/fan-in, supervisor/worker, reviewer/verifier agents, splitting one script into several. PROCESS: an audit, review, migration, research project, compliance pass, manuscript — any long task run with a model across sessions where coverage matters. Also fires on symptoms stated without the vocabulary: "my pipeline is a mess", "one bad step kills the whole run", "it re-runs everything on failure", "it keeps looping forever", "costs exploded", "I keep losing track of where I am", "I don't know what I've already covered", "my report looked finished but wasn't", "how do I structure this so I stop missing things".
---

# Orchestration Design

Decide how much structure the work needs, design it on paper, show it to the human, build it on whatever runtime they use, and prove the build matches the design.

**"Loop or graph" is a false choice.** A loop is a graph with one node and one edge back to itself. The real questions are: *how many writers, and who decides the routing — the model or you?* The evidence answers both, and the answer is the same almost every time.

Two rules hold at every level, and both come from `references/evidence.md`:

1. **One writer. Always.** Extra nodes contribute judgement, never edits. Parallel writers making conflicting implicit decisions is the failure mode that killed agent-swarm designs industry-wide.
2. **Structure does not buy intelligence.** At matched token budgets a single agent matches or beats multi-agent designs. Climbing costs money and reliability. Most reported multi-agent wins track token spend, not architecture.

**Two tracks.** Building something new → phases 0 → 1 → 2 → 2.5 → 3 → 4 below. Something already exists and has rotted → read `references/auditing-an-existing-graph.md`, then rejoin at Phase 2.

## Phase 0 — Scope the work

Do not skip to the ladder. The level triggers are unanswerable without this, and a confident wrong decision here is the most expensive mistake this skill can make. Establish, in one round:

1. **The task** — what goes in, what comes out.
2. **Volume and cadence** — one item interactively, or 10,000 nightly? This alone decides fan-out.
3. **The failure that hurts** — wrong output reaching a user? A crashed batch? Blown budget? Failure modes are asymmetric; find out which way.
4. **Ceilings** — latency and cost limits that actually exist.
5. **Current pain** — for existing systems, what breaks today.

**State assumptions and keep going — do not burn a turn asking all five.** The user rarely knows they were questions. Write what you assumed, in a table, and label it correctable. The one exception: if a *single* unknown would change the level — "one domain or ten thousand nightly?" flips this between level 1 and level 6 — ask that one question and only that one. Phase 2.5 is the stop, not here.

**If the work touches data or systems you do not own** — third-party sites, personal data, anything under someone else's terms of service — bound that here, before design. Which sources are in scope, what authorisation exists, what is off-limits. A design that is elegant and not permitted is worthless.

Then run the **five-layer check**: prompt → context → harness → loop → orchestration. Each layer sits on the one below. If the real problem is a vague prompt, missing retrieval, or a tool the agent doesn't have, **say so and fix that layer instead**. Adding structure on top of a broken lower layer buries the bug.

## Phase 1 — Pick the level (the ladder)

**First: can you enumerate the valid paths?** If you can name the stages the work moves through — classify then answer, inspect then edit, draft then approve — the ladder applies. If you cannot, because the route depends on what the work turns up as it goes, **structure is the wrong tool**. Give one agent good tools, memory and a stopping condition, and let the path emerge. Forcing an open-ended task down fixed paths makes it worse, not safer — LangChain and GPT Researcher both migrated deep research *away* from fixed graphs for exactly this reason (`references/evidence.md` §6). Everything below assumes a knowable route.

**The ladder is six levels of orchestration, ordered simplest first.** A level describes the shape of the *solution*, never the difficulty of the *task*. **Pick a level per stage, not per system** — most real designs are mixed (a deterministic fetch, a level-3 judgement), and the system's headline level is the highest any stage needs. Start at level 1. **Stop at the first level that holds.** Climb only when that level's named trigger is *literally true*.

| Level | Shape | Climb past it only when |
|---|---|---|
| **1 · Plain script** | Deterministic code, no model | The work needs judgement a rule cannot encode |
| **2 · Loop** | One agent with tools, self-terminating | Output correctness cannot be asserted mechanically |
| **3 · Loop + reviewer** ← **default** | One writer, one read-only checker given clean context | — |
| **4 · Reviewer panel** | Several reviewers, different lenses, one synthesis | One reviewer provably misses a whole class of defect *and* the stakes justify the spend |
| **5 · Fan-out** | One branch per item, own context, isolated failures | **The work exceeds one context window** — independence alone is not enough |
| **6 · Durable workflow** | Persistent, resumable, scheduled | The run outlives a single process, or needs replay or a human pause |

**Level 3 is the default for serious work.** A read-only reviewer is the single highest-value addition — but note it *improves* a design without *justifying* a bigger one. Frameworks with explicit verifiers still failed often.

**What does NOT justify climbing:** task difficulty, step count, "feels complex", "could run in parallel", or wanting the design to look sophisticated. Parallelism buys wall-clock time and context isolation; at equal budget it does not buy accuracy. **Independence is a precondition for level 5, not a trigger** — nearly every batch has independent items, so treating that as sufficient sends everything to fan-out. Context pressure is the trigger; independence only decides whether fan-out is *safe*. Check what splitting costs too: any judgement needing to see items together — duplicates, ranking, dedupe — is destroyed once each branch sees one item.

Name the level and its trigger out loud: *"Level 3, because output quality can't be asserted mechanically"* is a decision, *"it's complex, so a graph"* is not. **Stopping at level 1 or 2 is a successful use of this skill** and the most common correct outcome.

## Phase 2 — Design on paper (runtime-free)

**This is the product.** The design object is identical whether you implement in Python, TypeScript, a workflow engine, or a Makefile.

Read `references/graph-design.md`. Produce exactly five parts:

1. **Nodes** — only real specialties, each with a **kind**: `fixed` (no model), `model` (one call), `agent` (loops with tools until done). An `agent` node **declares its own bounds**; the outer loop does not constrain it.
2. **Edges** — routing as a Mermaid diagram. As few conditional edges as the work needs.
3. **State schema** — type, reducer, and **which single node writes it**. Fan-in fields need append reducers. This is how rule 1 gets enforced.
4. **Bounds** — an attempt counter on every loop-back, a global step limit, and a spend budget a router reads. **Where nothing costs tokens, bound what does cost**: HTTP requests, pages fetched, wall clock. A level-1 design is still capable of running away.
5. **Cost, compared** — the level you chose **and the levels either side**. A single number informs nothing; the delta does. If the level below is nearly as cheap you climbed too far; if the level above buys nothing, say so out loud.

### Before you draw a loop-back, check its premise

**Name the state the re-entry point reads, then name the node inside the loop that writes it.** If no node in the cycle writes that field, the loop is decorative: it will run, consume its bounds, and terminate having changed nothing. Grep for the writer before you draw the edge — it costs one command and it is the cheapest design error to catch.

```
loop-back edge:   verify ──► map
map reads:        surface
who writes surface inside the loop?   grep -n 'add_surface' engine/*.py
  -> only recon(), which is OUTSIDE the loop   ==> DECORATIVE. Delete the edge.
```

This fails in both directions and both are common:

- **A cycle whose re-entry has no writer.** The design looks iterative and runs as a straight line with extra rounds. Symptom: round 2 onward does no work, every run reaches the dry condition immediately.
- **A straight line whose work is actually iterative.** Discovery feeds discovery — a finding reveals new inputs, a source reveals new sources — and a single pass silently stops at the first layer. Symptom: the output is complete-looking and shallow, and a human doing the same task by hand keeps going.

The test is the same for both: *does any node in the loop write the state the loop re-reads?* Answer it from the code or the process, not from intuition. Intuition gets this wrong in both directions.

**Landed on level 1 or 2? Take the exit ramp.** This is the most common outcome and it gets the **lightest** paperwork, not the heaviest. Produce the stages with their kinds (a list, not a table), one diagram, the bounds from part 4, one line of cost — *"zero model calls, zero tokens"* plus a sentence on what climbing would buy, no table — and the runtime recommendation. Nothing else.

**Skip the state table unless a field has more than one writer.** Its whole job is catching concurrent writes; if every field has one owner, write *"single writer throughout"* and move on. Where things do run concurrently — parallel fetches, gathered results — table **those fields only**, because that is exactly where results vanish silently.

## Phase 2.5 — Show the human the design

Do not go straight from design to code. Hand over, in one message:

1. an **ASCII sketch** of the flow — readable in the terminal with nothing installed. Skip it above ~8 nodes, where ASCII stops helping.
2. the **Mermaid block** — the source of truth, and the only thing Phase 4 asserts against.
3. a **mermaid.live link** if you can build one — the editor encodes its whole state as zlib-compressed JSON, base64url-encoded, in the URL fragment after `#pako:`. If that is awkward, tell them to paste the block into <https://mermaid.live> instead; the point is that editing costs them nothing. **Say that the diagram travels in the URL fragment, which browsers never send to the server — nothing is uploaded.** For a proprietary architecture that reassurance matters, and if they would still rather not, a local Mermaid preview does the same job.
4. the **stages/nodes**, **bounds**, and **cost** — at levels 1–2 in the exit-ramp form above, at levels 3+ the full node, state and cost tables
5. the **level chosen and its trigger**

Whatever they hand back is the source of truth — update the tables to match the edited diagram rather than arguing with it. The ASCII is a preview and may drift: **never assert against it**, and never let an image replace the Mermaid. Text is the only form a human can edit *and* Phase 4 can check.

**Ask one specific question, not "does this look good?"** Ask *"which node would you delete?"* or *"is any of this state written by two things?"*. Open approval questions get "looks fine"; specific ones get real answers, and people cut more than they add once they can see the shape.

### This is a hard stop

**End the turn on the design.** No implementation code, and no tool calls, after the design message. A gate you walk straight through is not a gate — "I'll show them the diagram and then build it" is the exact failure this phase prevents. Skip the stop **only** when the user said *in this request* to just build it; a general "go ahead" from earlier in the conversation does not carry.

**If you must proceed without a human** — autonomous run, scheduled job, no one to answer — say so explicitly and label the result **DESIGN NOT REVIEWED**. Do not silently treat unavailability as approval.

## Phase 3 — Choose a target, then implement

**3a. Choose the substrate.** First ask what the output actually *is*, because it decides everything below.

**Is the output a system, or a process?** A system is code that will run without you — a pipeline, a job, a service. A process is work that runs *with* you — a research project, an audit, a migration, a manuscript, a hiring round — where the nodes are prompts, subagents and human decisions, and there is no runtime to compile. Both are orchestration and the method is identical; only the substrate differs.

| Situation | Target file in `references/targets/` |
|---|---|
| **The output is a process, not a system** — no runtime to deploy | **`procedural.md`** |
| Few nodes, no LLM, or a team that won't adopt a dependency | **`plain-code.md`** ← try first, for systems |
| Python, LLM orchestration, wants a framework | `langgraph-python.md` |
| TypeScript / Node | `langgraph-js.md` |
| Orchestrating Claude Code subagents | `claude-code-subagents.md` |
| Long-running, needs durability/retries/schedules | `durable-workflow.md` |

Adopting a framework for a three-node pipeline is the same error as climbing a level you didn't need. `plain-code.md` is listed first among the runtimes because it is the honest answer more often than people expect — and `procedural.md` is listed above it because a great deal of multi-step work with a model is never going to be code at all.

**3b. Implement.** Read the chosen target file. Four rules hold on every runtime:

- **Single writer** — extra nodes contribute judgement, not actions. The state-ownership table enforces it.
- **Reviewer with teeth** — separate, read-only, ideally a different model, given **clean context rather than the producer's history**. It writes a verdict to its own field and never edits the work.
- **Failure isolation** — nodes return updates, never mutate. Risky nodes catch their own exceptions into `errors`. A checkpointer makes a retry resume instead of restart.
- **Hard bounds** — every conditional loop checks its counter; set the global step limit; route out when the budget is hit. If you chose a framework, use its routing and retries rather than reinventing them.

Deliver something runnable, plus a README carrying the approved design diagram — and, at levels 4–6, the one the code emits.

## Phase 4 — Verify by assertion, not by eye

Run it. Then prove it matches the design that was approved in Phase 2.5. **How you prove it depends on the level** — most designs stop at levels 1–3, which emit no diagram at all, so topology comparison does not apply there.

**Levels 4–6 — a framework compiled a graph.** Parse the approved Mermaid and the emitted `draw_mermaid()` output into edge sets and **assert they are equal**. Comparing two nine-edge diagrams by eye is exactly the check a tired builder skips, so make it a test: strip node shapes and edge labels, reduce both diagrams to sets of `(source, target)` pairs, and assert equality. Then write assertion 5 below — a matching topology says nothing about whether parallel branches lost results.

**Levels 1–3 — plain code, no diagram to emit.** There is no topology to compare, so assert the *behaviour* the design promised. Write these, and run them. **At levels 1–2 assertion 1 does not apply — there is no reviewer.** Skip it and say so; do not invent a reviewer to have something to assert.

1. **The reviewer is read-only** *(levels 3+ only)*. Snapshot the artifact, run the reviewer, assert it is unchanged. Proves it, rather than trusting the prompt.
2. **Every bound is live.** Force the condition each one guards — a reviewer that never passes, a source that always fails, a counter that never satisfies — and assert the run stops at the cap instead of looping forever. At level 1 this is your retry and timeout caps; they still need proving.
3. **The exhaustion terminal is reachable and marked.** Assert that run produces the caveat, park, or flag you designed — silently shipping unreviewed work is the bug.
4. **Failure is isolated.** Where the design claims one item can fail without killing the rest, force one to fail and assert the others still complete.
5. **The counts add up.** One output per input, no duplicate ids, successes + failures = total. Silent duplication and silent loss are what a wrong reducer or a missing fan-in reducer produce, and **no other assertion here notices** — the run looks fine and the data is wrong.

**At every level:** confirm each loop-back has a counter that is both read *and* incremented, and that every branch you documented actually fires in some run. A bounded reject path that never executes in any test is undemonstrated, not proven — add a second scenario that reaches it.

A mismatch means the implementation drifted from what the human approved. Fix it; don't hand-wave.

## Quick reference

| Symptom | Right move |
|---|---|
| One bad item aborts the whole batch | Per-branch error isolation — not more nodes |
| Re-runs everything from scratch after a failure | A checkpointer — not more nodes |
| Loops forever / costs exploded | Missing attempt cap, step limit, or spend field |
| Outputs change between identical runs | State drift — find the field with two writers |
| Duplicated results, or parallel results going missing | Wrong reducer — a replace field being appended, or a fan-in field that needs append. Assert the counts |
| "Everyone's using graphs, should we?" | `references/evidence.md` — most of that advantage was bought with tokens |

## References

- `references/evidence.md` — the research behind the two rules and the ladder. Cite it when someone pushes back.
- `references/graph-design.md` — the runtime-free design method. Read for Phase 2.
- `references/design-checklist.md` — the 8-point checklist with reasoning, for design reviews.
- `references/anti-patterns.md` — symptom → diagnosis → fix.
- `references/auditing-an-existing-graph.md` — Track B workflow.
- `references/targets/*.md` — one file per substrate. Read only the one chosen in Phase 3a. `procedural.md` covers the case where the output is a process rather than software — no runtime, ledger as state.
