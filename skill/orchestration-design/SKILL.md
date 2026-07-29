---
name: orchestration-design
description: Decide how much orchestration a piece of work actually needs, design it, implement it on any runtime, and verify what was built matches what was designed. Use whenever someone wants to build or fix a multi-agent system, agent workflow, pipeline, batch job, ETL, RAG ingestion, CI/CD flow, or any multi-step process; mentions graph engineering, orchestration, LangGraph, StateGraph, fan-out/fan-in, supervisor/worker, or reviewer/verifier agents; asks whether to split one loop or script into several parts; or describes the symptoms without the vocabulary — "my pipeline is a mess", "one bad step kills the whole run", "it re-runs everything on failure", "these steps should run in parallel", "this agent has grown too complex", "it keeps looping forever", "costs exploded".
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

Then run the **five-layer check**: prompt → context → harness → loop → orchestration. Each layer sits on the one below. If the real problem is a vague prompt, missing retrieval, or a tool the agent doesn't have, **say so and fix that layer instead**. Adding structure on top of a broken lower layer buries the bug.

## Phase 1 — Pick the level (the ladder)

**The ladder is six levels of orchestration, ordered simplest first.** A level describes the shape of the *solution*, never the difficulty of the *task*. Start at level 1. **Stop at the first level that holds.** Climb only when that level's named trigger is *literally true* — not because the task feels hard.

| Level | Shape | Climb past it only when |
|---|---|---|
| **1 · Plain script** | Deterministic code, no model | The work needs judgement a rule cannot encode |
| **2 · Loop** | One agent with tools, self-terminating | Output correctness cannot be asserted mechanically |
| **3 · Loop + reviewer** ← **default** | One writer, one read-only checker given clean context | — |
| **4 · Reviewer panel** | Several reviewers, different lenses, one synthesis | One reviewer provably misses a whole class of defect *and* the stakes justify the spend |
| **5 · Fan-out** | One branch per item, own context, isolated failures | **The work exceeds one context window** — independence alone is not enough |
| **6 · Durable workflow** | Persistent, resumable, scheduled | The run outlives a single process, or needs replay or a human pause |

**Level 3 is the default for serious work.** A read-only reviewer is the single highest-value addition — but note it *improves* a design without *justifying* a bigger one. Frameworks with explicit verifiers still failed often.

**What does NOT justify climbing:** task difficulty, number of steps, "feels complex", "could run in parallel", or wanting the design to look sophisticated. Parallelism buys wall-clock time and context isolation; at equal budget it does not buy accuracy.

**Independence is a precondition for level 5, not a trigger.** Nearly every batch has independent items, so treating independence as sufficient sends everything to fan-out — the opposite of what the evidence supports. Context pressure is the trigger; independence only decides whether fan-out is *safe*. And check what splitting costs you: if any judgement needs to see items together — spotting duplicates, ranking, deduping — fan-out destroys it, because each branch sees one item.

Name the level and its trigger out loud. *"Level 3, because output quality can't be asserted mechanically"* is a decision. *"It's complex, so a graph"* is not.

**Stopping at level 1 or 2 is a successful use of this skill** and the most common correct outcome. `reference-implementation/01-loop-not-graph/` is the worked version.

## Phase 2 — Design on paper (runtime-free)

**This is the product.** The design object is identical whether you implement in Python, TypeScript, a workflow engine, or a Makefile.

Read `references/graph-design.md`. Produce exactly five parts:

1. **Nodes** — only real specialties. Each needs a job a single loop couldn't hold: a different model, a different toolset, or a read-only reviewer role. Steps you could inline are not nodes.
2. **Edges** — routing as a Mermaid diagram: what's sequential, what fans out, what fans in, where the loop-back lives. Aim for one conditional edge.
3. **State schema** — every field: type, reducer (replace vs. append), and **which single node may write it**. Fan-in fields must have append reducers. This table is how rule 1 gets enforced.
4. **Bounds** — an attempt counter on every loop-back, a global step limit, and a spend budget a router actually reads.
5. **Cost, compared** — worst case for the level you chose **and the levels either side of it**. A single number does not inform the decision; the delta does. If the level below is nearly as cheap, you climbed too far. If the level above costs more and buys nothing, say so out loud. Method in `references/graph-design.md`.

## Phase 2.5 — Show the human the design

Do not go straight from design to code. Hand over, in one message:

1. an **ASCII sketch** of the flow — readable in the terminal with nothing installed. Skip it above ~8 nodes, where ASCII stops helping.
2. the **Mermaid block** — the source of truth, and the only thing Phase 4 asserts against.
3. a **pre-filled mermaid.live link**, so editing needs no copy-paste. `tools/mermaid_link.py` in this repo generates one from a diagram.
4. the **node table**, **state table**, **bounds**, and the **cost comparison** across adjacent levels
5. the **level chosen and its trigger**

Whatever they hand back is the source of truth — update the tables to match the edited diagram rather than arguing with it. The ASCII is a preview and may drift: **never assert against it**, and never let an image replace the Mermaid. Text is the only form a human can edit *and* Phase 4 can check.

**Ask one specific question, not "does this look good?"** Ask *"which node would you delete?"* or *"is any of this state written by two things?"*. Open approval questions get "looks fine"; specific ones get real answers, and people cut more than they add once they can see the shape.

