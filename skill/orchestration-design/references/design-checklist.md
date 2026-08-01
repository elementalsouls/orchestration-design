# The Graph Engineering Starting Checklist (with reasoning)

Use this when designing a new graph or reviewing an existing one. Walk each point and record the answer; a design that can't answer a point isn't ready to build.

## 1. Try to keep it a loop
Can a single well-scoped agent with a good verifier do this? If yes, stop — you're done. A loop is a one-node graph; every node you add multiplies cost, latency, and debugging surface. Most tasks are one-loop problems. A five-node graph (fetcher → chunker → summarizer → reviewer → formatter) for a summarization task is the canonical over-engineering anti-pattern: slower to build, harder to debug, more expensive to run.

## 2. Name the nodes only if they're real specialties
Each node should have a job a single loop genuinely couldn't hold — a different model, a different toolset, or a read-only reviewer role. "Steps I could inline" are not nodes. Test: if two adjacent nodes use the same model, same tools, and same prompt style, merge them.

## 3. Draw the edges before you code
Sketch the routing: what's sequential, what fans out, what fans in, and where the one conditional/loop-back edge lives. If you can't draw it on a napkin, it's too complex. Aim for a single conditional edge; every extra branch point doubles the paths you have to test.

## 3b. Check the premise of every loop-back
For each cycle, name the state its re-entry point reads and the node **inside** the loop that writes it. No writer inside means the loop is decorative — it will run, spend its bounds and change nothing. The inverse also fails: a straight line for work that genuinely iterates produces a complete-looking, shallow result. One grep answers both; intuition answers neither. See `graph-design.md`.

## 4. Design the shared state object explicitly
Decide what travels along the edges and who's allowed to write to it. For every field: type, reducer (replace vs append), owning node. State drift — multiple nodes writing the same field without a merge rule — is the #1 way graphs rot. Symptom: outputs that depend on node execution order.

## 5. Give the reviewer node teeth
The single highest-value node is usually a separate, read-only verifier — a different agent (ideally a different model) from the one that produced the work. Producers grading their own work rubber-stamp it. The reviewer writes only a verdict + reasons to its own field, and the reject edge loops back to the producer, bounded (see 8).

## 6. Isolate failure
One node must be able to fail and retry without corrupting shared state or poisoning downstream nodes. Mechanics: nodes return updates instead of mutating; risky nodes catch their own exceptions into an `errors` field; a checkpointer lets a retry resume from the last good state.

## 6b. Decide the substrate: is the output a system, or a process?
A system runs without you; a process runs *with* you — an audit, a review, a migration, a manuscript — where nodes are prompts, subagents and human decisions and there is no runtime. The method is identical; state becomes a **ledger** (one row per unit, one column per check, seeded `pending`, one writer per column) and bounds become rounds and wall clock. Get this wrong and you design a pipeline for work that was never going to be code. See `targets/procedural.md`.

## 7. Choose a runtime deliberately — then don't hand-roll it
Two failure modes here, and they point in opposite directions. Reinventing routing, retries and persistence when you have adopted a framework is slop. But adopting a framework for three sequential steps is the same error as building a graph you didn't need, one level up.

Decide from the design, not from habit: fan-out with durable state and complex routing earns a framework; a short linear pipeline does not. See `targets/` — `plain-code.md` is the honest answer more often than people expect, and the design object is identical either way.

## 8. Set a spend cap and a hard bound
A graph is many loops; a weak verifier now burns tokens in parallel. Cap it three ways: attempt counters on loop-back edges, a global step limit (LangGraph calls this `recursion_limit`; plain code calls it a counter in the driver; a process calls it `max_rounds`), and a budget field that at least one router actually reads.

## The five-layer sanity check
Graph engineering sits on top of layers that must already work: prompt (am I asking well?) → context (right info present?) → harness (tools/memory) → loop (verify & stop) → graph (who does what, in what order). If a lower layer is broken, fixing it beats adding nodes.
