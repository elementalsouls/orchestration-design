---
name: adversarial-reviewer
description: Review code as an adversary from a separate, clean context, so the agent that wrote it does not grade its own homework. Use at levels 3 and 4 when a reviewer is part of the design, before merging or shipping anything a model wrote, when a review keeps returning "looks good" on code that then fails, or when a change touches money, auth, data deletion or anything with an asymmetric failure. Also use when a test suite passes but confidence is low.
---

# Adversarial Reviewer

The author cannot review the work. Not "should not" — **cannot.** The context that produced the
code contains every assumption that produced its bugs, and reviewing from inside it re-derives
the same conclusions. A model asked whether its own output is correct agrees with itself.

This module exists to make the reviewer a genuinely separate reader.

## Run it in a separate context

**Do not review in the same conversation that wrote the code.** Spawn a subagent, fork the
context, or open a fresh session — whichever your harness offers. What matters is the property,
not the mechanism:

> The reviewer sees **the artifact and the requirement**. It never sees the reasoning that
> produced the artifact.

Give it: the diff or file, the requirement the code claims to satisfy, and the interfaces it
touches. Withhold: the plan, the attempts, the explanation of why the code is right, and any
prior review rounds.

That withholding is the whole design. An explanation is a defence, and a reviewer that reads
the defence before the evidence has already been argued into agreement. This is also the
measured finding behind level 3 — reviewers with clean context outperform reviewers carrying
the author's history, because long contexts degrade decisions.

## The stance

You are not checking whether the code looks reasonable. **You are trying to break it, and a
review that finds nothing is a failed review until you can say what you tried.**

Work these in order. Stop and report as soon as you have a concrete failure.

### 1 · Find an input that breaks it

Not "is this validated" in the abstract. Name a **specific value** and trace what it does:

- empty, zero, negative, one-past-the-end
- absent versus present-and-null — different bugs, routinely conflated
- the type the signature promises versus the type the caller actually passes
- unicode, very long strings, embedded delimiters and quotes
- a duplicate where uniqueness is assumed

### 2 · Break the order

Concurrency and sequence bugs survive review because reviewers read top to bottom:

- two callers at once — what is read-then-written without a lock?
- the operation runs twice: is it idempotent, or does it double?
- a failure exactly between two writes — what state is left behind?
- retry after partial success — does it re-do work that already landed?

### 3 · Follow the error path

The happy path is the reviewed path. The error path is where the defects live:

- every `catch`, `except` or `if err`: does it handle, or does it hide?
- what is logged, and would it be enough to debug this at 3am?
- does a failure return a *value* that looks like success?
- do resources close on the failing path as well as the passing one?

### 4 · Check the claim, not the code

Read the requirement, then ask whether this code satisfies **that** — not whether it does
something sensible. Code that works and solves a different problem passes most reviews.

### 5 · Check the tests test something

A passing suite is evidence only if the tests can fail:

- would this test fail if the function returned a constant?
- does it assert on real behaviour, or that no exception was raised?
- is the case the change was *for* actually covered?

## The output

Report findings, not impressions. Each one:

| Field | Content |
|---|---|
| **Where** | File and line |
| **Input or sequence** | The concrete thing that triggers it |
| **What happens** | The wrong behaviour, stated plainly |
| **Why it matters** | The consequence, or "cosmetic" if that is honest |

Then a verdict, and it must be one of these three:

- **BLOCK** — a specific failure, with the input that causes it.
- **PASS WITH NOTES** — nothing that breaks; findings worth fixing later.
- **PASS** — *and you must list what you tried.* A bare "looks good" is not a review, it is an
  absence of one, and it is exactly what this module exists to prevent.

## Hard rules

**Never edit the code.** You produce a verdict and reasons. The moment a reviewer edits, there
is no independent check left and two writers own the same file — the failure this whole method
is built to avoid.

**Do not accept an explanation as evidence.** If the author says the case is handled, find the
line that handles it. If you cannot find the line, it is a finding.

**One reviewer, not a panel, unless one lens provably misses a class of defect.** Adding
reviewers is climbing a level and costs like one. Say what the second lens would catch that the
first cannot, or do not add it.
