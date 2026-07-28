"""Planner -> Plan Reviewer -> resident Worker -> parallel reviewer panel ->
Synthesise -> Pass? gate -> format_output -> END.

LangGraph v1.0 reference implementation (Pattern D: multi-reviewer judge panel,
plus a bounded plan-review loop after the Planner).

Runs with deterministic stub models by default (no API key needed; stub
reviewers FAIL round 1 and PASS round 2 so the reject loop is exercised).
If ANTHROPIC_API_KEY is set, real Anthropic models are used instead.
"""

from __future__ import annotations

import operator
import os
from typing import Annotated, Any

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

# ---------------------------------------------------------------- bounds ----
MAX_ATTEMPTS = 3        # worker <-> reviewer-panel loop cap
MAX_PLAN_ATTEMPTS = 2   # planner <-> plan-reviewer loop cap (one bounded replan)
RECURSION_LIMIT = 25    # hard step bound on the whole run
BUDGET_TOKENS = 20_000  # token budget checked by the Pass? gate

LENSES = ["correctness", "clarity", "completeness"]

# ---------------------------------------------------------------- models ----
USE_REAL_MODELS = bool(os.environ.get("ANTHROPIC_API_KEY"))

if USE_REAL_MODELS:
    from langchain_anthropic import ChatAnthropic

    planner_model = ChatAnthropic(model="claude-sonnet-4-5", max_tokens=1024)
    worker_model = ChatAnthropic(model="claude-sonnet-4-5", max_tokens=2048)
    # reviewers deliberately use a different model than the producer
    review_model = ChatAnthropic(model="claude-haiku-4-5", max_tokens=512)
    format_model = ChatAnthropic(model="claude-haiku-4-5", max_tokens=512,
                                 temperature=0)
else:
    class _Stub:
        """Deterministic stand-in with a .invoke(...).content interface."""

        def __init__(self, fn):
            self._fn = fn

        def invoke(self, prompt: Any):
            class R:
                content = self._fn(str(prompt))
                usage_metadata = {"total_tokens": 50}
            return R()

    def _plan(prompt: str) -> str:
        """Thin plan for an under-specified task; a real one once told to replan.

        This is what makes the plan-reject branch reachable without flipping a
        flag: the planner is genuinely worse when the task is vague.
        """
        if "Replan" in prompt:
            return ("1. Restate the goal concretely\n2. Draft against it\n"
                    "3. Check the draft answers the restated goal")
        if "make it better" in prompt.lower():
            return "1. Improve it\n2. Ship"
        return "1. Understand the task\n2. Draft\n3. Refine"

    planner_model = _Stub(_plan)
    worker_model = _Stub(
        lambda p: ("REVISED DRAFT (v2): a thorough, clear, complete answer "
                   "addressing all feedback.") if "FEEDBACK" in p
        else "DRAFT (v1): a first attempt at the task.")
    # Stub reviewers FAIL round 1 (draft v1), PASS round 2 (v2) -> the
    # reject loop fires exactly once in the default demo run.
    review_model = _Stub(
        lambda p: "PASS: looks good on this lens." if "v2" in p
        else "FAIL: draft v1 is too thin on this lens.")
    format_model = _Stub(lambda p: "== FINAL ==\n" + p.split("POLISH:")[-1].strip())


def _tokens(resp: Any) -> int:
    meta = getattr(resp, "usage_metadata", None) or {}
    return meta.get("total_tokens", 0)


# ----------------------------------------------------------------- state ----
class State(TypedDict):
    # field                          owner (writer) node        reducer
    task: str                        # caller input              replace
    plan: str                        # planner only              replace
    plan_verdict: str                # plan_reviewer only        replace
    plan_attempts: int               # planner only              replace (counter)
    worker_messages: Annotated[list[str], operator.add]
    #                                # worker only               operator.add —
    #                                # the worker's RESIDENT history across rounds
    draft: str                       # worker only               replace
    attempts: int                    # worker only               replace (counter)
    reviews: Annotated[list[dict], operator.add]
    #                                # review (N parallel) only  operator.add —
    #                                # fan-in; each entry tagged {"round": attempts}
    #                                # so synthesise counts only the current round
    verdict: str                     # synthesise only           replace
    feedback: str                    # synthesise only           replace
    tokens_spent: Annotated[int, operator.add]
    #                                # every model-calling node  operator.add (sum)
    errors: Annotated[list[str], operator.add]
    #                                # any failing node          operator.add
    final: str                       # format_output only        replace


