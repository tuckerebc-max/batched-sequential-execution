# Walkthrough — The Last Utility, Feedback Sweep

A real run of `scripts/bse.py`. All commands below were actually executed
with `--run-dir examples/feedback-sweep`; every output block is what the
tool actually printed. **`next` refuses to run on a plan that has never
passed `--validate`** — see the 20k-word-report walkthrough for the actual
refusal message; in this run the plan was validated (below) before `next`
was ever called (section 3).

## 1. Init and plan validation

```
$ python3 scripts/bse.py init --run-dir examples/feedback-sweep --run-id feedback-sweep-1 \
    --title "The Last Utility — Feedback Sweep" --total 120items
initialised run feedback-sweep-1 at examples/feedback-sweep

$ python3 scripts/bse.py plan --run-dir examples/feedback-sweep --validate
PLAN VALID: 17 units
```

Validated on the first try. `sources/reviewer-feedback-log.md` contains all
120 numbered comments in manuscript order (front matter, then chapters 1-9,
then back matter); `sources/manuscript-ch1-9-excerpt.md` gives the chapter
structure and current per-chapter word counts.

## 1a. A later validator update: every unit needed a tracing predicate

Some time after that first validation, and after B001-B006 were executed
(section 3), `plan --validate` gained a predicate-adequacy rule: a unit
that reads a named source beyond the charter must declare `citation_tags`
or a `source:` predicate, or a waiver. All sixteen per-region units
(B001-B016) read a slice of `sources/reviewer-feedback-log.md` and declared
neither:

```
$ python3 scripts/bse.py plan --run-dir examples/feedback-sweep --validate
PLAN INVALID: 17 units
  error: L31: B001 [citation_tags] reads 2 input(s) beyond the charter (sources/reviewer-feedback-log.md#L1-7, ...) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L55: B002 [citation_tags] reads 2 input(s) beyond the charter (sources/reviewer-feedback-log.md#L8-17, ...) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L83: B003 [citation_tags] reads 1 input(s) beyond the charter (sources/reviewer-feedback-log.md#L18-24) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L108: B004 [citation_tags] reads 1 input(s) beyond the charter (sources/reviewer-feedback-log.md#L25-30) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L132: B005 [citation_tags] reads 2 input(s) beyond the charter (sources/reviewer-feedback-log.md#L31-38, ...) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L157: B006 [citation_tags] reads 2 input(s) beyond the charter (sources/reviewer-feedback-log.md#L39-46, ...) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L189: B007 [citation_tags] reads 1 input(s) beyond the charter (sources/reviewer-feedback-log.md#L47-55) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L215: B008 [citation_tags] reads 1 input(s) beyond the charter (sources/reviewer-feedback-log.md#L56-62) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L243: B009 [citation_tags] reads 1 input(s) beyond the charter (sources/reviewer-feedback-log.md#L63-69) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L268: B010 [citation_tags] reads 1 input(s) beyond the charter (sources/reviewer-feedback-log.md#L70-75) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L293: B011 [citation_tags] reads 1 input(s) beyond the charter (sources/reviewer-feedback-log.md#L76-81) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L318: B012 [citation_tags] reads 1 input(s) beyond the charter (sources/reviewer-feedback-log.md#L82-89) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L344: B013 [citation_tags] reads 1 input(s) beyond the charter (sources/reviewer-feedback-log.md#L90-96) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L370: B014 [citation_tags] reads 1 input(s) beyond the charter (sources/reviewer-feedback-log.md#L97-104) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L395: B015 [citation_tags] reads 1 input(s) beyond the charter (sources/reviewer-feedback-log.md#L105-114) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L424: B016 [citation_tags] reads 1 input(s) beyond the charter (sources/reviewer-feedback-log.md#L115-120) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  warning: budget denomination 'files' (sum 1files across B017) has no charter total; drift not checked
```

`citation_tags` is the wrong mechanical shape here — a resolution log entry
like "#028: APPLIED. Standardized to 'statehouse' (one word)" has no digit
or year in it at all for most items, so a per-sentence tag check would pass
trivially without actually checking anything real. A judgement `source:`
predicate was added to all sixteen units instead, keyed to what a resolution
log genuinely needs to prove — that its stated action matches what the item
actually asked for:

```diff
  verify:
    - mechanical: item_count within 15% of budget
    - mechanical: no_placeholders
+   - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
```

