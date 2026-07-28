"""Intake -> fan out one branch per document -> Extract -> Answer -> fan in to
Collect -> Report -> END.

LangGraph v1.0 reference implementation (Pattern C: fan-out/fan-in with the
Send API), on vendor security questionnaires.

Runs with deterministic stub models by default (no API key needed; fixture D3
is a corrupt scan whose branch deterministically fails, so failure isolation
is exercised on every run). If ANTHROPIC_API_KEY is set, real Anthropic models
are used instead.

The three things this example exists to teach:
  1. Fan-in reducers are mandatory. Every field the parallel branches write is
     Annotated[..., operator.add]. Without it, N concurrent writers collide:
     LangGraph raises InvalidUpdateError, or — with a replace channel that
     tolerates it — the last branch to finish silently wins and the other N-1
     results vanish with no error at all. That second failure mode is the one
     that ships to production.
  2. Failure isolation is the point of fanning out. One bad document must not
     take the run down. Each branch try/excepts into `errors` and simply stops
     (no goto), so 5 of 6 branches still produce answers and the report still
     renders.
  3. Per-item payloads, not shared state. A Send payload carries ONLY what that
     branch needs. Branches must never read sibling state: within a superstep
     the siblings' writes are not committed yet, so a read is a race — you'd
     see stale data, in an order that changes run to run.
"""

from __future__ import annotations

import operator
import os
from typing import Annotated, Any

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, Send

# ---------------------------------------------------------------- bounds ----
MAX_FANOUT = 12          # hard cap on branch degree (never fan out an unbounded list)
RECURSION_LIMIT = 25     # hard step bound on the whole run
BUDGET_TOKENS = 5_000    # total token budget, summed across ALL branches
EST_TOKENS_PER_DOC = 200  # pre-flight estimate used by the fan-out router

# ------------------------------------------------------------- fixtures ----
# Six vendor questionnaires. D3 is a corrupt scan: its blob has no %PDF header,
# so its branch deterministically raises inside extract() on every run.
FIXTURES = [
    {"doc_id": "D1", "path": "vendors/acme/security_questionnaire.pdf",
     "blob": "%PDF-1.7\nQ: encryption-at-rest\nQ: mfa\nQ: incident-response"},
    {"doc_id": "D2", "path": "vendors/globex/vendor_review_2026.pdf",
     "blob": "%PDF-1.7\nQ: mfa\nQ: subprocessors\nQ: pen-test-cadence"},
    {"doc_id": "D3", "path": "vendors/initech/scanned_questionnaire.pdf",
     "blob": "\x00\x00JFIF scanned-image-no-text-layer\x00"},   # <- the bad one
    {"doc_id": "D4", "path": "vendors/umbrella/soc2_followup.pdf",
     "blob": "%PDF-1.7\nQ: encryption-at-rest\nQ: data-residency"},
    {"doc_id": "D5", "path": "vendors/hooli/annual_diligence.pdf",
     "blob": "%PDF-1.7\nQ: incident-response\nQ: byo-key\nQ: subprocessors"},
    {"doc_id": "D6", "path": "vendors/stark/ai_addendum.pdf",
     "blob": "%PDF-1.7\nQ: model-training-on-customer-data\nQ: pen-test-cadence"},
]

# The policy corpus each branch drafts from. Handed to the branch in its Send
# payload, so a branch is self-contained and never reaches back into state.
POLICY = {
    "encryption-at-rest": "AES-256 at rest, keys in KMS, rotated every 90 days.",
    "mfa": "MFA enforced org-wide via SSO; hardware keys for admins.",
    "incident-response": "24/7 on-call; Sev1 customer notification within 24h.",
    "subprocessors": "Published subprocessor list; 30-day notice on changes.",
    "pen-test-cadence": "Annual third-party pen test; summary letter on request.",
    "data-residency": "EU and US regions; data pinned to region of signup.",
    "byo-key": "BYOK available on Enterprise; CMK via KMS grants.",
}

# ---------------------------------------------------------------- models ----
USE_REAL_MODELS = bool(os.environ.get("ANTHROPIC_API_KEY"))

if USE_REAL_MODELS:
    from langchain_anthropic import ChatAnthropic

    extract_model = ChatAnthropic(model="claude-haiku-4-5", max_tokens=1024,
                                  temperature=0)
    answer_model = ChatAnthropic(model="claude-sonnet-4-5", max_tokens=2048)
