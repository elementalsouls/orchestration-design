# orchestration-design

A Claude Code skill that decides **how much orchestration your work actually needs** — and usually concludes it's less than you think.

Eleven markdown files. No dependencies, no engine, nothing to run.

---

## The problem

You want to build something with AI agents. Every framework's docs and most tutorials show you the same picture: five boxes with arrows between them. Planner → Researcher → Writer → Reviewer → Formatter. It looks like engineering.

So you build it. Then it costs ~15× what you expected, runs slower than one agent would have, and when it's wrong you can't tell which box did it. And you can't say whether it beats a single agent, because you never compared them at the same cost.

Here's the part that stings. From the 2026 literature:

- Anthropic's widely-quoted result — multi-agent beating single-agent by **90.2%** — came with a footnote almost nobody repeats: it used **~15× the tokens**, and **token spend alone explained 80% of the performance variance**.
- Two follow-up papers held compute constant. Most of the advantage disappeared. Under matched thinking-token budgets a single agent was **best or statistically indistinguishable from best at every budget except the lowest**.
- Across seven multi-agent frameworks, measured correctness was poor — ChatDev at **33.3%** on ProgramDev, AppWorld at **86.7% failure** on cross-app tests.

Most people building agent systems right now are paying multi-agent prices for single-agent quality.

## What this does

It's an opinionated advisor that interrupts you *before* you write the wrong thing.

**You ask:** *"Build me a multi-agent system that fetches an article, chunks it, summarizes each chunk, reviews the summary, and formats it as markdown."*

**It answers:**

> Fetching is a tool call. Chunking is a `for` loop. Formatting is a template. That's three functions, not three agents. And your "reviewer" is the same model grading its own homework, so it will approve almost anything.
>
> What you want is one agent with a fetch tool and one *independent* checker. That's rung 3 of 6. Here's the design — change anything before I build it?

You ship in an afternoon instead of a week, and you can debug it with a print statement.

When the work **genuinely** needs structure, the same ladder says so — and names the specific trigger (*"the work exceeds one context window"*, not *"this feels complicated"*). Then it designs on paper first, shows you the diagram so you can delete what you don't want, builds on whatever stack you actually use, and **asserts** that the code matches the diagram you approved.

## Install

```bash
git clone https://github.com/elementalsouls/orchestration-design.git
cd orchestration-design
./build.sh
```

That packages the skill and copies it to `~/.claude/skills/orchestration-design/`. Re-run after any edit under `skill/`.

To uninstall: `rm -rf ~/.claude/skills/orchestration-design`.

**It fires on symptoms, not jargon.** You don't need the words "graph" or "orchestration" — try *"my pipeline is a mess"*, *"one bad step kills the whole run"*, or *"it re-runs everything on failure"*.

## The ladder

Phase 1 is the core of the skill. Start at rung 1, stop at the first rung that holds, and climb only when that rung's named trigger is **literally true** — not because the task feels hard.

| Rung | Shape | Climb past it only when |
|---|---|---|
| **1 · Plain script** | Deterministic code, no model | Work needs judgement a rule cannot encode |
| **2 · Loop** | One agent with tools, self-terminating | Correctness cannot be asserted mechanically |
| **3 · Loop + reviewer** ← **default** | One writer, one read-only checker with clean context | — |
| **4 · Reviewer panel** | Several reviewers, different lenses, one synthesis | One reviewer provably misses a defect class *and* stakes justify the spend |
| **5 · Fan-out** | One branch per item, own context, isolated failures | **Work exceeds one context window**, or items are genuinely independent |
| **6 · Durable workflow** | Persistent, resumable, scheduled | Run outlives a process, or needs replay or a human pause |

**What does not justify climbing:** task difficulty, step count, "feels complex", "could run in parallel", or wanting the design to look sophisticated.

Two rules hold at every rung:

1. **One writer, always.** Extra nodes contribute judgement, never edits. Parallel writers making conflicting implicit decisions is the failure mode that killed agent-swarm designs industry-wide.
2. **Structure does not buy intelligence.** It buys context isolation and wall-clock time. At equal budget it does not buy accuracy.

## What's in the skill

| File | What it gives you |
|---|---|
| `SKILL.md` | The six phases: scope → ladder → paper design → **visual review** → build → verify |
| `references/evidence.md` | Every claim sourced, with honest strength ratings per source |
| `references/graph-design.md` | Nodes, edges, state ownership, bounds, cost — framework-free |
| `references/anti-patterns.md` | Starts from the symptom you'd notice, gives mechanism and fix |
| `references/auditing-an-existing-graph.md` | For when something already exists and has rotted |
| `references/design-checklist.md` | The 8-point review checklist with reasoning |
| `references/targets/*.md` | Five runtimes: LangGraph Python, LangGraph.js, plain code, Claude Code subagents, durable engines |

### The visual review gate

Phase 2.5 exists so a human can see the architecture **before** any code is written, and it is a **hard stop** — the skill ends its turn on the design rather than presenting a diagram and building anyway.

