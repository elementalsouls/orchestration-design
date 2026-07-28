"""collect_commits -> classify -> draft -> tighten -> END.

LangGraph v1.0 reference implementation (Pattern A: sequential pipeline).

The simplest thing that is still legitimately a graph: four steps in a straight
line, no conditionals, no loops. The ONLY thing that earns the graph here is
that every step needs a DIFFERENT model (or no model at all) — a deterministic
parse, then a cheap/fast classifier, then a strong writer, then a temperature-0
trimmer. If all four steps ran on the same model this would be a for-loop over
four prompts and should be written as one.

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
RECURSION_LIMIT = 10    # hard step bound on the whole run (4 nodes, no loops)
BUDGET_TOKENS = 5_000   # spend cap checked by tighten() before its model call
MAX_CHARS = 600         # length target tighten() enforces on the final notes

BUCKETS = ["breaking", "feat", "fix", "chore"]

# Hardcoded fixture standing in for `git log --format='%h %s' v1.4.0..v1.5.0`.
FIXTURE_LOG = [
    "a91c4de feat: add per-workspace API tokens",
    "3f0b17a fix: stop double-charging annual plan proration",
    "c72e9b1 feat!: drop the v1 /export endpoint",
    "0d5a8f2 chore: bump pinned postgres client to 16.2",
    "b6e3c40 fix: correct timezone on scheduled report emails",
    "e18d772 feat: bulk CSV import for contacts",
    "7ac0195 chore: rotate the staging signing key",
]

# ---------------------------------------------------------------- models ----
USE_REAL_MODELS = bool(os.environ.get("ANTHROPIC_API_KEY"))

if USE_REAL_MODELS:
    from langchain_anthropic import ChatAnthropic

    # Three DIFFERENT models — this heterogeneity is the whole justification
    # for the graph. collect_commits calls no model at all.
    classify_model = ChatAnthropic(model="claude-haiku-4-5", max_tokens=512)
    draft_model = ChatAnthropic(model="claude-sonnet-4-5", max_tokens=2048)
    tighten_model = ChatAnthropic(model="claude-haiku-4-5", max_tokens=1024,
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

    def _stub_classify(prompt: str) -> str:
        """Reads the '<sha> <subject>' lines out of the prompt, emits
        '<sha> <bucket>' — the same contract a real cheap model would honour."""
        out = []
        for line in prompt.splitlines():
            sha, _, subject = line.strip().partition(" ")
            if len(sha) != 7 or not all(c in "0123456789abcdef" for c in sha):
                continue
            head = subject.split(":")[0].lower()
            if "!" in head:
                bucket = "breaking"
            elif head.startswith("fix"):
                bucket = "fix"
            elif head.startswith("feat"):
                bucket = "feat"
            else:
                bucket = "chore"
            out.append(f"{sha} {bucket}")
        return "\n".join(out)

    def _stub_draft(prompt: str) -> str:
        """Deliberately verbose prose, so tighten() has real work to do."""
        lines = [l.strip() for l in prompt.splitlines() if l.strip().startswith("*")]
        body = " ".join(l.lstrip("* ") + "." for l in lines)
        return ("This release focuses on giving teams finer-grained control "
                "over access and on cleaning up a handful of long-standing "
                "billing and scheduling papercuts that customers have reported "
                "over the last two cycles. " + body + " As always, we recommend "
                "reading the breaking-change section carefully before you "
                "upgrade a production workspace, and we are happy to help with "
                "migrations if you reach out to support.")

    def _stub_tighten(prompt: str) -> str:
        text = prompt.split("TIGHTEN:")[-1].strip()
        return _truncate(text, MAX_CHARS)

    classify_model = _Stub(_stub_classify)
    draft_model = _Stub(_stub_draft)
    tighten_model = _Stub(_stub_tighten)


def _tokens(resp: Any) -> int:
    meta = getattr(resp, "usage_metadata", None) or {}
    return meta.get("total_tokens", 0)


def _truncate(text: str, limit: int) -> str:
    """Trim to <= limit chars on a sentence boundary. Also the fallback path
    when the token budget is blown, so tighten() never simply gives up."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = cut.rfind(". ")
    return (cut[:stop + 1] if stop > 0 else cut.rstrip()) + " [trimmed]"


# ----------------------------------------------------------------- state ----
class State(TypedDict):
    # field                          owner (writer) node        reducer
    repo_range: str                  # caller input              replace
    commits: list[dict]              # collect_commits only      replace
    buckets: dict[str, list[str]]    # classify only             replace
    notes_draft: str                 # draft only                replace
    notes_final: str                 # tighten only              replace
    tokens_spent: Annotated[int, operator.add]
    #                                # classify/draft/tighten    operator.add (sum)
    #                                # collect_commits adds 0 — it calls no model
    errors: Annotated[list[str], operator.add]
    #                                # any failing node          operator.add