# ----------------------------------------------------------------- nodes ----
def planner(state: State) -> dict:
    note = ""
    if state.get("plan_verdict", "").startswith("REJECT"):
        note = f"\nPrevious plan was rejected: {state['plan_verdict']}. Replan."
    r = planner_model.invoke(f"Make a short numbered plan for: {state['task']}{note}")
    return {"plan": r.content,
            "plan_attempts": state.get("plan_attempts", 0) + 1,
            "tokens_spent": _tokens(r)}


def plan_reviewer(state: State) -> dict:
    """Read-only: reviews the plan, writes only its verdict."""
    if USE_REAL_MODELS:
        r = review_model.invoke(
            "You are a read-only plan reviewer. Reply APPROVE or REJECT: <reason>.\n"
            f"Task: {state['task']}\nPlan:\n{state['plan']}")
        return {"plan_verdict": r.content, "tokens_spent": _tokens(r)}
    # stub rule: a plan with fewer than 3 steps is too thin to check work against
    steps = [ln for ln in state["plan"].splitlines() if ln.strip()]
    verdict = ("APPROVE" if len(steps) >= 3
               else f"REJECT: only {len(steps)} steps; too thin to verify against")
    return {"plan_verdict": verdict, "tokens_spent": 10}


def route_after_plan_review(state: State) -> str:
    if state["plan_verdict"].startswith("REJECT") and \
            state["plan_attempts"] < MAX_PLAN_ATTEMPTS:
        return "planner"       # one bounded replan
    return "worker"            # approved, or replan budget exhausted


def worker(state: State) -> dict:
    """Resident agent: its history lives in state and grows across rounds."""
    history = "\n".join(state.get("worker_messages", []))
    feedback = state.get("feedback", "")
    prompt = (f"TASK: {state['task']}\nPLAN: {state['plan']}\n"
              f"HISTORY:\n{history}\n"
              + (f"FEEDBACK to address:\n{feedback}\n" if feedback else "")
              + "Write the next draft.")
    try:
        r = worker_model.invoke(prompt)
        draft = r.content
        spent = _tokens(r)
        err: list[str] = []
    except Exception as e:  # failure isolation: never poison downstream state
        draft = state.get("draft", "")
        spent = 0
        err = [f"worker failed on attempt {state.get('attempts', 0) + 1}: {e}"]
    attempt = state.get("attempts", 0) + 1
    return {"draft": draft,
            "attempts": attempt,
            "worker_messages": [f"[attempt {attempt}] feedback={feedback!r} "
                                f"-> draft={draft[:120]!r}"],
            "tokens_spent": spent,
            "errors": err}


def fan_out_reviews(state: State) -> list[Send]:
    """Fan out to N ephemeral reviewers: payload is ONLY the current draft
    (+ lens + round tag) — never the worker's history."""
    return [Send("review", {"draft": state["draft"], "lens": lens,
                            "round": state["attempts"]})
            for lens in LENSES]


def review(payload: dict) -> dict:
    """Ephemeral reviewer: fresh eyes, sees only the current draft."""
    r = review_model.invoke(
        f"Review this draft strictly through the {payload['lens']} lens. "
        f"Reply 'PASS: ...' or 'FAIL: <what to fix>'.\nDRAFT:\n{payload['draft']}")
    return {"reviews": [{"lens": payload["lens"], "round": payload["round"],
                         "result": r.content}],
            "tokens_spent": _tokens(r)}


def synthesise(state: State) -> dict:
    """Majority verdict + merged feedback, counting ONLY the current round."""
    current = [r for r in state["reviews"] if r["round"] == state["attempts"]]
    fails = [r for r in current if r["result"].upper().startswith("FAIL")]
    verdict = "PASS" if len(fails) <= len(current) // 2 else "FAIL"
    feedback = "\n".join(f"[{r['lens']}] {r['result']}" for r in fails)
    return {"verdict": verdict, "feedback": feedback}


