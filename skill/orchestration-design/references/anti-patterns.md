# Anti-patterns — symptom → diagnosis → fix

Use when something is already built and behaving badly. Each entry starts from what the builder *observes*, because that is what they can tell you.

---

## Runaway and cost

### "It loops forever" / "the run never finishes"
**Diagnosis:** a loop-back edge whose router has no attempt counter, or a counter that is read but never incremented — usually because the incrementing node returns a fresh dict that omits it.
**Fix:** the node that owns the counter increments it in every returned update, including on its error path. Add the global step limit as a backstop. Verify by forcing the failure condition and confirming the run terminates.

### "Costs exploded overnight"
**Diagnosis:** almost always a weak verifier in a fan-out. Each of N branches retries up to `MAX_ATTEMPTS`, so a reviewer that is slightly too strict multiplies spend by N.
**Fix:** add a spend field summed across every model call and read by at least one router. Then look at *why* the reviewer rejects — a verifier with vague criteria fails good work, and the cheapest fix is a sharper rubric, not a bigger budget.

### "It's slow but nothing is running"
**Diagnosis:** a fan-in barrier waiting on a branch that is retrying, or accidental sequencing — branches that look parallel but share a resource (a rate-limited key, one DB connection).
**Fix:** per-branch timeouts, and check whether the parallelism is real. A "parallel" fan-out through one rate-limited client is a queue with extra steps.

---

## State

### "Output changes between identical runs"
**Diagnosis:** state drift — two nodes write the same field with no merge rule, so the result depends on execution order.
**Fix:** find every field with more than one writer. Either give it an append reducer, or split it into per-node fields. This is the single most common structural bug in graphs.

### "Results from parallel branches go missing"
**Diagnosis:** a fan-in field using replace instead of append. Concurrent writes overwrite each other and the loss is silent — you get one result where you expected six.
**Fix:** append reducer on every field the branches write. Then assert the count: `len(results) == len(items) - len(errors)`. Silent partial loss is the failure mode here, so the count assertion is the guard.

### "I can't clear the list between rounds"
**Diagnosis:** correct — you cannot reset an append-reduced field by replacing it.
**Fix:** tag each entry with its round number and filter on read. Do not fight the reducer.

### "One branch sees another branch's data" / flaky cross-contamination
**Diagnosis:** a fanned-out branch reading shared state instead of its own payload. It races: sometimes the sibling has written, sometimes not.
**Fix:** send each branch exactly the payload it needs. Branches read their payload, never sibling state.

---

## Reviewers

### "The reviewer approves everything"
**Diagnosis:** the producer is grading itself — same model, sometimes literally the same context. Models rubber-stamp their own output.
**Fix:** a separate read-only node, ideally a different (usually cheaper) model, which sees only the artifact and returns a verdict plus reasons to its own field. If it still approves everything, the rubric is too vague to fail anything.

### "The reviewer edits the work"
**Diagnosis:** the reviewer node returns an updated draft. Now there is no independent check and two writers on `draft`.
**Fix:** reviewers write only their own verdict field. Revision belongs to the producer, which receives the feedback on the next pass.

### "Quality is fine but it never passes"
**Diagnosis:** an unbounded quality bar — a reviewer that can always find something.
**Fix:** PASS/FAIL against explicit criteria, not "is this good". Cap attempts and choose a deliberate terminal so the run ends either way.

---

## Structure

### "It re-runs everything from scratch after one failure"
**Diagnosis:** no checkpointer. Not an orchestration problem — a persistence problem.
**Fix:** add one and key it per run. A retry then resumes from the last good state. This is usually a much smaller change than the four-hour re-run suggests, and it does not require adding a single node.

### "One bad item kills the whole batch"
**Diagnosis:** an exception propagating out of a branch instead of being caught inside it.
**Fix:** risky nodes catch their own exceptions into an `errors` field and return normally. Downstream routes around them, and the report names what failed. Assert on the counts so isolation stays proven.

### "It's a mess and I can't debug it"
**Diagnosis:** usually node count. Past roughly seven nodes, most designs contain steps masquerading as nodes.
**Fix:** run the merge test on every adjacent pair, and the determinism test on every node — anything not calling a model is a plain function. Designs commonly halve.

### "The code doesn't match the diagram"
**Diagnosis:** drift. The diagram was drawn once and the code moved.
**Fix:** emit the diagram *from* the compiled graph and assert it against the design. `verify_topology.py` in the reference implementations does this. A diagram maintained by hand is documentation; one emitted from code is a test.

---

## Over-engineering

### "Five nodes for a summarizer"
**Diagnosis:** the canonical over-build: fetch → chunk → summarize → review → format. Four of these are functions and the fifth grades itself.
**Fix:** one loop, a fetch tool, chunking as a function, a real verifier. See `reference-implementation/01-loop-not-graph/`.

### "We adopted a framework for three sequential steps"
**Diagnosis:** same error as building an unnecessary graph, one level up.
**Fix:** `references/targets/plain-code.md`. A framework earns its place at real fan-out, durable state, or genuinely complex routing — not before.

### "Every node is an agent"
**Diagnosis:** deterministic work wrapped in prompts. Slower, costlier, and non-deterministic where it did not need to be.
**Fix:** anything expressible as parsing, arithmetic, schema validation or formatting becomes a plain function. Reserve model calls for judgement.
