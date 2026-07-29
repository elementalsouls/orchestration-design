# Target: LangGraph (Python)

**Read this only after Phase 2 produced a design and Phase 3a chose this target.** This file implements a design; it does not decide one. If you have not yet run the loop-first gate, go back — a framework is the wrong place to discover you did not need a graph.

Choose this target when: Python, LLM orchestration, real fan-out or durable state, and a team willing to take the dependency. For three sequential steps or no model calls at all, `plain-code.md` is the better answer.

Current as of mid-2026. Install: `pip install -U langgraph langchain`.
Breaking changes vs old tutorials: `set_entry_point()`/`set_finish_point()` are gone — use `add_edge(START, ...)` / `add_edge(..., END)`. `ToolExecutor` → `ToolNode`.

Every pattern below is written to run offline with deterministic stub models and assert its own behaviour — build them that way, so they cannot silently rot.

## Contents
1. Core imports & state schema
2. Pattern A — sequential pipeline
3. Pattern B — reviewer node with bounded reject loop (the canonical pattern)
4. Pattern C — fan-out/fan-in with the Send API
5. Pattern D — multi-reviewer panel with synthesis (judge panel)
6. Guardrails: spend caps, recursion limits, failure isolation
7. Checkpointing & retries
8. Pitfalls checklist

## 1. Core imports & state schema

```python
from typing import Annotated
from typing_extensions import TypedDict
import operator

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    # reducer = how concurrent/sequential updates merge
    messages: Annotated[list, add_messages]     # append messages
    notes: Annotated[list[str], operator.add]   # append lists (needed for fan-in!)
    draft: str                                  # replace (last write wins)
    verdict: str                                # written ONLY by reviewer
    attempts: int                               # loop-back counter
    tokens_spent: int
```

Design rule: document which node writes each field. A field written by more than one node needs a reducer or it's a state-drift bug waiting to happen. Nodes receive state and **return an update dict** — they never mutate state in place:

```python
def writer(state: State) -> dict:
    draft = writer_model.invoke(...).content
    return {"draft": draft, "attempts": state["attempts"] + 1}
```

## 2. Pattern A — sequential pipeline

```python
builder = StateGraph(State)
builder.add_node("research", research)
builder.add_node("write", writer)
builder.add_edge(START, "research")
builder.add_edge("research", "write")
builder.add_edge("write", END)
graph = builder.compile()
```

## 3. Pattern B — reviewer with a bounded reject loop

The single highest-value node in most graphs. Rules: the reviewer is **read-only** (returns a verdict, never edits the draft), ideally a **different model** than the producer, and the loop-back edge is **bounded by an attempt counter**.

```python
MAX_ATTEMPTS = 3

def reviewer(state: State) -> dict:
    # read-only: looks at draft, writes only its own fields
    verdict = review_model.invoke(
        f"Score this draft PASS/FAIL with reasons:\n{state['draft']}"
    ).content
    return {"verdict": verdict}

def route_after_review(state: State) -> str:
    if "PASS" in state["verdict"]:
        return "ship"
    if state["attempts"] >= MAX_ATTEMPTS:
        return "ship"        # or a "flag_for_human" node — never loop forever
    return "write"

builder.add_node("review", reviewer)
builder.add_conditional_edges("review", route_after_review,
                              {"ship": END, "write": "write"})
builder.add_edge("write", "review")
```

## 4. Pattern C — fan-out/fan-in with Send

For the same work over N independent items. Fan-in fields **must** have an append reducer (`operator.add`), otherwise parallel writes collide.

```python
from langgraph.types import Send

def fan_out(state: State):
    # returns a list of Send objects → one "summarize" run per item, in parallel
    return [Send("summarize", {"item": it}) for it in state["items"]]

def summarize(payload: dict) -> dict:
    return {"notes": [do_one(payload["item"])]}   # appended via operator.add

def merge(state: State) -> dict:
    return {"draft": combine(state["notes"])}

builder.add_node("summarize", summarize)
builder.add_node("merge", merge)
builder.add_conditional_edges("plan", fan_out, ["summarize"])
builder.add_edge("summarize", "merge")   # implicit fan-in barrier
```

### Pitfall: `Send` payloads do not survive to a second node in the branch

`Send` overrides the input of **only the node it targets**. If a branch is two
nodes deep (`extract` → `answer`), a plain edge from `extract` to `answer` gives
`answer` the *global* state, not the per-item payload — every branch silently
answers the same item. A conditional edge does not help either; the router also
sees global state.

For a multi-node branch, have the first node return a `Command` that carries the
payload forward, and declare `destinations` so the compiled diagram still shows
the edge:

```python
from langgraph.types import Command, Send

def extract(payload: dict) -> Command:
    questions = parse(payload["doc"])
    return Command(update={"questions": [questions]},
                   goto=[Send("answer", {"doc": payload["doc"],
                                         "questions": questions})])

# without destinations=, the drawn graph drops extract->answer and invents
# a bogus extract->__end__ edge, so Phase 4 verification fails on a lie
builder.add_node("extract", extract, destinations=("answer",))
```

Failure isolation falls out cleanly: a branch that fails returns a `Command`
with **no** `goto` and simply stops, writing to `errors` on the way out. The
siblings are untouched. `04-fanout-fanin/graph.py` is the worked version.

