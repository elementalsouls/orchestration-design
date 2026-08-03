# Tactical interventions — when execution gets stuck

Phases 0 through 4 decide *what to build* and prove the build matches the design. This file
covers the other failure: the design is right, the level is right, and **execution is going in
circles anyway.**

That is a different problem and it needs a different tool. No amount of re-designing fixes a
loop, and climbing a level to escape one makes it worse — you get the same guessing, spread
across more nodes and more spend.

## Recognising it

An execution loop is observable, not a mood. Any one of these is enough:

| Signal | What it means |
|---|---|
| Same file edited 3+ times, error unchanged | The model of the problem is wrong, so every edit is a coin flip |
| A test failed the same way twice | The second attempt did not encode anything learned from the first |
| Next action chosen because the last failed | Sequence, not selection — the definition of guessing |
| About to add a retry, sleep, cast or flag | A workaround for a cause nobody has named |
| Cannot state what is wrong in one sentence | There is no model to act on yet |

Do not wait for a fourth attempt to be sure. The cost of stopping early is one paragraph; the
cost of stopping late is the rest of the budget.

## The modules

Each is a self-contained protocol under `modules/`. Read the one that matches and follow it
literally — they are written to be executed, not skimmed.

| Module | Fires | Use when |
|---|---|---|
| `modules/context-auditor/SKILL.md` | **Before** a loop starts | The premises are suspect. Verifies every count, path, version and name in the always-loaded files, and scopes or cuts rules whose reason nobody can state. Run it before a long build, after a refactor or rename, and whenever an agent keeps making the same wrong assumption |
| `modules/rubber-duck-verifier/SKILL.md` | **During** a loop | Stuck, guessing, or repeatedly failing tests. Forces a text-only tear-down — goal, failure, failed assumptions, missing context — before any further edit |
| `modules/adversarial-reviewer/SKILL.md` | **After** work exists | A reviewer keeps passing work that then fails, or the change touches money, auth or deletion. Reviews from a separate clean context and tries to break the code rather than confirm it |

The order is not decorative. `context-auditor` prevents loops by removing the wrong premises
that cause them; `rubber-duck-verifier` breaks one already running; `adversarial-reviewer`
catches what survives. Reaching for the third when the first was skipped is common and
expensive — a reviewer cannot see a premise that is wrong in both the code and the review.

## Where this sits in the method

Interventions are **orthogonal to the ladder**. They apply at any level, and they do not
change the level:

- At **levels 1–2** the loop is yours to break — you are the thing writing the code.
- At **levels 3–4** it usually surfaces as a reviewer that keeps rejecting. That is the signal
  to stop the write-review cycle and tear the failure down in text, because a bounded loop
  will otherwise burn every attempt it has and ship the exhaustion terminal.
- At **levels 5–6** a stuck branch must not become a stuck run. Isolate it, let its siblings
  finish, and tear it down separately — one branch guessing is a bug in that branch, not a
  reason to re-architect the fan-out.

## The relationship to bounds

An intervention and a bound do different jobs, and having one is not having the other.

A **bound** stops a loop from running forever. It is a safety net: it caps the damage and
routes to a terminal. It does not make the next attempt smarter, and a design that relies on
bounds alone reliably burns its full attempt budget before shipping a flagged failure.

An **intervention** tries to make the loop *unnecessary* — to replace the next guess with a
decision. Bounds cap cost; interventions recover the work.

Use both. Bounds are not optional just because a protocol exists, and a protocol does not
excuse an unbounded loop.

## Why this is not a level

A reasonable instinct on hitting a loop is to add structure: another reviewer, a planner, a
retry graph. Resist it. The evidence in `evidence.md` is that structure does not buy
intelligence, and that holds here too — the loop is a *context* problem, not a topology
problem. Something needed to be known and was not. More nodes will not learn it; a targeted
read will.
