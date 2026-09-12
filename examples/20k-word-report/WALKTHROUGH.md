# Walkthrough — Bridging the Interconnection Queue

This is a real run of `scripts/bse.py`, not a mockup. Every command below was
actually executed against this directory; every block of output is what the
tool actually printed. The full report is not drafted end to end here — that
would mean pasting an entire policy report into an example directory — but
the first three units are executed for real, including one genuine
verification failure and its fix, plus a real reviewer pass on the two units
that declare judgement predicates, so a reader can see exactly what the loop
looks like in practice. Units B004-B015 exist only as validated plan entries;
running them is left as the same loop, repeated.

All commands were run from the repo root with `--run-dir examples/20k-word-report`
so this run never touches `./.bse` or interferes with the other two examples.

**Before running `next`, the plan must be validated.** The tool refuses to
schedule work on a plan it has never seen pass `--validate`:

```
$ python3 scripts/bse.py next --run-dir <a plan never validated in this run>
error: PLAN NOT VALIDATED: run `bse.py plan --validate` before executing (the plan gate)
```

(That transcript is from a disposable copy of this run with the
`plan_validated` marker stripped out of `ledger.json`, to show the refusal
without disturbing this run's real state — this run's plan was validated
before `next` was ever called, in section 1 below.)

## 1. CHARTER and PLAN (already written)

`CHARTER.md` and `PLAN.md` in this directory are the actual charter and the
actual 15-unit plan for this report. They were authored by hand (the plan is
the part of BSE worth spending real effort on — see DESIGN.md P1), then
validated:

```
$ python3 scripts/bse.py plan --run-dir examples/20k-word-report --validate
PLAN VALID: 17 units
```

That took two tries. The first attempt failed:

```
$ python3 scripts/bse.py plan --run-dir examples/20k-word-report --validate
PLAN INVALID: 17 units
  error: L374: B014 depends_on mismatch: table [] vs spec ['B001']
```

B014's spec block declared `depends_on: [B001]` but the table line had no
`[dep:B001]`. This is exactly the class of error the validator exists to
catch before any executor time is spent: a real dependency that the table
(which drives scheduling) didn't know about. Fix was one line in the table:

```diff
- - [ ] B014 [research] Appendix A: Data tables and methodology notes — budget: 8items
+ - [ ] B014 [research] [dep:B001] Appendix A: Data tables and methodology notes — budget: 8items
```

Re-running `--validate` then passed cleanly, as shown above, and units
B001-B003 were executed against that 17-unit plan (sections 3-6 below).

## 2. A later validator update: predicate adequacy, and no more front/back-matter units

The plan above passed for the run recorded in sections 3-6. Some time after
B001-B003 were done, `plan --validate` gained three predicate-adequacy
checks (a word-budgeted unit needs `word_count`; a unit reading named
sources needs `citation_tags` or a `source:` predicate; a non-final
`compose` unit needs `no_conclusion`), each waivable, plus a structural
change: front matter and back matter are no longer plan units at all — they
are `front-matter.md` / `back-matter.md`, written by hand in the seam pass
and included by `stitch` automatically. Re-running `--validate` on the old
17-unit plan under the updated tool failed on all four counts at once:

```
$ python3 scripts/bse.py plan --run-dir examples/20k-word-report --validate
PLAN INVALID: 17 units
  error: L25: B001 [citation_tags] reads 5 input(s) beyond the charter (sources/ferc-order-2222-summary.md, ...) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L169: B006 [citation_tags] reads 1 input(s) beyond the charter (sources/ferc-order-2222-summary.md) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L374: B014 [citation_tags] reads 3 input(s) beyond the charter (sources/state-survey-2026.md, ...) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L431: B016 [no_conclusion] non-final compose unit does not declare no_conclusion: add '- mechanical: no_conclusion' (or add 'waive: no_conclusion — <reason>' to the spec block)
  warning: budget denomination 'items' (sum 18items across B001, B014) has no charter total; drift not checked
```

Four fixes, one per error, plus the structural change the last error was
really pointing at:

- **B001** (the source catalog) reads all five source files but declared no
  tracing predicate. It already tags every numeric claim correctly (its
  cross-source-cautions section states dollar figures with the `[S#]` they
  come from), so the honest fix was to declare that mechanically:
  `- mechanical: citation_tags`, confirmed by re-running `check` (section 4).
- **B006** (Section 3.3, Technical Standards) reads the Order 2222-B summary
  memo and was missing `citation_tags` that its sibling sections (B004,
  B005) already declare — added `- mechanical: citation_tags`.
