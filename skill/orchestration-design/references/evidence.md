# The evidence base

Why this skill gates toward loops. Every claim below is sourced. Read it when someone
pushes back on the gate, or when you are tempted to add agents because the field is.

---

## 1. The headline pro-multi-agent numbers do not survive compute control

The most cited result for multi-agent is Anthropic's: a lead Claude Opus 4 with Sonnet 4
subagents **outperformed single-agent Opus 4 by 90.2%** on their internal research eval.

The same write-up reports the confound. Multi-agent runs used **~15× the tokens** of chat
(single agents ~4×), and on BrowseComp **"token usage by itself explains 80% of the
variance"** in performance, with model choice and tool-call count explaining ~15% more.
So most of the measured advantage tracks spend, not structure.

Two 2026 papers tested this directly by holding compute constant:

**Tran & Kiela, "Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning
Under Equal Thinking Token Budgets"** (arXiv 2604.02460, Stanford / Contextual AI).
Qwen3-30B, DeepSeek-R1-Distill-Llama-70B and Gemini 2.5 on FRAMES and MuSiQue 4-hop,
against five multi-agent variants (sequential, subtask-parallel, parallel-roles, debate,
ensemble). With *thinking tokens* matched, the single agent "is the best-performing system
or statistically indistinguishable from the best for all budgets except the lowest one."
At 1000 tokens: 0.418 single vs 0.379 sequential multi-agent. At 5000: 0.427 vs 0.386.

**"The Illusion of Multi-Agent Advantage"** (arXiv 2606.13003) reproduces the pattern on
GPQA, SWE-bench and BrowseCompPlus: once tokens, inference steps and model capacity are
matched, most reported multi-agent gains disappear.

**The theory.** Tran & Kiela ground it in the Data Processing Inequality: a subagent's
message is a *function of* the context it saw, so it cannot carry more mutual information
with the correct answer than that context did. Every handoff can lose information; none
can create it. A single agent holding full context is therefore information-theoretically
guaranteed to do at least as well — **given perfect context utilization.**

That last clause is the whole game.

## 2. Where multi-agent genuinely wins: context pressure, not parallelism

Real agents do not have perfect context utilization, and the same paper shows where the
guarantee breaks. In their degradation experiments, multi-agent overtakes single-agent
once effective context is sufficiently degraded — under heavy masking (α = 0.7) sequential
multi-agent beat the single agent, with a crossover under moderate substitution noise.
Their conclusion: "when effective single-agent context utilization deteriorates enough,
structured multi-agent reasoning becomes competitive."

This reframes the whole decision. **A graph does not add intelligence. It buys context
hygiene.** It wins when the work does not fit cleanly in one context — Anthropic's own
stated sweet spot is "breadth-first queries pursuing multiple independent directions
simultaneously" where "information exceeds single context windows."

Consequence for the gate: *parallelism alone is not a reason.* Parallelism buys wall-clock
time and context isolation. At equal token budget it does not buy accuracy. Ask whether
the work **exceeds one context window** — not whether it could be run concurrently.

Independence is a **precondition**, not a trigger. Nearly every batch has independent
items, so treating independence as sufficient sends all batch work to fan-out, which is
the opposite of what this evidence supports. Independence only tells you whether fan-out
is *safe*; context pressure tells you whether it is *warranted*. And splitting has a
cost the DPI argument predicts: any judgement that needs to see items together —
deduplication, ranking, cross-referencing — becomes impossible once each branch sees one
item.

## 3. Multi-agent systems fail a lot, and verifiers are not a silver bullet

**MAST** (Cemri et al., "Why Do Multi-Agent LLM Systems Fail?", arXiv 2503.13657,
NeurIPS 2025): 1,600+ annotated traces across 7 frameworks, expert-annotated at
κ = 0.88, yielding 14 failure modes in three categories — system design, inter-agent
misalignment, and task verification.

Reported correctness is poor: ChatDev at **33.3%** on ProgramDev, AppWorld at **86.7%
failure** on cross-app tests. Verification-related modes alone: incorrect verification
**9.1%**, no or incomplete verification **8.2%**, premature termination **6.2%**.

The finding that matters most here: frameworks *with* explicit verifiers showed fewer
failures but still low overall success. **Adding a reviewer helps and does not rescue a
bad architecture.** The authors state the failures need structural fixes, not better
prompting.

## 4. Cognition changed its mind in public, and the corrected rule is narrow

The most useful practitioner datapoint, because it is the same team revising with
production data.

**2025 — "Don't Build Multi-Agents."** Parallel subagents fragment context and make
conflicting implicit decisions. Their example: one subagent built a Super Mario background
while another built an incompatible bird sprite. Principles: *share full agent traces, not
just individual messages*; *actions carry implicit decisions, and conflicting decisions
carry bad results.* Recommendation: single-threaded linear agents.

**2026 — "Multi-Agents: What's Actually Working."** A narrow reversal, not a retraction.
The rule they land on:

