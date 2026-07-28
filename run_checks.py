#!/usr/bin/env python3
"""Run every verification check in this repo. One command, one exit code.

Replaces the six manual commands that used to live in HANDOFF_PROMPT.md.

Designed with the orchestration-design skill:
  Phase 1  rung 1 (plain script). The climb trigger — "needs judgement a rule
           cannot encode" — is false. Exit codes are the entire signal.
  Phase 2  discover -> run_one (per check) -> report. No models, no loop-back,
           so no attempt counter and no spend budget. Only bound that applies
           is a per-check timeout so a hung example cannot hang CI.

Missing dependencies FAIL by default: in CI a skipped check that silently
passes is how green builds start lying. Use --allow-skip locally.

    python run_checks.py                  # langgraph missing -> FAIL, exit 1
    python run_checks.py --allow-skip     # langgraph missing -> SKIP, exit 0
    python run_checks.py --python /path/to/venv/bin/python
    python run_checks.py --selftest
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REF = ROOT / "reference-implementation"
TIMEOUT = 30          # the one bound that applies: a hung check must not hang CI

PASS, FAIL, SKIP, TIMED_OUT, DEPMISS = "PASS", "FAIL", "SKIP", "TIMEOUT", "NO-DEP"
BAD = {FAIL, TIMED_OUT}          # always fatal
ICON = {PASS: "ok", FAIL: "XX", SKIP: "--", TIMED_OUT: "TO", DEPMISS: "!!"}


def discover() -> list[dict]:
    """Not a node — no model call. Lists the checks and what each one needs."""
    checks = [{"name": "01-loop-not-graph",
               "path": REF / "01-loop-not-graph" / "loop.py", "needs": None}]
    for d in ("02-sequential", "03-reviewer-loop",
              "04-fanout-fanin", "05-judge-panel"):
        checks.append({"name": d, "path": REF / d / "graph.py",
                       "needs": "langgraph"})
    checks.append({"name": "verify-topology",
                   "path": REF / "verify_topology.py", "needs": None})
    return checks


def has_module(python: str, module: str) -> bool:
    return subprocess.run([python, "-c", f"import {module}"],
                          capture_output=True).returncode == 0


def run_one(check: dict, python: str, available: dict[str, bool],
            allow_skip: bool) -> dict:
    """Run one check. Catches its own failures so one broken check cannot
    abort the sweep — the others still report."""
    if not check["path"].exists():
        return {**check, "status": FAIL, "secs": 0.0,
                "tail": f"missing file: {check['path']}"}

    need = check["needs"]
    if need and not available.get(need, False):
        return {**check, "status": SKIP if allow_skip else DEPMISS, "secs": 0.0,
                "tail": f"{need} not importable by {python} — pip install -U {need}"}

    start = time.monotonic()
    try:
        p = subprocess.run([python, str(check["path"])],
                           capture_output=True, text=True, timeout=TIMEOUT)
        status = PASS if p.returncode == 0 else FAIL
        out = (p.stdout + p.stderr).strip().splitlines()
        tail = out[-1] if out else ""
    except subprocess.TimeoutExpired:
        status, tail = TIMED_OUT, f"exceeded {TIMEOUT}s"
    except Exception as e:                    # never let one check kill the run
        status, tail = FAIL, f"runner error: {e!r}"
    return {**check, "status": status, "secs": time.monotonic() - start,
            "tail": tail}


def report(results: list[dict], allow_skip: bool) -> int:
    width = max(len(r["name"]) for r in results)
    for r in results:
        print(f"  [{ICON[r['status']]}] {r['name']:<{width}}  "
              f"{r['secs']:5.2f}s  {r['tail'][:70]}")

    counts = {s: sum(r["status"] == s for r in results) for s in
              (PASS, FAIL, SKIP, TIMED_OUT, DEPMISS)}
    print("\n  " + "  ".join(f"{k}={v}" for k, v in counts.items() if v))

    fatal = BAD | (set() if allow_skip else {DEPMISS})
    failed = [r for r in results if r["status"] in fatal]
    if failed:
        print(f"\n  FAILED: {', '.join(r['name'] for r in failed)}")
        if any(r["status"] == DEPMISS for r in failed):
            print("  (missing deps fail by default — pass --allow-skip to tolerate)")
        return 1
    print("\n  all checks passed")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Run every check in this repo.")
    ap.add_argument("--python", default=sys.executable,
                    help="interpreter to run checks with (default: this one)")
    ap.add_argument("--allow-skip", action="store_true",
                    help="tolerate missing dependencies instead of failing")
    args = ap.parse_args(argv)

    checks = discover()
    needed = {c["needs"] for c in checks if c["needs"]}
    available = {m: has_module(args.python, m) for m in needed}

    print(f"  python: {args.python}")
    for m, ok in sorted(available.items()):
        print(f"  {m}: {'available' if ok else 'MISSING'}")
    print()

    results = [run_one(c, args.python, available, args.allow_skip) for c in checks]
    return report(results, args.allow_skip)


# ------------------------------------------------------------- selftest -----
def _selftest() -> int:
    """Phase 4 for rung 1: assert the behaviour the design promised.

    Assertion 1 (reviewer is read-only) does not apply — rung 1 has no
    reviewer. The other three do.
    """
    import tempfile, textwrap

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "ok.py").write_text("print('fine')\n")
        (t / "bad.py").write_text("import sys; print('boom'); sys.exit(3)\n")
        (t / "hang.py").write_text("import time; time.sleep(60)\n")

        avail = {"langgraph": False}
        mk = lambda n, needs=None: {"name": n, "path": t / f"{n}.py", "needs": needs}

        # bound is live: the timeout actually fires
        global TIMEOUT
        saved, TIMEOUT = TIMEOUT, 1
        try:
            r = run_one(mk("hang"), sys.executable, avail, False)
            assert r["status"] == TIMED_OUT, r
        finally:
            TIMEOUT = saved

        # failure is isolated: a failing check does not stop its siblings
        res = [run_one(mk(n), sys.executable, avail, False)
               for n in ("ok", "bad", "ok")]
        assert [x["status"] for x in res] == [PASS, FAIL, PASS], res

        # a missing file is reported, not raised
        assert run_one(mk("nope"), sys.executable, avail, False)["status"] == FAIL

        # the dep decision: FAIL by default, SKIP only when asked
        assert run_one(mk("ok", "langgraph"), sys.executable, avail,
                       False)["status"] == DEPMISS
        assert run_one(mk("ok", "langgraph"), sys.executable, avail,
                       True)["status"] == SKIP

        # exhaustion terminal is reachable AND marked: exit code follows
        import contextlib, io

        def quiet_report(res, allow):        # report() prints; selftest shouldn't
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                code = report(res, allow)
            return code, buf.getvalue()

        code, text = quiet_report([run_one(mk("ok", "langgraph"), sys.executable,
                                           avail, False)], False)
        assert code == 1 and "--allow-skip" in text, text
        assert quiet_report([run_one(mk("ok", "langgraph"), sys.executable,
                                     avail, True)], True)[0] == 0
        assert quiet_report([run_one(mk("ok"), sys.executable, avail, False)],
                            False)[0] == 0

    print("OK: timeout fires, failures isolated, missing deps fail by default "
          "and skip only with --allow-skip.")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main(sys.argv[1:]))