### This is a hard stop

**End the turn on the design.** Do not write implementation code in the same turn you present it — no tool calls after the design message. A gate you walk straight through is not a gate, and "I'll show them the diagram and then build it" is the failure mode this phase exists to prevent.

Skip the stop **only** when the user said *in this request* to just build it. A general "go ahead" from earlier in the conversation does not carry.

**If you must proceed without a human** — autonomous run, scheduled job, no one to answer — say so explicitly and label the result **DESIGN NOT REVIEWED**. Do not silently treat unavailability as approval.

## Phase 3 — Choose a target, then implement

**3a. Choose the runtime.** Ask what they actually use; do not default to a framework.

| Situation | Target file in `references/targets/` |
|---|---|
| Python, LLM orchestration, wants a framework | `langgraph-python.md` |
| TypeScript / Node | `langgraph-js.md` |
| Few nodes, no LLM, or a team that won't adopt a dependency | `plain-code.md` |
| Orchestrating Claude Code subagents | `claude-code-subagents.md` |
| Long-running, needs durability/retries/schedules | `durable-workflow.md` |

Adopting a framework for a three-node pipeline is the same error as climbing a level you didn't need. `plain-code.md` is the honest answer more often than people expect.

**3b. Implement.** Read the chosen target file. Rules that hold on every runtime:

- **Single writer** — writes stay single-threaded; extra nodes contribute judgement, not actions. The state-ownership table is how you enforce it.
- **Reviewer with teeth** — separate, read-only, ideally a different model, given **clean context rather than the producer's history**. Reviewers with fresh context measurably outperform ones carrying the producer's trace. It writes a verdict to its own field and never edits the work.
- **Failure isolation** — nodes return updates, never mutate shared state. Risky nodes catch their own exceptions into an `errors` field. Use a checkpointer so a retry resumes instead of restarting.
- **Hard bounds** — every conditional loop checks its counter; set the global step limit; track spend in state and route out when the budget is hit.
- **Don't hand-roll the runtime** if you chose a framework.

Deliver something runnable, plus a README carrying the approved design diagram — and, at levels 4–6, the one the code emits.

## Phase 4 — Verify by assertion, not by eye

Run it. Then prove it matches the design that was approved in Phase 2.5. **How you prove it depends on the level** — most designs stop at levels 1–3, which emit no diagram at all, so topology comparison does not apply there.

**Levels 4–6 — a framework compiled a graph.** Parse the approved Mermaid and the emitted `draw_mermaid()` output into edge sets and **assert they are equal**. Comparing two nine-edge diagrams by eye is exactly the check a tired builder skips. This repo ships a working version as `reference-implementation/verify_topology.py`. Then write assertion 5 below — a matching topology says nothing about whether parallel branches lost results.

**Levels 1–3 — plain code, no diagram to emit.** There is no topology to compare, so assert the *behaviour* the design promised. Write these five, and run them:

1. **The reviewer is read-only.** Snapshot the artifact, run the reviewer, assert it is unchanged. Proves it, rather than trusting the prompt.
2. **The bound is live.** Substitute a reviewer that never passes; assert the run stops at `MAX_ATTEMPTS` instead of looping forever.
3. **The exhaustion terminal is reachable and marked.** Assert that run produces the caveat, park, or flag you designed — silently shipping unreviewed work is the bug.
4. **Failure is isolated.** Where the design claims one item can fail without killing the rest, force one to fail and assert the others still complete.
5. **The counts add up.** One output per input, no duplicate ids, successes + failures = total. Silent duplication and silent loss are what a wrong reducer or a missing fan-in reducer produce, and **no other assertion here notices** — the run looks fine and the data is wrong.

**At every level:** confirm each loop-back has a counter that is both read *and* incremented, and that every branch you documented actually fires in some run. A bounded reject path that never executes in any test is undemonstrated, not proven — add a second scenario that reaches it.

A mismatch means the implementation drifted from what the human approved. Fix it; don't hand-wave.

## Quick reference

| Symptom | Right move |
|---|---|
| Choosing how much structure | The ladder above. Start at level 1; climb only on a named trigger |
| One bad item aborts the whole batch | Per-branch error isolation — not more nodes |
| Re-runs everything from scratch after a failure | A checkpointer — not more nodes |
| Loops forever / costs exploded | Missing attempt cap, step limit, or spend field |
| Outputs change between identical runs | State drift — find the field with two writers |
| Same item appears twice, at two different values | Wrong reducer — a replace field is being appended |
| Results from parallel branches go missing | Fan-in field needs an append reducer; assert the counts |
| "Everyone's using graphs, should we?" | `references/evidence.md` — most of that advantage was bought with tokens |

## References

- `references/evidence.md` — the research behind the two rules and the ladder. Cite it when someone pushes back.
- `references/graph-design.md` — the runtime-free design method. Read for Phase 2.
- `references/design-checklist.md` — the 8-point checklist with reasoning, for design reviews.
- `references/anti-patterns.md` — symptom → diagnosis → fix.
- `references/auditing-an-existing-graph.md` — Track B workflow.
- `references/targets/*.md` — one file per runtime. Read only the one chosen in Phase 3a.
