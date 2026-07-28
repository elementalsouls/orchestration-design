# Target: Claude Code subagents

When the "nodes" are Claude Code agents rather than model API calls. The runtime is Claude Code itself: the Agent tool spawns a node, and the Workflow tool provides deterministic orchestration around a set of them.

Choose this when the work is *development* work — reviewing a diff across dimensions, migrating many files, researching several subsystems in parallel, auditing a codebase — and each node needs tools, a filesystem, and the ability to run commands. Do not choose it for a production data path; it is an interactive/agentic runtime, not a service.

## How the Phase 2 design maps

| Design artifact | Here |
|---|---|
| Node | one `agent()` call, or one Agent tool invocation |
| Edge, sequential | `await` one agent before spawning the next |
| Edge, fan-out | `parallel()` / `pipeline()`, or several Agent calls in one message |
| Edge, conditional | a plain `if` in the workflow script |
| State | return values threaded through the script — **not** shared mutable state |
| Reducer | array concat in the script |
| Bounds | loop conditions and the token budget |

The important structural difference: **there is no shared mutable state object.** Each agent gets a prompt and returns a result. That removes state drift as a failure mode entirely — and replaces it with a different one, context loss, because anything a node needs must be in its prompt.

## The two ways to run

**Ad-hoc, in the main loop.** Spawn agents directly for a single fan-out. Send independent agents in one message so they run concurrently.

**Deterministic, via a workflow script.** When the control flow matters — loops, conditionals, staged fan-out — write a script so the orchestration is code rather than model judgement.

```js
export const meta = {
  name: 'review-changes',
  description: 'Review a diff across dimensions, verify each finding',
  phases: [{ title: 'Review' }, { title: 'Verify' }],
}

const DIMENSIONS = [
  { key: 'correctness', prompt: '…' },
  { key: 'security',    prompt: '…' },
]

const results = await pipeline(
  DIMENSIONS,
  d => agent(d.prompt, { label: `review:${d.key}`, phase: 'Review', schema: FINDINGS }),
  review => parallel(review.findings.map(f => () =>
    agent(`Adversarially verify: ${f.title}. Default to refuted if uncertain.`,
          { phase: 'Verify', schema: VERDICT })
      .then(v => ({ ...f, verdict: v })))),
)

return { confirmed: results.flat().filter(Boolean).filter(f => f.verdict?.isReal) }
```

Note that this *is* Pattern D — producer nodes, an independent reviewer panel, and a synthesis step — expressed in a different runtime. The design did not change.

## Structured output is your state schema

`schema` forces the agent to return a validated object instead of prose. Use it for every node whose output another node consumes. Free-text returns are the equivalent of an untyped state field, and they fail the same way.

```js
const FINDINGS = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: {
      type: 'object',
      properties: { file: {type:'string'}, line: {type:'number'}, summary: {type:'string'} },
      required: ['file', 'summary'],
    }},
  },
  required: ['findings'],
}
```

## Pipeline over barrier

`pipeline()` runs each item through all stages independently — item A can be in stage 3 while item B is still in stage 1. `parallel()` is a barrier that waits for everything.

Default to `pipeline()`. A barrier is only correct when a stage genuinely needs *all* prior results together: deduplication across the full set, an early exit on a zero count, or a synthesis step that compares findings against each other. "I need to flatten the array first" is not a reason — do that inside a stage.

## Failure isolation

A thunk that throws resolves to `null` rather than rejecting the whole call, so:

```js
const results = (await parallel(tasks)).filter(Boolean)
```

Always filter. An agent can also die on a terminal error and return `null`, which is the same shape as a skipped one — treat both as an isolated branch failure and report the count rather than pretending it did not happen.

## Bounds

| Bound | Form |
|---|---|
| Attempt counter | loop variable in the script |
| Fan-out width | array length — cap it deliberately, and `log()` anything you dropped |
| Spend | `budget.remaining()` in the loop condition |
| Concurrency | capped automatically; excess queues |

```js
const bugs = []
while (budget.total && budget.remaining() > 50_000) {
  const r = await agent('Find bugs…', { schema: BUGS })
  bugs.push(...r.bugs)
}
```

**Never cap silently.** If you take top-N or skip retries, `log()` what was dropped — silent truncation reads as complete coverage when it is not.

## Reviewer with teeth, here

The rule survives translation: the verifying agent must be a **separate spawn** from the producing one, and prompted to refute rather than to confirm. An agent asked "is this finding real?" agrees with itself; an agent asked "try to refute this, default to refuted if uncertain" does the job. For anything high-stakes, use several verifiers with *different lenses* rather than several identical ones — diversity catches failure modes that redundancy cannot.

## Loop until dry

For unknown-size discovery, a fixed count misses the tail:

```js
const seen = new Set(); let dry = 0
while (dry < 2) {
  const found = await runFinders()
  const fresh = found.filter(b => !seen.has(key(b)))
  if (!fresh.length) { dry++; continue }
  dry = 0; fresh.forEach(b => seen.add(key(b)))
}
```

Deduplicate against everything seen, not against confirmed results — otherwise rejected findings resurface every round and the loop never converges.

## Pitfalls

- **Context loss between nodes.** A fresh agent knows nothing. Anything it needs goes in the prompt.
- **Over-spawning.** Agents are expensive. A three-step task in one agent beats three agents plus the prompting to connect them.
- **Prose where structure was needed.** Use `schema` whenever output is consumed by code.
- **Barrier by habit.** `parallel()` between stages wastes the fast branches' time; reach for `pipeline()` unless you need cross-item context.
- **Unverified findings.** An agent reporting a bug is a hypothesis, not a result. Verify before acting.