else:
    class _Stub:
        """Deterministic stand-in with a .invoke(...).content interface."""

        def __init__(self, fn, tokens: int = 50):
            self._fn = fn
            self._tokens = tokens

        def invoke(self, prompt: Any):
            class R:
                content = self._fn(str(prompt))
                usage_metadata = {"total_tokens": self._tokens}
            return R()

    # Stub extractor: echoes back the "Q: ..." lines it was handed.
    extract_model = _Stub(
        lambda p: "\n".join(ln[3:].strip() for ln in p.splitlines()
                            if ln.startswith("Q: ")),
        tokens=40)
    # Stub drafter: one line per question, marking anything with no policy hit.
    answer_model = _Stub(
        lambda p: "\n".join(
            f"{ln.split('|')[0].strip()} -> {ln.split('|', 1)[1].strip()}"
            for ln in p.splitlines() if "|" in ln),
        tokens=60)


def _tokens(resp: Any) -> int:
    meta = getattr(resp, "usage_metadata", None) or {}
    return meta.get("total_tokens", 0)


# ----------------------------------------------------------------- state ----
class State(TypedDict):
    # field                          owner (writer) node        reducer
    docs: list[dict]                 # intake only               replace
    questions: Annotated[list[dict], operator.add]
    #                                # extract (N parallel)      operator.add — FAN-IN
    answers: Annotated[list[dict], operator.add]
    #                                # answer (N parallel)       operator.add — FAN-IN
    #                                # one entry per document that survived its branch
    errors: Annotated[list[str], operator.add]
    #                                # any failing branch        operator.add — FAN-IN
    #                                # failure isolation: a branch buries its own
    #                                # exception here instead of killing the run
    tokens_spent: Annotated[int, operator.add]
    #                                # every model-calling node  operator.add (sum) — FAN-IN
    summary: dict                    # collect only              replace
    report: str                      # report only               replace


# ----------------------------------------------------------------- nodes ----
def intake(state: State) -> dict:
    """List the work. No models, no I/O — just the unit-of-work manifest."""
    return {"docs": FIXTURES}


