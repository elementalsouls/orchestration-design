#!/usr/bin/env python3
"""Score a Claude Code skill directory against the skill-design standard.

The standard is in `docs/skill-design-standard.md`. This file is the part of it a
machine can check, and it is deliberately the smaller part: vocabulary coverage and
evidence discipline need a cold run and a human, not a regex.

Every rule here exists because of a measurement across the 719 skills installed on
this machine, or a defect this repo actually shipped. None of them are style.

    python skill_lint.py <skill-dir>          one skill, exit 1 on any FAIL
    python skill_lint.py --corpus <dir>       score every skill under <dir>
    python skill_lint.py --selftest           prove the rules before trusting them

Severity: FAIL is a silent failure or a broken promise — an over-cap description
nobody sees truncated, a referenced file that is not in the bundle. WARN is a smell
that may well be deliberate. Only FAIL moves the exit code, because a linter that
fails on smells is a linter that gets switched off.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Codex truncates the description at 1024 characters without telling anyone. The
# author sees a working skill locally and a silently unroutable one there.
DESC_CAP = 1024
DESC_WARN = 850
DESC_THIN = 60

# SKILL.md loads in full on every trigger; references/ load on demand. Corpus median
# for user-authored skills is 318 lines with no references at all.
BODY_WARN = 250
BODY_FAIL = 600

# Directories a skill conventionally ships. A path is only checked for existence when
# it is rooted in one of these (or in a directory the skill really has) — otherwise it
# is a filename the skill hunts for on a target, not a promise about the bundle.
CONV_DIRS = {"references", "reference", "scripts", "assets",
             "templates", "targets", "examples"}

LITTER = (".DS_Store", "__pycache__", ".pyc", ".orig", ".rej", ".swp")

FAIL, WARN, PASS = "FAIL", "WARN", "PASS"

_PATHISH = re.compile(r'`([A-Za-z0-9_][A-Za-z0-9_./-]*\.[A-Za-z0-9]{1,5})`')
_MDLINK = re.compile(r'\]\(([A-Za-z0-9_][A-Za-z0-9_./-]*\.[A-Za-z0-9]{1,5})\)')
# "when to use" signals, in the forms skill authors actually write them
_ROUTING = re.compile(r'\b(use (this )?(when|for|if)|fires? on|invoke when|'
                      r'when (you|the user|starting|asked)|for (any|multi|when))\b', re.I)


def frontmatter(text: str) -> tuple[str, str]:
    """Split a SKILL.md into (frontmatter, body). Missing frontmatter -> ('', text)."""
    m = re.match(r'^---\n(.*?)\n---\n?', text, re.S)
    return (m.group(1), text[m.end():]) if m else ("", text)


def field(fm: str, key: str) -> str:
    """Read one top-level key, including folded multi-line values."""
    m = re.search(rf'^{key}:\s*(.+?)(?=\n[a-zA-Z][a-zA-Z0-9_-]*:|\Z)', fm, re.M | re.S)
    return m.group(1).strip() if m else ""


def referenced_paths(body: str) -> list[str]:
    return sorted(set(_PATHISH.findall(body)) | set(_MDLINK.findall(body)))


def check(skill_dir: Path) -> list[tuple[str, str, str]]:
    """Return [(rule, severity, message)] for one skill directory."""
    out: list[tuple[str, str, str]] = []
    add = lambda r, s, m: out.append((r, s, m))

    md = skill_dir / "SKILL.md"
    if not md.exists():
        return [("frontmatter", FAIL, "no SKILL.md")]

    text = md.read_text(errors="replace")
    fm, body = frontmatter(text)

    # --- pillar 1: the trigger contract -------------------------------------
    if not fm:
        add("frontmatter", FAIL, "no YAML frontmatter — the skill cannot be routed")
    name, desc = field(fm, "name"), field(fm, "description")

    if not name:
        add("frontmatter", FAIL, "no name: field")
    elif name != skill_dir.name:
        add("name-matches-dir", FAIL, f"name '{name}' != directory '{skill_dir.name}'")
    else:
        add("name-matches-dir", PASS, name)

    if not desc:
        add("description-cap", FAIL, "no description: field — the skill can never fire")
    elif len(desc) > DESC_CAP:
        add("description-cap", FAIL,
            f"{len(desc)} chars — over the {DESC_CAP} cap, truncated silently on Codex")
    elif len(desc) > DESC_WARN:
        add("description-cap", WARN, f"{len(desc)} chars — close to the {DESC_CAP} cap")
    elif len(desc) < DESC_THIN:
        add("description-cap", WARN, f"{len(desc)} chars — too thin to route reliably")
    else:
        add("description-cap", PASS, f"{len(desc)} chars")

    if desc:
        if _ROUTING.search(desc):
            add("description-routing", PASS, "states when to use it")
        else:
            add("description-routing", WARN,
                "no 'use when' signal — says what it is, not when to fire")

    # --- pillar 2: load budget and progressive disclosure --------------------
    refs = [p for p in skill_dir.rglob("*.md") if p.name != "SKILL.md"]
    lines = body.count("\n") + 1
    if lines > BODY_FAIL and not refs:
        add("load-budget", FAIL,
            f"{lines} lines, no reference files — every trigger loads all of it")
    elif lines > BODY_WARN and not refs:
        add("load-budget", WARN, f"{lines} lines with no references/ — split the depth out")
    elif lines > BODY_FAIL:
        add("load-budget", WARN, f"{lines} lines even with {len(refs)} reference files")
    else:
        add("load-budget", PASS, f"{lines} lines, {len(refs)} reference files")

    # --- pillar 3: reference integrity --------------------------------------
    missing = []
    for tok in referenced_paths(body):
        if "/" not in tok:
            continue                      # bare filename — usually a target-side artifact
        first = tok.split("/", 1)[0]
        if first not in CONV_DIRS and not (skill_dir / first).is_dir():
            continue                      # not a promise about this bundle
        if not (skill_dir / tok).exists():
            missing.append(tok)
    if missing:
        add("reference-integrity", FAIL,
            f"{len(missing)} referenced path(s) not in the bundle: {', '.join(missing[:3])}")
    else:
        add("reference-integrity", PASS, "every intra-skill path resolves")

    # --- pillar 7: distribution hygiene -------------------------------------
    junk = [p.name for p in skill_dir.rglob("*")
            if any(p.name == b or p.name.endswith(b) for b in LITTER)]
    if junk:
        add("bundle-hygiene", FAIL, f"litter in the bundle: {', '.join(sorted(set(junk))[:4])}")
    else:
        add("bundle-hygiene", PASS, "clean")

    return out


def worst(results: list[tuple[str, str, str]]) -> str:
    sev = {r[1] for r in results}
    return FAIL if FAIL in sev else WARN if WARN in sev else PASS


def report_one(skill_dir: Path) -> int:
    results = check(skill_dir)
    print(f"\n  {skill_dir.name}")
    for rule, sev, msg in results:
        icon = {PASS: "ok", WARN: "??", FAIL: "XX"}[sev]
        print(f"    [{icon}] {rule:22} {msg}")
    verdict = worst(results)
    print(f"\n  {verdict}")
    return 1 if verdict == FAIL else 0


def report_corpus(root: Path) -> int:
    skills = sorted({p.parent for p in root.rglob("SKILL.md")})
    rows = [(d, check(d)) for d in skills]

    # the one rule that needs more than a single skill to see
    from collections import Counter
    names = Counter(field(frontmatter((d / "SKILL.md").read_text(errors="replace"))[0],
                          "name") or d.name for d in skills)
    dups = {n: c for n, c in names.items() if c > 1}

    rows.sort(key=lambda r: (-sum(s == FAIL for _, s, _ in r[1]),
                             -sum(s == WARN for _, s, _ in r[1])))
    print(f"  {len(skills)} skills under {root}\n")
    print(f"  {'skill':32} {'FAIL':>4} {'WARN':>4}  first failure")
    print(f"  {'-'*32} {'-'*4} {'-'*4}  {'-'*40}")
    nfail = 0
    for d, res in rows:
        f = sum(s == FAIL for _, s, _ in res)
        w = sum(s == WARN for _, s, _ in res)
        nfail += bool(f)
        first = next((f"{r}: {m}" for r, s, m in res if s == FAIL), "")
        print(f"  {d.name[:32]:32} {f:4} {w:4}  {first[:56]}")
    print(f"\n  {nfail} of {len(skills)} skills have at least one FAIL")
    if dups:
        print(f"\n  duplicate names (routing ambiguity): "
              f"{', '.join(f'{n}×{c}' for n, c in sorted(dups.items()))}")
    return 0                                    # corpus mode reports; it does not gate


def _selftest() -> int:
    """Build fixtures with known defects and assert the rules catch exactly those."""
    import tempfile, textwrap

    def mk(root: Path, name: str, fm: str, body: str = "method here\n") -> Path:
        d = root / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\n{fm}\n---\n{body}")
        return d

    def sev_of(res, rule):
        return next((s for r, s, _ in res if r == rule), None)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        good = mk(root, "good-skill",
                  "name: good-skill\ndescription: Does a thing. Use when the thing "
                  "is needed and you want it done well.")
        (good / "references").mkdir()
        (good / "references" / "depth.md").write_text("depth\n")
        (good / "SKILL.md").write_text(
            "---\nname: good-skill\ndescription: Does a thing well. Use when the thing "
            "is needed and the obvious approach has already failed.\n---\n"
            "See `references/depth.md`.\n")
        r = check(good)
        assert worst(r) == PASS, r
        assert sev_of(r, "reference-integrity") == PASS

        over = "x" * (DESC_CAP + 5)
        d = mk(root, "over-cap", f"name: over-cap\ndescription: Use when {over}")
        assert sev_of(check(d), "description-cap") == FAIL

        d = mk(root, "wrong-name", "name: something-else\ndescription: Use when asked.")
        assert sev_of(check(d), "name-matches-dir") == FAIL

        d = mk(root, "huge", "name: huge\ndescription: Use when asked.",
               "line\n" * (BODY_FAIL + 10))
        assert sev_of(check(d), "load-budget") == FAIL

        d = mk(root, "broken-ref", "name: broken-ref\ndescription: Use when asked.",
               "Read `references/missing.md` first.\n")
        assert sev_of(check(d), "reference-integrity") == FAIL

        # a security skill naming target-side artifacts must NOT be flagged — this is
        # the false-positive class that would get the linter switched off
        d = mk(root, "target-paths", "name: target-paths\ndescription: Use when hunting.",
               "Fetch `swagger.json`, `package.json` and `_next/static/chunks/main.js`.\n")
        assert sev_of(check(d), "reference-integrity") == PASS, check(d)

        d = mk(root, "no-routing", "name: no-routing\ndescription: A tool that "
               "reticulates splines and produces a report of the reticulation.")
        assert sev_of(check(d), "description-routing") == WARN

        d = mk(root, "littered", "name: littered\ndescription: Use when asked.")
        (d / ".DS_Store").write_text("junk")
        assert sev_of(check(d), "bundle-hygiene") == FAIL

        d = root / "no-skill-md"
        d.mkdir()
        assert check(d)[0][1] == FAIL

    print("  OK: 9 fixtures — cap, name, budget, broken ref, target-path "
          "false positive, routing, litter, missing SKILL.md, clean pass.")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        return _selftest()
    if "--corpus" in args:
        i = args.index("--corpus")
        return report_corpus(Path(args[i + 1]).expanduser())
    if not args:
        print(__doc__.strip().splitlines()[0])
        print("usage: skill_lint.py <skill-dir> | --corpus <dir> | --selftest")
        return 2
    return report_one(Path(args[0]).expanduser())


if __name__ == "__main__":
    sys.exit(main())
