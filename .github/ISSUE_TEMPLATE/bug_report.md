---
name: Bug report
about: Something in the repo is broken — a check fails, a reference points at nothing, an example does not run
title: "bug: "
labels: bug
---

## What's broken

One sentence.

**If the skill gave you a design you disagree with, that is not this template** — file a
[counterexample](?template=counterexample.md) instead. That is a more useful issue and it gets
read more carefully.

## Where

- [ ] `SKILL.md` or a file under `references/`
- [ ] A tactical module under `modules/`
- [ ] A reference implementation (`reference-implementation/0*`)
- [ ] A tool (`tools/`) or the check runner (`run_checks.py`)
- [ ] `build.sh` — packaging or install
- [ ] Docs: README, `CLAUDE.md`, or something under `docs/`

## To reproduce

```bash
# the exact command
```

## What happened

Paste the actual output, not a summary of it. A remembered error is frequently a different
error.

```
```

## What you expected instead

## Did the checks catch it?

Everything here is supposed to be verified by one command. If this got past that, the gap in
the harness is part of the bug:

```bash
python run_checks.py                          # every check
python tools/skill_lint.py skill/orchestration-design
```

- [ ] `run_checks.py` fails too — good, the harness caught it
- [ ] `run_checks.py` passes and the bug is real — **say so here**, the missing check matters as much as the fix
- [ ] Didn't run it

## Environment

Only if it might be environmental — a packaging, install or example-runner problem.

- OS:
- Python:
- Installed via `./build.sh`, or reading the repo directly:
