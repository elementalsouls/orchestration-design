# Target: durable workflow engines

Temporal, Airflow, AWS Step Functions, Dagster, Prefect, Windmill. Choose when the run outlives a single process: hours or days long, scheduled, needs guaranteed retries, must survive a deploy mid-run, or has to be auditable after the fact.

The signal is usually one of these sentences:

- "it re-runs everything from scratch when one step fails"
- "it runs nightly and someone has to babysit it"
- "we need to know exactly what happened three weeks ago"
- "a deploy in the middle of a run loses the run"
- "step 4 needs a human to approve before step 5"

None of these are solved by adding nodes. They are solved by durability, which is a property of the runtime, not of the design.

## How the Phase 2 design maps

| Design artifact | Temporal | Airflow | Step Functions |
|---|---|---|---|
| Node | Activity | Task | State (Task) |
| Edge, sequential | `await` in the workflow fn | `>>` dependency | `Next` |
| Edge, fan-out | list of activity futures | dynamic task mapping | `Map` |
| Edge, conditional | plain `if` | `BranchPythonOperator` | `Choice` |
| State | workflow-function locals | XCom (keep it small) | state machine data |
| Bounds | `RetryPolicy`, timeouts | `retries`, `execution_timeout` | `Retry` / `Catch` |
| Checkpoint | automatic (event-sourced) | task-level | automatic |

**The design object survives unchanged.** Nodes, edges, state ownership, bounds. What changes is that persistence and retry stop being your code.

## The one rule that matters: determinism

On event-sourced engines (Temporal most strictly), the workflow function is **replayed** from history after any failure. Anything non-deterministic in it corrupts replay.

Inside a workflow function, never call: `now()`, `random()`, `uuid4()`, the network, the filesystem, or anything that reads mutable global state. All of it goes in an activity, or through the engine's deterministic API.

```python
# WRONG — replay produces a different value and history diverges
deadline = datetime.now() + timedelta(hours=2)

# RIGHT — recorded in history, identical on replay
deadline = workflow.now() + timedelta(hours=2)
```

This is the mistake that bites hardest, because it works in testing and fails weeks later during an unrelated retry.

## Sequential and fan-out (Temporal shape)

```python
@workflow.defn
class QuestionnaireWorkflow:
    @workflow.run
    async def run(self, doc_ids: list[str]) -> Report:
        policy = RetryPolicy(maximum_attempts=3,
                             initial_interval=timedelta(seconds=2))

        results = await asyncio.gather(*[
            workflow.execute_activity(
                answer_one, doc_id,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=policy,
            )
            for doc_id in doc_ids
        ], return_exceptions=True)      # isolate: one failure ≠ dead workflow

        ok  = [r for r in results if not isinstance(r, Exception)]
        bad = [str(r) for r in results if isinstance(r, Exception)]
        return Report(answers=ok, errors=bad)
```

Note that failure isolation here is `return_exceptions=True` plus partitioning — the engine already retried each activity three times before it reached you, so an exception at this level means genuinely exhausted, not transient.

## Human in the loop

The capability that most justifies this target. A run can pause for days without holding a process open:

```python
@workflow.signal
async def approve(self, decision: str) -> None:
    self._decision = decision

# inside run(), after producing the draft:
await workflow.wait_condition(lambda: self._decision is not None,
                              timeout=timedelta(days=3))
if self._decision != "approved":
    return Report(status="rejected")
```

The Phase 2 equivalent is a reviewer node whose reviewer happens to be a person. Bounds still apply — note the timeout, which is the exhaustion terminal.

## Airflow shape

Airflow is the right fit when the work is a scheduled batch DAG and the nodes are chunky data steps. Dynamic task mapping is its fan-out:

```python
@task
def answer_one(doc_id: str) -> dict: ...

@task
def collect(results: list[dict]) -> dict: ...

with DAG("questionnaires", schedule="0 2 * * *",
         default_args={"retries": 3}) as dag:
    ids = list_docs()
    collect(answer_one.expand(doc_id=ids))
```

**Keep XCom small.** It is a metadata channel, not a data bus — pass object-store keys, not payloads. Passing large results through XCom is the most common way Airflow pipelines become slow and fragile.

Airflow does *not* do loops. A bounded reject loop must be expressed as a fixed number of retry tasks, or the loop must live inside a single task. If your design has a real loop-back edge, that is a signal for Temporal instead.

## Step Functions shape

Best when the nodes are already Lambdas and you want the orchestration declarative and visible.

```json
{
  "StartAt": "FanOut",
  "States": {
    "FanOut": {
      "Type": "Map", "ItemsPath": "$.docs", "MaxConcurrency": 10,
      "Iterator": { "StartAt": "Answer", "States": {
        "Answer": {
          "Type": "Task", "Resource": "arn:…:answerOne", "End": true,
          "Retry": [{ "ErrorEquals": ["States.TaskFailed"], "MaxAttempts": 3 }],
          "Catch": [{ "ErrorEquals": ["States.ALL"], "Next": "RecordError" }]
        },
        "RecordError": { "Type": "Pass", "End": true }
      }},
      "Next": "Collect"
    },
    "Collect": { "Type": "Task", "Resource": "arn:…:collect", "End": true }
  }
}
```

`Catch` inside the `Map` iterator is the failure-isolation mechanism — without it one failed item fails the whole map. Watch the 256KB state payload limit: pass S3 keys, not documents.

## Bounds on this target

| Bound | Where it lives |
|---|---|
| Per-node retry | engine retry policy — **not** a hand-written loop |
| Attempt counter | still yours, for *semantic* retries (reviewer rejected) as opposed to transient failures |
| Global step limit | workflow-level timeout |
| Spend budget | accumulated in workflow state, checked before the next expensive activity |
| Concurrency | `MaxConcurrency` / pool / worker count |

Keep transient retries and semantic retries separate. "The API timed out" is the engine's job. "The reviewer said this draft is wrong" is your attempt counter. Conflating them produces a system that retries bad work nine times.

## Verify

The engines give you real observability, so use it as the Phase 4 check: run once and compare the emitted execution graph or DAG render against the Phase 2 diagram. Then force a failure in one branch and confirm the others complete — failure isolation on this target is a claim about configuration, and configuration should be tested.

## Don't choose this if

The run is short, synchronous, and fits in one process. These engines carry real operational weight: a server or scheduler to run, workers to deploy, versioning rules to respect, and a determinism constraint that surprises people. For a five-minute pipeline, `plain-code.md` plus a JSON checkpoint file gets you resume-on-failure without any of that.
