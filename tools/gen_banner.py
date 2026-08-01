#!/usr/bin/env python3
"""Generate the README banner, light and dark.

The banner is the thesis in one image: the five-box diagram everyone draws,
next to the two-node design the work actually needed. Nothing else on it.

    python3 tools/gen_banner.py      -> docs/img/banner-{light,dark}.svg

Self-contained SVG: system font stack, no external refs, no <style> media
queries (GitHub does not reliably honour them inside an <img>). Two files
plus a <picture> element is the pattern that actually works.
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "img"

THEMES = {
    # surface is transparent; every colour must read on white AND on #0d1117
    "light": dict(ink="#1f2328", muted="#59636e", faint="#8c959f",
                  stale="#adb5bd", accent="#0969da", rule="#d1d9e0"),
    "dark":  dict(ink="#e6edf3", muted="#9198a1", faint="#6e7681",
                  stale="#484f58", accent="#58a6ff", rule="#30363d"),
}

W, H = 1200, 340
FONT = ("ui-sans-serif,-apple-system,'Segoe UI',Roboto,"
        "'Helvetica Neue',Arial,sans-serif")
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def box(x, y, w, h, stroke, label, t, dashed=False, fill="none", weight=1.5):
    dash = ' stroke-dasharray="4 4"' if dashed else ""
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{weight}"{dash}/>'
        f'<text x="{x + w/2}" y="{y + h/2 + 4}" text-anchor="middle" '
        f'font-family="{FONT}" font-size="11" fill="{stroke}">{label}</text>'
    )


def arrow(x1, x2, y, colour, head=5):
    return (f'<line x1="{x1}" y1="{y}" x2="{x2 - head}" y2="{y}" stroke="{colour}" '
            f'stroke-width="1.5"/>'
            f'<path d="M{x2},{y} L{x2 - head - 2},{y - 3.5} L{x2 - head - 2},{y + 3.5} Z" '
            f'fill="{colour}"/>')


def render(name):
    t = THEMES[name]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="orchestration-design. Left: the five-box agent diagram everyone '
         f'draws, greyed out and struck through. Right: the two-node design the work '
         f'actually needed, in blue. Tagline: decide how much orchestration your work '
         f'actually needs. Usually less than you think.">']
    a = o.append

    # ---- wordmark -------------------------------------------------------
    a(f'<text x="60" y="76" font-family="{MONO}" font-size="34" font-weight="600" '
      f'fill="{t["ink"]}" letter-spacing="-0.5">orchestration-design</text>')
    a(f'<text x="60" y="108" font-family="{FONT}" font-size="16" fill="{t["muted"]}">'
      f'Decide how much orchestration your work actually needs — usually less than you think.</text>')
    a(f'<line x1="60" y1="136" x2="{W-60}" y2="136" stroke="{t["rule"]}" stroke-width="1"/>')

    # ---- left: the diagram everyone draws --------------------------------
    a(f'<text x="60" y="176" font-family="{FONT}" font-size="11" font-weight="600" '
      f'letter-spacing="0.09em" fill="{t["faint"]}">WHAT YOU WERE ABOUT TO BUILD</text>')
    labels = ["plan", "research", "write", "review", "format"]
    x, y, bw, bh, gap = 60, 200, 86, 42, 22
    for i, lab in enumerate(labels):
        bx = x + i * (bw + gap)
        a(box(bx, y, bw, bh, t["stale"], lab, t, dashed=True))
        if i < len(labels) - 1:
            a(arrow(bx + bw, bx + bw + gap, y + bh / 2, t["stale"]))
    span = len(labels) * bw + (len(labels) - 1) * gap
    a(f'<line x1="{x - 6}" y1="{y + bh/2}" x2="{x + span + 6}" y2="{y + bh/2}" '
      f'stroke="{t["stale"]}" stroke-width="2"/>')          # struck through
    a(f'<text x="{x}" y="{y + bh + 26}" font-family="{FONT}" font-size="12" '
      f'fill="{t["faint"]}">5 agents · ~15× the tokens · you cannot tell which box was wrong</text>')

    # ---- right: what it actually was ------------------------------------
    rx = x + span + 84
    a(f'<text x="{rx}" y="176" font-family="{FONT}" font-size="11" font-weight="600" '
      f'letter-spacing="0.09em" fill="{t["accent"]}">WHAT THE WORK ACTUALLY NEEDED</text>')
    a(box(rx, y, 116, bh, t["accent"], "agent + tools", t, weight=2))
    a(arrow(rx + 116, rx + 116 + 26, y + bh / 2, t["accent"]))
    a(box(rx + 142, y, 116, bh, t["accent"], "checker", t, weight=2))
    a(f'<text x="{rx}" y="{y + bh + 26}" font-family="{FONT}" font-size="12" '
      f'fill="{t["muted"]}">2 nodes · debuggable with a print statement</text>')

    # ---- footer ---------------------------------------------------------
    a(f'<text x="60" y="{H-28}" font-family="{FONT}" font-size="12.5" fill="{t["muted"]}">'
      f'A Claude Code skill · 12 markdown files · no dependencies, no engine, nothing to run</text>')
    a("</svg>")
    return "\n".join(o)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name in THEMES:
        p = OUT / f"banner-{name}.svg"
        p.write_text(render(name))
        print(f"  wrote {p.relative_to(OUT.parent.parent)} ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