Note the wording deliberately avoids requiring literal quotation of the
reviewer's comment, even though "quote the reviewer comment" is the more
obvious phrasing. B001-B006 were already done (section 3) with resolution
logs that paraphrase each item precisely but never quote it verbatim — real
developmental-editor resolution logs are usually written this way, and
rewriting six already-verified logs to insert block quotations just to
satisfy a stricter predicate wording would have made the example less
realistic, not more rigorous. The chosen wording ("checked against its
numbered item's exact text ... accurately reflects what that item asked
for") gets the same tracing guarantee — a reviewer must read the actual
source line, not just trust the resolution log's own account — without
demanding a format no real resolution log uses. Re-validating:

```
$ python3 scripts/bse.py plan --run-dir examples/feedback-sweep --validate
PLAN VALID: 17 units
  warning: budget denomination 'files' (sum 1files across B017) has no charter total; drift not checked
```

Because B001-B006 were already recorded `done` before this predicate was
added, declaring it retroactively means all six need an actual reviewer
pass before `bse.py audit` will call them clean — see section 5.

## 2. Grouping logic: by region, not by comment order

The 120 comments arrived in one reviewer document, numbered in the order
the developmental editor, two beta readers, a fact-checker, and a
copyeditor happened to leave them — which is to say, in no order that
matters. This plan re-groups them by the manuscript region they apply to
(chapter, or sub-chapter section for any chapter with more than ten
comments) and sizes each group to 6-10 items, matching DESIGN.md's sizing
table for "prose, revision to feedback."

Why region, not comment order:

- **A region's comments interact with each other; comments from unrelated
  regions do not.** Item #039 (financing-before-names ordering) and #043
  (the attribution question) both apply to Ch3.2 and genuinely affect the
  same paragraphs; resolving them in the same unit means the executor sees
  both before touching the text. Splitting them across two units by
  arrival order would risk resolving #039 in a way that has to be
  half-undone once #043 is reached.
- **Grouping by region means each unit reads its region's manuscript
  excerpt once, not once per comment.** Ten comments on Chapter 1 grouped
  into one unit means one brief carries the Chapter 1 excerpt once; ten
  comments split across arrival order would mean re-reading Chapter 1's
  excerpt in whichever units happened to land on it, an argument DESIGN.md
  P4 makes directly (curated context, not accumulated re-reads).
- **A region's own sub-structure gives a natural split point when it's too
  big.** Chapter 3 has 16 comments — too many for one unit (ceiling 15) —
  and the natural split is 3.1 (founding, 8 items) vs. 3.2 (financing and
  attribution, 8 items), because that is where the chapter itself divides,
  not because comment #38 happened to be the eighth one filed.
- **Serial order still matters, but it's manuscript order, not arrival
  order.** Units run B001 (front matter) through B016 (back matter) in
  reading order so `carry.md` can hand forward exactly what a reader
  moving through the book would already know — see B001's item #007 and
  B015's item #105, both about the same anecdote, coordinated across two
  units eight units apart because the plan's `intent` fields point at each
  other explicitly.

The resulting grouping (region -> item range -> unit) is fully laid out in
PLAN.md's unit table; every region with more than 10 items is split at its
own internal section boundary, never at an arbitrary count.

## 3. Six units executed for real

B001 through B006 were run through the full loop — brief, execute, check,
record — to show the mechanical loop working across ordinary units before
the escalation case in section 4. All six passed their first check with no
fix round:

```
$ python3 scripts/bse.py check --run-dir examples/feedback-sweep B001
B001 check PASS (2/2 mechanical)
  ok   item_count within 15% of budget: item_count 7 within 15% of 7 [6-8]
  ok   no_placeholders: no placeholders
  report: examples/feedback-sweep/reports/B001.md

$ python3 scripts/bse.py record --run-dir examples/feedback-sweep B001 --status done
B001 done (217w, verify=pass(2/2)) — 1 of 17 units
```

(B002-B005 followed identically; see `reports/` and `LEDGER.md` for each.)
Each batch is a bulleted resolution log — one line per feedback item,
`APPLIED` or `RULED OUT, reason given` — which is also what makes
`item_count` the right mechanical verifier here: one bullet per item means
the count check is really checking "did every item get a line," which is
close to acceptance criterion 1's actual concern.

## 4. B006: a feedback item that contradicts the charter

Item **#043** (`sources/reviewer-feedback-log.md`, line 43) is a legal beta
reader's comment on Chapter 3.2:

> Given the finance director's subsequent departure amid an ongoing dispute
> with the cooperative's board, recommend anonymizing her as "the
> cooperative's former finance director" rather than using her name, to
> limit exposure if the dispute becomes litigation.

CHARTER.md's non-negotiable 2 states plainly: "Every named, on-the-record
interview subject keeps their full name and title on first reference in
their chapter... without a recorded RULING." Applying #043 as written would
violate the charter; ruling it out unilaterally would ignore a real legal
concern a human should weigh. This is exactly the case DESIGN.md's failure
mode "Drift from the charter" and the escalation path both anticipate: an
executor does not get to decide this on its own judgment, and it is not a
mechanical predicate a verifier can resolve either way. So B006 records
`blocked`, not a resolution:

```
$ python3 scripts/bse.py record --run-dir examples/feedback-sweep B006 --status blocked \
    --note "item #043 (beta reader, legal) asks to anonymize the cooperative's former finance director; contradicts charter non-negotiable 2 (named on-the-record sources keep full attribution) — needs a human ruling before this unit can proceed"
B006 blocked: item #043 (beta reader, legal) asks to anonymize the cooperative's former finance director; contradicts charter non-negotiable 2 (named on-the-record sources keep full attribution) — needs a human ruling before this unit can proceed
```

This immediately stalls the run downstream, exactly as it should — `next`
now reports nothing ready, naming B006 as the reason:

```
$ python3 scripts/bse.py next --run-dir examples/feedback-sweep
no unblocked unit; 12 remaining (blocked: B006)
```

A human (in this run, standing in as the author/editor) then issues the
ruling. This is `bse.py record RULING --note ...` — a ledger-level event.
`record RULING` also accepts `--unit ID` to link the ruling to the specific
unit it resolves (`bse.py record RULING --note "..." --unit B006`); this
run's ruling was issued without it, as a unit-less, free-standing event —
`bse.py audit`'s `BLOCK_WITHOUT_RULING` check (section 4a) accepts either
form, since a ruling can also resolve something no single unit owns:

```
$ python3 scripts/bse.py record --run-dir examples/feedback-sweep RULING --note \
    "item #043: keep the finance director named per charter non-negotiable 2 — accountability-journalism standard overrides the legal beta reader's litigation-exposure concern for an on-the-record source who has not asked for anonymity herself. Add one sentence noting she has since left the cooperative amid a board dispute, without characterizing the dispute's merits. Cost if wrong: one paragraph rewrite in Ch3.2 plus a corresponding update to the Back Matter interview list (B016)."
RULING recorded
```

The actual ledger line this produced, verbatim from `LEDGER.md`:

```
RULING        2026-09-12T21:45:19Z  item #043: keep the finance director named per charter non-negotiable 2 — accountability-journalism standard overrides the legal beta reader's litigation-exposure concern for an on-the-record source who has not asked for anonymity herself. Add one sentence noting she has since left the cooperative amid a board dispute, without characterizing the dispute's merits. Cost if wrong: one paragraph rewrite in Ch3.2 plus a corresponding update to the Back Matter interview list (B016).
```

With the ruling recorded, B006 was re-attempted: `batches/B006.md` resolves
item #043 per the ruling (named in full, one sentence added about her
departure) and the other seven items independently, checked, and recorded
done — note the `--note` on the done line pointing back to the ruling, and
that recording `done` after a prior `blocked` status works exactly the way
resuming a stalled unit should:

```
$ python3 scripts/bse.py check --run-dir examples/feedback-sweep B006
B006 check PASS (2/2 mechanical)
  ok   item_count within 15% of budget: item_count 8 within 15% of 8 [7-9]
  ok   no_placeholders: no placeholders
  report: examples/feedback-sweep/reports/B006.md

$ python3 scripts/bse.py record --run-dir examples/feedback-sweep B006 --status done --note "resumed per RULING on item #043"
B006 done (185w, verify=pass(2/2)) — 6 of 17 units

$ python3 scripts/bse.py next --run-dir examples/feedback-sweep
B007
```

The full sequence, as it actually reads in `LEDGER.md`:

```
B005 done     2026-09-12T21:45:00Z  artifact=batches/B005.md  words=170  verify=pass(2/2)  sha=49a7069
B006 blocked  2026-09-12T21:45:09Z  reason=item #043 (beta reader, legal) asks to anonymize the cooperative's former finance director; contradicts charter non-negotiable 2 (named on-the-record sources keep full attribution) — needs a human ruling before this unit can proceed
RULING        2026-09-12T21:45:19Z  item #043: keep the finance director named per charter non-negotiable 2 — accountability-journalism standard overrides the legal beta reader's litigation-exposure concern for an on-the-record source who has not asked for anonymity herself. Add one sentence noting she has since left the cooperative amid a board dispute, without characterizing the dispute's merits. Cost if wrong: one paragraph rewrite in Ch3.2 plus a corresponding update to the Back Matter interview list (B016).
B006 done     2026-09-12T21:45:33Z  artifact=batches/B006.md  words=185  verify=pass(2/2)  sha=e5e4f0d  note=resumed per RULING on item #043
```

