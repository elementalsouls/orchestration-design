# Corpus audit — 76 installed skills

**Run:** 2026-08-02 · `python tools/skill_lint.py --corpus ~/.claude/skills`
**Standard:** `docs/skill-design-standard.md`

Read-only. Nothing in `~/.claude/skills` was edited. This is a diagnostic, and the
annotations below say where the linter is right, where it is merely technically right, and
where a human should overrule it.

## Headline

| | Count |
|---|---|
| Skills scanned | 76 |
| At least one FAIL | **7** |
| Completely clean — no FAIL, no WARN | **13** |

| Rule | FAIL | WARN |
|---|---|---|
| `load-budget` | 6 | 48 |
| `description-cap` | 3 | 10 |
| `description-routing` | — | 12 |
| `reference-integrity` | 0 | — |
| `bundle-hygiene` | 0 | — |
| `name-matches-dir` | 0 | — |

Three rules found nothing at all. That is a real result, not a gap: these skills ship clean
bundles, name themselves consistently, and do not reference files they fail to include.

## The seven failures

| Skill | FAIL | Detail |
|---|---|---|
| `bug-bounty` | 2 | description **1405** chars; body **1600** lines, no references |
| `bb-local-toolkit` | 2 | description **1405** chars; body **1554** lines, no references |
| `osint-methodology` | 1 (+1 WARN) | description **1290** chars; body **1641** lines with 1 reference file |
| `graphify` | 1 | body **1063** lines, no references |
| `security-arsenal` | 1 | body **908** lines, no references |
| `web2-recon` | 1 | body **694** lines, no references |
| `web3-audit` | 1 | body **602** lines, no references |

### The description failures are the urgent ones

`bug-bounty`, `bb-local-toolkit` and `osint-methodology` exceed the Codex 1024-character cap
by 266 to 381 characters. Everything past 1024 is **discarded without a warning**. Whatever
triggers live in that tail — and in descriptions this long, the tail is usually the specific
symptom phrasings — do not exist as far as routing is concerned.

This is invisible from the author's side. The skill behaves normally in Claude Code, so
there is no symptom to notice.

Two more sit close enough to be one edit away: `hunt-ato` at **1020** and `hunt-llm-ai` at
**1014**, both within ten characters.

*(An earlier hand count of this same data said five skills were over the cap. Three are.
`hunt-ato` and `hunt-llm-ai` are under it. The linter corrected the author — which is the
argument for building the checker before writing the prose about it.)*

### The body failures cost context on every unrelated trigger

Four skills carry 600 to 1641 lines with no `references/` split. All of it loads whenever the
skill fires, including when it fires for a narrow question that needs one section.

`osint-methodology` is the sharpest case: it *has* a reference file, so the pattern is
understood — it just kept 1641 lines in the body anyway.

## The 48 load-budget WARNs — where the linter is too blunt

Forty-eight skills exceed 250 body lines with no references. Most are the `hunt-*` family at
roughly 250–400 lines each, one per vulnerability class.

**The linter is technically right and practically wrong about these.** A `hunt-nosqli` skill
is a single coherent procedure that a user wants in full when it fires; splitting it into
`references/` buys nothing because there is no branch where you would want only part of it.
The threshold exists for skills where the body is a *table of contents* over material most
triggers never touch — which is what the 600+ line failures are.

Treat 250 as the line where you should *ask* whether the body is one procedure or several,
not the line where you must split.

The `hunt-*` family scores well on everything else: clean bundles, consistent names, no
broken references, and thirteen of them are completely clean.

## The 12 routing WARNs

Twelve descriptions state what the skill *is* without stating when to fire it. This is the
cheapest fix in the audit — one clause — and it is the one that most directly changes whether
the skill loads at all.

The failure mode is not theoretical: this repo's own skill was invisible to an entire class
of request until its description named a second vocabulary.

## What this audit cannot tell you

Whether any of these skills are any *good*. Every rule here is about being loadable,
routable and honest about what ships. `hunt-nosqli` could be 400 lines of excellent
methodology or 400 lines of nonsense and this document would score it identically.

## If you fix three things

1. Trim the three over-cap descriptions to 1024. Nothing else in this audit is silently losing behaviour right now.
2. Split the four 600+ line bodies. Biggest context saving per hour spent.
3. Add a "use when" clause to the twelve descriptions missing one.

Everything else can wait, and the 48 body WARNs should be judged case by case rather than
cleared.