- **B014** (Appendix A) reproduces whole data tables from three sources
  rather than making individual tagged claims; a per-sentence mechanical tag
  check is the wrong shape for a table. A judgement predicate fits instead:
  `- source: every reproduced data table is captioned with the [S#] source
  file it was reproduced from`.
- **B016/B017 no longer exist.** The `no_conclusion` error on B016 was a
  symptom of a bigger problem: the plan still modeled the executive summary
  and the introduction/conclusion as budgeted, ordered plan units at the
  *end* of the table, which is exactly backwards — `stitch` assembles in
  plan order, so the introduction would have landed after Section 6 and the
  Appendix in `draft.md`. Front matter and back matter are not plan units at
  all now; they are `front-matter.md` / `back-matter.md`, written by hand in
  the seam pass once every body unit is done (SKILL.md move 7, step 5), and
  `stitch` prepends/appends them automatically once they contain prose.
  B016 and B017 were removed from both the unit table and the Specs section;
  nothing else depended on them, so no other unit needed a change. The
  charter's `Total size` dropped from `20000w` to `15800w` — the sum of the
  remaining body units (B002-B015) — with a note that the finished
  deliverable (front matter and back matter included) runs longer than that
  and isn't itself budget-checked; acceptance criterion 1 was reworded to
  match.

With those four fixes, `--validate` passes again, now against 15 units:

```
$ python3 scripts/bse.py plan --run-dir examples/20k-word-report --validate
PLAN VALID: 15 units
  warning: budget denomination 'items' (sum 18items across B001, B014) has no charter total; drift not checked
```

(The `items` warning is informational and pre-existing: B001 and B014 are
budgeted in `items`, a denomination the charter's `Total size` line never
declared, so drift on it is simply not checked. This is a warning, not an
error, and does not block validation.)

## 3. Status and next, before any work

```
$ python3 scripts/bse.py status --run-dir examples/20k-word-report
# BSE ledger — run: report-2026 — charter: /home/claude/bse/examples/20k-word-report/CHARTER.md — created: 2026-09-12T21:29:42Z
id     type       status   att   budget     words  review   title
B001   research   pending    0   10items        -  -        Build the annotated source catalog
B002   compose    pending    0   1100w          -  pending  Section 1: Problem statement
...
0 of 17 units done

$ python3 scripts/bse.py next --run-dir examples/20k-word-report
B001
```

(`status` now has a `review` column — `-` for units with no judgement
predicates, else `pending` / `stale` / `pass` / `fail` depending on whether a
stored review matches the artifact's current sha256. B001 shows `-`; B002
and B003 showed `pending` at this point, before section 5's review pass. The
run above still shows 17 units, before the plan restructuring in section 2;
after it, B004-B015 replace what B004-B017 used to be, unchanged in content.)

## 4. B001 — the source catalog, including a real failed check

`bse.py brief B001` assembled `briefs/B001.md` (charter + this unit's spec
block + carry.md + the five named input files — nothing else, per the
executor's brief contract):

```
$ python3 scripts/bse.py brief --run-dir examples/20k-word-report B001
brief written: examples/20k-word-report/briefs/B001.md (1571 words)
```

The executor (in this run, me, standing in for a dispatched subagent) read
only that brief and wrote `batches/B001.md`: five annotated source entries.
Checking it produced a genuine failure:

```
$ python3 scripts/bse.py check --run-dir examples/20k-word-report B001
B001 check FAIL (1/2)
  FAIL item_count within 20% of budget: item_count 5 outside 20% of 10 [8-12]
  ok   no_placeholders: no placeholders
  report: examples/20k-word-report/reports/B001.md
```

The unit's budget was `10items` (8-12 with the default 20% tolerance), and
the first draft had exactly one item per source — 5 items. This is a real
plan-sizing miss (the catalog should have been scoped to 5 items, or scoped
to include more than one item per source), caught by the mechanical check
before it ever reached a human. The failing report is kept for reference at
`reports/B001.attempt1.md`.

Per the loop, the failure was recorded as a fix round (not silently
re-tried):

```
$ python3 scripts/bse.py record --run-dir examples/20k-word-report B001 --status fix \
    --note "catalog listed 5 sources as 5 items; budget calls for 8-12 — expand with per-source cross-reference items, not padding"
B001 fix round 1/3 recorded
```

The fix was not to pad the existing five entries with filler — it was to add
a genuinely useful second section, "Cross-source cautions for downstream
units" (five more items: which sources must never be conflated, which
figures are illustrative vs. observed, which case studies are composites).
That is real content later units rely on, not budget-gaming. Re-checking:

