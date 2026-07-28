"""fetch -> chunk -> summarise -> review -> format, as ONE agent loop.

This is the orchestration-design skill's most common correct outcome: the gate in
Phase 1 rejected the graph. The request ("fetch an article, chunk it, summarise
each chunk, review it, format as markdown") looks like a 5-node graph and is
really one loop with a verifier.

Why it is NOT a graph:
  - no real specialties      -- every step is the same model with the same tools,
                                or plain Python (chunking and markdown rendering
                                are functions, not agents)
  - no useful parallelism    -- one article, a handful of chunks; fan-out would
                                cost more coordination than it saves
  - failure isolation moot   -- if a step fails the whole summary is worthless;
                                there is nothing downstream worth protecting
  - routing is not auditable-worthy -- there is exactly one decision in the whole
                                task ("is the draft good enough?")
  - independent reviewer     -- the ONE criterion that hits. A loop already covers
                                it: a read-only verifier on a different model,
                                called from the loop condition.

So: no LangGraph, no StateGraph, no nodes, no edges. A while loop with a bound.
Runs offline, stdlib only: `python3 loop.py`.
"""

from __future__ import annotations

import re

# ----------------------------------------------------------------- bounds ----
MAX_ATTEMPTS = 3       # hard cap on the revise loop
BUDGET_TOKENS = 5_000  # spend cap, checked in the loop condition
CHUNK_CHARS = 400

SOURCE_URL = "https://example.invalid/articles/grid-storage"

# Stands in for a real HTTP fetch; kept offline so the demo has no deps.
ARTICLE = """\
Grid-scale batteries crossed a threshold this year. Installed capacity in the
region reached eleven gigawatt-hours, up from four the year before. Operators
now treat storage as a scheduling asset rather than an emergency reserve.

Costs fell faster than forecast. A pack that cost 180 dollars per kilowatt-hour
in 2020 now lands near 65 dollars, and the installed system price followed it
down by roughly half. Cheap cells changed which projects clear the hurdle rate.

Duration is the open question. Most deployed systems discharge for four hours,
which covers the evening peak but not a still, overcast week. Two pilots are
testing twelve-hour chemistries, and neither has published cycle-life data yet.

Regulation lags the hardware. Market rules in most jurisdictions still classify
storage as generation, which forces operators into contracts written for plants
that burn something. Three regulators have opened dockets to fix the mismatch.
"""


# ----------------------------------------------------------------- models ----
class _Stub:
    """Deterministic stand-in with a .invoke(prompt).content interface."""

    def __init__(self, fn):
        self._fn = fn

    def invoke(self, prompt: str):
        text = str(prompt)
        out = self._fn(text)

        class R:
            content = out
            usage_metadata = {"total_tokens": max(1, len(text) // 4)}

        return R()


def _first_sentence(text: str) -> str:
    return text.replace("\n", " ").split(". ")[0].strip().rstrip(".")


def _write(prompt: str) -> str:
    chunk = prompt.split("CHUNK:", 1)[1].strip()
    bullet = "- " + _first_sentence(chunk) + "."
    if "FEEDBACK:" in prompt:
        figures = re.findall(r"\d[\d.,]*", chunk)
        if figures:
            bullet += " (figures: " + ", ".join(figures) + ")"
    return bullet


def _judge(prompt: str) -> str:
    draft = prompt.split("DRAFT:", 1)[1]
    if re.search(r"\d", draft):
        return "PASS: claims are traceable to numbers in the source."
    return ("FAIL: the summary drops every concrete figure from the source; "
            "a reader cannot check any claim.")


writer_model = _Stub(_write)
# Separate instance, and in real mode a different model: the producer must
# never grade its own output.
verifier_model = _Stub(_judge)


def _tokens(resp) -> int:
    return getattr(resp, "usage_metadata", {}).get("total_tokens", 0)


# ------------------------------------------------------------- plain code ----
def fetch_article(url: str) -> str:
    """Not a node. A function."""
    assert url.startswith("https://")
    return ARTICLE


def chunk(text: str, size: int = CHUNK_CHARS) -> list[str]:
    """Not a node either. Deterministic, no model, no state."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    out: list[str] = []
    for p in paragraphs:
        if out and len(out[-1]) + len(p) + 2 <= size:
            out[-1] = out[-1] + "\n\n" + p
        else:
            out.append(p)
    return out


def render_markdown(url: str, bullets: list[str]) -> str:
    """Also not a node. A string template."""
    return "\n".join(["# Summary", "", f"Source: {url}", ""] + bullets)


# ------------------------------------------------------------------- loop ----
def summarise(chunks: list[str], feedback: str) -> tuple[list[str], int]:
    spent = 0
    bullets = []
    for c in chunks:
        prompt = ("Summarise this chunk as one bullet.\n"
                  + (f"FEEDBACK: {feedback}\n" if feedback else "")
                  + f"CHUNK: {c}")
        r = writer_model.invoke(prompt)
        bullets.append(r.content)
        spent += _tokens(r)
    return bullets, spent


def verify(draft: str) -> tuple[str, str, int]:
    """Read-only. Returns (verdict, reasons, tokens) and never touches `draft`."""
    r = verifier_model.invoke(
        "You are a read-only reviewer. Reply 'PASS: <why>' or 'FAIL: <what to "
        f"fix>'. Do not rewrite anything.\nDRAFT:\n{draft}")
    verdict, _, reasons = r.content.partition(":")
    return verdict.strip(), reasons.strip(), _tokens(r)


def run(url: str) -> dict:
    chunks = chunk(fetch_article(url))

    attempts = 0
    spent = 0
    feedback = ""
    verdict = ""
    draft = ""
    trace: list[str] = []

    while attempts < MAX_ATTEMPTS and spent < BUDGET_TOKENS:
        attempts += 1
        bullets, cost = summarise(chunks, feedback)
        spent += cost
        draft = render_markdown(url, bullets)

        before = draft
        verdict, feedback, cost = verify(draft)
        spent += cost
        assert draft == before, "verifier mutated the draft"

        trace.append(f"attempt {attempts}: {verdict} - {feedback}")
        if verdict == "PASS":
            break

    return {"draft": draft, "verdict": verdict, "attempts": attempts,
            "tokens_spent": spent, "chunks": len(chunks), "trace": trace}


if __name__ == "__main__":
    result = run(SOURCE_URL)

    print("=== loop trace ===")
    print(f"chunks (plain function, not nodes): {result['chunks']}")
    for line in result["trace"]:
        print("  ", line)
    print(f"tokens_spent: {result['tokens_spent']} / {BUDGET_TOKENS}")
    print("=== final ===")
    print(result["draft"])

    assert result["attempts"] == 2, "expected the retry loop to fire exactly once"
    assert result["trace"][0].startswith("attempt 1: FAIL")
    assert result["verdict"] == "PASS"
    assert result["tokens_spent"] < BUDGET_TOKENS
    print(f"\nOK: 1 retry, verdict PASS, {result['chunks']} chunks, 0 graph nodes.")
