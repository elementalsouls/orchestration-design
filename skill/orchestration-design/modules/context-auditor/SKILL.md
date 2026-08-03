---
name: context-auditor
description: Clean the always-loaded context before a long build, so the agent is not reasoning from stale facts or rules that no longer apply. Use when starting a long or iterative task, when an agent keeps making the same wrong assumption, when it cites a file, count, path or version that does not match reality, when it refuses something reasonable for no visible reason, or when onboarding a project whose instruction files have grown by accretion. Run it after a big refactor, rename or dependency bump, and whenever a task is about to loop.
---

# Context Auditor

Run this **before** a long build, not after it goes wrong.

Everything in an always-loaded instruction file is a premise the agent reasons from on every
turn. Premises rot. A count that was right in March, a path that moved, a rule written for one
incident and never scoped — each one is a small confident wrongness the agent cannot detect,
because from the inside a stale fact and a true fact look identical.

The cost is not one bad answer. It is a whole session built on a wrong premise, and the loop
that follows when the work does not match what the instructions promised.

## What you are looking for

Two defects, and they fail differently.

### 1 · Stale facts — true when written, false now

Anything that names a **number, a path, a version, or a name** is a claim about the world that
the world can invalidate. These are cheap to check and worth checking every time:

| Kind | Example of the rot |
|---|---|
| Counts | "12 services", after two were merged |
| Paths | A file reference that moved in a refactor |
| Versions | A pinned tool version the lockfile has since bumped |
| Names | A module, script or command renamed |
| Layout | A directory tree that no longer matches `ls` |
| Status | "currently migrating to X", long after the migration finished |

**Check them, do not read past them.** Every one is verifiable in a second: run `ls`, read the
manifest, grep for the name. A claim you can check and did not is worse than no claim, because
it carries authority it has not earned.

### 2 · Overconstraints — rules broader than the reason behind them

Harder to spot, and they do more damage. An overconstraint is a rule that was correct in one
situation and got written down without its scope, so it now applies everywhere:

- **A prohibition with no live reason.** "Never use X" — because of an incident that a later
  fix already resolved. The rule outlived the cause.
- **A rule with its scope stripped.** "Always do Y" was true of one module; it is now stated as
  a project-wide law, and it fights the code everywhere else.
- **Mutually exclusive rules.** Two instructions that cannot both be satisfied. The agent
  satisfies one, appears to disobey the other, and looks unreliable when it is actually stuck.
- **Rules already enforced mechanically.** A convention a linter, formatter or CI check already
  guarantees. Harmless but not free — it takes context budget and adds nothing.
- **Instructions describing what the code already shows.** A layout, a signature, a dependency
  list. Derivable in one command, so it is paying rent to say what `ls` would say.

The tell for an overconstraint: **you cannot state the reason it exists.** If nobody can say
what goes wrong when the rule is broken, it is not protecting anything.

## The audit

Work through the always-loaded files — the project instruction file, anything it imports, and
any rules file loaded on every turn. Not every doc in the repo: **only what is in context on
every turn**, because that is what shapes reasoning whether or not it is relevant.

For each claim, put it in one of three buckets:

| Verdict | Meaning | Action |
|---|---|---|
| **Verified** | Checked against reality, still true | Leave it |
| **Stale** | Checked, no longer true | Propose the correction, with what you checked |
| **Unscoped** | Cannot state the live reason, or it is broader than its cause | Propose scoping it or cutting it, and say which |

Then report: what you checked, what you changed, and **what you could not verify** — that last
list is the honest part, and it is where the next failure will come from.

## Rules for the audit itself

**Propose, do not silently edit.** These files encode decisions you were not present for. A
rule you cannot see the reason for may still have one. Show the diff and let a human decide.

**Check, do not infer.** "This probably still points at the right directory" is how a stale
fact survives an audit. Run the command.

**When in doubt, keep it.** A slightly redundant rule costs a little context. A deleted rule
that was load-bearing costs an incident. The asymmetry is not close.

**Never cut a safety prohibition for looking generic.** "Never force-push to the shared
branch", "never edit generated files", "never commit secrets" stay, whether or not anyone can
recall the incident behind them. Those are the rules whose reason is *supposed* to be invisible
— the incident did not happen because the rule worked.

## What good looks like afterwards

Every remaining claim is either verified or explicitly marked unverified. Every remaining rule
has a reason someone can state in one sentence. Anything derivable from the code in one command
is gone.

The agent is now reasoning from a smaller set of premises that are actually true — which is
worth more than any amount of additional instruction sitting on top of a wrong one.
