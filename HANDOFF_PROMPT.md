# First prompt to paste into Claude Code

Copy-paste this as your first message after `cd ~/Research/orchestration-design && claude`:

---

Read CLAUDE.md first — it explains the layout and conventions.

Context: this repo contains (1) a Claude skill called `orchestration-design` (source in `skill/orchestration-design/`, packaged as `orchestration-design.skill`) that teaches you to design orchestrated systems — agent graphs, pipelines, batch jobs — using a scope phase, a loop-first gate, a runtime-free paper design, a chosen implementation target, and assertion-based verification; and (2) five runnable reference implementations in `reference-implementation/`, one per pattern, all running offline with stub models.

Do the following to get oriented:
1. Read CLAUDE.md and `skill/orchestration-design/SKILL.md`. Read `references/graph-design.md` for the design method. Read a file under `references/targets/` only if you need that specific runtime.
2. Confirm the skill is installed: `ls ~/.claude/skills/orchestration-design`. If missing, run `./build.sh`.
3. Verify everything still runs:
   ```
   python reference-implementation/01-loop-not-graph/loop.py
   for d in 02-sequential 03-reviewer-loop 04-fanout-fanin 05-judge-panel; do
     python reference-implementation/$d/graph.py
   done
   python reference-implementation/verify_topology.py
   ```
   All must exit 0 offline. `pip install -U langgraph` if needed.
4. Give me a short status report: what the skill does, which patterns the five examples cover, and confirmation the runs and the topology check passed.

From then on, whenever I ask you to build or fix any multi-step system — agent workflow, pipeline, batch job, ETL — follow the orchestration-design skill's process. Expect it to talk me out of a graph when a loop would do; that is the intended behaviour, not a failure.

---

# One-time setup on your machine

1. Install Claude Code if not already: `npm install -g @anthropic-ai/claude-code`
2. Install the skill: `./build.sh` — packages the zip and copies the source to `~/.claude/skills/orchestration-design/`. Re-run it after any edit under `skill/`.
3. Optional: set `ANTHROPIC_API_KEY` if you want the reference graphs to use real models instead of stubs. Claude Code handles its own auth separately via `claude login`.

CLAUDE.md in the repo root is picked up automatically every session, and the skill (once in `~/.claude/skills/`) triggers on its own — including on symptom phrasings like "my pipeline is a mess" or "one bad step kills the whole run", not just on the word "agent".
