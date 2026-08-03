---
name: rubber-duck-verifier
description: Break an execution loop by explaining the failure in text before touching code again. Use when stuck in a loop, guessing, or repeatedly failing tests — when the same file has been edited three or more times without the error changing, when fixes are being tried in sequence rather than chosen, when a test has failed the same way twice, or when a build or pipeline step keeps failing and each attempt is a variation of the last. Also use before a fourth attempt at anything, and when about to add a workaround for a cause that has not been identified.
---

# Rubber Duck Verification Protocol

You are stuck. Stop writing code.

Not "write one more fix and see" — **stop**. The next edit will not work either, because
the thing producing wrong edits is a wrong model of the problem, and another edit does not
change the model. Every attempt from here is a coin flip that also costs a test run.

## When this fires

You are in a loop when any of these is true. They are observations, not feelings:

- The same file has been edited three or more times and the error has not changed.
- A test has failed the same way twice.
- You are about to try something because the last thing did not work, rather than because
  you expect this one to.
- You are about to add a retry, a sleep, a try/except, a cast, or a config flag around a
  cause you have not named.
- You could not answer "what exactly is wrong?" in one sentence without hedging.

One of those is enough. Do not wait for a fourth attempt to confirm it.

## The protocol

Write these four sections **as text, in your reply, before any tool call**. No code blocks,
no edits, no test runs. Writing them is the intervention — the point is to force the model
of the problem into words, where its gaps become visible.

### 1 · The Goal

What is supposed to happen, stated as observable behaviour. Not "fix the auth bug" —
*"a request with an expired token returns 401 and does not reach the handler."*

If you cannot state the goal in one concrete sentence, that is the bug. Stop here and go
find out what correct looks like.

### 2 · The Failure

What actually happens, quoted exactly. The real error string, the real exit code, the real
diff between expected and observed. Not a paraphrase and not your interpretation of it.

If you are working from a summary of the failure rather than the failure itself, go and read
the actual output first. A remembered error is frequently a different error.

### 3 · The Failed Assumptions

List what you believed that turned out not to hold. This is the section that does the work,
and the one people skip.

For each attempt you made, write the belief behind it and what the result proved about that
belief. *"I assumed the config was loaded before the client was constructed. Attempt 2 moved
the load earlier and the error was identical, so load order is not the cause."*

A loop is a sequence of attempts that never updated a belief. If you cannot name what each
attempt ruled out, you have been guessing, and the list will show you that in one line.

### 4 · Missing Context

Name what you do not know and cannot deduce from what is in front of you. Be specific about
the artefact, not the topic:

- the actual value at runtime, versus what the code implies it should be
- the real schema, config or environment, rather than the one the code assumes
- what the caller passes, when you have only read the callee
- what changed most recently, when this used to work
- the full log or stack trace, when you have been working from its last line

Then **go and get one of them**. A single targeted read — one log, one value, one caller —
is worth more than three more attempts, and it is the only move that reliably ends the loop.

## After the tear-down

One of three things is now true:

1. **The cause is obvious.** It usually is, and it is usually in section 3. Fix that, not the
   symptom.
2. **You know what to look at.** Go read that one thing, then re-run the protocol with the
   answer in hand.
3. **The goal was wrong.** The behaviour you were driving toward is not the behaviour that is
   wanted. Say so and ask — this is a real outcome and by far the cheapest one to discover.

**Never resume editing straight from the tear-down without one of those three.** If all four
sections are written and none of them changed anything, you have documented the loop rather
than broken it — say that plainly and escalate to a human instead of starting attempt five.

## What this protocol is not

It is not a retry with better formatting. If the tear-down produces the same fix you were
about to make anyway, you wrote it too quickly — section 3 in particular is not "the previous
attempts failed", it is *what each one proved false*.

It is also not a substitute for reading. The most common ending is section 4: the loop
continued because a value, a log or a caller was never actually looked at.
