"""write_postmortem -> review -> Pass? gate -> publish | flag_for_human -> END.

LangGraph v1.0 reference implementation (Pattern B: single read-only reviewer,
bounded reject loop).

A customer-facing incident postmortem is drafted by a producer model and graded
by ONE read-only reviewer running a different, cheaper model. The reviewer never
edits the draft — it returns PASS, or FAIL plus reasons that loop back to the
writer. The loop is bounded twice over (attempt counter + token budget) and when
the bounds run out it routes to `flag_for_human` instead of publishing an
unreviewed postmortem. Shipping silently on bound-exhaustion is the classic bug
in this pattern: the safe branch exists but is never reachable in practice.

Both branches are exercised on every run — see the two scenarios in __main__.

Runs with deterministic stub models by default (no API key needed).
If ANTHROPIC_API_KEY is set, real Anthropic models are used instead.
"""

from __future__ import annotations

import operator
import os
from typing import Annotated, Any

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

# ---------------------------------------------------------------- bounds ----
MAX_ATTEMPTS = 3        # writer <-> reviewer loop cap
RECURSION_LIMIT = 25    # hard step bound on the whole run
BUDGET_TOKENS = 4_000   # token budget checked by the Pass? gate

# What the reviewer requires before a postmortem may go out to customers.
REQUIRED_SECTIONS = ["## Root cause", "## Customer impact"]

# ---------------------------------------------------------------- models ----
USE_REAL_MODELS = bool(os.environ.get("ANTHROPIC_API_KEY"))

if USE_REAL_MODELS:
    from langchain_anthropic import ChatAnthropic

    writer_model = ChatAnthropic(model="claude-sonnet-4-5", max_tokens=2048)
    # The reviewer is deliberately a different, cheaper model than the
    # producer: a model never grades its own homework.
    review_model = ChatAnthropic(model="claude-haiku-4-5", max_tokens=512,
                                 temperature=0)
else:
    class _Stub:
        """Deterministic stand-in with a .invoke(...).content interface."""

        def __init__(self, fn):
            self._fn = fn

        def invoke(self, prompt: Any):
            class R:
                content = self._fn(str(prompt))
                usage_metadata = {"total_tokens": 60}
            return R()

    def _stub_writer(prompt: str) -> str:
        """Writes only what the FACTS support — like a well-behaved model that
        refuses to invent a root cause it was not given.

        Rigging: draft v1 (no FEEDBACK yet) always omits '## Customer impact',
        so round 1 always FAILs. v2+ adds it. '## Root cause' appears only if
        the facts actually contain one — which is what separates the two demo
        scenarios below."""
        facts = [l[2:].strip() for l in prompt.splitlines() if l.startswith("- ")]
        cause = next((f for f in facts if f.lower().startswith("root cause:")), None)
        revised = "FEEDBACK" in prompt
        out = ["## What happened",
               " ".join(f for f in facts if f is not cause) or "Service degradation."]
        if cause:
            out += ["## Root cause", cause]
        if revised:
            out += ["## Customer impact",
                    "Requests from affected workspaces failed during the window; "
                    "no data was lost and no action is required from you."]
        return "\n".join(out)

    def _stub_reviewer(prompt: str) -> str:
        """Read-only: looks at the draft only, names what is missing. Note the
        split on 'DRAFT:' — the instructions above it also mention the required
        section names, and grading those would pass everything."""
        draft = prompt.split("DRAFT:", 1)[-1]
        missing = [s for s in REQUIRED_SECTIONS if s not in draft]
        if not missing:
            return "PASS: publishable — cause and impact are both stated."
        return ("FAIL: not publishable, missing section(s): "
                + ", ".join(missing) + ".")

    writer_model = _Stub(_stub_writer)
    review_model = _Stub(_stub_reviewer)


def _tokens(resp: Any) -> int:
    meta = getattr(resp, "usage_metadata", None) or {}
    return meta.get("total_tokens", 0)


# ----------------------------------------------------------------- state ----
class State(TypedDict):
    # field                          owner (writer) node        reducer
    incident: str                    # caller input              replace
    facts: list[str]                 # caller input              replace
    draft: str                       # write_postmortem only     replace
    attempts: int                    # write_postmortem only     replace (counter)
    verdict: str                     # review only               replace
    feedback: str                    # review only               replace
    review_log: Annotated[list[str], operator.add]
    #                                # review only               operator.add —
    #                                # one entry per round, kept for the audit
    #                                # trail (you can't clear an add-reduced field)
    tokens_spent: Annotated[int, operator.add]
    #                                # writer + reviewer         operator.add (sum)
    errors: Annotated[list[str], operator.add]
    #                                # any failing node          operator.add
    status: str                      # publish OR flag_for_human replace
    #                                # exactly one terminal node runs per invoke
    final: str                       # publish OR flag_for_human replace


# ----------------------------------------------------------------- nodes ----
def write_postmortem(state: State) -> dict:
    """Producer. Rewrites the whole draft each round from facts + feedback."""
    facts = "\n".join(f"- {f}" for f in state["facts"])
    feedback = state.get("feedback", "")
    prompt = (f"INCIDENT: {state['incident']}\nFACTS:\n{facts}\n"
              + (f"FEEDBACK from review to address:\n{feedback}\n" if feedback else "")
              + "Write a customer-facing postmortem. Do not invent facts.")
    try:
        r = writer_model.invoke(prompt)
        draft, spent, errs = r.content, _tokens(r), []
    except Exception as e:  # failure isolation: keep the last good draft
        draft, spent = state.get("draft", ""), 0
        errs = [f"writer failed on attempt {state.get('attempts', 0) + 1}: {e}"]
    return {"draft": draft,
            "attempts": state.get("attempts", 0) + 1,
            "tokens_spent": spent,
            "errors": errs}


