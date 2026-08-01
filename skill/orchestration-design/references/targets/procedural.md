# Target: a process (no runtime)

**Pick this when the output is work, not software.** A research project, an audit, a migration, a manuscript, a literature review, a due-diligence pass, a hiring round. The nodes are prompts, subagents and human decisions. There is nothing to deploy and nothing to compile.

This is the most common substrate for multi-step work with a model, and the one people most often fail to design at all — they just start prompting and hope the shape emerges. It doesn't. It sprawls, it repeats itself, and it stops when attention runs out rather than when the work is done.

The design object from Phase 2 does not change. **Nodes become steps, edges become the order you actually work in, state becomes a file, bounds become rounds and budget and wall clock.** All four still exist and all four are still load-bearing.

---

## State: one file, one writer per column

The single highest-value artifact in a procedural design is a **ledger**: one row per unit of work, one column per check, seeded with the value `pending`.

```markdown
| Unit          | Check A | Check B | Check C |
|---------------|---------|---------|---------|
| chapter-01    | done    | pending | n/a     |
| chapter-02    | pending | pending | pending |
| chapter-03    | done    | done    | blocked |
```

Its whole job is to make **absence visible**. Without it, "what have I not done?" is answered from memory, and memory returns a confident, incomplete list. With it, that question is a filter.

**One writer per column.** If a discovery step and a verification step both write "status," they will disagree and the last one to run wins silently. Split them:

```markdown
| Unit | discovery_verdict | verification_verdict |   <- two columns, two owners
```

**Allowed values, declared up front.** Pick a closed set and reject anything outside it — a typo like `cleaned` instead of `clean` silently reads as "never done" forever:

```
done · not_applicable · out_of_scope · blocked · pending
```

**Only some of those count as covered.** `blocked` and `pending` are gaps. That distinction is the entire point: a unit nobody could reach is *not* a unit that passed.

---

## Pattern A — sequential

```
scope ──► gather ──► process ──► review ──► deliver
```

If this is your whole design, you did not need orchestration. Write the steps down, keep the ledger, and go. **This is a successful outcome**, not a failure to find complexity.

## Pattern B — bounded review loop

```
draft ──► review ──► good enough? ──no, attempt < 3──► draft
                          │ yes
                          ▼
                       deliver
```

The reviewer must be a **separate step with clean context** — a fresh subagent or a fresh session, given the artifact and the criteria but not the history of how it was produced. A reviewer that has watched the work being made will rationalise it.

`attempt < 3` is not decoration. Without it, "not quite right" loops until you give up, which is a stopping condition set by fatigue rather than by quality.

## Pattern C — fan-out to subagents

Use when the material genuinely exceeds one context window — not merely because the units are independent. Independence makes fan-out *safe*; context pressure is what makes it *necessary*.

Each branch gets **its own unit and the scope rules as data**, never a shared scratchpad it might write to. Then:

```
assert rows_completed + rows_failed == rows_dispatched
```

Silent loss in a fan-out is invisible without that count. A branch that dies quietly looks exactly like a branch that found nothing.

## Pattern D — loop until dry, with a coverage gate

The pattern for anything where **completeness matters and the work reveals more work**:

```
CLOSE CLEAN when
  every (unit × applicable check) has a verdict
  AND K consecutive rounds produced nothing new
  AND every blocked item carries a reason
FORCE-CLOSE when
  rounds >= max_rounds OR budget exhausted
  -> terminal is MARKED, and the gaps ship as caveats
```

Two properties make this worth the trouble:

**The ledger grows mid-run.** Discovery adds rows. A completeness check computed once, at the start, is wrong by round two.

**The forced terminal is a feature.** When the criteria cannot be met, the work must end *loudly* — with the unreached units named in the output — rather than quietly stopping and reading as complete. See "the caveat section writes itself" below.

---

## Bounds without a runtime

| Bound | Procedural form |
|---|---|
| Attempt counter | `max_rounds`, tracked in the ledger's round log |
| Global step limit | a wall-clock or session cap you write down before starting |
| Spend budget | token or cost ceiling, checked between rounds |
| Per-node timeout | "if this step has produced nothing in 20 minutes, rotate" |
| Retry | re-dispatch a failed unit once, then mark it `blocked` with the reason |

Every one of these is a number you decide **before** you start, because deciding it afterwards means deciding it while invested in the outcome.

---

## The caveat section writes itself

This is the payoff, and it generalises to every domain.

A deliverable that lists what was found — and says nothing about what was not examined — implies complete coverage it did not achieve. That implication is rarely deliberate and almost always wrong. It is the default failure of every report, audit, review and summary produced by a person or a model working from memory.

If the ledger is the source, the "not covered" section is **generated, not remembered**:

```markdown
## Not covered — do not read as passing

**Blocked** — reachable but could not be assessed:
- supplier-14 · financial check — accounts not filed for FY24

**Never reached** — discovered but never examined:
- chapter-09 · fact-check
```

Generate it every time, including when it is empty. An explicit *"every unit reached a verdict"* is a claim; a missing section is an omission, and the reader cannot tell the difference.

---

## Verify

Phase 4 applies with no runtime to compile. Assert the behaviour the design promised:

1. **The reviewer is read-only.** It writes a verdict; it does not edit the artifact. If your reviewer hands back a rewritten draft, it is a second writer, not a reviewer.
2. **Every bound is live.** Force the condition each one guards. A `max_rounds` you have never actually hit is undemonstrated, not proven.
3. **The forced terminal is reachable and marked.** Run a case that cannot close clean and confirm the caveats appear in the output.
4. **The counts add up.** `units dispatched == completed + failed`, no unit settled twice.
5. **The ledger's allowed values are enforced.** Try to write an invalid verdict and confirm it is rejected at write time, not discovered three rounds later.

---

## When to graduate to a runtime

Move to `plain-code.md` when the process is run often enough, or by enough people, that consistency matters more than flexibility — or when the ledger has grown past what a human can maintain by hand. Not before. A process that runs twice does not need a pipeline, and a pipeline built for a process nobody has run yet encodes guesses as constraints.
