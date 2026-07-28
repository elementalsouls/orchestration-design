"""Phase 4 verification: assert the drawn design matches the compiled graph.

Comparing two nine-edge Mermaid diagrams by eye is exactly the check a tired
builder skips, so this makes it an assertion instead.

Usage:
    python verify_topology.py                 # check every example dir
    python verify_topology.py 03-reviewer-loop

Each example's README.md must contain two ```mermaid fences:
  1. the hand-drawn Phase 2 design
  2. the output of graph.get_graph().draw_mermaid()

Both are parsed down to a set of (source, target) pairs. Node shapes, edge
labels, dotted-vs-solid styling and declaration order are all ignored — only
the topology is compared, because that is the thing that must not drift.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent

# START/END spelled several ways across hand-drawn and compiled diagrams
ALIASES = {"__start__": "START", "__end__": "END", "S": "START", "E": "END"}

FENCE = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)

# node shape decorations: n([x]) n((x)) n[[x]] n{{x}} n(x) n[x] n{x} -> n
SHAPE = re.compile(
    r"([A-Za-z_]\w*)\s*"
    r"(?:\(\(.*?\)\)|\(\[.*?\]\)|\[\[.*?\]\]|\{\{.*?\}\}|\(.*?\)|\[.*?\]|\{.*?\})"
)

# every arrow spelling collapses to a plain --> before matching
ARROWS = (
    (re.compile(r'-\.\s*"[^"]*"\s*\.->'), "-->"),   # -. "label" .->
    (re.compile(r"-\.\s*\|[^|]*\|\s*\.->"), "-->"),  # -. |label| .->
    (re.compile(r"-\.[^.>]*\.->"), "-->"),           # -. label .->
    (re.compile(r"-\.->"), "-->"),                   # -.->
    (re.compile(r"[-=]{2,3}>\s*\|[^|]*\|"), "-->"),  # -->|label|
    (re.compile(r"={2,3}>"), "-->"),                 # ==>
    (re.compile(r"-{3,}>"), "-->"),                  # --->
)

EDGE = re.compile(r"([A-Za-z_]\w*)\s*-->\s*([A-Za-z_]\w*)")

SKIP_PREFIXES = ("style ", "classDef ", "class ", "subgraph", "end",
                 "direction", "config:", "flowchart:", "curve:", "---")


def normalise(name: str) -> str:
    return ALIASES.get(name, name)


def edge_set(mermaid: str) -> set[tuple[str, str]]:
    """Reduce a Mermaid block to bare (source, target) pairs.

    Node shapes, edge labels, dotted-vs-solid and declaration order are all
    discarded — only which node points at which node survives.
    """
    edges: set[tuple[str, str]] = set()
    for line in mermaid.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(SKIP_PREFIXES):
            continue
        line = SHAPE.sub(r"\1", line)
        for pattern, repl in ARROWS:
            line = pattern.sub(repl, line)
        # one line may chain: a --> b --> c
        parts = [p.strip() for p in line.split("-->")]
        for src, dst in zip(parts, parts[1:]):
            m_src = re.search(r"([A-Za-z_]\w*)\s*$", src)
            m_dst = re.match(r"\s*([A-Za-z_]\w*)", dst)
            if m_src and m_dst:
                edges.add((normalise(m_src.group(1)), normalise(m_dst.group(1))))
    return edges


def check(readme: Path) -> tuple[bool, str]:
    blocks = FENCE.findall(readme.read_text())
    if len(blocks) < 2:
        return False, f"expected 2 mermaid fences, found {len(blocks)}"

    design, compiled = edge_set(blocks[0]), edge_set(blocks[-1])
    if not design or not compiled:
        return False, "a mermaid fence parsed to zero edges"
    if design == compiled:
        return True, f"{len(design)} edges match"

    missing = design - compiled      # drawn but not built
    extra = compiled - design        # built but not drawn
    parts = []
    if missing:
        parts.append("in design, not in code: "
                     + ", ".join(f"{a}->{b}" for a, b in sorted(missing)))
    if extra:
        parts.append("in code, not in design: "
                     + ", ".join(f"{a}->{b}" for a, b in sorted(extra)))
    return False, "; ".join(parts)


def main(argv: list[str]) -> int:
    targets = ([ROOT / a for a in argv[1:]] if len(argv) > 1
               else sorted(d for d in ROOT.iterdir()
                           if d.is_dir() and (d / "README.md").exists()))

    failures = 0
    for d in targets:
        readme = d / "README.md"
        if not readme.exists():
            print(f"SKIP {d.name}: no README.md")
            continue
        blocks = FENCE.findall(readme.read_text())
        if len(blocks) < 2:
            # 01-loop-not-graph is deliberately not a graph — one diagram only
            print(f"SKIP {d.name}: not a compiled graph ({len(blocks)} fence(s))")
            continue
        ok, detail = check(readme)
        print(f"{'OK  ' if ok else 'FAIL'} {d.name}: {detail}")
        failures += not ok

    print()
    if failures:
        print(f"{failures} topology mismatch(es) — the code drifted from the design.")
        return 1
    print("All topologies match their documented design.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