def review(state: State) -> dict:
    """READ-ONLY reviewer. Sees the draft, writes only verdict/feedback/log —
    it must never touch `draft`, or the producer stops owning its own output."""
    r = review_model.invoke(
        "You are a read-only reviewer for customer-facing incident postmortems. "
        f"It is not publishable unless it contains {REQUIRED_SECTIONS}. "
        "Reply 'PASS: <why>' or 'FAIL: <what is missing>'.\n"
        f"DRAFT:\n{state['draft']}")
    verdict = "PASS" if r.content.upper().startswith("PASS") else "FAIL"
    return {"verdict": verdict,
            "feedback": "" if verdict == "PASS" else r.content,
            "review_log": [f"[attempt {state['attempts']}] {r.content}"],
            "tokens_spent": _tokens(r)}


def gate(state: State) -> str:
    """Pass? gate. Publish only on a real PASS; every exhausted-bound path
    goes to a human, never straight to the customer."""
    if state["verdict"] == "PASS":
        return "publish"
    if state["attempts"] >= MAX_ATTEMPTS:
        return "flag_for_human"         # attempt bound hit
    if state["tokens_spent"] > BUDGET_TOKENS:
        return "flag_for_human"         # spend bound hit
    return "write_postmortem"           # bounded retry with feedback


def publish(state: State) -> dict:
    """Terminal: the reviewer passed it."""
    return {"status": "published",
            "final": f"# {state['incident']}\n\n{state['draft']}"}


def flag_for_human(state: State) -> dict:
    """Terminal: bounds exhausted. Hand the best effort plus the full review
    trail to a person — this branch is the entire reason the gate exists."""
    trail = "\n".join(state["review_log"])
    return {"status": "needs_human",
            "final": (f"# [UNPUBLISHED] {state['incident']}\n"
                      f"Blocked after {state['attempts']} attempts "
                      f"({state['tokens_spent']} tokens). Review trail:\n{trail}\n\n"
                      f"Best effort draft:\n{state['draft']}")}


# ----------------------------------------------------------------- graph ----
builder = StateGraph(State)
builder.add_node("write_postmortem", write_postmortem)
builder.add_node("review", review)
builder.add_node("publish", publish)
builder.add_node("flag_for_human", flag_for_human)

builder.add_edge(START, "write_postmortem")
builder.add_edge("write_postmortem", "review")
builder.add_conditional_edges("review", gate,
                              {"write_postmortem": "write_postmortem",
                               "publish": "publish",
                               "flag_for_human": "flag_for_human"})
builder.add_edge("publish", END)
builder.add_edge("flag_for_human", END)

graph = builder.compile()


# ------------------------------------------------------------------ demo ----
def _inputs(incident: str, facts: list[str]) -> dict:
    return {"incident": incident, "facts": facts, "draft": "", "attempts": 0,
            "verdict": "", "feedback": "", "review_log": [],
            "tokens_spent": 0, "errors": [], "status": "", "final": ""}


def _trace(name: str, result: dict) -> None:
    print(f"=== run trace: {name} ===")
    print(f"attempts: {result['attempts']}  verdict: {result['verdict']}  "
          f"status: {result['status']}  tokens_spent: {result['tokens_spent']}")
    for line in result["review_log"]:
        print("  ", line)
    if result["errors"]:
        print("errors:", result["errors"])
    print("--- final ---")
    print(result["final"])
    print()


if __name__ == "__main__":
    print("=== compiled mermaid ===")
    print(graph.get_graph().draw_mermaid())
    print(f"models: {'REAL Anthropic' if USE_REAL_MODELS else 'stub (deterministic)'}\n")

    cfg = {"recursion_limit": RECURSION_LIMIT}

    # Scenario 1 — the happy path IS a reject loop: v1 is missing the customer
    # impact section, the reviewer FAILs it, the writer fixes it, v2 passes.
    ok = graph.invoke(_inputs(
        "2026-07-21 API 5xx spike (34 min)",
        ["Elevated 5xx on api.example.com from 14:02 to 14:36 UTC.",
         "root cause: a bad connection-pool limit shipped in release v1.5.0.",
         "Mitigated by rolling back v1.5.0 at 14:31 UTC."]), config=cfg)
    _trace("passes after one rejection", ok)

    # Scenario 2 — the facts never establish a root cause, so no amount of
    # rewriting can satisfy the reviewer. MAX_ATTEMPTS is spent and the run
    # lands on flag_for_human rather than publishing something unreviewable.
    stuck = graph.invoke(_inputs(
        "2026-07-24 intermittent checkout failures (cause unknown)",
        ["Checkout error rate rose from 0.2% to 6% between 09:10 and 11:45 UTC.",
         "No deploy, config change, or infra alert correlates with the window.",
         "Investigation is ongoing; no cause has been established."]), config=cfg)
    _trace("bounds exhausted -> human", stuck)

    assert ok["attempts"] == 2, "expected exactly one rejection then a pass"
    assert ok["verdict"] == "PASS" and ok["status"] == "published"
    assert len(ok["review_log"]) == 2

    assert stuck["attempts"] == MAX_ATTEMPTS, "expected the attempt bound to bind"
    assert stuck["verdict"] == "FAIL" and stuck["status"] == "needs_human"
    assert len(stuck["review_log"]) == MAX_ATTEMPTS
    assert "UNPUBLISHED" in stuck["final"]

    assert not ok["errors"] and not stuck["errors"]
    print("OK: reject loop fired once then published; "
          "second scenario exhausted MAX_ATTEMPTS and reached flag_for_human.")
