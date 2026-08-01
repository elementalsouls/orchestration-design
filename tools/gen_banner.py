#!/usr/bin/env python3
"""Generate the README banner.

Full-bleed dark canvas, so one file works on both GitHub themes.

The banner's job is to carry the evidence, because the evidence is the
differentiator. Anyone can claim "you don't need multi-agent". This repo can
put three numbers from controlled experiments on the front page and cite them.

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
      f'role="img" aria-label="orchestration-design. A Claude Code skill that decides how much '
      f'orchestration your work actually needs, and usually concludes it is less than you think. '
      f'The evidence: a widely quoted 90.2 percent multi-agent win used 15 times the tokens, and '
      f'token spend alone explained 80 percent of the performance variance. Six levels, twelve '
      f'markdown files, zero dependencies, eight cited sources, MIT licence.">')

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
    a(txt(60, 40, "ORCHESTRATION-DESIGN / MAIN / CLAUDE CODE SKILL", 10.5, FAINT, 600, track=2.4))
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

    # ---------- feature strip ----------
    for i, (label, x) in enumerate((("DESIGN GATE, NOT A GRAPH BUILDER", 216),
                                    ("EVIDENCE-BACKED", 592),
                                    ("ANY RUNTIME — OR NONE", 800))):
        a(txt(x, 244, "+", 12, TEAL, 700))
        a(txt(x + 13, 244, label, 11, DIM, 600, track=1.5))

    a(txt(216, 278, "Decides how much orchestration your work actually needs — and usually "
                    "concludes it's less than you think.", 15.5, DIM))

    # ---------- metadata card ----------
    bx, by, bw, bh = W - 60 - 268, 96, 268, 108
    a(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="7" fill="{CARD}" '
      f'stroke="{TEAL}" stroke-width="1.2" opacity="0.95"/>')
    a(f'<circle cx="{bx+18}" cy="{by+22}" r="4" fill="{TEAL}"/>')
    a(txt(bx + 30, by + 26, "LOADS ON TOPIC", 10.5, TEAL, 700, track=1.8))
    a(f'<line x1="{bx+16}" y1="{by+38}" x2="{bx+bw-16}" y2="{by+38}" stroke="{RULE}"/>')
    for i, (k, v) in enumerate((("LICENCE", "MIT"), ("AUTHOR", "Sachin Sharma"),
                                ("UPDATED", "2026-08"))):
        y = by + 58 + i * 19
        a(txt(bx + 16, y, k, 9.5, FAINT, 600, track=1.4))
        a(txt(bx + bw - 16, y, v, 10.5, DIM, 500, anchor="end"))

    # ---------- the evidence ----------
    a(f'<line x1="60" y1="322" x2="{W-60}" y2="322" stroke="{RULE}"/>')
    a(txt(60, 350, "THE EVIDENCE — WHY \"LESS THAN YOU THINK\" IS A CLAIM, NOT AN OPINION",
          10.5, FAINT, 700, track=2.2))

    ev = ((60,  "90.2%", AMBER, "the multi-agent win everyone quotes",
           "Anthropic, multi-agent research system"),
          (498, "15×", AMBER, "the token cost in that same footnote",
           "same paper, rarely repeated"),
          (936, "80%", TEAL, "of the variance explained by spend alone",
           "not by architecture"))
    for x, big, colour, line1, line2 in ev:
        a(txt(x, 412, big, 44, colour, 700, MONO, track=-1))
        a(txt(x, 438, line1, 12.5, DIM, 500))
        a(txt(x, 456, line2, 11, FAINT, 400))

    a(txt(60, 492, "Two follow-ups held compute constant. Under matched budgets a single agent was "
                   "best or statistically indistinguishable from best at every budget but the lowest.",
          12.5, DIM))

    # ---------- stats + install ----------
    a(f'<line x1="60" y1="516" x2="{W-60}" y2="516" stroke="{RULE}"/>')
    stats = (("6", "LEVELS"), ("12", "FILES"), ("0", "DEPENDENCIES"),
             ("8", "CITED SOURCES"), ("13", "DEFECTS SELF-FOUND"))
    for i, (n, lab) in enumerate(stats):
        x = 60 + i * 138
        a(f'<text x="{x}" y="552" font-family="{MONO}" font-size="27" font-weight="700" '
          f'fill="{TEAL}">{n}'
          f'<tspan font-family="{FONT}" font-size="9.5" font-weight="600" fill="{FAINT}" '
          f'letter-spacing="1.3" dx="7"> {lab}</tspan></text>')

    a(f'<rect x="{W-60-430}" y="530" width="430" height="30" rx="5" fill="{CARD}" stroke="{RULE}"/>')
    a(txt(W - 60 - 414, 550, "$", 11.5, TEAL, 700, MONO))
    a(txt(W - 60 - 400, 550, "./build.sh", 11.5, INK, 500, MONO))
    a(txt(W - 60 - 16, 550, "installs in seconds · zero lock-in", 10, FAINT, 400, MONO, anchor="end"))

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
