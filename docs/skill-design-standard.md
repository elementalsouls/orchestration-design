# The skill-design standard

**What a Claude Code skill needs to be, for a professional to rely on it.**

Derived 2026-08-02 from the 719 unique skills installed on one working machine, not from
opinion. Every rule below traces to a measurement across that corpus or to a defect that
actually shipped in this repo. Where a rule is machine-checkable, a linter checks it and you
can run it yourself. It lives at `tools/skill_lint.py` in
<https://github.com/elementalsouls/orchestration-design> — one dependency-free file that
knows nothing about this project:

```bash
python tools/skill_lint.py <skill-dir>          # one skill; exit 1 on any FAIL
python tools/skill_lint.py --corpus ~/.claude/skills
python tools/skill_lint.py --selftest           # the rules prove themselves first
```

If you are reading this document standalone, fetch that file before working the rules —
otherwise half of them are unverifiable, which is the exact defect Pillar 3 exists to prevent.

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

A skill's frontmatter is two required keys. The whole routing decision is the second one:

```yaml
---
name: db-migration-safety          # must equal the directory name
description: >
  Plan and review database schema migrations so they cannot lock a hot table,
  and so every one has a rollback. Use when writing, reviewing or running a
  migration, or mid-incident when one is already misbehaving. Fires on symptoms
  stated without the vocabulary: "my ALTER TABLE is still running", "I ran it
  straight against prod", "the migration locked the table and everything timed
  out", "I have no way to undo this".
---
```

Optional keys (`allowed-tools`, `license`, `model`) are permitted and rare. Nothing else
in the frontmatter affects routing.

| Rule | Severity |
|---|---|
| ≤ 1024 characters | FAIL over |
| > 850 characters | WARN — near a cap you cannot see yourself cross |
| States *when to use it*, not only what it is | WARN if absent |
| Names every domain vocabulary the skill claims to serve | **cold run only** |

**When the last two rules fight, vocabulary wins.** Symptom phrasings are long, and a
description that names four domains in the user's words will push past 850. That WARN means
*compress the prose* — cut the capability description, keep the triggers. It does not mean
drop a vocabulary. A 900-character description that routes four ways beats a 400-character
one that routes one way; a truncated 1100-character one routes nowhere. This repo's own skill
sits at 985 and stays there deliberately.

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

**The unit is lines of `SKILL.md` below the frontmatter.** Not the bundle, not the reference
files, not the frontmatter itself. Reference files have no budget of their own — that is the
point of moving depth into them.

| Rule | Severity |
|---|---|
| > 600 lines with no reference files | FAIL |
| > 250 lines with no reference files | WARN |
| > 600 lines even with references | WARN |

Your own repo may declare a stricter budget, and when it does, **it wins**. This repo's is 160
lines, recorded in `CLAUDE.md`. The numbers above are the floor below which nobody should
ship; they are not a target.

**Why FAIL sits at 600 when the corpus median is 318.** The gate is deliberately set where
the cost is undeniable rather than where the practice is merely better. A 318-line body is
often one coherent procedure a user wants in full; a 900-line one is a table of contents over
material most triggers never touch. Progressive disclosure being the highest-leverage
property is a claim about the *practice* — the 250-line WARN is where you should start
asking. Only past 600 is it beyond argument.

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

| Rule | Severity |
|---|---|
| Ships something runnable (a script, a generator, a validator) → it has a self-check reachable by one command with one exit code | **human** |
| Ships only prose → Pillar 6 is the check; no script is required | — |

**A prose-only skill does not owe you a Python file.** If the skill is six phases and a
decision table, the thing that proves it works is a cold run, not a linter. Write a script
only when the skill *ships* something that can silently rot — and then hold it to
`--selftest`.

A linter cannot know what your skill promised, so the rule above is human-checked. What a
linter *can* see is whether the check exists at all.

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

**A domain vocabulary is a set of trigger words a *different kind of user* would say for the
same underlying problem** — not a feature of your skill. "Postgres" and "MySQL" are one
vocabulary (both say *migration*, *lock*, *rollback*). "Software pipeline" and "compliance
audit" are two, because those users share no nouns. Count the vocabularies in your
description, and run one cold test per vocabulary.

**Two grades of cold run, and they test different pillars.**

*Routing test — the only one that checks Pillar 1.* Install the skill (`~/.claude/skills/`),
open a fresh session, and make a request that **never names the skill**. Either it fires or
it does not. This is binary and it is the whole point of the description.

*Followability test.* Hand a fresh agent the skill file and a realistic request, and forbid
access to your repo and history. This tests whether the method survives contact with someone
who did not write it. It **cannot** test routing, because you told the agent where to look.

Running only the second and calling it a cold run leaves Pillar 1 untested. That is the
easiest mistake here to make, and this document's own author made it.

**The bar:** the routing test fires on the first turn for every vocabulary claimed. The
followability test has no pass mark — it returns a critique, and the standard is that you
fix what it found and run it again. Zero findings on a first cold run means the test was too
easy, not that the skill was ready.

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
| Licence granted wherever the skill is distributed from | human |
| Name not colliding with an installed skill | corpus mode, advisory |

**If your skill ships a script, its bytecode is your problem.** Running it writes
`__pycache__/` next to it, and packaging the directory afterwards ships a hygiene FAIL. Add
it to `.gitignore` and strip it at package time — this repo's `build.sh` deletes `.DS_Store`
before zipping for exactly this reason. Pillar 4 asks you to ship a runnable check; this
pillar is what that costs.

**Licence.** Do not assert one you have not granted. This repo's banner claimed MIT for weeks
with no `LICENSE` file — on GitHub that means all rights reserved, so nobody could legally
use it. The claim was in the artwork and the grant was nowhere.

The rule is scoped to the **distribution unit**, not the skill directory. A skill inside a
repo is covered by that repo's licence and needs no file of its own. A skill distributed
standalone needs one. **If you are authoring on someone else's behalf you cannot grant it** —
name them as the holder or leave it to them, because a licence file with a vague holder is
the same defect as the banner was.

**Name collisions** are real and common: four names appear eight times each across installed
plugins, and two skills with the same name are a routing coin-flip. It is **advisory**,
because you can only check the corpus on your own machine and never the installer's. Prefer a
specific name (`db-migration-safety`) over a generic one (`migrations`).

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
