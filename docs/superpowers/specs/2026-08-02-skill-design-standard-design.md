# Spec — a skill-design standard, derived from the installed corpus

**Date:** 2026-08-02 · **Status:** approved · **Scope:** one implementation cycle

## Problem

Every improvement to this repo so far has been reactive. A reader misread the LangGraph
position, so that line got fixed. A cold run failed to fire, so the description got fixed.
The banner asserted the wrong topology, so it got redrawn. Each fix was correct; none came
from a design.

There is no written account of what a professional-grade Claude Code skill *is*. So the
next skill repeats the same errors, and the 76 already installed on this machine carry them
today — including five whose descriptions are silently truncated by the Codex 1024-character
cap, and one whose 1641-line body loads in full on every unrelated trigger.

This spec designs the class, not the instance.

## Method

The repo's own ethos decides the method: claims are **measured, not asserted**. So the
standard is derived from the corpus already on this machine, and it ships with a runnable
checker, so conformance is a command rather than an opinion.

### Baseline measurement

736 `SKILL.md` files scanned, 719 unique, 76 user-authored.

| Property | Finding |
|---|---|
| Progressive disclosure | **18 of 719 (2.5%)** use a `references/` directory |
| Body size, user skills | median **318** lines, max **1641** (`osint-methodology`) |
| Description size | plugin median **142** chars; user median **556**; no norm |
| Over the 1024 Codex cap | **three**: `bug-bounty` 1405, `bb-local-toolkit` 1405, `osint-methodology` 1290. Two more sit within ten characters of it — `hunt-ato` 1020, `hunt-llm-ai` 1014 — one edit from silent truncation. (An earlier hand count said five over; the linter corrected it. That is the point of building the checker before writing the prose.) |
| Name collisions | `coding-standards`, `security-review`, `tdd-workflow`, `backend-patterns` — 8× each |
| `orchestration-design` | 160 body lines (35th percentile), 985-char description, 11 reference files |

Two of these fail silently. An over-cap description is truncated with no warning, and a
long body costs context on every fire without ever announcing it.

## Design

### Seven pillars

| # | Pillar | Checked by |
|---|---|---|
| 1 | Trigger contract — the `description:` field is the entire routing surface | linter (shape, cap) + cold run (vocabulary) |
| 2 | Load budget and progressive disclosure — method in `SKILL.md`, depth in `references/` | linter |
| 3 | Reference integrity — every intra-skill path resolves in the shipped bundle | linter |
| 4 | Behavioural verification — self-claims provable by a runnable check | partly linter |
| 5 | Evidence discipline — sourced, dated, strength-separated, unverifiable marked | human |
| 6 | Cold-run acceptance — an agent with no memory of authoring it must follow it | human |
| 7 | Distribution hygiene — licence, clean bundle, unique name matching its directory | linter |

Each rule exists because of a measurement above or a defect this repo actually shipped.
Pillar 1 comes from the run-B failure: a process-vocabulary request produced **zero**
invocations because every trigger was written in software nouns. Pillar 3 comes from a
cold run that found file references to things the bundle does not ship. Pillar 7 comes from
the banner asserting MIT for weeks with no `LICENSE` file in the repo.

### Component boundaries

**`tools/skill_lint.py`** — pure function of a directory. Takes a skill directory, returns
a list of `(rule, severity, message)`. Knows nothing about this repo. `--corpus` scores many
directories and adds the one cross-skill rule (duplicate names). `--selftest` asserts the
rules against fixtures built in a temporary directory, so the rules are proven before they
are trusted. Exit code is the interface: non-zero if any rule FAILs.

**`docs/skill-design-standard.md`** — prose. Written *after* the linter, from what it
actually enforces, so the document cannot drift into aspiration.

**`docs/corpus-audit-2026-08.md`** — generated output plus hand annotation. Read-only with
respect to the 76 skills; it reports and does not edit.

### Severity model

`FAIL` is a silent-failure or broken-promise condition — over the cap, a missing referenced
file, a body large enough to hurt with no disclosure. `WARN` is a smell that may be
deliberate. Anything else passes. Only `FAIL` moves the exit code, because a linter that
fails on smells gets disabled.

### Known false-positive class

A naive "every path-like token must exist" rule flags 18 of 76 skills, and most are wrong:
`swagger.json`, `package.json`, `_buildManifest.js` are filenames those skills hunt for *on
a target*, not files they ship. The rule is therefore scoped: a path is only checked when it
contains a directory separator **and** its first segment is a conventional skill directory or
an existing directory in the skill. Everything else is treated as target-side and skipped.

This is deliberate under-reporting. A rule that cries wolf on security skills would be
switched off by the one person who most needs it.

## Verification

```bash
python tools/skill_lint.py --selftest
python tools/skill_lint.py ~/.claude/skills/orchestration-design    # exit 0
python tools/skill_lint.py --corpus ~/.claude/skills                # 76 rows
python run_checks.py                                                # ten checks, exit 0
```

Acceptance: the linter re-detects the over-cap descriptions and the largest un-split bodies
**without being given those names**; the target-side false-positive class stays silent;
`orchestration-design` passes with no FAIL; and a cold agent, given only the standard and a
skill-authoring request, produces a conforming skill without further prompting.

## Out of scope

Remediating the 76 audited skills. Publishing the standard as its own meta-skill. A docs
site. Distribution and marketing. Each is a separate spec.
