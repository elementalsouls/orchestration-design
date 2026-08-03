#!/usr/bin/env python3
"""Assert that every documented run can still route into the skill.

## What this proves, and what it does not

The skill has exactly one routing surface: the `description:` field in SKILL.md.
It is a single 1024-character string, permanently under pressure to be shortened,
and it decides which requests reach the skill at all. **It has already failed
once.** Cold runs 3-4 handed the skill a compliance audit with no code in it and
got zero invocations, because every trigger in the description was a software
noun. The method was fine. The door was shut.

Nothing in the harness would have caught that, and nothing would catch it
recurring — every existing check verifies that the reference implementations run,
which says nothing about whether a user's request reaches the skill.

So: each fixture records the routing terms its request depends on, and this
asserts they are all still present. Drop "compliance pass" while compressing the
description and this fails, naming the run that would stop firing.

**It cannot verify the skill then picks the right level.** That needs a model, a
transcript and a judgement — it is the human-run decision eval, and pretending to
automate it would be worse than not having it. `expected_level` and `trigger` are
recorded for that eval and checked here only for completeness, never for accuracy.
The gap is stated in the output rather than hidden by a green tick.

    python3 evals/check_routing.py             # the assertions
    python3 evals/check_routing.py --selftest  # same, plus this file's own tests
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skill" / "orchestration-design" / "SKILL.md"
FIXTURES = Path(__file__).resolve().parent / "routing-fixtures.json"

DESC_CAP = 1024                       # Codex truncates past this, silently


def description(skill_md: str) -> str:
    """The `description:` value from the frontmatter, or "" if absent."""
    fm = re.match(r"^---\n(.*?)\n---", skill_md, re.S)
    if not fm:
        return ""
    m = re.search(r"^description:\s*(.+?)(?=\n[a-zA-Z_-]+:|\Z)", fm.group(1), re.S | re.M)
    return " ".join(m.group(1).split()) if m else ""


def check(desc: str, fixtures: list[dict]) -> list[str]:
    """Return a list of failures. Empty means every documented run still routes."""
    bad = []
    low = desc.lower()

    if not desc:
        return ["SKILL.md has no `description:` — nothing can route in at all"]
    if len(desc) > DESC_CAP:
        bad.append(f"description is {len(desc)} chars, over the {DESC_CAP} cap "
                   f"— Codex truncates the tail silently, so late triggers stop firing")

    seen = set()
    for f in fixtures:
        fid = f.get("id", "<no id>")
        if fid in seen:
            bad.append(f"duplicate fixture id: {fid}")
        seen.add(fid)

        # completeness of the record itself — a fixture missing its label is not
        # a fixture, it is a note, and it will quietly stop testing anything
        for field in ("task", "kind", "expected_level", "trigger", "routing_terms"):
            if not f.get(field):
                bad.append(f"{fid}: fixture is missing `{field}`")
        if not isinstance(f.get("expected_level"), int) or not 1 <= f.get("expected_level", 0) <= 6:
            bad.append(f"{fid}: expected_level must be an int in 1..6")

        for term in f.get("routing_terms", []):
            if term.lower() not in low:
                bad.append(f"{fid}: routing term {term!r} is gone from `description:` "
                           f"— this request would stop reaching the skill")
    return bad


def report(desc: str, fixtures: list[dict]) -> int:
    bad = check(desc, fixtures)
    levels = sorted({f.get("expected_level") for f in fixtures if f.get("expected_level")})
    kinds = sorted({f.get("kind") for f in fixtures if f.get("kind")})

    if bad:
        print(f"  FAIL: {len(bad)} problem(s)")
        for b in bad:
            print(f"    - {b}")
        return 1

    missing = [n for n in range(1, 7) if n not in levels]
    print(f"  OK: {len(fixtures)} documented runs still route in "
          f"({len(desc)}/{DESC_CAP} chars used). Levels covered: {levels}; kinds: {kinds}.")
    if missing:
        # not a failure — a disclosed gap. The README says the same thing, and a
        # check that stayed silent here would let the green tick overstate itself.
        print(f"  NOTE: no fixture reaches level(s) {missing}. Routing is asserted; "
              f"level choice is not — that eval needs a model and a human.")
    return 0


def _selftest() -> int:
    """The check has to fail on the regression it exists to catch."""
    fx = json.loads(FIXTURES.read_text())["fixtures"]
    desc = description(SKILL.read_text())

    assert desc, "could not parse `description:` out of SKILL.md"
    assert check(desc, fx) == [], check(desc, fx)

    # 1. the historical failure: PROCESS vocabulary stripped out
    stripped = re.sub(r"PROCESS:.*?(?=DESIGNING,)", "", desc, flags=re.S)
    fails = check(stripped, fx)
    assert any("compliance pass" in f for f in fails), fails
    assert any("compliance-audit-process" in f for f in fails), fails

    # 2. over the cap
    assert any("over the" in f for f in check(desc + "x" * DESC_CAP, fx))

    # 3. an empty description is total failure, not a partial one
    assert len(check("", fx)) == 1

    # 4. a fixture that lost its label is caught
    assert any("missing `routing_terms`" in f
               for f in check(desc, [{"id": "x", "task": "t", "kind": "software",
                                      "expected_level": 1, "trigger": "t"}]))

    # 5. and a plausible-but-wrong level is rejected
    assert any("1..6" in f
               for f in check(desc, [{"id": "x", "task": "t", "kind": "software",
                                      "expected_level": 9, "trigger": "t",
                                      "routing_terms": []}]))

    print("  OK: routing fixtures hold, and the check fails on the regression it guards.")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return _selftest()
    return report(description(SKILL.read_text()),
                  json.loads(FIXTURES.read_text())["fixtures"])


if __name__ == "__main__":
    raise SystemExit(main())
