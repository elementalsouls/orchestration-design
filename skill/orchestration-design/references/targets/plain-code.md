# Target: plain code (no framework)

**Choose this more often than feels natural.** A framework earns its place at real fan-out with durable state, complex routing, or a need for replay and checkpointing. Below that, it is a dependency, a vocabulary, and an abstraction layer between you and a bug.

Pick plain code when any of these hold:

- fewer than ~5 nodes and at most one conditional edge
- no model calls at all (ETL, batch, build pipelines)
- the team will not adopt a new dependency, or the deploy target makes it awkward
- you need this working today and the design is simple
- it is a prototype whose shape is still moving

The design object from Phase 2 does not change. Nodes become functions, edges become control flow, state becomes a dataclass, bounds become loop conditions. **All four still exist and all four are still load-bearing** — that is the entire point. Losing them is how "just a script" becomes the mess in six months.

---

## State: a dataclass, one writer per field

```python
from dataclasses import dataclass, field

@dataclass
class State:
    task: str                                  # caller       replace
    draft: str = ""                            # writer       replace
    verdict: str = ""                          # reviewer     replace
    feedback: str = ""                         # reviewer     replace
    attempts: int = 0                          # writer       counter
    tokens_spent: int = 0                      # any model call, sum
    notes: list[str] = field(default_factory=list)   # append
    errors: list[str] = field(default_factory=list)  # append
```

Keep the ownership comments. They are the same table Phase 2 produced, and they are the thing that stops two functions writing `draft`.

Nodes take state and **return an update**, exactly as in a framework — do not mutate in place. It keeps nodes independently testable and makes adding a checkpointer later a small change rather than a rewrite.

```python
def writer(s: State) -> dict:
    r = model.invoke(prompt_for(s))
    return {"draft": r.content, "attempts": s.attempts + 1,
            "tokens_spent": r.usage["total_tokens"]}

# Reducers are DECLARED, copied from the Phase 2 state table. Never inferred.
# `+` covers TWO of the four: append for lists, sum for ints. Both go here.
APPEND = {"notes", "errors", "tokens_spent"}     # everything else replaces


def apply(s: State, update: dict) -> State:
    for k, v in update.items():
        setattr(s, k, getattr(s, k) + v if k in APPEND else v)
    return s
```

That `apply` function is your reducer layer. Six lines, and it is the piece frameworks charge the most abstraction for.

### Never infer the reducer from the type

The tempting version is one line shorter and quietly wrong:

```python
# WRONG — "it's a list, so append"
setattr(s, k, cur + v if isinstance(cur, list) else v)
```

Plenty of list fields are **replace**: a set of per-item results the owner
rewrites whole on each pass, a ranked list, a parsed batch. Type-inference
appends them instead, so round 2 stacks on top of round 1 — **the same item
appears twice, at two different values** — and nothing raises. It surfaces as a
duplicate-data bug three files from the cause.

`APPEND` is literally the append-reduced column of your Phase 2 state table.
Copying it across is the reason you wrote the table down.

**Then guard it with a count.** Silent duplication and silent loss are the two
failures a wrong reducer produces, and neither is visible without one:

```python
assert len(s.results) == len(s.items) - len(s.errors)
assert len({r["id"] for r in s.results}) == len(s.results)   # no duplicates
```

## Pattern A — sequential

```python
state = State(task=task)
for node in (collect, classify, draft, tighten):
    state = apply(state, node(state))
```

If this is your whole design, you did not need a framework and you may not have needed a graph.

## Pattern B — bounded reviewer loop

```python
MAX_ATTEMPTS, BUDGET = 3, 20_000

while state.attempts < MAX_ATTEMPTS and state.tokens_spent < BUDGET:
    state = apply(state, writer(state))
    state = apply(state, reviewer(state))       # read-only, different model
    if state.verdict.startswith("PASS"):
        break
else:
    state.errors.append("bounds exhausted before PASS")
```

Both bounds live in the loop condition, so neither can be forgotten. Python's `while/else` is doing real work here: the `else` runs only when the loop exits without `break`, which is exactly the exhaustion terminal. Decide deliberately whether that path ships the draft with a caveat or routes to a human.

## Pattern C — fan-out/fan-in with isolation

```python
import asyncio

async def run_one(item) -> dict:
    try:
        return {"notes": [await process(item)]}
    except Exception as e:                      # isolate: never abort siblings
        return {"errors": [f"{item}: {e}"]}

updates = await asyncio.gather(*(run_one(i) for i in items))
for u in updates:
    state = apply(state, u)

assert len(state.notes) + len(state.errors) == len(items)
```

Three things this gets right that hand-rolled fan-out usually gets wrong:

- **`return_exceptions` is not needed** because each branch catches its own — isolation belongs inside the branch, not at the gather.
- **The assertion is the guard against silent loss.** Parallel result loss is invisible without a count check.
- **Branches receive their item, not shared state.** Reading shared state from a branch is a race that passes in testing.

Bound concurrency when the work hits a rate-limited resource, or the parallelism is fictional:

```python
sem = asyncio.Semaphore(8)
async def run_one(item):
    async with sem:
        ...
```

## Bounds without a framework

| Bound | Plain-code form |
|---|---|
| Attempt counter | loop condition on `state.attempts` |
| Global step limit | a step counter incremented in the driver, raising past a cap |
| Spend budget | `state.tokens_spent` in the loop condition |
| Per-node timeout | `asyncio.wait_for(node(state), timeout=n)` |
| Retry | a small `for _ in range(3)` with backoff, inside the node |

## Checkpointing, if you need it

The moment "resume instead of restart" matters, you need persistence — but not necessarily a framework:

```python
import json, pathlib

def save(state: State, run_id: str):
    pathlib.Path(f"runs/{run_id}.json").write_text(json.dumps(state.__dict__))

def load(run_id: str) -> State | None:
    p = pathlib.Path(f"runs/{run_id}.json")
    return State(**json.loads(p.read_text())) if p.exists() else None
```

Save after each node. A crashed run resumes from the last completed one. If you find yourself needing replay, versioned state, or distributed workers on top of this, *that* is the signal to move to `durable-workflow.md` — not before.

## Verify

Phase 4 still applies. Without an emitted diagram, assert the topology directly:

```python
def test_reviewer_never_edits_draft():
    s = State(task="x", draft="original")
    apply(s, reviewer(s))
    assert s.draft == "original"        # read-only, proven not claimed

def test_loop_terminates_when_reviewer_always_fails():
    s = run(always_fail_reviewer, task="x")
    assert s.attempts == MAX_ATTEMPTS   # bound is live, not decorative
```

These two tests catch the two failure modes that actually bite.

## When to graduate

Move to a framework when you hit: fan-out large enough that you need managed concurrency and retries, durable state across process restarts, human-in-the-loop pauses mid-run, or routing complex enough that the control flow is harder to read than a graph declaration would be. Until then, the plain version is smaller, faster to debug, and has no upgrade treadmill.