def fan_out_documents(state: State) -> list[Send]:
    """One Send per document == one independent branch.

    The payload is the WHOLE contract for that branch: its doc, and the policy
    snippets it will need. A branch never reads `state` — sibling writes are
    uncommitted mid-superstep, so reading them is a race, not a shortcut.

    Also where the bounds live: fan degree is capped, and the pre-flight token
    estimate trims the fan-out rather than discovering the overspend after
    paying for it.
    """
    docs = state["docs"][:MAX_FANOUT]
    affordable = max(1, BUDGET_TOKENS // EST_TOKENS_PER_DOC)
    docs = docs[:affordable]
    return [Send("extract", {"doc": d, "policy": POLICY}) for d in docs]


def extract(payload: dict) -> Command:
    """Branch step 1: pull the questions out of one document.

    Owns its own failure. On a bad document it writes to `errors` and returns
    NO goto — the branch stops here while every sibling branch runs to
    completion. This is the entire reason to fan out instead of looping.
    """
    doc = payload["doc"]
    try:
        if not doc["blob"].startswith("%PDF"):
            raise ValueError("no text layer (bad PDF header) — needs OCR")
        r = extract_model.invoke(
            "Extract every questionnaire item, one per line, verbatim.\n"
            + doc["blob"])
        questions = [q for q in r.content.splitlines() if q.strip()]
        if not questions:
            raise ValueError("parsed 0 questions")
    except Exception as e:
        return Command(update={
            "errors": [f"{doc['doc_id']} ({doc['path']}): extract failed: {e}"],
            "tokens_spent": 0,
        })  # no goto -> this branch is done; the other branches are untouched

    return Command(
        update={"questions": [{"doc_id": doc["doc_id"], "items": questions}],
                "tokens_spent": _tokens(r)},
        # per-item payload again: the answer step gets this doc's questions,
        # not the shared `questions` channel (which is mid-fan-in and partial).
        goto=[Send("answer", {"doc_id": doc["doc_id"], "path": doc["path"],
                              "questions": questions,
                              "policy": payload["policy"]})],
    )


def answer(payload: dict) -> dict:
    """Branch step 2: draft answers for one document from the policy snippets."""
    policy = payload["policy"]
    try:
        prompt = "Answer each item from the policy snippet after the pipe.\n" + \
            "\n".join(f"{q} | {policy.get(q, 'NO POLICY MATCH — escalate')}"
                      for q in payload["questions"])
        r = answer_model.invoke(prompt)
        drafted = [ln for ln in r.content.splitlines() if ln.strip()]
    except Exception as e:
        return {"errors": [f"{payload['doc_id']}: answer failed: {e}"]}

    gaps = [q for q in payload["questions"] if q not in policy]
    return {"answers": [{"doc_id": payload["doc_id"], "path": payload["path"],
                         "drafted": drafted, "gaps": gaps}],
            "tokens_spent": _tokens(r)}


def collect(state: State) -> dict:
    """Fan-in barrier. Runs once, after every branch has settled.

    Branches finish in nondeterministic order, so anything order-sensitive gets
    sorted HERE — never assume `answers` came back in fixture order.
    """
    answers = sorted(state["answers"], key=lambda a: a["doc_id"])
    return {"summary": {
        "requested": len(state["docs"]),
        "answered": len(answers),
        "failed": len(state["errors"]),
        "questions": sum(len(q["items"]) for q in state["questions"]),
        "gaps": sorted({g for a in answers for g in a["gaps"]}),
        "over_budget": state["tokens_spent"] > BUDGET_TOKENS,
    }}


def report(state: State) -> dict:
    """Render the deliverable — including the partial-failure caveat."""
    s = state["summary"]
    lines = [f"VENDOR QUESTIONNAIRE RUN — {s['answered']}/{s['requested']} "
             f"documents answered, {s['questions']} questions drafted"]
    for a in sorted(state["answers"], key=lambda a: a["doc_id"]):
        lines.append(f"  [{a['doc_id']}] {a['path']}  "
                     f"({len(a['drafted'])} answers"
                     + (f", {len(a['gaps'])} policy gap(s)" if a["gaps"] else "")
                     + ")")
    for e in state["errors"]:
        lines.append(f"  [SKIPPED] {e}")
    if s["gaps"]:
        lines.append(f"  policy gaps to escalate: {', '.join(s['gaps'])}")
    if s["failed"]:
        lines.append(f"  NOTE: partial result — {s['failed']} document(s) "
                     "isolated to the errors channel; rerun those alone.")
    if s["over_budget"]:
        lines.append(f"  NOTE: token budget {BUDGET_TOKENS} exceeded.")
    return {"report": "\n".join(lines)}


# ----------------------------------------------------------------- graph ----
builder = StateGraph(State)
builder.add_node("intake", intake)
# `destinations` declares where extract's Command(goto=...) can land, so the
# compiled diagram shows the real extract -> answer edge.
builder.add_node("extract", extract, destinations=("answer",))
builder.add_node("answer", answer)
builder.add_node("collect", collect)
builder.add_node("report", report)

builder.add_edge(START, "intake")
builder.add_conditional_edges("intake", fan_out_documents, ["extract"])
builder.add_edge("answer", "collect")    # implicit fan-in barrier
builder.add_edge("collect", "report")
builder.add_edge("report", END)

graph = builder.compile()


if __name__ == "__main__":
    print("=== compiled mermaid ===")
    print(graph.get_graph().draw_mermaid())

    inputs = {"docs": [], "questions": [], "answers": [], "errors": [],
              "tokens_spent": 0, "summary": {}, "report": ""}
    result = graph.invoke(inputs, config={"recursion_limit": RECURSION_LIMIT})

    n = len(FIXTURES)
    print("=== run trace ===")
    print(f"models: {'REAL Anthropic' if USE_REAL_MODELS else 'stub (deterministic)'}")
    print(f"fanned out : {n} branches (cap {MAX_FANOUT})")
    for q in sorted(result["questions"], key=lambda q: q["doc_id"]):
        print(f"  extract [{q['doc_id']}] {len(q['items'])} questions: "
              f"{', '.join(q['items'])}")
    for a in sorted(result["answers"], key=lambda a: a["doc_id"]):
        for line in a["drafted"]:
            print(f"  answer  [{a['doc_id']}] {line}")
    for e in result["errors"]:
        print(f"  ERROR   {e}")
    print(f"summary: {result['summary']}")
    print(f"tokens_spent: {result['tokens_spent']} / {BUDGET_TOKENS}")
    print("=== final ===")
    print(result["report"])

    # 1. failure isolation: one branch died, the rest completed, run did not crash
    assert len(result["answers"]) == n - 1, \
        f"expected {n - 1} answered docs, got {len(result['answers'])}"
    assert len(result["errors"]) == 1, \
        f"expected exactly 1 isolated failure, got {result['errors']}"
    assert "D3" in result["errors"][0], "the corrupt fixture should be the failure"
    # 2. fan-in reducers actually merged every branch's write
    assert len(result["questions"]) == n - 1
    assert result["tokens_spent"] > 0 and not result["summary"]["over_budget"]
    # 3. the run still produced a deliverable despite the partial failure
    assert result["report"].startswith(f"VENDOR QUESTIONNAIRE RUN — {n - 1}/{n}")
    print(f"\nOK: {len(result['answers'])} branches answered, "
          f"{len(result['errors'])} isolated failure, report still produced.")