You get three things: an **ASCII sketch** you can read in the terminal with nothing installed, the **Mermaid source**, and a **pre-filled [mermaid.live](https://mermaid.live) link** that opens the diagram already loaded — no copy-paste. Drag nodes around, delete what you don't want, hand it back. Your edited diagram becomes the spec. (`tools/mermaid_link.py` generates the link; the ASCII is a preview only and is never asserted against.)

Designs stay **text, never images** — text is the only form you can edit *and* Phase 4 can assert against. The moment a design becomes a PNG, verification breaks and the diagram starts drifting from the code.

## Reference implementations

Five runnable examples. All run offline with deterministic stub models — **no API key** — and every one asserts its own behaviour, so they cannot silently rot.

```bash
python run_checks.py --setup   # once: creates ./.venv and installs langgraph
python run_checks.py           # all six checks, one exit code
```

`run_checks.py` uses the repo's own `.venv` when it exists, so the bare command
is green with no flags. `.venv` is gitignored, so a fresh clone runs `--setup`
first.

A missing dependency is a **failure**, not a skip — in CI a silently-skipped
check is how green builds start lying. Pass `--allow-skip` to tolerate it
anyway, or `--python /other/bin/python` to run under a different interpreter.

| Example | Pattern | What it demonstrates |
|---|---|---|
| `01-loop-not-graph` | *(no graph)* | The gate **refusing**. Stdlib only, no framework. The most common correct outcome. |
| `02-sequential` | A | The smallest thing that's still legitimately a graph — heterogeneous models per step |
| `03-reviewer-loop` | B | Bounded reject loop, plus a `flag_for_human` terminal that a second scenario actually reaches |
| `04-fanout-fanin` | C | `Send` fan-out where one branch deliberately fails and the other five still finish |
| `05-judge-panel` | D | Parallel reviewers, majority synthesis, bounded gate — every conditional edge exercised |

`verify_topology.py` parses the hand-drawn diagram and the compiled one out of each README, reduces both to edge sets, and asserts they're equal. Comparing two nine-edge diagrams by eye is exactly the check a tired developer skips.

## Why this might help you

**Someone finally wrote down the "no."** There's an enormous amount of material on how to build multi-agent systems and almost none on when not to. Nobody gets engagement from a post saying "you probably need one agent." This treats the refusal as its primary output and cites its reasons.

**Your design outlives your framework.** Nodes, state ownership and bounds are identical whether you use LangGraph, TypeScript, or eighty lines of `asyncio`. The runtime is picked **last**, and `plain-code.md` is the honest answer more often than framework marketing suggests.

**It gives junior developers an argument.** When a lead says "let's make it multi-agent," you can now point at controlled experiments and say: *let's match the token budget first, then compare.*

## Honest limits

**It is a prompt, not a program.** There's no engine. Nothing scans your codebase or generates architecture. Its entire power is that Claude reads good instructions and follows them. The `.py` files here are examples for humans and are deliberately **not** shipped in the skill bundle.

**It will argue with you.** If you want a graph and the work doesn't justify one, it says so. That's the design, and some people will find it annoying.

**The research will age.** Core papers are 2025–2026. If models get dramatically better at coordinating, the loop-first default weakens. `evidence.md` is dated so you can see the shelf life, and it separates strong evidence (controlled experiments) from weaker (single-company production reports).

**Tested end to end once.** On one real task it behaved correctly — refused the graph, routed to a plain script, and its own verification step caught two real bugs in what it had just built. That's one trial, not a track record.

## Sources

- [Anthropic — How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — the 90.2% claim, 15× token cost, 80%-of-variance finding
- [Tran & Kiela — Single-Agent LLMs Outperform Multi-Agent Systems Under Equal Thinking Token Budgets](https://arxiv.org/abs/2604.02460) — the controlled comparison
- [The Illusion of Multi-Agent Advantage](https://arxiv.org/abs/2606.13003) — replication across GPQA, SWE-bench, BrowseCompPlus
- [Cemri et al. — Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) (NeurIPS 2025) — the MAST taxonomy and failure rates
- [Cognition — Don't Build Multi-Agents](https://cognition.com/blog/dont-build-multi-agents) (2025)
- [Cognition — Multi-Agents: What's Actually Working](https://cognition.com/blog/multi-agents-working) (2026) — the single-writer rule
- Original checklist: [aibuilderclub — Graph Engineering Guide 2026](https://www.aibuilderclub.com/blog/graph-engineering-guide-2026)

## Repo layout

```
skill/orchestration-design/    skill source — edit here, then ./build.sh
reference-implementation/      five runnable examples + verify_topology.py
tools/mermaid_link.py          diagram -> pre-filled mermaid.live edit URL
run_checks.py                  run every check; one command, one exit code
orchestration-design.skill     packaged bundle (zip)
build.sh                       package + install to ~/.claude/skills/
CLAUDE.md                      conventions for working on this repo
```

> **Why not "graph engineering"?** That was the original name, and it set the wrong expectation — you'd install it looking for a graph builder and get a gatekeeper. "Loop vs. graph" is a false choice anyway: **a loop is a graph with one node and one edge back to itself.** The real questions are how many writers, and who decides the routing. Ask it that way and the answer is usually *one writer, plus a reviewer*.
