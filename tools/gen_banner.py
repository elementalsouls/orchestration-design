#!/usr/bin/env python3
"""Generate the README banner.

Full-bleed dark canvas, so one file works on both GitHub themes.

The banner leads with the hook, not the literature. The research is the
differentiator, but "why should I believe you" is the second question a reader
asks — the first is "what is this". So the claim gets the largest block and the
three numbers sit inside the terminal strip at the foot, cited but not competing.

Layout is hand-positioned and SVG text does not wrap, so any copy change needs
the rendered result measured: every text node must stay inside its container or
a column runs into its neighbour on a renderer whose font metrics differ.
Geometry is derived from the band constants rather than typed twice — move a
band's y or change CARD_W and the pieces follow.

    python3 tools/gen_banner.py      -> docs/img/banner.svg

Self-contained: system font stack, no external references, no <style> media
queries (GitHub does not honour them inside an <img>).
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "img"
W, H = 1400, 610
M = 60                                    # page margin

BG0, BG1 = "#0b1120", "#131c31"           # canvas gradient
PANEL = "#0f172a"                         # card fill
BORDER = "#1e293b"                        # card keyline
INK = "#f1f5f9"                           # headline white
BODY = "#e2e8f0"                          # card body text
MICRO = "#94a3b8"                         # muted micro-copy — slate, not grey
FAINT = "#64748b"                         # chrome, labels
CYAN = "#00f0ff"                          # primary accent
CYAN_DIM = "#3fbdca"                      # accent at small-label weight
AMBER = "#ff9f1c"                         # the cost, the warning, the brake
GREEN = "#4ade80"                         # shell prompt

FONT = "ui-sans-serif,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# ---- bands (the whole vertical budget, in one place) ------------------------
HERO_Y = 122                              # metadata card top — set to the wordmark's cap height,
                                          # so the card's top edge and the letterforms share a line
CARD_Y, CARD_H = 278, 112                 # pillar row
TERM_Y, TERM_H = 412, 166                 # terminal window
CARD_W = (W - 2 * M - 44) // 3            # 3 cards, two 22px gutters
LEAD = 8                                  # spacing under a column header


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, s, size=12, fill=INK, weight=400, font=FONT, anchor="start",
        track=0, opacity=1):
    ls = f' letter-spacing="{track}"' if track else ""
    op = f' opacity="{opacity}"' if opacity != 1 else ""
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{font}" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}"{ls}{op}>{esc(s)}</text>')


def panel(x, y, w, h, fill=PANEL, stroke=BORDER, rx=8, sw=1):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>')


def mark():
    """The identity mark: a six-level node ladder, level 3 lit.

    Deliberately NOT a graph of agents. An earlier mark was a ring of nodes wired
    to a bright centre — a supervisor with five workers, the exact topology this
    skill argues against. A logo asserting the opposite of the thesis is worse
    than no logo.

    Six levels, nodes on each rail, and only level 3 glows: that is the product
    in one glyph. The rails read as structure; without them six bars look like a
    menu icon. Levels above the lit one are dimmest — those are the climbs you
    rarely earn.
    """
    o = []
    a = o.append

    XL, XR = 76, 146                      # rails
    LIT, STEP = 3, 24
    # level 1 at the bottom, counting up — a ladder is climbed, not read.
    # Base is tuned so the rails' midpoint lands on the title block's optical
    # centre (wordmark cap to headline baseline), measured, not eyeballed.
    y_of = {lvl: 246 - (lvl - 1) * STEP for lvl in range(1, 7)}

    for x in (XL, XR):
        a(f'<line x1="{x}" y1="{y_of[6] - 17}" x2="{x}" y2="{y_of[1] + 17}" '
          f'stroke="{BORDER}" stroke-width="2" stroke-linecap="round"/>')

    for lvl, y in y_of.items():
        if lvl == LIT:
            continue
        op = 0.30 if lvl > LIT else 0.62
        a(f'<line x1="{XL}" y1="{y}" x2="{XR}" y2="{y}" stroke="{FAINT}" '
          f'stroke-width="2.5" opacity="{op}" stroke-linecap="round"/>')
        for x in (XL, XR):
            a(f'<circle cx="{x}" cy="{y}" r="4" fill="{FAINT}" opacity="{op + 0.15}"/>')

    ly = y_of[LIT]
    a(f'<line x1="{XL}" y1="{ly}" x2="{XR}" y2="{ly}" stroke="{CYAN}" '
      f'stroke-width="4" stroke-linecap="round" filter="url(#glow)"/>')
    for x in (XL, XR):
        a(f'<circle cx="{x}" cy="{ly}" r="7.5" fill="{CYAN}" filter="url(#glow)"/>')
        a(f'<circle cx="{x}" cy="{ly}" r="3" fill="{BG0}"/>')
    a(f'<text x="{XR + 16}" y="{ly + 5}" font-family="{MONO}" font-size="13" '
      f'font-weight="700" fill="{CYAN}">3</text>')
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
      f'Built by Sachin Sharma, AI systems engineering, MIT licence. '
      f'Installs in seconds with build.sh.">')

    # ---------- defs ----------
    a('<defs>'
      f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
      f'<stop offset="0%" stop-color="{BG0}"/><stop offset="100%" stop-color="{BG1}"/></linearGradient>'
      f'<linearGradient id="wash" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0%" stop-color="{CYAN}" stop-opacity="0.10"/>'
      f'<stop offset="55%" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>'
      f'<linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0%" stop-color="{CYAN}" stop-opacity="0.6"/>'
      f'<stop offset="100%" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>'
      '<filter id="glow" x="-150%" y="-150%" width="400%" height="400%">'
      '<feGaussianBlur stdDeviation="3.2" result="b"/>'
      '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
      '</filter>'
      '</defs>')
    a(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    a(f'<rect width="{W}" height="{H}" fill="url(#wash)"/>')

    # ---------- chrome ----------
    a(txt(M, 40, "ORCHESTRATION-DESIGN / MAIN / CLAUDE CODE + HERMES", 10.5, FAINT, 600, track=2.4))
    a(txt(W - M, 40, "github.com/elementalsouls/orchestration-design", 10.5, FAINT,
          500, MONO, anchor="end"))
    a(f'<line x1="{M}" y1="58" x2="{W-M}" y2="58" stroke="{BORDER}" stroke-width="1"/>')

    a(mark())

    # ---------- wordmark + hook ----------
    # tspans, not separate <text>: the renderer computes advance widths, so the
    # parts cannot collide even where its mono metrics differ from ours
    a(f'<text x="192" y="176" font-family="{MONO}" font-size="58" font-weight="700" '
      f'letter-spacing="-2" fill="{INK}">orchestration'
      f'<tspan fill="{FAINT}" font-weight="300"> / </tspan>'
      f'<tspan fill="{CYAN}">design</tspan></text>')
    # the rule must outrun the wordmark (which ends near x=916) or the fade
    # finishes mid-word and reads as a clipped underline rather than a flourish
    a(f'<line x1="192" y1="196" x2="980" y2="196" stroke="url(#rule)" stroke-width="2.5"/>')

    a(txt(192, 232, "Stop paying multi-agent prices", 26, INK, 700))
    a(txt(192, 264, "for single-agent quality.", 26, CYAN, 700))

    # ---------- engine metadata card ----------
    mw, mh = 300, 118
    mx, my = W - M - mw, HERO_Y
    a(panel(mx, my, mw, mh))
    a(f'<circle cx="{mx+20}" cy="{my+24}" r="3.5" fill="{CYAN}" filter="url(#glow)"/>')
    a(txt(mx + 32, my + 28, "ENGINE METADATA", 10, CYAN_DIM, 700, track=2))
    a(f'<line x1="{mx+16}" y1="{my+40}" x2="{mx+mw-16}" y2="{my+40}" stroke="{BORDER}"/>')
    for i, (k, v) in enumerate((("AUTHOR", "Sachin Sharma"),
                                ("ROLE", "AI Systems Engineering"),
                                ("LICENSE", "MIT"))):
        y = my + 62 + i * 22
        a(txt(mx + 16, y, k, 9.5, FAINT, 700, track=1.6))
        a(txt(mx + mw - 16, y, v, 11.5, BODY, 500, anchor="end"))

    # ---------- pillar cards ----------
    # Three cards because the product genuinely has three claims and a paragraph
    # buries all of them. Copy is hand-wrapped to two fixed lines: SVG <text>
    # does not wrap, so a renderer disagreeing with our metrics would otherwise
    # run a card's copy past its own border.
    pillars = (
        ("01", "THE GATEKEEPER", CYAN,
         "Decides exactly how much orchestration", "your pipeline actually needs."),
        ("02", "THE EMERGENCY BRAKE", AMBER,
         "Tactical micro-skills to snap agents out", "of endless execution loops."),
        ("03", "RUNTIME FREE", CYAN,
         "Designs built for plain code, LangGraph,", "or any framework you choose."),
    )
    hdr = CARD_Y + 30
    for i, (num, label, accent, l1, l2) in enumerate(pillars):
        x = M + i * (CARD_W + 22)
        a(panel(x, CARD_Y, CARD_W, CARD_H))
        # accent keyline down the leading edge, so the card reads as tabbed
        a(f'<rect x="{x}" y="{CARD_Y}" width="3" height="{CARD_H}" rx="1.5" fill="{accent}"/>')
        a(txt(x + 22, hdr, num, 10.5, accent, 700, MONO, track=1.2))
        a(txt(x + 46, hdr, label, 12, accent, 700, track=2.2))
        a(txt(x + 22, hdr + 14 + LEAD + 8, l1, 14, BODY, 600))
        a(txt(x + 22, hdr + 14 + LEAD + 30, l2, 14, MICRO, 400))

    # ---------- terminal window ----------
    tw = W - 2 * M
    a(panel(M, TERM_Y, tw, TERM_H, rx=9))
    a(f'<path d="M{M} {TERM_Y+9} a9,9 0 0 1 9,-9 h{tw-18} a9,9 0 0 1 9,9 v27 h-{tw} z" '
      f'fill="#0b1324" stroke="{BORDER}" stroke-width="1"/>')
    for j, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        a(f'<circle cx="{M + 22 + j*17}" cy="{TERM_Y + 18}" r="5.5" fill="{c}"/>')
    a(txt(M + tw / 2, TERM_Y + 23, "orchestration-design — the evidence", 10.5, FAINT,
          500, MONO, anchor="middle"))
    a(f'<line x1="{M}" y1="{TERM_Y+36}" x2="{M+tw}" y2="{TERM_Y+36}" stroke="{BORDER}"/>')

    # left: the numbers, small on purpose — they answer the second question
    a(txt(M + 26, TERM_Y + 66, "BACKED BY 2026 AI RESEARCH", 10, FAINT, 700, track=2.2))
    ev = ((0,   "90.2%", AMBER, "quoted multi-agent win"),
          (236, "15×",   AMBER, "tokens it actually cost"),
          (408, "80%",   CYAN,  "of variance = spend, not architecture"))
    for dx, big, colour, note in ev:
        a(f'<text x="{M + 26 + dx}" y="{TERM_Y + 66 + 14 + LEAD + 16}" font-family="{MONO}" '
          f'font-size="24" font-weight="700" fill="{colour}">{big}'
          f'<tspan font-family="{FONT}" font-size="10" font-weight="500" fill="{MICRO}" '
          f'dx="8">{esc(note)}</tspan></text>')
    a(txt(M + 26, TERM_Y + 134, "Two follow-ups held compute constant: at matched budgets a "
                                "single agent matched or beat every multi-agent variant.",
          11, MICRO))

    # right: the command
    bw, bh = 320, 42
    bx, by = M + tw - 26 - bw, TERM_Y + 74
    a(panel(bx, by, bw, bh, fill="#0b1324", stroke=CYAN, rx=6))
    a(txt(bx + 16, by + 27, "$", 13, GREEN, 700, MONO))
    a(txt(bx + 32, by + 27, "./build.sh", 13, INK, 600, MONO))
    a(f'<rect x="{bx+126}" y="{by+15}" width="8" height="15" fill="{GREEN}" opacity="0.85"/>')
    a(txt(bx + bw - 16, by + 27, "installs in seconds", 10, MICRO, 400, MONO, anchor="end"))
    a(txt(bx + bw - 16, by + bh + 22, "zero lock-in · markdown only · no dependencies", 10,
          FAINT, 400, MONO, anchor="end"))

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
