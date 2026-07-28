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

## Two tracks

| Situation | Track |
|---|---|
| Building something new | **Track A** — phases 0 → 1 → 2 → 2.5 → 3 → 4 below |
| Something exists and has rotted | **Track B** — read `references/auditing-an-existing-graph.md`, then rejoin at Phase 2 |

## Phase 0 — Scope the work

Do not skip to the ladder. The rung triggers are unanswerable without this, and a confident wrong decision here is the most expensive mistake this skill can make. Establish, in one round:

1. **The task** — what goes in, what comes out.
2. **Volume and cadence** — one item interactively, or 10,000 nightly? This alone decides fan-out.
3. **The failure that hurts** — wrong output reaching a user? A crashed batch? Blown budget? Failure modes are asymmetric; find out which way.
4. **Ceilings** — latency and cost limits that actually exist.
5. **Current pain** — for existing systems, what breaks today.

Then run the **five-layer check**: prompt → context → harness → loop → orchestration. Each layer sits on the one below. If the real problem is a vague prompt, missing retrieval, or a tool the agent doesn't have, **say so and fix that layer instead**. Adding structure on top of a broken lower layer buries the bug.

## Phase 1 — Pick the rung (the ladder)

Start at rung 1. **Stop at the first rung that holds.** Climb only when that rung's named trigger is *literally true* — not because the task feels hard.

| Rung | Shape | Climb past it only when |
|---|---|---|
| **1 · Plain script** | Deterministic code, no model | The work needs judgement a rule cannot encode |
| **2 · Loop** | One agent with tools, self-terminating | Output correctness cannot be asserted mechanically |
| **3 · Loop + reviewer** ← **default** | One writer, one read-only checker given clean context | — |
| **4 · Reviewer panel** | Several reviewers, different lenses, one synthesis | One reviewer provably misses a whole class of defect *and* the stakes justify the spend |
| **5 · Fan-out** | One branch per item, own context, isolated failures | **The work exceeds one context window**, or items are genuinely independent |
| **6 · Durable workflow** | Persistent, resumable, scheduled | The run outlives a single process, or needs replay or a human pause |

**Rung 3 is the default for serious work.** A read-only reviewer is the single highest-value addition — but note it *improves* a design without *justifying* a bigger one. Frameworks with explicit verifiers still failed often.

**What does NOT justify climbing:** task difficulty, number of steps, "feels complex", "could run in parallel", or wanting the design to look sophisticated. Parallelism buys wall-clock time and context isolation; at equal budget it does not buy accuracy.

Name the rung and its trigger out loud. *"Rung 3, because output quality can't be asserted mechanically"* is a decision. *"It's complex, so a graph"* is not.

**Stopping at rung 1 or 2 is a successful use of this skill** and the most common correct outcome. `reference-implementation/01-loop-not-graph/` is the worked version.

## Phase 2 — Design on paper (runtime-free)

**This is the product.** The design object is identical whether you implement in Python, TypeScript, a workflow engine, or a Makefile.

Read `references/graph-design.md`. Produce exactly five parts:

1. **Nodes** — only real specialties. Each needs a job a single loop couldn't hold: a different model, a different toolset, or a read-only reviewer role. Steps you could inline are not nodes.
2. **Edges** — routing as a Mermaid diagram: what's sequential, what fans out, what fans in, where the loop-back lives. Aim for one conditional edge.
3. **State schema** — every field: type, reducer (replace vs. append), and **which single node may write it**. Fan-in fields must have append reducers. This table is how rule 1 gets enforced.
4. **Bounds** — an attempt counter on every loop-back, a global step limit, and a spend budget a router actually reads.
5. **Cost estimate** — worst-case calls × attempts × branches × tokens. A number, before anyone builds. If it's shocking, the design is wrong, not the budget.

## Phase 2.5 — Show the human the design

Do not go straight from design to code. Hand over, in one message:

- the **Mermaid block**
- the **node table**, **state table**, **bounds** and **cost estimate**
- the **rung chosen and its trigger**

