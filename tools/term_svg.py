#!/usr/bin/env python3
"""Render captured terminal output as an SVG "screenshot" for the README.

SVG rather than PNG on purpose: GitHub renders it inline, it stays diffable in
review, and it can be regenerated from real output instead of drifting away
from what the tool actually prints.

    python tools/term_svg.py --title "python triage.py" -o docs/img/x.svg < out.txt
Self-check:
    python tools/term_svg.py --selftest
"""

from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

CW, LH, PAD, TOP = 8.42, 20, 18, 40      # char width, line height, padding, chrome
BG, FG, DIM = "#12191d", "#d7e1e4", "#7d8f95"
GREEN, RED, AMBER, CYAN = "#6fc694", "#e08581", "#d9ae4e", "#56c2cb"


def colour(line: str) -> str:
    s = line.strip()
    if s.startswith(("OK:", "all checks passed")) or "[ok]" in line:
        return GREEN
    if s.startswith(("FAIL", "!", "Traceback")) or "[XX]" in line or "[!!]" in line:
        return RED
    if s.startswith(("###", "===")) or "UNREVIEWED" in line:
        return AMBER
    if s.startswith(("$", "models", "tickets", "attempts", "tokens", "python:")):
        return CYAN
    if s.startswith("-" * 6):
        return DIM
    return FG


def render(text: str, title: str = "terminal") -> str:
    lines = text.rstrip("\n").split("\n")
    cols = max([len(l) for l in lines] + [len(title) + 8, 40])
    w = int(cols * CW + PAD * 2)
    h = int(len(lines) * LH + TOP + PAD)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="ui-monospace,SFMono-Regular,'
        f'Menlo,Consolas,monospace" font-size="13.5">',
        f'<rect width="{w}" height="{h}" rx="8" fill="{BG}"/>',
        f'<rect width="{w}" height="{TOP}" rx="8" fill="#1b262b"/>',
        f'<rect y="{TOP-8}" width="{w}" height="8" fill="#1b262b"/>',
    ]
    for i, c in enumerate(("#e0655f", "#e0b341", "#5fb865")):
        out.append(f'<circle cx="{20 + i*17}" cy="{TOP/2}" r="5.5" fill="{c}"/>')
    out.append(f'<text x="{75}" y="{TOP/2 + 4.5}" fill="{DIM}">'
               f'{html.escape(title)}</text>')

    for i, line in enumerate(lines):
        y = TOP + PAD + i * LH - 4
        out.append(f'<text x="{PAD}" y="{y}" fill="{colour(line)}" '
                   f'xml:space="preserve">{html.escape(line)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def _selftest() -> int:
    svg = render("OK: fine\nFAIL: bad\n$ echo <hi> & 'bye'", title="t")
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    assert GREEN in svg and RED in svg
    assert "&lt;hi&gt; &amp; &#x27;bye&#x27;" in svg, "text not XML-escaped"
    assert svg.count("<text") == 4, "expected title + 3 lines"
    print("OK: renders, escapes markup, colours by line kind.")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="terminal")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    p = Path(a.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render(sys.stdin.read(), a.title))
    print(f"wrote {p}")