> Multi-agent systems work best today when **writes stay single-threaded** and the
> additional agents contribute **intelligence rather than actions.**

What works in production:

- **Code review loop.** Devin Review catches ~2 bugs per PR, **58% of them severe**. It
  works *best when the reviewer has completely clean context* — no access to the coding
  agent's history — because long contexts degrade decisions (context rot). The reviewer
  rediscovers context from the diff alone.
- **"Smart friend."** A cheaper primary model escalating to a frontier model on demand;
  works between two strong models as a capability router.
- **Manager coordination.** A manager decomposing work to children, live in Devin, but it
  took heavy context engineering to stop managers over-prescribing.

What still does not work: parallel writer swarms; arbitrary networks of agents negotiating
with each other ("mostly a distraction"); and asymmetric delegation where a weaker primary
must recognise when to escalate.

## 5. The industry converged on a shape that looks like a loop with helpers

By 2026 Anthropic, OpenAI, Cognition, Microsoft/AutoGen and LangChain had converged on
**orchestrator + isolated ephemeral subagents**: one coordinator owning the full
conversation context, workers in fresh isolated contexts returning **compressed summaries
only**, and no peer-to-peer channels. Earlier peer-collaboration designs (GroupChat-style)
lost.

Documented failure modes of the designs that lost: full transcript replay on every wakeup,
coordinator bloat, redundant supervisor↔worker translation, conflicting implicit
assumptions, O(n²) communication edges, and "herding" where parallel agents reinforce a
confident wrong conclusion.

Note how close the winning shape is to a loop with a reviewer: one context owner, one
writer, helpers that return judgement.

---

## 6. The graph vendor says loops are graphs, and moved its own flagship off a graph

**LangChain, "3 Years of Graph Engineering with LangGraph"** (22 July 2026).
*Strength: practitioner experience report. No benchmarks, no controlled comparison,
and the author sells the graph framework. Weigh it like the Cognition posts, not
like Tran & Kiela.*

Two passages are worth having anyway, because both cut against the author's interest.

**On the framing this whole skill rests on:**

> "loops are simple graphs. Loop engineering isn't an alternative to graphs, so
> much as a simple version of them... a loop is just a directed, cyclic graph."

That is the same claim as this skill's opening line, arrived at independently by
the people selling graphs. It is why "loop vs. graph" is a false choice: the
question was never which one, it is how many writers and who decides routing.

**On migrating away from graphs:**

> "We built early deep research on predefined LangGraph workflows, then moved to a
> more agentic core loop. GPT Researcher, a popular deep research implementation,
> made the same move, swapping its graph-shaped multi-agent pipeline for Deep
> Agents so planning, delegation, and context management emerge in the harness
> rather than being hardcoded in the graph."

Two independent teams migrated graph → loop, reported by the graph vendor. An
admission against interest is worth more than a claim in favour of one.

**And the reason, which the ladder had been missing entirely:**

> "Some tasks are more agentic by nature, and forcing them into deterministic
> paths is the wrong move. In these cases, you don't want to represent the system
> as a graph but rather just use an agent harness."

This is a **different axis from every other trigger in the ladder**. All the
others measure load — judgement, assertability, context pressure, durability.
This one asks whether the route is knowable at all. A task can be heavy on every
load dimension and still be wrong to structure, because you cannot enumerate
paths that depend on what the work turns up as it goes.

**Not cited from this article:** its 65M-downloads-per-month figure. Adoption is
not correctness, and citing it would weaken everything above.

## What this means for the gate

1. **Loop-first is the evidence-backed default,** not a stylistic preference. At equal
   budget the single agent wins or ties.
2. **Reframe the parallelism criterion as context pressure.** "Could run concurrently" is
   not a reason, and neither is "the items are independent" — that is a precondition for
   fan-out being safe, not evidence that it is warranted. "Exceeds one context window" is.
3. **Single writer is a law, not a preference.** Extra nodes should contribute judgement,
   not edits. This is the same rule the state-ownership table enforces.
4. **Give reviewers clean context deliberately.** Ephemeral reviewers are not just
   philosophically nicer; they measurably outperform reviewers carrying producer history.
5. **A reviewer improves a graph but does not justify one.** Verifier-bearing frameworks
   still failed often.
6. **Compare at equal token budget or you are measuring your own spend.** If a graph is
   pitched against a loop, match the budget before believing the delta.
7. **Ask whether the route is knowable before applying the ladder at all.** Every other
   trigger measures load; this one asks whether you can enumerate the paths. If you
   cannot, no level is correct — use an agent harness and let the path emerge (§6).

## Honest counterweight

Multi-agent does win in real, specific places, and the gate should let those through:
breadth-first research over independent sources exceeding one context window (Anthropic),
orchestrator fan-out on agentic benchmarks, disjoint tool or security domains requiring
separate data access, and narrow high-stakes domains where an independent reviewer catches
what the producer structurally cannot see. The claim is not that graphs are bad. It is
that the bar is higher than current practice assumes, and that most of the reported
advantage in the wild is bought with tokens.
