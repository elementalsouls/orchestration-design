---
name: Counterexample — the ladder gave you the wrong answer
about: A case where the skill picked the wrong level, or refused something that turned out to be right. This is the most useful issue you can file here.
title: "counterexample: "
labels: counterexample
---

## Why this template exists

The ladder is a **well-argued default, not a measured one.** Nine end-to-end runs, five of them
cold, and every single one landed at level 1, 3 or 5. Levels 4 and 6 have never been exercised
by anyone but the author, and Track B — auditing a system that already exists — has never been
run cold at all.

So a case where it got the answer wrong is worth more here than a bug report. It is the only
evidence that moves the default.

**You do not need to have been right.** "It said level 1, I built level 3, and level 1 would
actually have been fine" is a useful counterexample too — it tells us the trigger reads as
weaker than it is.

---

## What you were building

One or two sentences. Software or process, roughly what shape, roughly what scale.

## What the skill said

**Level it picked:**

**The trigger it named** — the skill is supposed to say a specific one out loud, e.g. *"level 3,
because output correctness can't be asserted mechanically"*. Paste it if you have it:

## What you actually needed

**Level that turned out right:**

## How you know

This is the part that matters, and the part that is easy to skip. Not "it felt wrong" —
what *happened*?

- If it under-called: what broke, and how did you find out? Did it fit in context and then
  stop fitting? Did a single writer turn out to be several?
- If it over-called: what did you build that never earned its cost? Did the extra structure
  catch anything in production?
- If it refused and you built it anyway: what did the thing you built do that the simpler
  version could not?

## Which part misread

Tick anything that applies — a guess is fine, this is diagnosis, not blame.

- [ ] **Phase 0** — it assumed something about volume, cadence or the failure that hurts, and the assumption was wrong
- [ ] **The pre-ladder question** — the route was knowable and it said it wasn't, or vice versa
- [ ] **A level trigger** — the trigger was true and it read as false, or the reverse
- [ ] **Level 5's context-pressure trigger specifically** — this one is the most load-bearing and the least tested
- [ ] **Per-stage levels** — it gave one level for a system that genuinely needed different levels per stage
- [ ] **The cost comparison** — the numbers pointed the wrong way
- [ ] **Track B** — auditing something that already existed
- [ ] Something else, described below

## Anything else

Diagram, design output, or the transcript if you still have it. Redact freely — the shape of
the decision is what's useful, not your code.

---

*Filing this at all is a favour to everyone using the skill. If you only have half the detail,
file it anyway; a partial counterexample beats a missing one.*