```
$ python3 scripts/bse.py check --run-dir examples/20k-word-report B001
B001 check PASS (2/2)
  ok   item_count within 20% of budget: item_count 10 within 20% of 10 [8-12]
  ok   no_placeholders: no placeholders
  report: examples/20k-word-report/reports/B001.md
```

And recorded:

```
$ python3 scripts/bse.py record --run-dir examples/20k-word-report B001 --status done
B001 done (407w, verify=pass(2/2)) — 1 of 17 units
```

Note that `check` itself now counts fix rounds automatically, not just
`record --status fix`: if an artifact changes after a failing check and is
re-checked, the tool notices the sha256 changed since the last failing
check and counts that as a fix round on its own (capped at 3, same as an
explicit `record --status fix`), and says so in the report and the ledger
line — `bse.py check --help` documents this as "re-running on a changed
artifact after a failing check counts a fix round." In this run the fix was
recorded explicitly with `record --status fix` before the re-check, so that
explicit round is what's counted, not a duplicate automatic one.

After section 2's validator update added `citation_tags` to B001's declared
predicates, `check` was re-run against the already-recorded artifact to
confirm it actually satisfies the new predicate (it does — B001's
cross-source-cautions section already tags every dollar figure to its
source):

```
$ python3 scripts/bse.py check --run-dir examples/20k-word-report B001
B001 check PASS (3/3 mechanical)
  ok   item_count within 20% of budget: item_count 10 within 20% of 10 [8-12]
  ok   no_placeholders: no placeholders
  ok   citation_tags: all numeric claims tagged
  report: examples/20k-word-report/reports/B001.md
```

## 5. B002 and B003 — two straightforward passes, then a real review

Both followed brief -> execute -> check -> record with no recorded fix round.
Final checks:

```
$ python3 scripts/bse.py check --run-dir examples/20k-word-report B002
B002 check PASS (5/5)
  ok   word_count within 15% of budget: word_count 1055 within 15% of 1100 [935-1265]
  ok   contains_headings ["1. Problem Statement"]: all headings present
  ok   no_placeholders: no placeholders
  ok   citation_tags: all numeric claims tagged
  ok   no_conclusion: no concluding language
  report: examples/20k-word-report/reports/B002.md

$ python3 scripts/bse.py record --run-dir examples/20k-word-report B002 --status done
B002 done (1,055w, verify=pass(5/5)) — 2 of 17 units

$ python3 scripts/bse.py check --run-dir examples/20k-word-report B003
B003 check PASS (5/5)
  ok   word_count within 15% of budget: word_count 1046 within 15% of 1200 [1020-1380]
  ok   contains_headings ["2. Policy Landscape"]: all headings present
  ok   no_placeholders: no placeholders
  ok   citation_tags: all numeric claims tagged
  ok   no_conclusion: no concluding language
  report: examples/20k-word-report/reports/B003.md

$ python3 scripts/bse.py record --run-dir examples/20k-word-report B003 --status done
B003 done (1,046w, verify=pass(5/5)) — 3 of 17 units
```

Both units declare judgement predicates (`source: ...` and
`charter: acceptance criteria 1`), which `check` correctly does not attempt
to grade — its report lists them under "Judgement predicates (reviewer pass
required; not counted above)" and `record --status done` succeeds because
mechanical checks pass, but the unit is not actually clean until a reviewer
pass runs. That reviewer pass is `bse.py review`, and it needs a real
written report, not a rubber stamp. For this run the reviewer read each
artifact against only its own predicates and the exact source files named
in the charter (never the brief, never the other unit), quoting the
matching source text for every numeric claim; the full reports are at
`reports/B002-review.md` and `reports/B003-review.md`. Recording the
verdicts:

```
$ python3 scripts/bse.py review --run-dir examples/20k-word-report B002 --verdict pass --report examples/20k-word-report/reports/B002-review.md
B002 review PASS (2 judgement predicates, sha=054094e)

$ python3 scripts/bse.py review --run-dir examples/20k-word-report B003 --verdict pass --report examples/20k-word-report/reports/B003-review.md
B003 review PASS (2 judgement predicates, sha=bb2f78f)
```

