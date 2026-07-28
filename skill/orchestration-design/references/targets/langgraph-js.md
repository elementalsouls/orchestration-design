# Target: LangGraph.js (TypeScript / Node)

Choose when the team is TypeScript and the design has real fan-out, loops, or durable state. For a few sequential steps, `plain-code.md` applies just as well in TS — `Promise.all` and a typed state object cover a surprising amount.

Install: `npm i @langchain/langgraph @langchain/core`.

The concepts map one-to-one onto the Python target; the API differs in three ways worth knowing up front:

| Concept | Python | TypeScript |
|---|---|---|
| State declaration | `TypedDict` + `Annotated` | `Annotation.Root({...})` |
| Reducer | `Annotated[list, operator.add]` | `reducer: (a, b) => a.concat(b)` |
| Fan-out | `Send("node", payload)` | `new Send("node", payload)` |
| Step limit | `config={"recursion_limit": 25}` | `{ recursionLimit: 25 }` |

## State with reducers

Reducers are explicit functions here, which makes the append-vs-replace choice harder to get wrong by accident.

```ts
import { Annotation } from "@langchain/langgraph";

const State = Annotation.Root({
  task:    Annotation<string>(),                      // caller      replace
  draft:   Annotation<string>(),                      // worker      replace
  verdict: Annotation<string>(),                      // synthesise  replace
  attempts: Annotation<number>({                      // worker      counter
    reducer: (_prev, next) => next,
    default: () => 0,
  }),
  reviews: Annotation<Review[]>({                     // FAN-IN — must append
    reducer: (prev, next) => prev.concat(next),
    default: () => [],
  }),
  tokensSpent: Annotation<number>({                   // every model node, sum
    reducer: (a, b) => a + b,
    default: () => 0,
  }),
  errors: Annotation<string[]>({
    reducer: (prev, next) => prev.concat(next),
    default: () => [],
  }),
});
```

Default `Annotation<T>()` with no reducer is last-write-wins. **Any field written by parallel branches needs an explicit concat reducer** — the same rule as Python, and the same silent result loss if you skip it.

## Nodes return partial updates

```ts
type S = typeof State.State;

async function worker(state: S): Promise<Partial<S>> {
  const r = await workerModel.invoke(promptFor(state));
  return {
    draft: r.content as string,
    attempts: state.attempts + 1,
    tokensSpent: r.usage_metadata?.total_tokens ?? 0,
  };
}
```

`Partial<S>` is doing useful work: it makes "return an update, don't mutate state" a type-level rule rather than a convention.

## Graph construction

```ts
import { StateGraph, START, END, Send } from "@langchain/langgraph";

const graph = new StateGraph(State)
  .addNode("worker", worker)
  .addNode("review", review)
  .addNode("synthesise", synthesise)
  .addNode("format", format)
  .addEdge(START, "worker")
  .addConditionalEdges("worker", fanOutReviews, ["review"])
  .addEdge("review", "synthesise")              // implicit fan-in barrier
  .addConditionalEdges("synthesise", gate, {
    format: "format",
    worker: "worker",
  })
  .addEdge("format", END)
  .compile();
```

## Fan-out with Send

```ts
const LENSES = ["correctness", "clarity", "completeness"] as const;

function fanOutReviews(state: S) {
  // payload carries only what the branch needs, plus the round tag
  return LENSES.map(
    (lens) => new Send("review", { draft: state.draft, lens, round: state.attempts }),
  );
}

async function review(payload: { draft: string; lens: string; round: number }) {
  const r = await reviewModel.invoke(`Review via the ${payload.lens} lens…`);
  return { reviews: [{ lens: payload.lens, round: payload.round, result: r.content }] };
}
```

Same pitfall as Python: **an append-reduced field cannot be cleared by returning `[]`** — the reducer concatenates. Round-tag on write, filter on read.

```ts
function synthesise(state: S): Partial<S> {
  const current = state.reviews.filter((r) => r.round === state.attempts);
  const fails = current.filter((r) => r.result.toUpperCase().startsWith("FAIL"));
  return {
    verdict: fails.length <= Math.floor(current.length / 2) ? "PASS" : "FAIL",
    feedback: fails.map((r) => `[${r.lens}] ${r.result}`).join("\n"),
  };
}
```

## Bounds

```ts
const MAX_ATTEMPTS = 3;
const BUDGET_TOKENS = 20_000;

function gate(state: S): string {
  if (state.verdict === "PASS") return "format";
  if (state.attempts >= MAX_ATTEMPTS) return "format";   // ship best-effort
  if (state.tokensSpent > BUDGET_TOKENS) return "format";
  return "worker";
}

await graph.invoke(inputs, { recursionLimit: 25 });
```

## Failure isolation

```ts
async function riskyNode(state: S): Promise<Partial<S>> {
  try {
    return { notes: [await fetchSource(state.url)] };
  } catch (e) {
    return { errors: [`fetch failed: ${e instanceof Error ? e.message : e}`] };
  }
}
```

Catch **inside** the node. An exception escaping a fanned-out branch aborts siblings, which is the failure isolation criterion silently not being met.

## Checkpointing

```ts
import { MemorySaver } from "@langchain/langgraph";
const graph = builder.compile({ checkpointer: new MemorySaver() });
await graph.invoke(inputs, {
  configurable: { thread_id: "run-001" },
  recursionLimit: 25,
});
```

`MemorySaver` is development only — state vanishes on restart. Use the SQLite or Postgres saver in production.

## Verify

```ts
const mermaid = (await graph.getGraphAsync()).drawMermaid();
console.log(mermaid);
```

Assert this against the Phase 2 design rather than reading it. Node's built-in test runner is enough:

```ts
import { test } from "node:test";
import assert from "node:assert";

test("topology matches design", async () => {
  const edges = edgeSet((await graph.getGraphAsync()).drawMermaid());
  assert.deepEqual(edges, edgeSet(DESIGN_MERMAID));
});
```

## TypeScript-specific pitfalls

- **Missing reducer on a fan-in field.** The default is replace, and TS will not warn you. This is the number-one bug on this runtime.
- **`await` forgotten in a node.** Returning a `Promise` where an update is expected fails at runtime, not compile time, because the node's return type is loose.
- **Mutating `state` directly.** Nothing stops you at compile time. Return `Partial<S>` and never assign to `state.x`.
- **Streaming.** `graph.stream()` yields per-node updates and is usually what you want for a UI; `invoke` only resolves at the end.