Then tell them: *paste the Mermaid into <https://mermaid.live> to move nodes, delete them, or re-route the edges.* Whatever they hand back is the source of truth — update the tables to match the edited diagram rather than arguing with it. Ask directly whether any node should be merged or removed; people cut more than they add once they can see it.

**Keep the design as Mermaid text, not an image.** Text is the only form the human can edit *and* Phase 4 can assert against. The moment the design becomes a PNG or a drawing-tool file, verification breaks and the diagram starts drifting from the code.

Wait for approval before Phase 3, unless told to just build it.

## Phase 3 — Choose a target, then implement

**3a. Choose the runtime.** Ask what they actually use; do not default to a framework.

| Situation | Target file in `references/targets/` |
|---|---|
| Python, LLM orchestration, wants a framework | `langgraph-python.md` |
| TypeScript / Node | `langgraph-js.md` |
| Few nodes, no LLM, or a team that won't adopt a dependency | `plain-code.md` |
| Orchestrating Claude Code subagents | `claude-code-subagents.md` |
| Long-running, needs durability/retries/schedules | `durable-workflow.md` |

Adopting a framework for a three-node pipeline is the same error as climbing a rung you didn't need. `plain-code.md` is the honest answer more often than people expect.

**3b. Implement.** Read the chosen target file. Rules that hold on every runtime:

- **Single writer** — writes stay single-threaded; extra nodes contribute judgement, not actions. The state-ownership table is how you enforce it.
- **Reviewer with teeth** — separate, read-only, ideally a different model, given **clean context rather than the producer's history**. Reviewers with fresh context measurably outperform ones carrying the producer's trace. It writes a verdict to its own field and never edits the work.
- **Failure isolation** — nodes return updates, never mutate shared state. Risky nodes catch their own exceptions into an `errors` field. Use a checkpointer so a retry resumes instead of restarting.
- **Hard bounds** — every conditional loop checks its counter; set the global step limit; track spend in state and route out when the budget is hit.
- **Don't hand-roll the runtime** if you chose a framework.

Deliver something runnable, plus a README carrying both the design diagram and the one emitted by the code.

## Phase 4 — Verify by assertion, not by eye

Run it. Then prove the topology: parse the approved design and the emitted diagram into edge sets and **assert they are equal**. Comparing two nine-edge diagrams by eye is exactly the check a tired builder skips. The Graph-Engineering repo ships a working version as `verify_topology.py` alongside its reference implementations.

A mismatch means the implementation drifted from what the human approved in Phase 2.5. Fix it; don't hand-wave. Confirm every loop-back has a live counter, and that every branch you documented is actually reachable — a bounded reject path that never fires in any test is undemonstrated, not proven.

## Quick reference

| Symptom | Right move |
|---|---|
| One agent, one goal, verifiable output | Rung 2 — loop |
| Summarize / fetch / format pipeline | Rung 2 with tools; a 5-node graph is over-engineering |
| Output quality needs an independent check | Rung 3 — one read-only reviewer, bounded reject loop |
| High-stakes output, one reviewer isn't enough | Rung 4 — panel → synthesise → bounded gate |
| Work exceeds one context window | Rung 5 — fan-out |
| One bad item aborts the whole batch | Rung 5 with per-branch error isolation |
| Re-runs everything from scratch after a failure | Checkpointer, not more nodes |
| Loops forever / costs exploded | Missing attempt caps + step limit + spend field |
| Outputs change depending on node order | State drift — find the field with two writers |
| "People are using graphs, should we?" | Read `references/evidence.md` — most of that advantage was bought with tokens |

## References

- `references/evidence.md` — the research behind the two rules and the ladder. Cite it when someone pushes back.
- `references/graph-design.md` — the runtime-free design method. Read for Phase 2.
- `references/design-checklist.md` — the 8-point checklist with reasoning, for design reviews.
- `references/anti-patterns.md` — symptom → diagnosis → fix.
- `references/auditing-an-existing-graph.md` — Track B workflow.
- `references/targets/*.md` — one file per runtime. Read only the one chosen in Phase 3a.