`bse.py audit` had flagged both units as `DONE_WITHOUT_REVIEW` before this
step (section 7) — recorded done, with judgement predicates declared, but
no stored review matching the recorded artifact's sha256. That finding is
exactly what these two `review` calls resolve: the review is keyed to the
artifact's sha256, so it would go stale again (and `audit` would flag it
again) if either section were edited after the fact without a fresh review.

## 6. The baton after unit 3

After B003, `carry.md` was replaced (not appended to) with an updated
baton — established facts so far, the terms now defined, open threads the
next units must pick up (in particular: 3.1 must define "queue stage"
precisely; 3.2 must keep [S5]'s figures labeled illustrative; 4.1/4.2 must
not name real states), what not to repeat, and a one-line tone note:

```
$ python3 scripts/bse.py carry --run-dir examples/20k-word-report --set /path/to/carry-after-b003.md
carry.md replaced (304/400 words)
```

The 400-word cap is hard-enforced by the tool (`set_carry` raises if the
word count exceeds it); 304 was comfortably under.

## 7. Status and audit after three units

```
$ python3 scripts/bse.py status --run-dir examples/20k-word-report
# BSE ledger — run: report-2026 — charter: /home/claude/bse/examples/20k-word-report/CHARTER.md — created: 2026-09-12T21:29:42Z
id     type       status   att   budget     words  review   title
B001   research   done       2   10items      407  -        Build the annotated source catalog
B002   compose    done       1   1100w       1055  pass     Section 1: Problem statement
B003   compose    done       1   1200w       1046  pass     Section 2: Policy landscape overview
B004   compose    pending    0   1200w          -  pending  Section 3.1: Interconnection queue mechanics
B005   compose    pending    0   1200w          -  pending  Section 3.2: Cost allocation methods
B006   compose    pending    0   1100w          -  pending  Section 3.3: Technical standards (IEEE 1547)
B007   compose    pending    0   1200w          -  pending  Section 4.1: Case study — shared-queue priority
B008   compose    pending    0   1200w          -  pending  Section 4.2: Case study — hosting-capacity maps
B009   compose    pending    0   1300w          -  pending  Section 4.3: Comparative analysis
B010   compose    pending    0   1300w          -  pending  Section 5.1: Model legislation options
B011   compose    pending    0   1200w          -  pending  Section 5.2: Rate design and cost recovery
B012   compose    pending    0   1000w          -  pending  Section 5.3: Implementation timeline
B013   compose    pending    0   1300w          -  pending  Section 6: Stakeholder risk analysis
B014   research   pending    0   8items         -  pending  Appendix A: Data tables and methodology notes
B015   revise     pending    0   1500w          -  -        Consistency and terminology audit
3 of 15 units done

$ python3 scripts/bse.py next --run-dir examples/20k-word-report
B004

$ python3 scripts/bse.py audit --run-dir examples/20k-word-report
audit: clean (1 informational)
  PLAN_BUDGET_UNCHECKED    -      info: plan budgets sum 18items (B001, B014) but the charter declares no 'items' total; drift not checked
```

This is the audit *after* the two `review` calls in section 5. Before them,
the same command reported:

```
$ python3 scripts/bse.py audit --run-dir examples/20k-word-report
audit: 2 finding(s) (1 informational)
  DONE_WITHOUT_REVIEW      B002   done with 2 judgement predicate(s) but no review stored for the recorded artifact (run `bse.py review B002 ...`)
  DONE_WITHOUT_REVIEW      B003   done with 2 judgement predicate(s) but no review stored for the recorded artifact (run `bse.py review B003 ...`)
  PLAN_BUDGET_UNCHECKED    -      info: plan budgets sum 18items (B001, B014) but the charter declares no 'items' total; drift not checked
```

`LEDGER.md` at this point reads:

```
# BSE ledger — run: report-2026 — charter: /home/claude/bse/examples/20k-word-report/CHARTER.md — created: 2026-09-12T21:29:42Z
B001 fix 1/3  2026-09-12T21:32:22Z  verify=fail(1/2): item_count 5 outside 20% of 10 [8-12]  note=catalog listed 5 sources as 5 items; budget calls for 8-12 — expand with per-source cross-reference items, not padding
B001 done     2026-09-12T21:32:41Z  artifact=batches/B001.md  words=407  verify=pass(2/2)  sha=d7bafa9
B002 done     2026-09-12T21:34:09Z  artifact=batches/B002.md  words=1055  verify=pass(5/5)  sha=054094e
B003 done     2026-09-12T21:35:04Z  artifact=batches/B003.md  words=1046  verify=pass(5/5)  sha=bb2f78f
B002 review pass  2026-09-12T22:23:56Z  predicates=2  report=reports/B002-review.md  sha=054094e
B003 review pass  2026-09-12T22:23:56Z  predicates=2  report=reports/B003-review.md  sha=bb2f78f
B002 review pass  2026-09-12T22:25:58Z  predicates=2  report=reports/B002-review.md  sha=054094e
B003 review pass  2026-09-12T22:25:58Z  predicates=2  report=reports/B003-review.md  sha=bb2f78f
```

