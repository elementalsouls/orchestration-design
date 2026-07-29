#!/usr/bin/env python3
"""Support ticket triage — level 3: one writer, one read-only reviewer.

The request that produced this looked like it needed three agents:
a labeller, a prioritiser, and a duplicate-detector. The ladder collapsed it
to ONE writer doing all three (same model, same context, no handoff loss) plus
ONE independent reviewer whose only job is catching under-prioritisation —
the failure that actually hurts.

    load (fn) -> [ triage -> review ]* -> digest (fn)

The reviewer sees the tickets and the assignments. It never sees the writer's
reasoning, so it cannot inherit the writer's mistake.

Run:        python triage.py
Self-check: python triage.py --selftest
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- bounds ----
MAX_ATTEMPTS = 3
BUDGET_TOKENS = 20_000

PRIORITIES = ["P0", "P1", "P2", "P3"]


# ----------------------------------------------------------------- state ----
@dataclass
class State:
    # field                       owner (only writer)   reducer
    tickets: list[dict] = field(default_factory=list)      # load      replace
    assignments: list[dict] = field(default_factory=list)  # triage    replace
    verdict: str = ""                                      # review    replace
    feedback: str = ""                                     # review    replace
    attempts: int = 0                                      # triage    counter
    tokens_spent: int = 0                                  # any model sum
    errors: list[str] = field(default_factory=list)        # any       append
    digest: str = ""                                       # digest    replace


# Reducers are declared, never inferred. Guessing "list means append" is a
# footgun: `assignments` is a list the design marks REPLACE (single owner,
# rewritten whole each round). Inferring append silently stacks round 2 on top
# of round 1 — the same ticket appears twice at two different priorities.
APPEND = {"errors", "tickets"}       # everything else replaces


def apply(s: State, update: dict) -> State:
    for k, v in update.items():
        setattr(s, k, getattr(s, k) + v if k in APPEND else v)
    return s


# ---------------------------------------------------------------- models ----
USE_REAL_MODELS = bool(os.environ.get("ANTHROPIC_API_KEY"))

# Phrases that mean "this is an emergency regardless of how politely it is
# worded". The reviewer checks these independently of the writer.
CRITICAL = [
    ("cross-account", ["belonging to a different account", "not mine",
                       "other customers"]),
    ("total outage", ["locked out", "returns 500", "blocking all work"]),
]


class _Stub:
    def __init__(self, fn):
        self._fn = fn

    def invoke(self, payload):
        fn = self._fn

        class R:
            content = fn(payload)
            usage_metadata = {"total_tokens": 240}
        return R()


def _tokens(resp) -> int:
    return (getattr(resp, "usage_metadata", None) or {}).get("total_tokens", 0)


def _stub_triage(payload: dict) -> str:
    """Keyword triage. On the first pass it UNDER-PRIORITISES the cross-account
    data leak as P2 — a plausible, quiet mistake. That is the whole point of
    the example: it is exactly what a reviewer has to catch."""
    fixed = "raise-to-p0" in payload.get("feedback", "")
    out = []
    for t in payload["tickets"]:
        blob = f"{t['subject']} {t['body']}".lower()
        if "belonging to a different account" in blob:
            label, prio = "security", ("P0" if fixed else "P2")
        elif "locked out" in blob or "returns 500" in blob:
            label, prio = "outage", "P0"
        elif "vat" in blob or "invoice" in blob:
            label, prio = "billing", "P1"
        elif "webhook" in blob or "truncates" in blob or "slow" in blob:
            label, prio = "bug", "P2"
        elif "reset" in blob or "log in" in blob:
            label, prio = "auth", "P2"
        else:
            label, prio = "enhancement", "P3"
        out.append({"id": t["id"], "label": label, "priority": prio})
    return json.dumps(out)


def _stub_review(payload: dict) -> str:
    """Read-only. Sees tickets + assignments, never the writer's reasoning."""
    by_id = {a["id"]: a for a in payload["assignments"]}
    for t in payload["tickets"]:
        blob = f"{t['subject']} {t['body']}".lower()
        for kind, phrases in CRITICAL:
            if any(p in blob for p in phrases):
                got = by_id.get(t["id"], {}).get("priority")
                if got != "P0":
                    return (f"FAIL: {t['id']} describes a {kind} issue but was "
                            f"filed {got}. raise-to-p0")
    return "PASS: no under-prioritised critical tickets."


if USE_REAL_MODELS:
    from langchain_anthropic import ChatAnthropic
    _w = ChatAnthropic(model="claude-sonnet-4-5", max_tokens=2048)
    _r = ChatAnthropic(model="claude-haiku-4-5", max_tokens=512)   # different model
    triage_model = type("M", (), {"invoke": staticmethod(
        lambda p: _w.invoke("Triage these tickets as JSON "
                            "[{id,label,priority}]. Priorities P0-P3.\n"
                            f"TICKETS:\n{json.dumps(p['tickets'], indent=1)}\n"
                            + (f"FEEDBACK: {p['feedback']}\n" if p.get("feedback") else "")))})()
    review_model = type("M", (), {"invoke": staticmethod(
        lambda p: _r.invoke("You are a read-only reviewer. Reply 'PASS: ...' or "
                            "'FAIL: <what to fix>'. Flag any ticket describing "
                            "cross-account data exposure or a total outage that "
                            "is not P0.\n"
                            f"TICKETS:\n{json.dumps(p['tickets'], indent=1)}\n"
                            f"ASSIGNMENTS:\n{json.dumps(p['assignments'], indent=1)}"))})()
