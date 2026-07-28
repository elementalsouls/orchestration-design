# Track B — Auditing an existing graph

For "this has grown too complex", "my pipeline is a mess", "it works but I'm scared of it". The job is different from Track A: you are not designing from a blank page, you are **reconstructing the design that is already implied by the code**, then diffing it against what a good design would be.

Do not start by suggesting fixes. Start by making the existing design visible — usually the builder has never seen it written down, and half the findings become obvious the moment it is.

---

## Step 1 — Reconstruct the design object

Read the code and rebuild the same five artifacts Phase 2 would have produced. This is the whole trick: once the existing system is expressed in the Phase 2 format, every tool in this skill applies to it unchanged.

**Nodes.** List every node with its actual job — what it does, not what its name says. Note the model and toolset for each. Flag any node that makes no model call.

**Edges.** Draw the real routing. Emit it from the compiled graph where the runtime supports it; hand-trace it where it doesn't. Do not draw the diagram from the README — the README is what you are checking.

**State.** For every field, find **every** node that writes it. Grep for the field name across the whole codebase rather than trusting structure. Record type, all writers, and reducer.

**Bounds.** For each loop-back edge, find the counter. For the run, find the step limit. Find the spend field. Record honestly what is missing.

**Cost.** Compute worst case from the real numbers. Compare against what they are actually spending — a large gap means a path is firing more than anyone realises.

## Step 2 — Diff against the checklist

Walk `design-checklist.md` and record a verdict per point. Then apply these specific probes, ordered by how often they find something real:

| Probe | How | What it means |
|---|---|---|
| **Two-writer fields** | For each state field, count writing nodes | More than one without a reducer = state drift. The highest-yield check. |
| **Unbounded loops** | Every loop-back edge — is a counter read *and* incremented? | Incremented-but-never-read and read-but-never-incremented both occur. |
| **Fan-in reducers** | Every field written by parallel branches | Replace instead of append = silent result loss. |
| **Self-review** | Compare producer and reviewer model + prompt | Same model reviewing itself is a rubber stamp. |
| **Reviewer scope** | Does the reviewer node return anything but its verdict? | If it edits the artifact, the check isn't independent. |
| **Unreachable branches** | For each documented edge, find a run that fires it | A never-exercised path is undemonstrated, and often broken. |
| **Diagram drift** | Emitted topology vs. the documented one | Drift means the docs are lying about something. |
| **Node necessity** | Merge test and determinism test on every node | Usually the largest simplification available. |
| **Failure isolation** | Does any node let an exception escape? | One escaping exception aborts the batch. |
| **Checkpointing** | Does a retry resume or restart? | Restart-from-scratch is a persistence gap, not a node gap. |

## Step 3 — Rank findings by cost to the builder

Rank by what it costs them, not by how wrong it is. The order that usually holds:

1. **Correctness** — state drift, silent result loss, unreachable error handling. These produce wrong output, sometimes invisibly.
2. **Runaway risk** — missing bounds. Fine until the day it isn't, then expensive.
3. **Structural** — too many nodes, self-review, agents doing deterministic work. Costs velocity and money continuously.
4. **Hygiene** — drifted diagrams, missing assertions, untested branches.

For each finding give: the symptom they would observe, the mechanism, the smallest fix, and whether it is safe to change now or needs a migration.

## Step 4 — Propose the smaller graph

Most audited graphs shrink. Say so explicitly, with the merge test as evidence: "these three nodes use the same model and tools and can be one; these two are parsing and belong in functions." Give the before and after node counts and a diagram of each.

Resist redesigning from scratch. A builder with a working system and a rewrite proposal will keep the working system and ignore the audit. Propose the sequence of small changes that gets there, ordered so each step ships independently.

---

## The conversation

Two rules make this land:

**Lead with what is right.** They built something that works. Name the good decisions — that is not a courtesy, it tells them which parts to protect during the fixes.

**Separate "wrong" from "would not be my choice."** Only flag things that produce a wrong result, a runaway, or a real maintenance cost. Style preferences dressed up as findings dilute the ones that matter, and the reader cannot tell which is which.

## Rejoining Track A

Once the design object exists and is ranked, you are back at **Phase 2**. The remaining work — revise the design, choose a target if migrating, verify by assertion — is identical to building new. The audit's output *is* a Phase 2 artifact, just produced by reading instead of writing.
