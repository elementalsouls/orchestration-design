#!/usr/bin/env python3
"""Generate the README banner.

Full-bleed dark canvas, so one file works on both GitHub themes.

The banner leads with the hook, not the literature. The research is the
differentiator, but "why should I believe you" is the second question a reader
asks — the first is "what is this". So the claim gets the largest block and the
three numbers sit inside the terminal strip at the foot, cited but not competing.

**Every position here is derived, never typed twice.** Three rounds of hand-tuned
coordinates drifted out of alignment in ways that survived an overlap check and
only showed up once someone looked at the picture: a ladder 8px off the page
margin, evidence stats with 49px and 20px gaps, two halves of one footer row on
baselines 4px apart. So the geometry is now expressed as bands and pitches, and
`--selftest` asserts the relationships that matter (shared margins, shared
centres, shared baselines, uniform pitch). Move a band and the parts follow;
break an alignment and the check fails.

What the self-test cannot cover is text *width*, which depends on the renderer's
font metrics — SVG text does not wrap, so a copy change still needs the rendered
result measured before it ships.

    python3 tools/gen_banner.py         -> docs/img/banner.svg
    python3 tools/gen_banner.py --selftest

Self-contained: system font stack, no external references, no <style> media
queries (GitHub does not honour them inside an <img>).
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "img"

# ---- page ------------------------------------------------------------------
W = 1400                                  # H is derived once the bands are laid out
M = 60                                    # page margin, every band honours it
MARGIN_Y = 30                             # top ink to canvas, and canvas to bottom ink

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

# Ink extents above and below the baseline, per font size, measured from
# getBBox() in a real renderer rather than assumed. Balancing padding by
# baseline alone is what put the pillar copy 5px high in its card: a baseline is
# not an edge, and the eye aligns edges.
INK_ASC = {10: 10, 11: 10, 12: 12, 14: 14, 24: 22, 26: 25, 58: 54}
INK_DESC = {10: 2, 11: 2, 12: 3, 14: 3, 24: 6, 26: 6, 58: 14}

LEAD = 8                                  # breathing space under a column header
GAP = 28                                  # the only gap between bands, everywhere

# ---- chrome ----------------------------------------------------------------
CHROME_BASE = MARGIN_Y + INK_ASC[10]      # 40
RULE_Y = CHROME_BASE + INK_DESC[10] + GAP // 2     # 56 — a hairline gets half a gap

# ---- hero band -------------------------------------------------------------
# The wordmark and the two-line hook are one optical block; the ladder and the
# metadata card are centred on it, so all three share a midline.
#
# Bands used to be positioned by hand, which left 64px of dead air under the
# rule, 8px between the hero and the pillars, and 22px between the pillars and
# the terminal — the same total space, distributed so badly the top of the
# banner read as empty. Every band edge below is now derived from GAP.
WORD_X, WORD_SIZE, HOOK_SIZE = 192, 58, 26
HERO_TOP = RULE_Y + GAP                            # 84
WORD_BASE = HERO_TOP + INK_ASC[WORD_SIZE]          # 138
HOOK_BASE_1 = WORD_BASE + INK_DESC[WORD_SIZE] + 17 + INK_ASC[HOOK_SIZE]   # 194
HOOK_BASE_2 = HOOK_BASE_1 + 32                     # 226 — line height for 26px
HERO_BOT = HOOK_BASE_2 + INK_DESC[HOOK_SIZE]       # 232
HERO_MID = (HERO_TOP + HERO_BOT) // 2              # 158

LADDER_STEP, LADDER_OV, NODE_R = 22, 14, 7.5
LADDER_X0 = M + NODE_R                    # lit node's outer edge lands on the margin
LADDER_X1 = LADDER_X0 + 70
# rails run y_base-5*STEP-OV .. y_base+OV, so the midline is y_base - 2.5*STEP
LADDER_BASE = HERO_MID + 2.5 * LADDER_STEP         # 213
LADDER_LIT = 3

META_W, META_H = 300, 118
META_X, META_Y = W - M - META_W, HERO_MID - META_H // 2

# ---- pillar band -----------------------------------------------------------
CARD_Y, CARD_H = HERO_BOT + GAP, 112       # 260
CARD_W = (W - 2 * M - 44) // 3            # 3 cards, two 22px gutters, flush to both margins
CARD_GAP = 22
CARD_PAD_X = 22
PILLAR_HDR = CARD_Y + 34                  # header baseline; see the padding assertion
PILLAR_L1 = PILLAR_HDR + INK_DESC[12] + LEAD + INK_ASC[14] + 5
PILLAR_L2 = PILLAR_L1 + 22

# ---- terminal band ---------------------------------------------------------
TERM_Y, TERM_H = CARD_Y + CARD_H + GAP, 166        # 400
TERM_W = W - 2 * M
TERM_BAR = 36                             # title-bar height
TERM_PAD = 26                             # inner gutter, both sides
TERM_PAD_Y = 24                           # inner gutter, top and bottom of the body
TERM_L = M + TERM_PAD
TERM_R = M + TERM_W - TERM_PAD

# Three rows. The two columns share the header row and the footer row; that is
# what makes them read as one strip rather than two unrelated blocks.
EV_HDR = TERM_Y + TERM_BAR + TERM_PAD_Y + INK_ASC[10]       # 470
EV_BASE = EV_HDR + INK_DESC[10] + LEAD + INK_ASC[24]        # 502
FOOT_BASE = TERM_Y + TERM_H - TERM_PAD_Y - INK_DESC[11]     # 540
H = TERM_Y + TERM_H + MARGIN_Y            # 596 — the canvas is whatever the bands need

EV_PITCH = 310                            # equal pitch: left edges form a grid, and the
                                          # row spans the space rather than clustering left
EV_MAX_W = 221                            # widest rendered stat cell, measured in-browser
EV_GUTTER = 24                            # smallest gap that still reads as separate cells

BOX_W, BOX_H = 320, 44
BOX_X = TERM_R - BOX_W
# centred on the stat row's ink, not on its baseline
BOX_Y = (EV_BASE - INK_ASC[24] + EV_BASE + INK_DESC[24]) // 2 - BOX_H // 2
BOX_BASE = BOX_Y + BOX_H // 2 + 4         # one baseline for everything in the box


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


def ladder_rungs():
    """Level 1 at the bottom, counting up — a ladder is climbed, not read."""
    return {lvl: LADDER_BASE - (lvl - 1) * LADDER_STEP for lvl in range(1, 7)}


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
    y_of = ladder_rungs()
    XL, XR = LADDER_X0, LADDER_X1

    for x in (XL, XR):
        a(f'<line x1="{x}" y1="{y_of[6] - LADDER_OV}" x2="{x}" y2="{y_of[1] + LADDER_OV}" '
          f'stroke="{BORDER}" stroke-width="2" stroke-linecap="round"/>')

    for lvl, y in y_of.items():
        if lvl == LADDER_LIT:
            continue
        op = 0.30 if lvl > LADDER_LIT else 0.62
        a(f'<line x1="{XL}" y1="{y}" x2="{XR}" y2="{y}" stroke="{FAINT}" '
          f'stroke-width="2.5" opacity="{op}" stroke-linecap="round"/>')
        for x in (XL, XR):
            a(f'<circle cx="{x}" cy="{y}" r="4" fill="{FAINT}" opacity="{op + 0.15}"/>')

    ly = y_of[LADDER_LIT]
    a(f'<line x1="{XL}" y1="{ly}" x2="{XR}" y2="{ly}" stroke="{CYAN}" '
      f'stroke-width="4" stroke-linecap="round" filter="url(#glow)"/>')
    for x in (XL, XR):
        a(f'<circle cx="{x}" cy="{ly}" r="{NODE_R}" fill="{CYAN}" filter="url(#glow)"/>')
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
    a(txt(M, CHROME_BASE, "ORCHESTRATION-DESIGN / MAIN / CLAUDE CODE + HERMES",
          10, FAINT, 600, track=2.4))
    a(txt(W - M, CHROME_BASE, "github.com/elementalsouls/orchestration-design",
          10, FAINT, 500, MONO, anchor="end"))
    a(f'<line x1="{M}" y1="{RULE_Y}" x2="{W-M}" y2="{RULE_Y}" stroke="{BORDER}" stroke-width="1"/>')

    a(mark())

    # ---------- wordmark + hook ----------
    # tspans, not separate <text>: the renderer computes advance widths, so the
    # parts cannot collide even where its mono metrics differ from ours
    a(f'<text x="{WORD_X}" y="{WORD_BASE}" font-family="{MONO}" font-size="{WORD_SIZE}" '
      f'font-weight="700" letter-spacing="-2" fill="{INK}">orchestration'
      f'<tspan fill="{FAINT}" font-weight="300"> / </tspan>'
      f'<tspan fill="{CYAN}">design</tspan></text>')
    # the rule must outrun the wordmark (which ends near x=916) or the fade
    # finishes mid-word and reads as a clipped underline rather than a flourish
    a(f'<line x1="{WORD_X}" y1="{WORD_BASE + 20}" x2="980" y2="{WORD_BASE + 20}" '
      f'stroke="url(#rule)" stroke-width="2.5"/>')

    a(txt(WORD_X, HOOK_BASE_1, "Stop paying multi-agent prices", HOOK_SIZE, INK, 700))
    a(txt(WORD_X, HOOK_BASE_2, "for single-agent quality.", HOOK_SIZE, CYAN, 700))

    # ---------- engine metadata card ----------
    a(panel(META_X, META_Y, META_W, META_H))
    a(f'<circle cx="{META_X+20}" cy="{META_Y+24}" r="3.5" fill="{CYAN}" filter="url(#glow)"/>')
    a(txt(META_X + 32, META_Y + 28, "ENGINE METADATA", 10, CYAN_DIM, 700, track=2))
    a(f'<line x1="{META_X+16}" y1="{META_Y+40}" x2="{META_X+META_W-16}" y2="{META_Y+40}" '
      f'stroke="{BORDER}"/>')
    for i, (k, v) in enumerate((("AUTHOR", "Sachin Sharma"),
                                ("ROLE", "AI Systems Engineering"),
                                ("LICENSE", "MIT"))):
        y = META_Y + 56 + i * 22
        a(txt(META_X + 16, y, k, 10, FAINT, 700, track=1.6))
        a(txt(META_X + META_W - 16, y, v, 11.5, BODY, 500, anchor="end"))

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
    for i, (num, label, accent, l1, l2) in enumerate(pillars):
        x = M + i * (CARD_W + CARD_GAP)
        a(panel(x, CARD_Y, CARD_W, CARD_H))
        # accent keyline down the leading edge, so the card reads as tabbed
        a(f'<rect x="{x}" y="{CARD_Y}" width="3" height="{CARD_H}" rx="1.5" fill="{accent}"/>')
        a(txt(x + CARD_PAD_X, PILLAR_HDR, num, 10.5, accent, 700, MONO, track=1.2))
        a(txt(x + CARD_PAD_X + 24, PILLAR_HDR, label, 12, accent, 700, track=2.2))
        a(txt(x + CARD_PAD_X, PILLAR_L1, l1, 14, BODY, 600))
        a(txt(x + CARD_PAD_X, PILLAR_L2, l2, 14, MICRO, 400))

    # ---------- terminal window ----------
    a(panel(M, TERM_Y, TERM_W, TERM_H, rx=9))
    a(f'<path d="M{M} {TERM_Y+9} a9,9 0 0 1 9,-9 h{TERM_W-18} a9,9 0 0 1 9,9 '
      f'v{TERM_BAR-9} h-{TERM_W} z" fill="#0b1324" stroke="{BORDER}" stroke-width="1"/>')
    for j, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        a(f'<circle cx="{M + 22 + j*17}" cy="{TERM_Y + 18}" r="5.5" fill="{c}"/>')
    a(txt(M + TERM_W / 2, TERM_Y + 23, "orchestration-design — the evidence", 10.5, FAINT,
          500, MONO, anchor="middle"))
    a(f'<line x1="{M}" y1="{TERM_Y+TERM_BAR}" x2="{M+TERM_W}" y2="{TERM_Y+TERM_BAR}" '
      f'stroke="{BORDER}"/>')

    # left: the numbers, small on purpose — they answer the second question
    a(txt(TERM_L, EV_HDR, "BACKED BY 2026 AI RESEARCH", 10, FAINT, 700, track=2.2))
    ev = (("90.2%", AMBER, "quoted multi-agent win"),
          ("15×",   AMBER, "tokens it actually cost"),
          ("80%",   CYAN,  "of variance = spend, not architecture"))
    for i, (big, colour, note) in enumerate(ev):
        a(f'<text x="{TERM_L + i * EV_PITCH}" y="{EV_BASE}" font-family="{MONO}" '
          f'font-size="24" font-weight="700" fill="{colour}">{big}'
          f'<tspan font-family="{FONT}" font-size="10" font-weight="500" fill="{MICRO}" '
          f'dx="8">{esc(note)}</tspan></text>')

    # right: the command
    a(panel(BOX_X, BOX_Y, BOX_W, BOX_H, fill="#0b1324", stroke=CYAN, rx=6))
    a(txt(BOX_X + 16, BOX_BASE, "$", 13, GREEN, 700, MONO))
    a(txt(BOX_X + 32, BOX_BASE, "./build.sh", 13, INK, 600, MONO))
    a(f'<rect x="{BOX_X+126}" y="{BOX_BASE-12}" width="8" height="15" fill="{GREEN}" '
      f'opacity="0.85"/>')
    a(txt(BOX_X + BOX_W - 16, BOX_BASE, "installs in seconds", 10, MICRO, 400, MONO,
          anchor="end"))

    # the footer row — one baseline across both columns
    a(txt(TERM_L, FOOT_BASE, "Two follow-ups held compute constant: at matched budgets a "
                             "single agent matched or beat every multi-agent variant.",
          11, MICRO))
    a(txt(TERM_R, FOOT_BASE, "zero lock-in · markdown only · no dependencies", 10, FAINT,
          400, MONO, anchor="end"))

    a("</svg>")
    return "\n".join(o)


def _selftest() -> int:
    """Assert the alignments, because eyeballing them has failed three times.

    Only relationships that are pure geometry are asserted here. Text *widths*
    depend on the renderer's font metrics and cannot be checked without one — a
    copy change still needs measuring in a browser.
    """
    y_of = ladder_rungs()

    # 1. page margins agree top and bottom
    assert CHROME_BASE - INK_ASC[10] == MARGIN_Y, CHROME_BASE
    assert H - (TERM_Y + TERM_H) == MARGIN_Y, H - (TERM_Y + TERM_H)

    # 2. everything that touches the left margin actually touches it
    assert LADDER_X0 - NODE_R == M, LADDER_X0            # the glow node, not the rail
    assert TERM_L - TERM_PAD == M, TERM_L

    # 3. and the right margin
    assert META_X + META_W == W - M
    assert M + 2 * (CARD_W + CARD_GAP) + CARD_W == W - M, CARD_W
    assert M + TERM_W == W - M
    assert BOX_X + BOX_W == TERM_R

    # 4. ladder, metadata card and the title block share one midline
    ladder_mid = ((y_of[6] - LADDER_OV) + (y_of[1] + LADDER_OV)) / 2
    assert ladder_mid == HERO_MID, ladder_mid
    assert META_Y + META_H / 2 == HERO_MID, META_Y
    assert (HERO_TOP + HERO_BOT) / 2 == HERO_MID

    # 5. pillar copy is optically centred in its card — ink edges, not baselines
    top_pad = (PILLAR_HDR - INK_ASC[12]) - CARD_Y
    bot_pad = (CARD_Y + CARD_H) - (PILLAR_L2 + INK_DESC[14])
    assert abs(top_pad - bot_pad) <= 2, (top_pad, bot_pad)

    # 6. the terminal's two columns share the footer baseline. They were 4px
    #    apart — visible, and impossible to justify. Assert against the emitted
    #    SVG, not the constant: a constant only proves what it is set to, and
    #    the bug was one column not using it.
    import re
    foot = re.findall(rf'<text x="([\d.]+)" y="{FOOT_BASE}"', render())
    assert len(foot) == 2, f"expected 2 text nodes on the footer baseline, got {len(foot)}"

    # 7. the stat row is a grid: uniform pitch, cells wide enough for their own
    #    content, and the last one clears the command box
    xs = [TERM_L + i * EV_PITCH for i in range(3)]
    assert len(set(round(b - a) for a, b in zip(xs, xs[1:]))) == 1, xs
    assert EV_PITCH >= EV_MAX_W + EV_GUTTER, EV_PITCH    # uniform but too tight = collision
    assert xs[-1] + EV_MAX_W < BOX_X, (xs[-1], BOX_X)

    # 8. the command box is centred on the stat row's ink
    stat_mid = (EV_BASE - INK_ASC[24] + EV_BASE + INK_DESC[24]) / 2
    assert abs((BOX_Y + BOX_H / 2) - stat_mid) <= 3, (BOX_Y, stat_mid)

    # 9. bands do not collide
    assert y_of[1] + LADDER_OV < CARD_Y, "ladder runs into the pillar row"
    assert META_Y + META_H < CARD_Y, "metadata card runs into the pillar row"
    assert CARD_Y + CARD_H < TERM_Y, "pillar row runs into the terminal"
    assert BOX_Y + BOX_H < FOOT_BASE - INK_ASC[11], "command box runs into the footer"

    # 10. one rhythm down the page. This is the check that was missing: the gaps
    #     had been 64 / 8 / 22, which no assertion above objected to, because
    #     nothing collided — it just left the top of the banner reading as empty.
    gaps = [HERO_TOP - RULE_Y, CARD_Y - HERO_BOT, TERM_Y - (CARD_Y + CARD_H)]
    assert set(gaps) == {GAP}, gaps

    # 11. it renders, and it renders the same way twice
    svg = render()
    assert svg == render()
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    import xml.dom.minidom
    xml.dom.minidom.parseString(svg)

    print("  OK: margins, midlines, baselines, pitch and band clearances all hold.")
    return 0


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Generate the README banner.")
    ap.add_argument("--out", default=None, help="write here instead of docs/img/banner.svg")
    ap.add_argument("--selftest", action="store_true", help="assert the layout, write nothing")
    args = ap.parse_args()

    if args.selftest:
        raise SystemExit(_selftest())

    OUT.mkdir(parents=True, exist_ok=True)
    p = Path(args.out) if args.out else OUT / "banner.svg"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render())
    print(f"  wrote {p} ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