else:
    triage_model, review_model = _Stub(_stub_triage), _Stub(_stub_review)


# ------------------------------------------------------------ plain fns -----
def load(path: Path) -> dict:
    """Not a node — no model call."""
    try:
        raw = json.loads(path.read_text())
    except Exception as e:
        return {"errors": [f"load failed: {e}"]}
    good, bad = [], []
    for t in raw:
        (good if {"id", "subject", "body"} <= t.keys() else bad).append(t)
    return {"tickets": good,
            "errors": [f"skipped malformed ticket: {t}" for t in bad]}


def digest(s: State) -> dict:
    """Not a node. Renders the digest, loudly marking unreviewed output."""
    lines = []
    if not s.verdict.startswith("PASS"):
        lines.append("> **UNREVIEWED** — shipped after exhausting review "
                     "attempts or budget. Check priorities by hand.\n")
    for p in PRIORITIES:
        rows = [a for a in s.assignments if a["priority"] == p]
        if rows:
            lines.append(f"### {p}")
            for a in rows:
                subj = next(t["subject"] for t in s.tickets if t["id"] == a["id"])
                lines.append(f"- `{a['id']}` [{a['label']}] {subj}")
            lines.append("")
    if s.errors:
        lines.append(f"_{len(s.errors)} ticket(s) skipped — see errors._")
    return {"digest": "\n".join(lines)}


# ------------------------------------------------------------- the loop -----
def run(path: Path = HERE / "tickets.json") -> State:
    s = State()
    s = apply(s, load(path))
    if not s.tickets:
        return s

    while s.attempts < MAX_ATTEMPTS and s.tokens_spent < BUDGET_TOKENS:
        r = triage_model.invoke({"tickets": s.tickets, "feedback": s.feedback})
        s = apply(s, {"assignments": json.loads(r.content),
                      "attempts": s.attempts + 1,
                      "tokens_spent": _tokens(r)})

        before = json.dumps(s.assignments, sort_keys=True)
        rv = review_model.invoke({"tickets": s.tickets,
                                  "assignments": s.assignments})
        s = apply(s, {"verdict": rv.content, "feedback": rv.content,
                      "tokens_spent": _tokens(rv)})
        assert json.dumps(s.assignments, sort_keys=True) == before, \
            "reviewer mutated the assignments — it must be read-only"

        if s.verdict.startswith("PASS"):
            break
    else:
        s.errors.append("bounds exhausted before PASS")

    return apply(s, digest(s))


# ------------------------------------------------------------- selftest -----
def _selftest() -> int:
    """Phase 4 at level 3 — assert behaviour, not topology."""
    global review_model
    s = run()

    # 1. the reviewer never edits (also asserted inline every round, above)
    snap = json.dumps(s.assignments, sort_keys=True)
    review_model.invoke({"tickets": s.tickets, "assignments": s.assignments})
    assert json.dumps(s.assignments, sort_keys=True) == snap

    # the demo's whole point: the leak was caught and raised
    assert s.attempts == 2, f"expected one reject round, got {s.attempts}"
    assert s.verdict.startswith("PASS")
    # counts catch silent duplication or loss — the failure a wrong reducer
    # produces, which no other assertion here would notice
    assert len(s.assignments) == len(s.tickets), \
        f"{len(s.assignments)} assignments for {len(s.tickets)} tickets"
    assert len({a["id"] for a in s.assignments}) == len(s.assignments), \
        "duplicate ticket ids in assignments"
    leak = next(a for a in s.assignments if a["id"] == "T-1044")
    assert leak["priority"] == "P0", leak
    assert "UNREVIEWED" not in s.digest

    # 2 + 3. bound is live, exhaustion terminal reachable AND marked
    saved, review_model = review_model, _Stub(lambda p: "FAIL: never happy")
    try:
        b = run()
        assert b.attempts == MAX_ATTEMPTS, b.attempts
        assert "UNREVIEWED" in b.digest
        assert "bounds exhausted" in b.errors[-1]
    finally:
        review_model = saved

    # 4. failure isolation: a malformed ticket is skipped, run still completes
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "t.json"
        good = json.loads((HERE / "tickets.json").read_text())
        p.write_text(json.dumps(good + [{"id": "T-BAD"}]))
        c = run(p)
        assert len(c.assignments) == len(good), "malformed ticket contaminated run"
        assert any("malformed" in e for e in c.errors)
        assert c.digest, "one bad ticket killed the digest"

    print("OK: leak raised to P0, reviewer read-only, bound live, "
          "exhaustion marked, malformed ticket isolated.")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    st = run()
    print(f"models   : {'REAL Anthropic' if USE_REAL_MODELS else 'stub (deterministic)'}")
    print(f"tickets  : {len(st.tickets)}")
    print(f"attempts : {st.attempts}   verdict: {st.verdict}")
    print(f"tokens   : {st.tokens_spent}  (budget {BUDGET_TOKENS})")
    if st.errors:
        for e in st.errors:
            print(f"  ! {e}")
    print("-" * 62)
    print(st.digest)
