# orchestration-design

## What this project is
A toolkit that helps builders decide how much orchestration a piece of work needs, design it on paper, show it to a human for visual review, implement it on any runtime, and verify the build matches the design. Based on the checklist from https://www.aibuilderclub.com/blog/graph-engineering-guide-2026, then re-grounded in 2026 research (see `references/evidence.md`).

**Repo, skill and install path are all `orchestration-design`.** It was originally called graph-engineering; renamed because its most common correct output is *not* a graph. "Loop vs. graph" is a false choice — a loop is a graph with one node. The real questions are how many writers and who decides routing.

**Two rules hold everywhere, both evidence-backed:**
1. **One writer, always.** Extra nodes contribute judgement, never edits.
2. **Structure does not buy intelligence.** At matched token budgets a single agent matches or beats multi-agent designs; most reported multi-agent wins track token spend.

**Core principle: the Phase 2 design object is runtime-free.** Nodes, edges, state schema, bounds and cost are the same artifact whether the target is LangGraph, TypeScript, a workflow engine, or plain code. LangGraph is one target among several, not the destination.

## Layout
- `orchestration-design.skill` — packaged Claude skill (zip). Source of truth is `skill/`.
- `skill/orchestration-design/` — skill source:
  - `SKILL.md` — Track A (phases 0, 1, 2, 2.5, 3, 4) and Track B (audit). Keep under ~150 lines.
  - Phase 1 is a **six-level ladder** (plain script → loop → loop+reviewer → panel → fan-out → durable). Default is level 3. Climb only when a level's named trigger is literally true.
  - Phase 2.5 is a **visual review gate and a hard stop**: hand over an ASCII sketch, the Mermaid block, a pre-filled mermaid.live link (`tools/mermaid_link.py`), and the tables; ask one specific question ("which node would you delete?"); then **end the turn**. The ASCII is a preview and is never asserted against. No implementation in the same turn. If running autonomously, label the result DESIGN NOT REVIEWED rather than treating absence as approval.
  - Phase 4 is **level-aware**. Levels 4–6 assert the edge sets match (`verify_topology.py`). Levels 1–3 emit no diagram, so they assert behaviour instead: reviewer is read-only, the bound is live, the exhaustion terminal is reachable and marked, failure is isolated.
  - `references/evidence.md` — the research behind the two rules and the ladder
  - `references/graph-design.md` — the runtime-free design method (Phase 2 core)
  - `references/design-checklist.md` — annotated 8-point design checklist
  - `references/anti-patterns.md` — symptom → diagnosis → fix
  - `references/auditing-an-existing-graph.md` — Track B workflow
  - `references/targets/` — one file per runtime: `langgraph-python.md`, `langgraph-js.md`, `plain-code.md`, `claude-code-subagents.md`, `durable-workflow.md`
- `reference-implementation/` — runnable examples, one per pattern:
  - `01-loop-not-graph/loop.py` — the gate REFUSING a graph; stdlib only, no LangGraph
  - `02-sequential/` — Pattern A, heterogeneous models per step
  - `03-reviewer-loop/` — Pattern B, bounded reject loop + `flag_for_human` terminal
  - `04-fanout-fanin/` — Pattern C, Send fan-out with per-branch failure isolation
  - `05-judge-panel/` — Pattern D, multi-reviewer panel + bounded plan-review loop
  - `verify_topology.py` — asserts each README's design diagram matches its compiled one
- `run_checks.py` — runs every check above; one command, one exit code. Missing deps FAIL by default.
- `tools/mermaid_link.py` — turns a Mermaid diagram into a pre-filled mermaid.live edit URL (Phase 2.5)

## Conventions (apply to ALL graph code in this repo)
- LangGraph v1.0 API only: StateGraph, START/END, Send, Command, add_conditional_edges, `add_node(..., destinations=(...))`. Never set_entry_point/set_finish_point/ToolExecutor.
- Multi-node fan-out branches use `Command(update=..., goto=[Send(...)])` with `destinations=` declared — a plain edge after a `Send` target loses the per-item payload and silently gives every branch the global state.
- Every state field documents its owner node and reducer; fan-in fields use operator.add or add_messages. An append-reduced field cannot be cleared by returning `[]` — round-tag on write, filter on read.
- Every loop-back edge has an attempt counter AND recursion_limit backstop; a token/spend field is checked by at least one router.
- Reviewers are read-only and separate from producers; nodes return update dicts, never mutate state.
- Risky nodes catch their own exceptions into an `errors` field so one branch failing cannot abort its siblings.
- **Every conditional branch must be exercised by a run and asserted.** A wired-but-never-fired branch is undemonstrated. Where one scenario cannot cover both arms, add a second scenario in `__main__`.
- Examples run offline with deterministic stub models (no API key) and assert their own behaviour; they upgrade to real Anthropic models when `ANTHROPIC_API_KEY` is set. Stub rigging must be self-consistent — a branch should fire for a principled reason, not a hardcoded flag.
- After changing any graph: run it, then run `verify_topology.py` and confirm `graph.get_graph().draw_mermaid()` still matches the documented design.

## Working on the skill itself
Edit files under `skill/orchestration-design/`, then run `./build.sh` — it repackages the zip and reinstalls to `~/.claude/skills/orchestration-design/`. Keep SKILL.md under ~150 lines; put depth in `references/`. Target files are loaded only when Phase 3a selects them, so depth there is cheap.

**The skill ships as markdown only — no Python, no engine.** Triggering is entirely the `description:` frontmatter field. Nothing parses code or builds a graph object; the `.py` files in `reference-implementation/` are examples for humans and are deliberately *not* in the bundle. Designs are Mermaid **text**, never images — text is the only form a human can edit and Phase 4 can assert against.

## Testing
```bash
python run_checks.py --setup               # once per clone: ./.venv + langgraph
python run_checks.py                       # all six checks, one exit code
python run_checks.py --selftest            # the runner's own assertions
python tools/mermaid_link.py --selftest    # URL payload round-trips
```
All must exit 0 offline with stub models. `run_checks.py` prefers the repo's
`.venv` (gitignored, langgraph 1.2.10), falling back to the current interpreter.
Missing dependencies FAIL by default — `--setup` fixes it, `--allow-skip`
tolerates it, `--python /other/bin/python` overrides the interpreter.
