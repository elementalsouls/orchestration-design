# Corpus audit — 76 installed skills

**First run:** 2026-08-01 · **Re-run after remediation:** 2026-08-02
**Command:** `python tools/skill_lint.py --corpus ~/.claude/skills`
**Standard:** `docs/skill-design-standard.md`

Read-only with respect to the skills themselves — the linter reports, it does not edit. The
remediation between the two runs was done by hand, and this document keeps both states so the
rules can be judged by what changed rather than by what they claim.

## Before and after

| | 2026-08-01 | 2026-08-02 |
|---|---|---|
| Skills scanned | 76 | 76 |
| At least one FAIL | 7 | **6** |
| Completely clean — no FAIL, no WARN | 13 | **20** |
| Descriptions over the 1024 cap | 3 | **0** |
| Byte-identical description pairs | 1 | **0** |
| Always-resident listing | ~11,381 est. tokens | **~9,259 est. tokens** |

| Rule | FAIL then | FAIL now | WARN then | WARN now |
|---|---|---|---|---|
| `load-budget` | 6 | 6 | 48 | 48 |
| `description-cap` | 3 | **0** | 10 | **1** |
| `description-routing` | — | — | 12 | 12 |
| `reference-integrity` | 0 | 0 | — | — |
| `bundle-hygiene` | 0 | 0 | — | — |
| `name-matches-dir` | 0 | 0 | — | — |

## What was fixed

**The three over-cap descriptions.** `bug-bounty` 1405 → 658, `bb-local-toolkit` 1405 → 493,
`osint-methodology` 1290 → 562. Everything past 1024 characters was being discarded without a
warning, and in descriptions that long the discarded tail is where the specific symptom
triggers live. Nineteen descriptions were trimmed in total, recovering roughly 1,860 est.
tokens per session; the remaining ten near-cap WARNs came down with them.

**A duplicate that was a routing coin-flip.** `bug-bounty` and `bb-local-toolkit` were 96% the
same file — 1603 vs 1557 lines, 63 lines of difference — with **byte-identical descriptions**.
Two skills with the same description are dispatched by chance. `bb-local-toolkit` is now
disabled via `skillOverrides`; `bug-bounty` survives because it is the copy that routes onward
to `bb-methodology` and `hunt-dispatch` rather than dead-ending.

**One unrelated skill disabled.** `meme-coin-audit` — zero uses across 82 startups.

Disabled skills still sit on disk, so the linter still scans and reports them. It reads
settings for nothing; **`skillOverrides` is invisible to it.** That is a real limitation of the
tool, not of the data — read the `bb-local-toolkit` row below as historical.

## What remains: six FAILs, all load-budget

| Skill | Body lines | Reference files |
|---|---|---|
| `bug-bounty` | 1600 | 0 |
| `bb-local-toolkit` *(disabled)* | 1554 | 0 |
| `graphify` | 1063 | 0 |
| `security-arsenal` | 908 | 0 |
| `web2-recon` | 694 | 0 |
| `web3-audit` | 602 | 0 |

All of it loads whenever the skill fires, including for a narrow question that needs one
section. Splitting these into `references/` is the largest remaining context win and the one
piece of the first audit's fix list that has not been done — trimming descriptions was the
cheap half.

`osint-methodology` dropped off this list by trimming alone, but at 1641 body lines with a
single reference file it still carries a WARN. The pattern is understood there; the split just
was not finished.

## The 48 load-budget WARNs — still where the linter is too blunt

Unchanged from the first run, and the annotation still holds. Forty-eight skills exceed 250
body lines with no references, most of them the `hunt-*` family at roughly 250–400 lines each,
one per vulnerability class.

**The linter is technically right and practically wrong about these.** A `hunt-nosqli` skill is
one coherent procedure a user wants in full when it fires; splitting it buys nothing, because
there is no branch where you would want only part of it. The threshold is for bodies that are a
*table of contents* over material most triggers never touch — which is what the 600+ line FAILs
are. Treat 250 as the line where you *ask*, not the line where you must split.

## The 12 routing WARNs

Twelve descriptions still state what the skill *is* without stating when to fire it. Unchanged,
and still the cheapest fix in the audit: one clause each, and it is the change that most
directly decides whether the skill loads at all.

## The one remaining description WARN

`orchestration-design` at 985 characters, and it stays there. The description deliberately
carries both a software and a process vocabulary, because a cold run proved that dropping the
second produced **zero** invocations for process-shaped requests. Per Pillar 1, when the cap
warning and the vocabulary rule conflict, vocabulary wins.

## Still true, and still the headline

The active listing is ~9,259 est. tokens against a budget of roughly 2,000 — about 1% of the
context window. Past that, entries get truncated and routing degrades. Description trimming
took ~2,100 tokens out of it and cannot take much more without eating trigger keywords.

The structural fix is that most `hunt-*` skills are dispatched **by** `hunt-dispatch` on a
fingerprint match rather than routed by topic, so their descriptions pay rent in the
always-resident listing for a decision they never participate in. That is a redesign of how the
suite loads, not a cleanup, and it is out of scope here.

## What this audit still cannot tell you

Whether any of these skills are any *good*. Every rule is about being loadable, routable and
honest about what ships. `hunt-nosqli` could be 400 lines of excellent methodology or 400 lines
of nonsense and this document would score it identically.