# ----------------------------------------------------------------- nodes ----
def collect_commits(state: State) -> dict:
    """NO MODEL. Deterministic parse of the git-log fixture — a model here
    would be strictly worse: slower, costlier, and able to hallucinate shas."""
    commits = []
    for line in FIXTURE_LOG:
        sha, _, subject = line.partition(" ")
        commits.append({"sha": sha, "subject": subject})
    return {"commits": commits, "tokens_spent": 0}


def classify(state: State) -> dict:
    """CHEAP FAST MODEL. Bucketing is a short, high-volume, low-judgement
    call — exactly what haiku is for. Falls back to prefix parsing if the
    model returns a bucket we did not ask for (failure isolation)."""
    listing = "\n".join(f"{c['sha']} {c['subject']}" for c in state["commits"])
    r = classify_model.invoke(
        f"Bucket each commit as one of {BUCKETS}. Reply one line per commit, "
        f"'<sha> <bucket>', nothing else.\n{listing}")
    labels = {}
    for line in r.content.splitlines():
        sha, _, bucket = line.strip().partition(" ")
        if bucket.strip() in BUCKETS:
            labels[sha] = bucket.strip()
    buckets: dict[str, list[str]] = {b: [] for b in BUCKETS}
    errs = []
    for c in state["commits"]:
        bucket = labels.get(c["sha"])
        if bucket is None:
            bucket = "chore"
            errs.append(f"classify: no usable label for {c['sha']}, defaulted to chore")
        buckets[bucket].append(c["subject"])
    return {"buckets": buckets, "tokens_spent": _tokens(r), "errors": errs}


def draft(state: State) -> dict:
    """STRONG MODEL. This is the only step that writes customer-facing prose,
    so it is the only step worth sonnet money."""
    outline = "\n".join(
        f"* [{b}] {s}" for b in BUCKETS for s in state["buckets"][b])
    r = draft_model.invoke(
        f"Write release notes for {state['repo_range']} from this outline. "
        f"Lead with breaking changes.\n{outline}")
    return {"notes_draft": r.content, "tokens_spent": _tokens(r)}


def tighten(state: State) -> dict:
    """TEMPERATURE-0 MODEL. Trimming must be reproducible: the same draft has
    to yield the same published notes twice. Creativity is a defect here."""
    if state["tokens_spent"] > BUDGET_TOKENS:
        # Spend cap: skip the model call, trim deterministically instead.
        return {"notes_final": _truncate(state["notes_draft"], MAX_CHARS),
                "errors": ["tighten: token budget exhausted, trimmed locally"]}
    r = tighten_model.invoke(
        f"Trim to under {MAX_CHARS} characters. Keep every breaking change. "
        f"Do not add facts.\nTIGHTEN: {state['notes_draft']}")
    return {"notes_final": r.content, "tokens_spent": _tokens(r)}


# ----------------------------------------------------------------- graph ----
builder = StateGraph(State)
builder.add_node("collect_commits", collect_commits)
builder.add_node("classify", classify)
builder.add_node("draft", draft)
builder.add_node("tighten", tighten)

builder.add_edge(START, "collect_commits")
builder.add_edge("collect_commits", "classify")
builder.add_edge("classify", "draft")
builder.add_edge("draft", "tighten")
builder.add_edge("tighten", END)

graph = builder.compile()


if __name__ == "__main__":
    print("=== compiled mermaid ===")
    print(graph.get_graph().draw_mermaid())

    inputs = {"repo_range": "v1.4.0..v1.5.0",
              "commits": [], "buckets": {}, "notes_draft": "",
              "notes_final": "", "tokens_spent": 0, "errors": []}
    result = graph.invoke(inputs, config={"recursion_limit": RECURSION_LIMIT})

    print("=== run trace ===")
    print(f"models: {'REAL Anthropic' if USE_REAL_MODELS else 'stub (deterministic)'}")
    print(f"commits parsed: {len(result['commits'])}")
    for b in BUCKETS:
        print(f"  {b:9} {len(result['buckets'][b])} {result['buckets'][b]}")
    print(f"draft chars: {len(result['notes_draft'])}  "
          f"final chars: {len(result['notes_final'])}  "
          f"tokens_spent: {result['tokens_spent']}")
    if result["errors"]:
        print("errors:", result["errors"])
    print("=== final ===")
    print(result["notes_final"])

    assert len(result["commits"]) == len(FIXTURE_LOG)
    assert result["buckets"]["breaking"] == ["feat!: drop the v1 /export endpoint"]
    assert len(result["buckets"]["feat"]) == 2 and len(result["buckets"]["fix"]) == 2
    assert len(result["notes_draft"]) > MAX_CHARS, "draft should need tightening"
    assert len(result["notes_final"]) <= MAX_CHARS + len(" [trimmed]")
    assert not result["errors"]
    print("\nOK: 4 heterogeneous steps ran in order, notes tightened "
          f"{len(result['notes_draft'])} -> {len(result['notes_final'])} chars.")