def gate(state: State) -> str:
    """Pass? gate: ship on PASS, or when bounds/budget are exhausted."""
    if state["verdict"] == "PASS":
        return "format_output"
    if state["attempts"] >= MAX_ATTEMPTS:
        return "format_output"          # ship best effort, never loop forever
    if state["tokens_spent"] > BUDGET_TOKENS:
        return "format_output"          # token budget exhausted
    return "worker"


def format_output(state: State) -> dict:
    """Deterministic-ish final polish (the diagram's 'turn into haiku' step)."""
    r = format_model.invoke(f"POLISH: {state['draft']}")
    caveat = "" if state["verdict"] == "PASS" else \
        "\n[NOTE: shipped after exhausting review attempts/budget]"
    return {"final": r.content + caveat, "tokens_spent": _tokens(r)}


# ----------------------------------------------------------------- graph ----
builder = StateGraph(State)
builder.add_node("planner", planner)
builder.add_node("plan_reviewer", plan_reviewer)
builder.add_node("worker", worker)
builder.add_node("review", review)
builder.add_node("synthesise", synthesise)
builder.add_node("format_output", format_output)

builder.add_edge(START, "planner")
builder.add_edge("planner", "plan_reviewer")
builder.add_conditional_edges("plan_reviewer", route_after_plan_review,
                              {"planner": "planner", "worker": "worker"})
builder.add_conditional_edges("worker", fan_out_reviews, ["review"])
builder.add_edge("review", "synthesise")     # implicit fan-in barrier
builder.add_conditional_edges("synthesise", gate,
                              {"format_output": "format_output",
                               "worker": "worker"})
builder.add_edge("format_output", END)

graph = builder.compile()


def run(task: str) -> dict:
    inputs = {"task": task,
              "plan_attempts": 0, "attempts": 0, "tokens_spent": 0,
              "worker_messages": [], "reviews": [], "errors": [],
              "feedback": "", "verdict": "", "plan_verdict": ""}
    return graph.invoke(inputs, config={"recursion_limit": RECURSION_LIMIT})


def _trace(label: str, result: dict) -> None:
    print(f"=== {label} ===")
    print(f"task           : {result['task']!r}")
    print(f"plan attempts  : {result['plan_attempts']}")
    print(f"plan verdict   : {result['plan_verdict']}")
    print(f"plan           : {result['plan'].splitlines()}")
    print(f"worker attempts: {result['attempts']}")
    for m in result["worker_messages"]:
        print("  ", m)
    for r in result["reviews"]:
        print(f"  round {r['round']} [{r['lens']}] {r['result']}")
    print(f"verdict: {result['verdict']}  tokens_spent: {result['tokens_spent']}")
    if result["errors"]:
        print("errors:", result["errors"])
    print("--- final ---")
    print(result["final"])
    print()


if __name__ == "__main__":
    print("=== compiled mermaid ===")
    print(graph.get_graph().draw_mermaid())
    print(f"models: {'REAL Anthropic' if USE_REAL_MODELS else 'stub (deterministic)'}\n")

    # Scenario A — well-specified task: plan approved first time, but the
    # reviewer panel rejects draft v1, so the WORKER loop fires once.
    a = run("Explain why the sky is blue")
    _trace("scenario A — plan approved, worker reject loop fires once", a)

    assert a["plan_attempts"] == 1, "plan should be approved on the first pass"
    assert a["plan_verdict"] == "APPROVE"
    assert a["attempts"] == 2, "expected worker reject loop to fire exactly once"
    assert a["verdict"] == "PASS"

    # Scenario B — under-specified task: the first plan is too thin, so the
    # PLAN-REJECT branch fires. Without this the branch is wired but unproven.
    b = run("make it better")
    _trace("scenario B — plan rejected once, then replanned", b)

    assert b["plan_attempts"] == 2, "expected exactly one replan"
    assert b["plan_verdict"] == "APPROVE", "replan should be approved"
    assert b["plan_attempts"] <= MAX_PLAN_ATTEMPTS, "replan bound exceeded"
    assert b["verdict"] == "PASS"

    print("OK: worker reject loop fired once (A); plan-reject branch fired "
          "once and was bounded (B). Every conditional edge is now exercised.")
