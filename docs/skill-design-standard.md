# The skill-design standard

**What a Claude Code skill needs to be, for a professional to rely on it.**

Derived 2026-08-02 from the 719 unique skills installed on one working machine, not from
opinion. Every rule below traces to a measurement across that corpus or to a defect that
actually shipped in this repo. Where a rule is machine-checkable, `tools/skill_lint.py`
checks it and you can run it yourself:

```bash
python tools/skill_lint.py <skill-dir>          # one skill; exit 1 on any FAIL
python tools/skill_lint.py --corpus ~/.claude/skills
python tools/skill_lint.py --selftest           # the rules prove themselves first
```

Where a rule is not machine-checkable, this document says so plainly rather than pretending.
Three of the seven pillars need a human or a cold run. That ratio is the honest one.

---

## What the corpus looks like

| Property | Finding |
|---|---|
| Progressive disclosure | **18 of 719 skills (2.5%)** use a `references/` directory. The other 97.5% load their entire body on every trigger. |
| Body size | User-authored median **318** lines; largest **1641**. |
| Description size | Plugin median **142** characters; user median **556**. No norm exists. |
| Over the Codex 1024-char cap | **3** — `bug-bounty` and `bb-local-toolkit` at 1405, `osint-methodology` at 1290. Two more sit within ten characters of it. |
| Name collisions | `coding-standards`, `security-review`, `tdd-workflow`, `backend-patterns` — **8 copies each** across installed plugins. |

The first two rows are the important ones, and they are both **silent**. An over-cap
description is truncated with no warning — the skill works locally and quietly stops routing
elsewhere. A 1600-line body costs context on every unrelated trigger and never announces it.
Neither is visible to an author reading their own file.

---

## Pillar 1 — The trigger contract

**The `description:` field is the entire routing surface.** Nothing else decides whether the
skill fires. The body is irrelevant until after that decision is made.

| Rule | Severity |
|---|---|
| ≤ 1024 characters | FAIL over |
| > 850 characters | WARN — near a cap you cannot see yourself cross |
| < 60 characters | WARN — too thin to route reliably |
| States *when to use it*, not only what it is | WARN if absent |
| Names every domain vocabulary the skill claims to serve | **cold run only** |

The last rule is the one that bites and the one no linter can check. This repo shipped a
skill whose triggers were written entirely in software nouns — *pipeline, agent, fan-out*.
A cold agent given a **process**-shaped request (a compliance audit, no code) produced
**zero** invocations. The method was fine. The vocabulary was the bug, and only an agent
that had never seen the file could reveal it.

**Write triggers in the user's words, not the author's.** A person with the problem says
*"my pipeline is a mess"* or *"I don't know what I've already covered."* They do not say
*"I require orchestration-level analysis."*

## Pillar 2 — Load budget and progressive disclosure

**`SKILL.md` carries the method. `references/` carries the depth.** The body loads on every
trigger; references load only when the method sends you to them.

| Rule | Severity |
|---|---|
| > 600 lines with no reference files | FAIL |
| > 250 lines with no reference files | WARN |
| > 600 lines even with references | WARN |

State the budget in your repo conventions and hold it. This repo's is 160 lines, recorded in
`CLAUDE.md` and true at the time of writing.

The rule of thumb that makes the split decidable: **a worked example belongs in
`references/`; the rule it demonstrates belongs in `SKILL.md`.**

At 2.5% adoption this is the rarest property in the corpus and the highest-leverage one.

## Pillar 3 — Reference integrity

**Every path the skill promises must exist in the shipped bundle.** A cold run of this repo
found references to files the bundle did not ship — invisible to the author, whose working
copy had them.

Checked only for paths rooted in a conventional skill directory (`references/`, `scripts/`,
`assets/`, `templates/`, `targets/`, `examples/`) or in a directory the skill really has.

**Deliberate under-reporting.** A naive version of this rule flagged 18 of 76 skills, almost
all wrongly: `swagger.json`, `package.json`, `_buildManifest.js` are filenames a security
skill hunts for *on a target*, not promises about its own bundle. A linter that cries wolf
gets switched off by the person who most needs it, so this rule stays narrow on purpose.

## Pillar 4 — Behavioural verification

**A claim a skill makes about itself must be provable by something you can run.**

Not machine-checkable in general; a linter cannot know what your skill promised. What is
checkable is whether a runnable check *exists* and is wired into one command with one exit
code.

Two defects from this repo, both invisible to re-reading and both obvious to one assertion:

- A loop-back edge whose re-entry point read state **no node inside the loop wrote**. Rounds 2 and 3 did no work and the run declared victory. One `grep` for the field's writers proved it. ~120 lines deleted.
- A spend budget incremented at the live API call — so under the project's own mock mode it never incremented, the cap never fired, and the bound was **untested by every test that existed**.

The general form: **force the condition each bound guards, and assert the run stops.** A cap
you have never actually hit is undemonstrated, not proven.

## Pillar 5 — Evidence discipline

**Factual claims carry a source and a date. Controlled experiments are separated from vendor
and production reports. Figures you could not verify are marked as unverified.**

Human-checked. This repo published a research table for weeks in which one paper was
mischaracterised and five figures were unverifiable, because the sources had been
reorganised from a secondary summary rather than read. Fetching all eight primary sources
changed four rows.

If a claim would change someone's architecture, you owe them the citation and the date, so
they can weigh its shelf life themselves.

## Pillar 6 — Cold-run acceptance

**Before shipping, an agent with no memory of writing it must be able to follow it.**

Give a fresh agent only a realistic user request and the installed skill — no repo access,
no project history, no hint about the intended answer. Run one per domain vocabulary the
description claims to serve.

This is the acceptance test, it cannot be automated, and it is the highest-yield activity in
this entire document. Two cold runs on this repo found six structural defects: references to
unshipped files, a design smell that fired on correct designs, a verification phase assuming
a reviewer that levels 1–2 do not have, a spend budget assuming tokens where nothing costs
tokens, an ambiguity about whether a phase asks or assumes, and no prompt anywhere about
legal or ethical bounds for a tool touching third-party data.

**None of them would have surfaced from re-reading the file.** An author cannot evaluate a
document he wrote from memory — he reads what he meant, not what it says.

## Pillar 7 — Distribution hygiene

| Rule | Severity |
|---|---|
| `name:` matches the directory name | FAIL |
| No `.DS_Store`, `__pycache__`, `.pyc`, `.orig`, `.rej`, `.swp` in the bundle | FAIL |
| Licence file present in the repo | human |
| Name not colliding with an installed skill | corpus mode |

Do not assert a licence you have not granted. This repo's banner claimed MIT for weeks with
no `LICENSE` file — which on GitHub means all rights reserved, so nobody could legally use
it. The claim was in the artwork and the grant was nowhere.

Name collisions are real and common: four names appear eight times each across installed
plugins. Two skills with the same name are a routing coin-flip.

---

## Severity model

**FAIL** is a silent failure or a broken promise — something the author cannot see and the
user pays for. **WARN** is a smell that may well be deliberate. Only FAIL moves the exit
code.

That asymmetry is the whole design. A linter that fails builds over style opinions gets
disabled within a week, and then catches nothing at all.

## What this standard does not cover

Whether the skill's *content* is any good. Nothing here checks whether the method works,
whether the advice is correct, or whether the domain is well understood. This standard makes
a skill **loadable, routable, followable and honest**. Being right is still on you.
