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
the work exceeds one context window or the items are genuinely independent — not whether
it could be run concurrently.

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

## What this means for the gate

1. **Loop-first is the evidence-backed default,** not a stylistic preference. At equal
   budget the single agent wins or ties.
2. **Reframe the parallelism criterion as context pressure.** "Could run concurrently" is
   not a reason. "Exceeds one context window" or "items genuinely independent" is.
3. **Single writer is a law, not a preference.** Extra nodes should contribute judgement,
   not edits. This is the same rule the state-ownership table enforces.
4. **Give reviewers clean context deliberately.** Ephemeral reviewers are not just
   philosophically nicer; they measurably outperform reviewers carrying producer history.
5. **A reviewer improves a graph but does not justify one.** Verifier-bearing frameworks
   still failed often.
6. **Compare at equal token budget or you are measuring your own spend.** If a graph is
   pitched against a loop, match the budget before believing the delta.

## Honest counterweight

Multi-agent does win in real, specific places, and the gate should let those through:
breadth-first research over independent sources exceeding one context window (Anthropic),
orchestrator fan-out on agentic benchmarks, disjoint tool or security domains requiring
separate data access, and narrow high-stakes domains where an independent reviewer catches
what the producer structurally cannot see. The claim is not that graphs are bad. It is
that the bar is higher than current practice assumes, and that most of the reported
advantage in the wild is bought with tokens.