## 5. Pattern D — multi-reviewer panel with synthesis (judge panel)

Upgrade of Pattern B for higher-stakes work: the worker's output fans out to N
reviewers in parallel (each with a different lens — correctness, clarity,
completeness), a synthesise node merges their verdicts, and one bounded Pass?
gate either ships or loops feedback back to the worker.

Design notes that make this pattern work:
- **Resident vs ephemeral agents.** The worker keeps context across iterations
  (feedback lands with memory of the previous attempt). Reviewers are best
  *ephemeral* — fresh eyes each round, no sunk-cost attachment to the draft.
  In LangGraph terms: the worker's history lives in state; reviewer nodes get
  only the current draft, never the conversation history.
- Each reviewer appends to a shared `reviews` field via `operator.add` — never
  a plain field, or parallel writes collide.
- Synthesise is the only node that writes `verdict`/`feedback`.
- The Pass?→no edge is bounded by an attempt counter, same as Pattern B.

```python
class State(TypedDict):
    task: str
    draft: str                                    # written only by worker
    reviews: Annotated[list[dict], operator.add]  # parallel reviewer fan-in
    feedback: str                                 # written only by synthesise
    verdict: str                                  # written only by synthesise
    attempts: int

LENSES = ["correctness", "clarity", "completeness"]

def fan_out_reviews(state: State):
    # payload carries ONLY what the branch needs, plus the round tag
    return [Send("review", {"draft": state["draft"], "lens": lens,
                            "round": state["attempts"]})
            for lens in LENSES]

def review(payload: dict) -> dict:               # ephemeral: sees only the draft
    r = review_model.invoke(
        f"Review via the {payload['lens']} lens. PASS/FAIL + reasons:\n{payload['draft']}")
    return {"reviews": [{"lens": payload["lens"], "round": payload["round"],
                         "result": r.content}]}

def synthesise(state: State) -> dict:
    # `reviews` is append-reduced and accumulates across rounds, so filter to
    # the current round rather than trying to clear it (see the pitfall below)
    current = [r for r in state["reviews"] if r["round"] == state["attempts"]]
    fails = [r for r in current if r["result"].upper().startswith("FAIL")]
    verdict = "PASS" if len(fails) <= len(current) // 2 else "FAIL"  # majority
    return {"verdict": verdict,
            "feedback": "\n".join(f"[{r['lens']}] {r['result']}" for r in fails)}

def gate(state: State) -> str:
    if state["verdict"] == "PASS" or state["attempts"] >= MAX_ATTEMPTS:
        return "format"      # ship (with caveats if attempts exhausted)
    return "work"

builder.add_conditional_edges("work", fan_out_reviews, ["review"])
builder.add_edge("review", "synthesise")
builder.add_conditional_edges("synthesise", gate, {"format": "format", "work": "work"})
```

### Pitfall: you cannot clear an append-reduced field

The obvious-looking way to reset the panel between rounds does **not** work:

```python
return {"verdict": verdict, "reviews": []}   # WRONG — operator.add appends [],
                                             # it does not replace the list
```

`operator.add` merges by concatenation, so returning `[]` is a no-op and round 2
would synthesise over round 1's verdicts as well. Round-tag on write and filter
on read, as above. `05-judge-panel/graph.py` is the working version.

## 6. Guardrails: spend caps, recursion limits, failure isolation

```python
# hard step bound on the whole run
result = graph.invoke(inputs, config={"recursion_limit": 25})

# spend cap in state — checked by routers
def route_after_review(state: State) -> str:
    if state["tokens_spent"] > BUDGET_TOKENS:
        return "ship"   # stop spending; surface partial result
    ...

# failure isolation: a risky node catches its own errors
def fetch(state: State) -> dict:
    try:
        return {"notes": [fetch_source(state["url"])]}
    except Exception as e:
        return {"errors": [f"fetch failed: {e}"]}   # downstream routes around it
```

Also available: `graph.compile(...)` + node-level `retry_policy=RetryPolicy(max_attempts=3)` on `add_node` for transient failures.

## 7. Checkpointing & retries

```python
from langgraph.checkpoint.memory import MemorySaver          # dev only
from langgraph.checkpoint.sqlite import SqliteSaver          # simple persistence
graph = builder.compile(checkpointer=MemorySaver())
config = {"configurable": {"thread_id": "run-001"}, "recursion_limit": 25}
graph.invoke(inputs, config)
```

Never ship MemorySaver to production — state vanishes on restart. Use SqliteSaver/Postgres. Checkpointing means a failed node can be retried from the last good state instead of rerunning the whole graph.

## 8. Pitfalls checklist

- [ ] Any field written by 2+ nodes has a reducer (or split it into per-node fields)
- [ ] Every loop-back edge has an attempt counter AND a recursion_limit backstop
- [ ] Reviewer never edits work product; producer never reads its own verdict logic
- [ ] Fan-in fields use `operator.add` / `add_messages`, not plain replace
- [ ] Nodes return update dicts; nothing mutates `state[...]` in place
- [ ] Budget/token field exists and at least one router checks it
- [ ] `graph.get_graph().draw_mermaid()` matches the paper design
- [ ] Old-API calls (`set_entry_point`, `ToolExecutor`) don't appear anywhere
