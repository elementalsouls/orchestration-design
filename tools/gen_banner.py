#!/usr/bin/env python3
"""Generate the README banner.

Full-bleed dark canvas, so one file works on both GitHub themes.

The banner leads with the hook, not the literature. The research is the
differentiator, but "why should I believe you" is the second question a reader
asks — the first is "what is this". So the claim gets the largest block, the
three numbers sit in a band of their own, and the install line gets a terminal
window to itself.

**Every position here is derived, never typed twice.** Rounds of hand-tuned
coordinates drifted in ways an overlap check could not see — a ladder 8px off
the page margin, evidence stats with 49px and 20px gaps, two halves of one row
on baselines 4px apart, and 64px of dead air under the chrome rule while the
hero sat 8px off the pillars. So the layout is expressed as bands, gaps and
pitches, and `--selftest` asserts the relationships that matter. Move a band and
the parts follow; break an alignment and the check fails.

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
# Panels have to sit *above* the canvas, not inside its range. #0f172a landed
# between the two gradient stops, so the cards dissolved into the background and
# read as loose text beside a coloured line. This is lighter than either stop, so
# a card is a container at a glance.
PANEL = "#16203a"
TERMINAL = "#0b1120"                      # the window is a hole, darker than the page
TERM_BAR_FILL = "#141d33"
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
WORD_X, WORD_SIZE, HOOK_SIZE = 208, 58, 26
HERO_TOP = RULE_Y + GAP                            # 84
WORD_BASE = HERO_TOP + INK_ASC[WORD_SIZE]          # 138
HOOK_BASE_1 = WORD_BASE + INK_DESC[WORD_SIZE] + 17 + INK_ASC[HOOK_SIZE]   # 194
HOOK_BASE_2 = HOOK_BASE_1 + 32                     # 226 — line height for 26px
HERO_BOT = HOOK_BASE_2 + INK_DESC[HOOK_SIZE]       # 232
HERO_MID = (HERO_TOP + HERO_BOT) // 2              # 158
HERO_H = HERO_BOT - HERO_TOP                       # 148

# ---- the ladder mark -------------------------------------------------------
# STEP is chosen so the rails span exactly the hero block: 5 gaps plus two
# overhangs == HERO_H. That is the "match the text block" requirement expressed
# as arithmetic instead of a number someone eyeballed once.
LADDER_OV = 14                                     # rail overhang past the end rungs
LADDER_STEP = (HERO_H - 2 * LADDER_OV) // 5        # 24
LADDER_SPAN = 92                                   # rail separation
NODE_R, DIM_R = 9, 5                               # lit node, dim node
RAIL_SW, RUNG_SW, LIT_SW = 3, 4, 5.5
LADDER_X0 = M + NODE_R                    # lit node's outer edge lands on the margin
LADDER_X1 = LADDER_X0 + LADDER_SPAN
# rails run y_base-5*STEP-OV .. y_base+OV, so the midline is y_base - 2.5*STEP
LADDER_BASE = HERO_MID + 2.5 * LADDER_STEP         # 218
LADDER_LIT = 3

META_W, META_H = 300, 118
META_X, META_Y = W - M - META_W, HERO_MID - META_H // 2

# ---- pillar band -----------------------------------------------------------
CARD_Y, CARD_H = HERO_BOT + GAP, 112       # 260
CARD_W = (W - 2 * M - 44) // 3            # 3 cards, two 22px gutters, flush to both margins
CARD_GAP = 22
CARD_PAD_X = 22
CARD_X = [M + i * (CARD_W + CARD_GAP) for i in range(3)]
PILLAR_HDR = CARD_Y + 34                  # header baseline; see the padding assertion
PILLAR_L1 = PILLAR_HDR + INK_DESC[12] + LEAD + INK_ASC[14] + 5
PILLAR_L2 = PILLAR_L1 + 22

# ---- evidence band ---------------------------------------------------------
# Lifted out of the terminal window. It was a bordered box inside a bordered box
# inside a bordered strip, which is three containers competing to be the frame.
# On the open canvas the numbers carry themselves, and the row inherits the
# pillar grid above it — the stats sit on the same three x positions as the
# cards, so the two bands lock together instead of merely stacking.
EV_TOP = CARD_Y + CARD_H + GAP                              # 400
EV_HDR = EV_TOP + INK_ASC[10]                               # 410
EV_BASE = EV_HDR + INK_DESC[10] + LEAD + INK_ASC[24]        # 442
EV_FOOT = EV_BASE + INK_DESC[24] + 22 + INK_ASC[11]         # 480
EV_BOT = EV_FOOT + INK_DESC[11]                             # 482
EV_PITCH = CARD_W + CARD_GAP                                # 434 — the pillar grid
EV_MAX_W = 221                            # widest rendered stat cell, measured in-browser

# ---- terminal band ---------------------------------------------------------
# One job now: the install line. Centred prompt, tagline on the right.
TERM_Y = EV_BOT + GAP                                       # 510
TERM_W = W - 2 * M
TERM_BAR = 36                             # title-bar height
TERM_PAD = 26                             # inner gutter, both sides
TERM_BODY_PAD = 16                        # above and below the command's ink
CMD_SIZE, TAG_SIZE = 24, 11
TERM_H = TERM_BAR + 2 * TERM_BODY_PAD + INK_ASC[CMD_SIZE] + INK_DESC[CMD_SIZE]   # 96
TERM_L = M + TERM_PAD
TERM_R = M + TERM_W - TERM_PAD
CMD_BASE = TERM_Y + TERM_BAR + TERM_BODY_PAD + INK_ASC[CMD_SIZE]                 # 584
# the tagline is centred on the command's *ink*, not parked on its baseline —
# two different sizes sharing a baseline do not look vertically centred
CMD_MID = CMD_BASE - (INK_ASC[CMD_SIZE] - INK_DESC[CMD_SIZE]) / 2                # 576
TAG_BASE = CMD_MID + (INK_ASC[TAG_SIZE] - INK_DESC[TAG_SIZE]) / 2                # 580

H = TERM_Y + TERM_H + MARGIN_Y            # 636 — the canvas is whatever the bands need


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
          f'stroke="{BORDER}" stroke-width="{RAIL_SW}" stroke-linecap="round"/>')

    for lvl, y in y_of.items():
        if lvl == LADDER_LIT:
            continue
        op = 0.30 if lvl > LADDER_LIT else 0.62
        a(f'<line x1="{XL}" y1="{y}" x2="{XR}" y2="{y}" stroke="{FAINT}" '
          f'stroke-width="{RUNG_SW}" opacity="{op}" stroke-linecap="round"/>')
        for x in (XL, XR):
            a(f'<circle cx="{x}" cy="{y}" r="{DIM_R}" fill="{FAINT}" opacity="{op + 0.15}"/>')

    ly = y_of[LADDER_LIT]
    a(f'<line x1="{XL}" y1="{ly}" x2="{XR}" y2="{ly}" stroke="{CYAN}" '
      f'stroke-width="{LIT_SW}" stroke-linecap="round" filter="url(#glow)"/>')
    for x in (XL, XR):
        # halo, then the disc, then a punched-out centre: the halo is what makes
        # the node read as emitting light rather than merely being cyan
        a(f'<circle cx="{x}" cy="{ly}" r="{NODE_R + 8}" fill="{CYAN}" opacity="0.13"/>')
        a(f'<circle cx="{x}" cy="{ly}" r="{NODE_R + 3.5}" fill="{CYAN}" opacity="0.22"/>')
        a(f'<circle cx="{x}" cy="{ly}" r="{NODE_R}" fill="{CYAN}" filter="url(#glow)"/>')
        a(f'<circle cx="{x}" cy="{ly}" r="{NODE_R - 5}" fill="{BG0}"/>')
    a(f'<text x="{XR + 20}" y="{ly + 5}" font-family="{MONO}" font-size="14" '
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
      f'Install by running build.sh: installs in seconds, zero lock-in.">')

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
      '<feGaussianBlur stdDeviation="3.6" result="b"/>'
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
    # the rule must outrun the wordmark or the fade finishes mid-word and reads
    # as a clipped underline rather than a flourish
    a(f'<line x1="{WORD_X}" y1="{WORD_BASE + 20}" x2="1000" y2="{WORD_BASE + 20}" '
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
    for x, (num, label, accent, l1, l2) in zip(CARD_X, pillars):
        a(panel(x, CARD_Y, CARD_W, CARD_H))
        # accent keyline down the leading edge, so the card reads as tabbed
        a(f'<rect x="{x}" y="{CARD_Y}" width="3" height="{CARD_H}" rx="1.5" fill="{accent}"/>')
        a(txt(x + CARD_PAD_X, PILLAR_HDR, num, 10.5, accent, 700, MONO, track=1.2))
        a(txt(x + CARD_PAD_X + 24, PILLAR_HDR, label, 12, accent, 700, track=2.2))
        a(txt(x + CARD_PAD_X, PILLAR_L1, l1, 14, BODY, 600))
        a(txt(x + CARD_PAD_X, PILLAR_L2, l2, 14, MICRO, 400))

    # ---------- evidence band (no container — see the constants) ----------
    a(txt(M, EV_HDR, "BACKED BY 2026 AI RESEARCH", 10, FAINT, 700, track=2.2))
    ev = (("90.2%", AMBER, "quoted multi-agent win"),
          ("15×",   AMBER, "tokens it actually cost"),
          ("80%",   CYAN,  "of variance = spend, not architecture"))
    for x, (big, colour, note) in zip(CARD_X, ev):
        a(f'<text x="{x}" y="{EV_BASE}" font-family="{MONO}" font-size="{CMD_SIZE}" '
          f'font-weight="700" fill="{colour}">{big}'
          f'<tspan font-family="{FONT}" font-size="10" font-weight="500" fill="{MICRO}" '
          f'dx="8">{esc(note)}</tspan></text>')
    a(txt(M, EV_FOOT, "Two follow-ups held compute constant: at matched budgets a single "
                      "agent matched or beat every multi-agent variant.", 11, MICRO))

    # ---------- terminal window ----------
    a(panel(M, TERM_Y, TERM_W, TERM_H, fill=TERMINAL, rx=9))
    a(f'<path d="M{M} {TERM_Y+9} a9,9 0 0 1 9,-9 h{TERM_W-18} a9,9 0 0 1 9,9 '
      f'v{TERM_BAR-9} h-{TERM_W} z" fill="{TERM_BAR_FILL}" stroke="{BORDER}" stroke-width="1"/>')
    for j, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        a(f'<circle cx="{M + 22 + j*17}" cy="{TERM_Y + 18}" r="5.5" fill="{c}"/>')
    a(txt(W / 2, TERM_Y + 23, "orchestration-design — install", 10.5, FAINT,
          500, MONO, anchor="middle"))
    a(f'<line x1="{M}" y1="{TERM_Y+TERM_BAR}" x2="{M+TERM_W}" y2="{TERM_Y+TERM_BAR}" '
      f'stroke="{BORDER}"/>')

    # the command, centred. One <text> with tspans and anchor="middle": the
    # renderer measures the parts, so a mono stack with different advance widths
    # still centres exactly — hand-computing the width would not survive that.
    a(f'<text x="{W/2}" y="{CMD_BASE}" text-anchor="middle" font-family="{MONO}" '
      f'font-size="{CMD_SIZE}" font-weight="700" fill="{CYAN}">'
      f'<tspan fill="{FAINT}">~ </tspan>'
      f'<tspan fill="{GREEN}">$ </tspan>./build.sh</text>')
    a(txt(TERM_R, TAG_BASE, "installs in seconds  |  zero lock-in", TAG_SIZE, MICRO,
          400, MONO, anchor="end"))

    a("</svg>")
    return "\n".join(o)


def _selftest() -> int:
    """Assert the alignments, because eyeballing them has failed repeatedly.

    Only relationships that are pure geometry are asserted here. Text *widths*
    depend on the renderer's font metrics and cannot be checked without one — a
    copy change still needs measuring in a browser.
    """
    import re
    y_of = ladder_rungs()
    svg = render()

    # 1. page margins agree top and bottom
    assert CHROME_BASE - INK_ASC[10] == MARGIN_Y, CHROME_BASE
    assert H - (TERM_Y + TERM_H) == MARGIN_Y, H - (TERM_Y + TERM_H)

    # 2. everything that touches the left margin actually touches it
    assert LADDER_X0 - NODE_R == M, LADDER_X0            # the glow node, not the rail
    assert TERM_L - TERM_PAD == M, TERM_L
    assert CARD_X[0] == M, CARD_X

    # 3. and the right margin
    assert META_X + META_W == W - M
    assert CARD_X[-1] + CARD_W == W - M, CARD_X
    assert M + TERM_W == W - M

    # 4. ladder, metadata card and the title block share one midline, and the
    #    ladder's rails span the title block exactly — "match the text block"
    #    as arithmetic rather than a number someone eyeballed
    assert y_of[6] - LADDER_OV == HERO_TOP, y_of[6]
    assert y_of[1] + LADDER_OV == HERO_BOT, y_of[1]
    assert META_Y + META_H / 2 == HERO_MID, META_Y
    assert (HERO_TOP + HERO_BOT) / 2 == HERO_MID

    # 5. pillar copy is optically centred in its card — ink edges, not baselines
    top_pad = (PILLAR_HDR - INK_ASC[12]) - CARD_Y
    bot_pad = (CARD_Y + CARD_H) - (PILLAR_L2 + INK_DESC[14])
    assert abs(top_pad - bot_pad) <= 2, (top_pad, bot_pad)

    # 6. all three cards put their body copy on the same two baselines. Asserted
    #    against the emitted SVG: the constants only prove what they are set to,
    #    and the claim is about what render() does with them three times over.
    for label, y in (("body line 1", PILLAR_L1), ("body line 2", PILLAR_L2)):
        xs = re.findall(rf'<text x="([\d.]+)" y="{y}"', svg)
        assert xs == [str(x + CARD_PAD_X) for x in CARD_X], (label, xs)

    # 7. the evidence row inherits the pillar grid, and its cells hold their text
    assert EV_PITCH == CARD_W + CARD_GAP
    assert EV_PITCH >= EV_MAX_W + 24, EV_PITCH           # uniform but too tight = collision
    assert CARD_X[-1] + EV_MAX_W < W - M, CARD_X

    # 8. the tagline is centred on the command's ink, and both clear the window
    assert TAG_BASE - INK_ASC[TAG_SIZE] > TERM_Y + TERM_BAR, TAG_BASE
    assert abs((TAG_BASE - (INK_ASC[TAG_SIZE] - INK_DESC[TAG_SIZE]) / 2) - CMD_MID) < 0.01
    assert CMD_BASE + INK_DESC[CMD_SIZE] < TERM_Y + TERM_H, CMD_BASE

    # 9. bands do not collide
    assert y_of[1] + LADDER_OV < CARD_Y, "ladder runs into the pillar row"
    assert META_Y + META_H < CARD_Y, "metadata card runs into the pillar row"
    assert CARD_Y + CARD_H < EV_TOP, "pillar row runs into the evidence band"
    assert EV_BOT < TERM_Y, "evidence band runs into the terminal"

    # 10. one rhythm down the page. This is the check that was missing when the
    #     gaps were 64 / 8 / 22: nothing collided, it just looked wrong.
    gaps = [HERO_TOP - RULE_Y, CARD_Y - HERO_BOT,
            EV_TOP - (CARD_Y + CARD_H), TERM_Y - EV_BOT]
    assert set(gaps) == {GAP}, gaps

    # 11. it renders, and it renders the same way twice
    assert svg == render()
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    import xml.dom.minidom
    xml.dom.minidom.parseString(svg)

    print("  OK: margins, midlines, baselines, grid, rhythm and clearances all hold.")
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