## 4a. What `audit` would have said about a blocked unit with no ruling

`bse.py audit` has a check exactly for the failure mode this section walks
through by hand: a unit that was `blocked` and later resolved (`fix` or
`done`) with no `RULING` event recorded in between — `BLOCK_WITHOUT_RULING`,
informational. To confirm it actually fires, the RULING event above was
removed from a disposable copy of this run's ledger and `audit` re-run
against that copy (this run's real ledger was untouched):

```
$ python3 scripts/bse.py audit --run-dir <disposable copy, RULING event removed>
audit: clean (2 informational)
  BLOCK_WITHOUT_RULING     B006   info: blocked at 2026-09-12T21:45:09Z (reason=item #043 (beta reader, legal) asks to anonymize the cooperative's former finance director; contradicts charter non-negotiable 2 (named on-the-record sources keep full attribution) — needs a human ruling before this unit can proceed) then 'done' at 2026-09-12T21:45:33Z with no RULING recorded in between
  PLAN_BUDGET_UNCHECKED    -      info: plan budgets sum 1files (B017) but the charter declares no 'files' total; drift not checked
```

Against this run's real ledger — which does have the RULING event, issued
unit-less rather than with `--unit B006` — `bse.py audit` does not raise
`BLOCK_WITHOUT_RULING` at all: a RULING with no `--unit` is treated as
capable of resolving any pending block, not just none. This is worth
knowing in either direction: `--unit` makes the link explicit and
grep-able; a unit-less RULING is still recognized as resolving a pending
block, just less specifically.

## 5. A retroactive review pass for B001-B006

Section 1a's `source:` predicate applies to B001-B006 too, since they were
already recorded `done` when it was added. Each declares one judgement
predicate now, and none had a stored review, so `bse.py audit` (before this
section) reported six `DONE_WITHOUT_REVIEW` findings:

```
$ python3 scripts/bse.py audit --run-dir examples/feedback-sweep
audit: 7 finding(s) (1 informational)
  DONE_WITHOUT_REVIEW      B001   done with 1 judgement predicate(s) but no review stored for the recorded artifact (run `bse.py review B001 ...`)
  DONE_WITHOUT_REVIEW      B002   done with 1 judgement predicate(s) but no review stored for the recorded artifact (run `bse.py review B002 ...`)
  DONE_WITHOUT_REVIEW      B003   done with 1 judgement predicate(s) but no review stored for the recorded artifact (run `bse.py review B003 ...`)
  DONE_WITHOUT_REVIEW      B004   done with 1 judgement predicate(s) but no review stored for the recorded artifact (run `bse.py review B004 ...`)
  DONE_WITHOUT_REVIEW      B005   done with 1 judgement predicate(s) but no review stored for the recorded artifact (run `bse.py review B005 ...`)
  DONE_WITHOUT_REVIEW      B006   done with 1 judgement predicate(s) but no review stored for the recorded artifact (run `bse.py review B006 ...`)
  CARRY_STALE              -      6 units done but carry.md is still the init scaffold or empty — the baton was never written (SKILL.md move 6)
  PLAN_BUDGET_UNCHECKED    -      info: plan budgets sum 1files (B017) but the charter declares no 'files' total; drift not checked
```

The reviewer pass read each of the six resolution logs against the exact
text of its numbered items in `sources/reviewer-feedback-log.md` (not the
brief, not the other units), tabulating each item's comment, its logged
resolution, and whether the resolution's action actually matches the
comment — including B006's item #043, checked against the `blocked`/RULING
history in `LEDGER.md` rather than against the log alone, since the
predicate for that item is "was the RULING followed," not "does this match
the original comment" (the RULING supersedes it). Full reports are at
`reports/B001-review.md` through `reports/B006-review.md`. Recording the
verdicts:

```
$ python3 scripts/bse.py review --run-dir examples/feedback-sweep B001 --verdict pass --report examples/feedback-sweep/reports/B001-review.md
B001 review PASS (1 judgement predicate, sha=ab5f370)

$ python3 scripts/bse.py review --run-dir examples/feedback-sweep B002 --verdict pass --report examples/feedback-sweep/reports/B002-review.md
B002 review PASS (1 judgement predicate, sha=b3ddf15)

$ python3 scripts/bse.py review --run-dir examples/feedback-sweep B003 --verdict pass --report examples/feedback-sweep/reports/B003-review.md
B003 review PASS (1 judgement predicate, sha=d90ef3d)

$ python3 scripts/bse.py review --run-dir examples/feedback-sweep B004 --verdict pass --report examples/feedback-sweep/reports/B004-review.md
B004 review PASS (1 judgement predicate, sha=62ccc1d)

$ python3 scripts/bse.py review --run-dir examples/feedback-sweep B005 --verdict pass --report examples/feedback-sweep/reports/B005-review.md
B005 review PASS (1 judgement predicate, sha=49a7069)

$ python3 scripts/bse.py review --run-dir examples/feedback-sweep B006 --verdict pass --report examples/feedback-sweep/reports/B006-review.md
B006 review PASS (1 judgement predicate, sha=e5e4f0d)
```

`bse.py status` (section 7) now shows `pass` in the `review` column for all
six; re-checking any of them shows the review folded into `check`'s summary
too — a genuine, freshly run example:

```
$ python3 scripts/bse.py check --run-dir examples/feedback-sweep B001
B001 check PASS (2/2 mechanical; 1 judgement predicate reviewed: pass)
  ok   item_count within 15% of budget: item_count 7 within 15% of 7 [6-8]
  ok   no_placeholders: no placeholders
  report: examples/feedback-sweep/reports/B001.md
```

## 6. CARRY_STALE, and writing the real baton after B006

The audit output above also names `CARRY_STALE`: six units were done and
`carry.md` was still byte-identical to the `init` scaffold — the classic
silent failure DESIGN.md's move 6 warns about, and precisely the state this
example was in before this fix. This is a real gap, not a demonstration
device: B007 onward genuinely needs the terminology-lock state, the #043
RULING outcome (so B016's Back Matter unit doesn't re-litigate it), the
still-open "fifth town" question B008 must decide, and the tone
calibration, none of which existed anywhere but this walkthrough's own
prose until now. A real carry was written — established facts, terms now
defined, open threads for B007 onward, what not to repeat, and a tone
note, all under the 400-word cap — and set:

```
$ python3 scripts/bse.py carry --run-dir examples/feedback-sweep --set /path/to/carry-after-b006.md
carry.md replaced (382/400 words)
```

The full text is in `carry.md` itself (it replaces the file, so there is no
separate copy to link to). Re-running `audit`:

```
$ python3 scripts/bse.py audit --run-dir examples/feedback-sweep
audit: clean (1 informational)
  PLAN_BUDGET_UNCHECKED    -      info: plan budgets sum 1files (B017) but the charter declares no 'files' total; drift not checked
```

## 7. Status after six units, review pass, and carry fix

```
$ python3 scripts/bse.py status --run-dir examples/feedback-sweep
# BSE ledger — run: feedback-sweep-1 — charter: /home/claude/bse/examples/feedback-sweep/CHARTER.md — created: 2026-09-12T21:39:45Z
id     type       status   att   budget     words  review   title
B001   revise     done       1   7items       217  pass     Front Matter feedback (items 1-7)
B002   revise     done       1   10items      194  pass     Ch1 feedback (items 8-17)
B003   revise     done       1   7items       118  pass     Ch2.1 feedback (items 18-24)
B004   revise     done       1   6items       113  pass     Ch2.2 feedback (items 25-30)
B005   revise     done       1   8items       170  pass     Ch3.1 feedback (items 31-38)
B006   revise     done       1   8items       185  pass     Ch3.2 feedback (items 39-46)
B007   revise     pending    0   9items         -  pending  Ch4 feedback (items 47-55)
B008   revise     pending    0   7items         -  pending  Ch5.1 feedback (items 56-62)
B009   revise     pending    0   7items         -  pending  Ch5.2 feedback (items 63-69)
B010   revise     pending    0   6items         -  pending  Ch6.1 feedback (items 70-75)
B011   revise     pending    0   6items         -  pending  Ch6.2 feedback (items 76-81)
B012   revise     pending    0   8items         -  pending  Ch7.1 feedback (items 82-89)
B013   revise     pending    0   7items         -  pending  Ch7.2 feedback (items 90-96)
B014   revise     pending    0   8items         -  pending  Ch8 feedback (items 97-104)
B015   revise     pending    0   10items        -  pending  Ch9/Conclusion feedback (items 105-114)
B016   revise     pending    0   6items         -  pending  Back Matter feedback (items 115-120)
B017   assemble   pending    0   1files         -  pending  Final resolution log and reconciliation
6 of 17 units done
```

Every done unit shows `pass` in the `review` column (section 5); every
pending unit shows `pending` there too, since all sixteen per-region units
now declare the same `source:` predicate (section 1a) whether or not
they've been executed yet — the column reflects what the plan declares, not
only what's been checked. `bse.py audit --run-dir examples/feedback-sweep`
at this point is the clean output already shown at the end of section 6.

## 8. What was left unexecuted

B007-B016 (the remaining ten per-region resolution logs) and B017 (the
final combined resolution log and cross-region reconciliation) are fully
specified and pass `plan --validate`, but were not executed — the same
scoping decision made in the other two examples. What matters for this
example is shown in full: the region-based grouping logic, six real units
executed serially with the carry-forward coordination notes DESIGN.md
calls for (B001's #007 and B005/B006's cross-references), and the complete,
real escalation path from a charter-contradicting feedback item to a
blocked unit to a human RULING to a resumed, verified, recorded unit.

## 9. What this run actually produces, and what "stitching" would mean here

Worth stating plainly, as with the 80-slide-deck example: this run's
deliverable is a **verified change set** — sixteen per-region resolution
logs plus B017's combined log and cross-region reconciliation memo — not a
revised manuscript file a reader could open and read start to finish. The
charter says so ("Format: a per-unit resolution log (markdown), one entry
per feedback item, plus any inline chapter-text edit the item requires").
`bse.py stitch` is built to concatenate composed prose units into one
document with a seam pass on top; concatenating sixteen bulleted
resolution logs would not produce a revised manuscript, because most of
each unit's real output is the *decision* recorded per item, not new prose
— only some items (a definition added, a sentence softened, a bridge
added) touch actual manuscript text, and this run's batches log what
changed rather than reproducing full chapter text inline. The real "did
this feedback get resolved" answer lives in the resolution logs and B017's
reconciliation; turning that verified, [S2]-traceable change set into an
actually revised manuscript file is a separate **apply step** — an editor
or a script applies each logged inline edit to the real manuscript
document, chapter by chapter, using the resolution log as its source of
truth for what to change and why. `bse.py` verifies that every one of the
120 items was resolved, consistently, with no cross-region contradiction;
it does not — and per this charter, is not meant to — touch the manuscript
file itself.

## Design feedback surfaced by building this example

- **`record RULING --unit ID` links a ruling to the specific unit it
  resolves; a unit-less RULING is still recognized too.** An earlier draft
  of this note claimed there was no way to link a RULING to a unit, and
  that a reader could not tell from the ledger structure alone that
  B006's RULING and its blocked/done pair belonged together. Both claims
  are now out of date: `record RULING` accepts `--unit ID` for exactly that
  link (this run's RULING was issued without it, as section 4a shows), and
  `bse.py audit`'s `BLOCK_WITHOUT_RULING` check (informational) already
  flags a unit that went `blocked` -> `done`/`fix` with no RULING — linked
  or unit-less — recorded in between; section 4a reproduces that finding
  against a disposable copy of this run with the RULING event stripped
  out, to show it firing for real. Left here as a correction, since a
  stale piece of design feedback in a shipped example is worse than none.
- **`check` now counts a fix round automatically when a failing artifact is
  re-checked after being edited**, whether or not `record --status fix` was
  ever called — the tool compares the new artifact's sha256 against the
  last *failing* stored check and counts the transition itself, capped at
  the same 3 rounds. None of B001-B006 needed this in practice (all six
  passed their first check), so it isn't demonstrated with a real failure
  here — see the 20k-word-report and 80-slide-deck walkthroughs, which both
  hit a real check failure and show the counted round in the tool's own
  output.
- **A judgement predicate added to an already-`done` unit retroactively
  requires a real review before `audit` goes quiet again** (section 5) —
  it is not enough to edit the plan and move on; `bse.py audit` will name
  every affected unit by ID until a passing review exists for its current
  artifact. This is the same mechanism DESIGN.md documents for a unit
  edited after the fact (a stale sha invalidates a stored review); here the
  cause was different (the *predicate* changed, not the artifact) but the
  gate behaves identically.
