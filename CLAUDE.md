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
  - `SKILL.md` — Track A (phases 0, 1, 2, 2.5, 3, 4) and Track B (audit). **Currently 160 lines; keep it there or below.** It loads on every trigger while `references/` load on demand, so the rule is *method here, depth there* — a worked example belongs in `references/`, the rule it demonstrates belongs here.
  - Phase 1 opens with a **pre-ladder question — can you enumerate the valid paths?** If not, structure is the wrong tool; use an agent harness and let the path emerge. The ladder assumes a knowable route.
  - Phase 1 is then a **six-level ladder** (plain script → loop → loop+reviewer → panel → fan-out → durable). Default is level 3. Climb only when a level's named trigger is literally true. **Levels are picked per stage, not per system** — the headline level is the highest any stage needs.
  - Phase 2.5 is a **visual review gate and a hard stop**: hand over an ASCII sketch, the Mermaid block, a pre-filled mermaid.live link (`tools/mermaid_link.py`), and the tables; ask one specific question ("which node would you delete?"); then **end the turn**. The ASCII is a preview and is never asserted against. No implementation in the same turn. If running autonomously, label the result DESIGN NOT REVIEWED rather than treating absence as approval.
  - Phase 4 is **level-aware**. Levels 4–6 assert the edge sets match (`verify_topology.py`). Levels 1–3 emit no diagram, so they assert behaviour instead: reviewer is read-only, the bound is live, the exhaustion terminal is reachable and marked, failure is isolated.
  - `references/evidence.md` — the research behind the two rules, dated, with controlled experiments separated from production reports
  - `references/graph-design.md` — the runtime-free design method (Phase 2 core), incl. the loop-back premise check
  - `references/design-checklist.md` — annotated design checklist, for reviews
  - `references/anti-patterns.md` — symptom → diagnosis → fix
  - `references/auditing-an-existing-graph.md` — Track B workflow
  - `references/targets/` — one file per substrate: `procedural.md` (output is a process, not software), `plain-code.md`, `langgraph-python.md`, `langgraph-js.md`, `claude-code-subagents.md`, `durable-workflow.md`
- `reference-implementation/` — one runnable example per pattern, `01-loop-not-graph` through `05-judge-panel`, plus `verify_topology.py`.
- `tools/` — `gen_banner.py` (README banner), `mermaid_link.py` (diagram → pre-filled edit URL), `term_svg.py` (terminal capture → SVG). All generated images regenerate; never hand-edit `docs/img/`.

## Conventions

**Scope note.** The rules below govern the **LangGraph example code** in
`reference-implementation/`. They are not the skill's position — the skill is runtime-last,
and `plain-code.md` and `procedural.md` are more often the right answer than any framework.
The runtime-independent rules are the four at the end of this list; those apply everywhere.
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
Edit files under `skill/orchestration-design/`, then run `./build.sh` — it repackages the zip and reinstalls to `~/.claude/skills/orchestration-design/`. Keep SKILL.md at or below ~160 lines; put depth in `references/`. Target files are loaded only when Phase 3a selects them, so depth there is cheap.

**The skill ships as markdown only — no Python, no engine.** Triggering is entirely the `description:` frontmatter field. Nothing parses code or builds a graph object. The `.py` files are deliberately *not* in the bundle — they are the reference implementations plus the harness that checks them, and they run here rather than being installed. Designs are Mermaid **text**, never images — text is the only form a human can edit and Phase 4 can assert against.

## The skill-design standard
`docs/skill-design-standard.md` is what this repo holds *itself* to, derived 2026-08-02 from the 719 skills installed on this machine. `tools/skill_lint.py` enforces the machine-checkable half and runs as one of the ten checks. Before changing `SKILL.md` frontmatter or adding a reference file:

```bash
python tools/skill_lint.py skill/orchestration-design    # exit 1 on any FAIL
```

The rules that bite most often: `description:` is capped at **1024 characters** because Codex truncates past it *silently*; `SKILL.md` stays at or below ~160 lines with depth in `references/`; every intra-skill path a file names must actually ship. `docs/corpus-audit-2026-08.md` is that linter run across all 76 installed skills — read-only, and a worked example of what the rules catch.

Two pillars are **not** machine-checkable and must not be faked: *evidence discipline* (sources fetched, dated, strength-separated) and *cold-run acceptance* (an agent with no memory of writing it follows it — one run per vocabulary the description claims).

## Testing
```bash
python run_checks.py --setup               # once per clone: ./.venv + langgraph
python run_checks.py                       # all ten checks, one exit code
python run_checks.py --selftest            # the runner's own assertions
python tools/mermaid_link.py --selftest    # URL payload round-trips
python tools/skill_lint.py --selftest      # the lint rules prove themselves
```
All must exit 0 offline with stub models. `run_checks.py` prefers the repo's
`.venv` (gitignored, langgraph 1.2.10), falling back to the current interpreter.
Missing dependencies FAIL by default — `--setup` fixes it, `--allow-skip`
tolerates it, `--python /other/bin/python` overrides the interpreter.
