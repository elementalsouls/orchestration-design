#!/usr/bin/env python3
"""Generate the README banner.

Full-bleed dark canvas, so one file works on both GitHub themes.

The banner leads with the hook, not the literature. The research is the
differentiator, but "why should I believe you" is the second question a reader
asks — the first is "what is this". So the claim gets the largest block and the
three numbers sit condensed underneath, cited but not competing.

Layout is hand-positioned and SVG text does not wrap, so any copy change needs
the rendered result measured: every text node must stay inside the right margin
or a column runs into its neighbour on a renderer whose font metrics differ.

    python3 tools/gen_banner.py      -> docs/img/banner.svg

Self-contained: system font stack, no external references, no <style> media
queries (GitHub does not honour them inside an <img>).
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "img"
W, H = 1400, 580

BG0, BG1 = "#0b0f1a", "#141b2e"          # canvas gradient
INK = "#e8edf7"                           # primary text
DIM = "#8f9bb3"                           # secondary text
FAINT = "#5a6580"                         # labels, chrome
RULE = "#232c42"                          # hairlines
TEAL = "#3ddad0"                          # primary accent — measured, evidence
AMBER = "#f2b544"                         # secondary — the "no", the struck-through
CARD = "#151d31"

FONT = ("ui-sans-serif,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif")
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, s, size=12, fill=INK, weight=400, font=FONT, anchor="start",
        track=0, opacity=1):
    ls = f' letter-spacing="{track}"' if track else ""
    op = f' opacity="{opacity}"' if opacity != 1 else ""
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{font}" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}"{ls}{op}>{esc(s)}</text>')


def mark():
    """The identity mark: the ladder, with level 3 lit.

    Deliberately NOT a graph. The previous mark was a ring of nodes all wired to
    a bright centre — which is a supervisor with five workers, the exact topology
    this skill exists to argue against. A logo that asserts the opposite of the
    thesis is worse than no logo.

    The ladder is the actual product: six levels, stop at the first one that
    holds, and level 3 is the default. Rails matter — six bars without them read
    as a hamburger menu or a bar chart. Rungs above the lit one are dimmest:
    those are the climbs you rarely need.
    """
    o = []
    a = o.append

    X0, X1 = 94, 160                        # rails
    LIT = 3                                 # the default level
    y_of = {lvl: 217 - (lvl - 1) * 19 for lvl in range(1, 7)}

    a(f'<line x1="{X0}" y1="112" x2="{X0}" y2="227" stroke="{FAINT}" '
      f'stroke-width="1.6" opacity="0.5"/>')
    a(f'<line x1="{X1}" y1="112" x2="{X1}" y2="227" stroke="{FAINT}" '
      f'stroke-width="1.6" opacity="0.5"/>')

    for lvl, y in y_of.items():
        if lvl == LIT:
            continue
        # above the default is dimmer than below it: 1 and 2 are common correct
        # outcomes, 4 to 6 are the rare earned climbs
        op = 0.28 if lvl > LIT else 0.55
        a(f'<line x1="{X0}" y1="{y}" x2="{X1}" y2="{y}" stroke="{FAINT}" '
          f'stroke-width="3" opacity="{op}" stroke-linecap="round"/>')

    ly = y_of[LIT]
    a(f'<line x1="{X0}" y1="{ly}" x2="{X1}" y2="{ly}" stroke="{TEAL}" '
      f'stroke-width="4.5" stroke-linecap="round"/>')
    a(f'<circle cx="82" cy="{ly}" r="4.5" fill="{TEAL}"/>')      # you are here
    a(f'<text x="170" y="{ly + 4}" font-family="{MONO}" font-size="11" '
      f'font-weight="700" fill="{TEAL}">3</text>')

    return "\n".join(o)


def render():
    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
      f'role="img" aria-label="orchestration-design, a skill for Claude Code and Hermes. '
      f'Stop paying multi-agent prices for single-agent quality. '
      f'The gatekeeper: decides exactly how much orchestration your pipeline actually needs. '
      f'The emergency brake: tactical micro-skills to snap agents out of endless execution loops. '
      f'Runtime free: designs built for plain code, LangGraph, or any framework you choose. '
      f'Backed by 2026 AI research — a quoted 90.2 percent multi-agent win cost 15 times the '
      f'tokens, and 80 percent of the variance was spend rather than architecture. '
      f'Built by Sachin Sharma, bug hunting and GenAI security research. '
      f'Installs in seconds with build.sh.">')

    # ---------- canvas ----------
    a('<defs>'
      f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
      f'<stop offset="0%" stop-color="{BG0}"/><stop offset="100%" stop-color="{BG1}"/></linearGradient>'
      f'<linearGradient id="glow" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0%" stop-color="{TEAL}" stop-opacity="0.16"/>'
      f'<stop offset="60%" stop-color="{TEAL}" stop-opacity="0"/></linearGradient>'
      f'<linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0%" stop-color="{TEAL}" stop-opacity="0.55"/>'
      f'<stop offset="100%" stop-color="{TEAL}" stop-opacity="0"/></linearGradient>'
      '</defs>')
    a(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    a(f'<rect width="{W}" height="{H}" fill="url(#glow)"/>')

    # ---------- chrome ----------
    a(txt(60, 40, "ORCHESTRATION-DESIGN / MAIN / CLAUDE CODE + HERMES", 10.5, FAINT, 600, track=2.4))
    a(txt(W - 60, 40, "github.com/elementalsouls/orchestration-design", 10.5, FAINT,
          500, MONO, anchor="end"))
    a(f'<line x1="60" y1="58" x2="{W-60}" y2="58" stroke="{RULE}" stroke-width="1"/>')

    a(mark())

    # ---------- wordmark ----------
    # one <text> with tspans: the renderer computes advance widths, so the parts
    # cannot overlap even if its mono metrics differ from the generator's
    a(f'<text x="214" y="196" font-family="{MONO}" font-size="62" font-weight="700" '
      f'letter-spacing="-2" fill="{INK}">orchestration'
      f'<tspan fill="{FAINT}" font-weight="300"> / </tspan>'
      f'<tspan fill="{TEAL}">design</tspan></text>')
    a(f'<line x1="214" y1="216" x2="880" y2="216" stroke="url(#rule)" stroke-width="2.5"/>')

    # ---------- the hook ----------
    # The one sentence someone should carry away. Sized to dominate: if a reader
    # takes nothing else off this image, it should be this.
    a(txt(214, 256, "Stop paying multi-agent prices", 27, INK, 700))
    a(txt(214, 290, "for single-agent quality.", 27, TEAL, 700))

    # ---------- author ----------
    # Right-aligned into the dead space beside the hook. It was previously a
    # three-row card sitting directly under the headline, where it competed with
    # the one sentence that matters; out here it credits without arguing.
    a(f'<line x1="{W-60}" y1="238" x2="{W-60}" y2="298" stroke="{RULE}" stroke-width="2"/>')
    a(txt(W - 76, 256, "BUILT BY", 9.5, FAINT, 700, track=2.2, anchor="end"))
    a(txt(W - 76, 276, "Sachin Sharma", 15, INK, 600, anchor="end"))
    a(txt(W - 76, 293, "Bug hunting & GenAI security research", 10.5, DIM, 400, anchor="end"))

    # ---------- the two engines, plus the portability ----------
    # Three columns because the product genuinely has three claims and the old
    # paragraph buried all of them. Label in accent, copy in two fixed lines —
    # wrapped by hand because SVG <text> does not wrap and a renderer that
    # disagrees with our metrics would otherwise run a column into its neighbour.
    a(f'<line x1="60" y1="340" x2="{W-60}" y2="340" stroke="{RULE}"/>')

    cols = (
        (60,   "01", "THE GATEKEEPER",      TEAL,
         "Decides exactly how much orchestration",
         "your pipeline actually needs."),
        (520,  "02", "THE EMERGENCY BRAKE", AMBER,
         "Tactical micro-skills to snap agents out",
         "of endless execution loops."),
        (980,  "03", "RUNTIME FREE",        TEAL,
         "Designs built for plain code, LangGraph,",
         "or any framework you choose."),
    )
    for x, num, label, colour, l1, l2 in cols:
        a(f'<line x1="{x}" y1="370" x2="{x}" y2="440" stroke="{colour}" '
          f'stroke-width="2.5" opacity="0.85"/>')
        a(txt(x + 16, 384, num, 10, colour, 700, MONO, track=1.2))
        a(txt(x + 40, 384, label, 12, colour, 700, track=2.2))
        a(txt(x + 16, 412, l1, 14.5, INK, 500))
        a(txt(x + 16, 433, l2, 14.5, DIM, 400))

    # ---------- evidence, condensed to a footnote ----------
    # Deliberately small. The numbers are the differentiator but they are not the
    # hook — they answer "why should I believe you", which is the second question
    # a reader asks, not the first.
    a(f'<line x1="60" y1="478" x2="{W-60}" y2="478" stroke="{RULE}"/>')
    a(txt(60, 504, "BACKED BY 2026 AI RESEARCH", 10, FAINT, 700, track=2.2))

    ev = ((60,  "90.2%", AMBER, "quoted multi-agent win"),
          (255, "15×",   AMBER, "tokens it actually cost"),
          (420, "80%",   TEAL,  "of variance = spend, not architecture"))
    for x, big, colour, note in ev:
        a(f'<text x="{x}" y="542" font-family="{MONO}" font-size="24" font-weight="700" '
          f'fill="{colour}">{big}'
          f'<tspan font-family="{FONT}" font-size="10" font-weight="500" fill="{DIM}" '
          f'dx="8">{esc(note)}</tspan></text>')

    # ---------- install ----------
    a(f'<rect x="{W-60-372}" y="518" width="372" height="32" rx="5" fill="{CARD}" '
      f'stroke="{TEAL}" stroke-width="1.1" opacity="0.9"/>')
    a(txt(W - 60 - 356, 539, "$", 12, TEAL, 700, MONO))
    a(txt(W - 60 - 342, 539, "./build.sh", 12, INK, 600, MONO))
    a(txt(W - 60 - 16, 539, "installs in seconds", 10.5, FAINT, 400, MONO, anchor="end"))

    a("</svg>")
    return "\n".join(o)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Generate the README banner.")
    ap.add_argument("--out", default=None, help="write here instead of docs/img/banner.svg")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    p = Path(args.out) if args.out else OUT / "banner.svg"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render())
    print(f"  wrote {p} ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