(the second B002/B003 review pair is a duplicate entry from re-running the
same `review` command a second time — once with `--run-dir .` while writing
the fix, once with `--run-dir examples/20k-word-report` to match this
walkthrough's path convention — both against the same unchanged artifact
and the same verdict; `audit` treats duplicate passing reviews of the
current sha256 as no finding at all.)

If this run were resumed after a context reset, or picked up on a different
day (`relay` mode), the resume rule applies exactly as SKILL.md states it:
read `LEDGER.md`, its first line names this run's charter, B001-B003 have
`done` lines and are not re-executed, and `bse.py next` correctly returns
`B004` as the resume point.

## 8. What was left unexecuted, and why that's still a faithful example

B004-B015 are fully specified (real spec blocks, real budgets, real verify
predicates) and pass `plan --validate`, but were not executed — writing and
verifying all fifteen ~1,200-word sections of a real policy report is a
full day of work, not something that belongs pasted into a documentation
example. What's shown here is the complete mechanical loop — including a
genuine failure and fix, and a genuine judgement review — for a
representative slice of the run. Nothing about executing B004-B015 differs
from what B001-B003 already show.

## 9. Stitch and the seam pass, not run here

`stitch` was not run in this example (only 3 of 15 units are done, and
`stitch` refuses to assemble while any unit — parallel or not — is
incomplete unless `--partial` is passed, which inserts `<!-- MISSING B00X
-->` markers instead of failing). Worth stating plainly since section 2
changed what stitching this plan will look like once every unit is done:

- `stitch` writes `draft.md` only, in plan order (B001 through B015). It
  refuses to write to a path named `final.md` — that file is written by
  hand in the seam pass, never generated by stitching.
- Once `front-matter.md` and `back-matter.md` contain real prose (written in
  the seam pass, after every body unit is done and `draft.md` has been read
  once against the charter's through-line), `stitch` includes them
  automatically — prepended and appended respectively — with no flag
  needed. `--no-front-matter` suppresses that; the older
  `--include-front-matter` flag is now a deprecated no-op, since inclusion
  is the default.
- Neither file has been written yet in this run (there is no through-line
  to summarize until B004-B015 exist), so a `stitch --partial` run today
  would report both as "not yet written" and would still refuse to produce
  `final.md` itself even if it were the complete run.

## Design feedback surfaced by building this example

- **`citation_tags` operates on paragraphs and list items, not physical
  lines — a wrapped sentence is fine.** An earlier draft of this note
  claimed the check was line-based (a number and its `[S#]` tag on
  different hard-wrapped lines would fail), based on testing against an
  older tool version. That is no longer true: the current verifier joins a
  paragraph's or list item's continuation lines into one chunk before
  splitting it into sentences, so a wrapped sentence whose tag lands one
  physical line down from its number still passes (verified directly
  against `v_citation_tags` while writing this walkthrough). Left here as a
  correction, since a stale piece of design feedback in a shipped example is
  worse than no note at all.
- **Word-count intuition runs low.** Dense, citation-heavy analytical prose
  reads as longer than it counts; a paragraph that feels like 150 words is
  often 100. Budgets in this range (1,100-1,300w, ±15%) took two or three
  iterations each to hit, which is exactly the kind of control-signal
  friction DESIGN.md P2 predicts is worth paying for.
- **`item_count` budget mismatch is caught early and specifically.** The
  B001 failure is a good example of the tool doing its job: it didn't say
  "content is bad," it said exactly what was wrong (5 vs. 8-12) with enough
  precision to fix it in one round rather than guessing.
- **Predicate-adequacy checking earns its keep on exactly this kind of
  plan.** All three flagged units (B001, B006, B014) really did read named
  source files with no tracing mechanism declared — not a false positive in
  the batch. B014 in particular needed a genuinely different fix
  (`source:`, not `citation_tags`) because reproducing whole data tables is
  a different shape of claim than composing cited prose; the validator
  correctly left the choice of predicate to the plan author rather than
  forcing one mechanism on every unit that touches a source file.
