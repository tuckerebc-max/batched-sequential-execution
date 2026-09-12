# Contributing

This is a small, deliberately narrow tool. Contributions that keep it small are
welcome; contributions that grow it into a general task runner are not.

## Adding a mechanical verifier

Verifiers live in `scripts/bse.py` in a single flat registry (`VERIFIERS`, a
dict of name -> function). Adding one is a five-line change:

```python
@verifier("my_check")
def v_my_check(text: str, args: str, ctx: dict) -> Tuple[bool, str]:
    """One-line docstring: what args means, e.g. 'my_check <threshold>'."""
    # text  = the artifact's full text
    # args  = whatever follows the verifier name on the plan's
    #         "- mechanical: my_check <args>" line
    # ctx   = {"unit": Unit, "run_dir": Path, ...}
    ok = ...            # bool
    detail = "..."      # short human-readable reason, shown in reports/ID.md
    return ok, detail
```

The `@verifier(...)` decorator inserts the function into `VERIFIERS` at import
time — nothing else needs to be registered or wired up. `bse.py plan
--validate` already checks any verifier name against this registry and fails
loudly on a typo or an unknown check, so a plan referencing your new verifier
will validate as soon as the function exists.

Guidelines for a new verifier:

- Bind to something external and checkable (a count, a regex, a schema, an
  exit code) — never to the model's own judgment of quality. See
  `references/verification.md` and `references/evidence.md` §4 for why.
- Keep it stdlib-only. No new imports beyond the Python standard library.
- Make failure detail actionable: name the line, the count, the offending
  string — whatever a fix round needs to act on without re-reading the whole
  artifact.
- Add both a passing and a failing test case (see below).

## Running the tests

```
python -m unittest discover -s tests -v
```

No network access, no third-party packages, and it must pass on Python 3.9
through 3.13 (the CI matrix in `.github/workflows/test.yml` enforces this on
every push and pull request).

## The rule

**Every behavior change needs a test.** A new verifier, a new CLI flag, a
change to ledger format, a change to how `stitch` or `audit` decide something
— each gets at least one test that would fail without the change. `record`
refusing `done` on a failed check (or, for a unit with judgment predicates, on
a missing/failing `review`) is load-bearing; do not weaken it without a test
proving the refusal still holds.

**The worked runs under `examples/` are exercised in CI, not just kept as
documentation.** The `examples` job in `.github/workflows/test.yml` runs
`bse.py audit` (and related checks) against every `examples/*/ledger.json`
directly against the code you're changing. A behavior change that affects
plan validation, the ledger schema, `stitch`, or `audit` can make an existing
example fail CI even though nothing under `examples/` looks wrong to a human
reader — regenerate or hand-edit the affected example's `CHARTER.md`,
`PLAN.md`, `ledger.json`, or `LEDGER.md` to match the new behavior, and check
that job locally before opening a PR, not just `python -m unittest`.

## Style commitments

- **Standard library only.** `scripts/bse.py` imports nothing beyond
  `argparse`, `json`, `hashlib`, `re`, `pathlib`, and friends. No pip
  dependencies, ever — the tool must run on a bare Python install.
- **Windows and POSIX.** Use `pathlib`, not hardcoded `/`. Writes are atomic
  (temp file + `os.replace`) so a crash mid-write cannot corrupt the ledger on
  either platform.
- **No emoji.** Anywhere — CLI output, docs, commit messages, code comments.
- **Evidence-backed claims only.** A design claim in `SKILL.md`, `DESIGN.md`,
  or a `references/` file should trace to something in
  `references/evidence.md`. If you add a design principle, add or extend the
  evidence entry it rests on, including the honest gaps (see evidence.md §7)
  rather than overstating what a source shows.
- **Progressive disclosure.** `SKILL.md` stays scannable; detail belongs in
  `references/`, loaded on demand, not inlined into the skill body.

## Reporting issues

Open an issue with the run directory's `LEDGER.md` and `ledger.json` attached
when the bug is about state or resume — those two files are what the tool
actually reasons from, and they reproduce the problem far better than a
description of what happened in a conversation.
