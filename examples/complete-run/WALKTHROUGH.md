# Walkthrough — Off-Peak Fare Capping at Riverton Transit Authority

This is a complete, real run of `scripts/bse.py`, start to finish: every
command below was actually executed against this directory, every block of
output is what the tool actually printed, and every batch, report, and
review is the real artifact the tool wrote or that a human (standing in for
a dispatched executor/reviewer) wrote by hand. Unlike this repo's other
examples, this run does not stop partway — all six units are executed,
checked, and reviewed; the draft is stitched; the seam pass is done by
hand; and `final.md` is the resulting deliverable. `bse.py audit` returns
clean at the end.

All commands were run from the repo root with `--run-dir examples/complete-run`.

## What to look at first

If you read nothing else in this directory, read these four things, in
this order:

1. **`CHARTER.md`** — the through-line, terminology lock, five numbered
   sources, and testable acceptance criteria this whole run is answerable
   to.
2. **`batches/B005.md`** next to **`reports/B005.md`** and the `B005 fix
   1/3` line in `LEDGER.md` — a real mechanical-check failure (untagged
   figures and a budget shortfall) and the fix that cleared it, with the
   reasoning recorded via `bse.py record --status fix` *before* the fix was
   made (see §5 below).
3. **`SEAM-PASS-NOTES.md`** — what the human editing pass actually changed
   between `draft.md` and `final.md`: one real cross-unit duplication the
   mechanical dedup check missed, one real terminology-lock violation it
   caught, and why the source catalog moved to an appendix.
4. **`final.md`** — the finished 4,949-word briefing note, meant to be read
   start to finish as one document, not as six stapled sections.

`reports/review-B00*.md` are the reviewer passes for every compose unit's
judgement predicates (`source:`/`charter:`) — each renders a PASS/FAIL
verdict per predicate with a quoted excerpt as evidence, per the
`bse.py review` contract.

## 1. Scaffold the run

```
$ python3 scripts/bse.py init --run-id riverton-fare-cap \
    --title "Off-Peak Fare Capping at Riverton Transit Authority: A Briefing Note" \
    --total "4200w, 5items" --run-dir examples/complete-run
initialised run riverton-fare-cap at examples/complete-run
  edit CHARTER.md and PLAN.md (replace the SAMPLE unit), then: bse.py plan --validate
```

`init` scaffolded `CHARTER.md`, `PLAN.md`, `carry.md`, `front-matter.md`,
`back-matter.md`, `LEDGER.md`, and `ledger.json` from templates. The five
source documents in `sources/` were written first, by hand, before the
charter: a peer-agency outcomes memo [S1], RTA's own FY2026 ridership and
revenue data [S2], a fare-system technical memo [S3], the Equity & Access
office's analysis [S4], and stakeholder interview notes [S5] — all
fictional but internally consistent, cross-checked against each other for
every figure this run cites.

## 2. CHARTER and PLAN

`CHARTER.md` states the through-line directly: *RTA should adopt an
off-peak fare cap through a phased, corridor-first pilot, because
peer-agency evidence shows off-peak capping grows ridership without a
full-fare-equivalent revenue loss, and RTA's own ridership and equity data
show the riders most underserved by its current all-day cap are exactly the
riders concentrated in the off-peak window.* That sentence goes into every
brief verbatim (see any `briefs/B00*.md`) and is the standard the seam pass
checks the finished draft against in step 0.

`PLAN.md` lays out six units: a research unit that builds the source
catalog, and five compose units, one per body section, budgeted 850w /
850w / 800w / 800w / 900w (summing to 4,200w against the charter's 4,200w
total — 0% drift by construction).

```
$ python3 scripts/bse.py plan --run-dir examples/complete-run --validate
PLAN VALID: 6 units
```

This passed on the first try because the predicate-adequacy rules were
designed in from the start: every word-budgeted unit declares `word_count`;
every unit reading a raw source file declares `citation_tags` (research
unit B001) or a `source:` judgement predicate (all five compose units);
every non-final compose unit declares `no_conclusion` (B006, the last unit
in the table, is exempt by the tool's own rule, but declares it anyway —
the actual recommendation still lives only in `back-matter.md`, written
later).

```
$ python3 scripts/bse.py status --run-dir examples/complete-run
# BSE ledger — run: riverton-fare-cap — charter: .../CHARTER.md — created: 2026-09-12T22:24:01Z
id     type       status   att   budget     words  review   title
B001   research   pending    0   5items         -  -        Build the source catalog
B002   compose    pending    0   850w           -  pending  Section 1: How Off-Peak Fare Capping Works and What Peer Agencies Found
B003   compose    pending    0   850w           -  pending  Section 2: RTA Ridership and Revenue by Time of Day
B004   compose    pending    0   800w           -  pending  Section 3: Equity and Access Implications
B005   compose    pending    0   800w           -  pending  Section 4: Operational and Technical Feasibility
B006   compose    pending    0   900w           -  pending  Section 5: Implementation Options and Tradeoffs
0 of 6 units done

$ python3 scripts/bse.py next --run-dir examples/complete-run
B001
```

## 3. B001 — the source catalog

```
$ python3 scripts/bse.py brief --run-dir examples/complete-run B001
brief written: examples/complete-run/briefs/B001.md (3539 words)
```

The brief (charter + this unit's spec + carry.md + the five full source
files) was the only input used to write `batches/B001.md`: five annotated
entries, one per source, each with its `[S#]` tag and which downstream
section relies on it.

```
$ python3 scripts/bse.py check --run-dir examples/complete-run B001
B001 check PASS (3/3 mechanical)
  ok   item_count within 15% of budget: item_count 5 within 15% of 5 [4-6]
  ok   no_placeholders: no placeholders
  ok   citation_tags: all numeric claims tagged
  report: examples/complete-run/reports/B001.md
```

B001 declares no judgement predicates, so `bse.py review` does not apply —
`check` is its only gate. A carry (`carry.md`) was written summarizing the
peer-agency and RTA figures for B002 to use, then:

```
$ python3 scripts/bse.py record --run-dir examples/complete-run B001 \
    --status done --carry <carry file>
B001 done (308w, verify=pass(3/3)) — 1 of 6 units
```

## 4. B002 — first compose unit, and the first reviewer pass

`batches/B002.md` (Section 1) was written from the brief, checked, and
passed mechanically on the first try:

```
$ python3 scripts/bse.py check --run-dir examples/complete-run B002
B002 check PASS (5/5 mechanical; 2 judgement predicates pending review)
  ok   word_count within 15% of budget: word_count 755 within 15% of 850 [722-978]
  ok   contains_headings [...]: all headings present
  ok   no_placeholders: no placeholders
  ok   citation_tags: all numeric claims tagged
  ok   no_conclusion: no concluding language
```

B002 declares two judgement predicates (`source:` and `charter:`), so it
cannot be recorded done without a review. The reviewer pass (`reports/
review-B002.md`) read only the brief, the artifact, and the predicates —
per the reviewer-prompt contract in `references/prompts.md` — and checked
every Meridian/Cedar Falls/Ashford figure against `sources/
peer-program-outcomes.md` directly:

```
$ python3 scripts/bse.py review --run-dir examples/complete-run B002 \
    --verdict pass --report reports/review-B002.md \
    --note "reviewer: seam-pass QA pass, source-fidelity check against S1"
B002 review PASS (2 judgement predicates, sha=1252a52)

$ python3 scripts/bse.py record --run-dir examples/complete-run B002 \
    --status done --carry <carry file>
B002 done (755w, verify=pass(5/5), review=pass) — 2 of 6 units
```

## 5. B003 — a genuine mechanical failure and fix round

`batches/B003.md` (Section 2, RTA's own ridership data) was drafted, then
checked:

```
$ python3 scripts/bse.py check --run-dir examples/complete-run B003
B003 check FAIL (3/5 mechanical; 2 judgement predicates pending review)
  FAIL word_count within 15% of budget: word_count 613 outside 15% of 850 [722-978]
  ok   contains_headings [...]: all headings present
  ok   no_placeholders: no placeholders
  FAIL citation_tags: untagged numeric/year sentences: L4-6
  ok   no_conclusion: no concluding language
```

Both failures were real, not staged. The word count was genuinely 237 words
under budget. The citation failure was subtler: the sentence *"Since 2019,
RTA has run a single fare product..."* was followed later in the same
sentence by *"6:00 a.m. to 11:59 p.m."* — the tool's sentence splitter
breaks on any period-then-space, including inside "a.m."/"p.m."
abbreviations, so "Since 2019, RTA has run a single fare product... 6:00
a.m." became its own fragment, orphaning the year "2019" from the `[S2]`
tag that had been placed at the end of the full sentence. The fix was to
place the tag directly after "2019" instead of relying on end-of-sentence
placement, rewrite the time range as "6:00 a.m.-11:59 p.m." (hyphenated, no
space after the abbreviation's period, so it cannot be split there either),
and add two genuine paragraphs of content to close the word-count gap.
Re-running check on the changed artifact counted this as fix round 1/3
automatically (the tool's rule: re-checking a changed artifact after a
failing check counts as a fix round whether or not `record --status fix`
was called separately):

```
$ python3 scripts/bse.py check --run-dir examples/complete-run B003
B003 check PASS (5/5 mechanical; 2 judgement predicates pending review)
  fix round 1/3 counted (artifact changed after a failing check)
  ok   word_count within 15% of budget: word_count 757 within 15% of 850 [722-978]
  ok   contains_headings [...]: all headings present
  ok   no_placeholders: no placeholders
  ok   citation_tags: all numeric claims tagged
  ok   no_conclusion: no concluding language
```

Reviewed and recorded the same way as B002 (`reports/review-B003.md`,
verdict pass, then `record --status done`).

## 6. B004 — equity section, another real fix round

`batches/B004.md` (Section 3) undershot its budget on the first draft (570
words against 800) and was expanded with two genuine additional points (not
padding) — again counted automatically as a fix round on re-check. Its
review (`reports/review-B004.md`) passed both judgement predicates but also
flagged, as a Minor finding outside the named predicates, that this unit's
explanation of the all-day cap's commuter mechanics nearly duplicated a
sentence already in B003 — a finding carried forward into the seam pass
(see `SEAM-PASS-NOTES.md` §1) rather than triggering a fix round, since it
failed no check and no predicate.

## 7. B005 — the deliberate failure and an explicit fix round

`batches/B005.md` (Section 4, fare-system feasibility) was drafted with a
closing paragraph that restated the two vendor quotes — $410,000 and
$85,000 — and their $325,000 difference without re-tagging them, on the
(wrong) assumption that tagging them earlier in the section was enough.
This is a realistic drafting mistake, not a contrived one: a writer
summarizing figures already stated nearby often forgets that the mechanical
citation check evaluates tag presence per sentence, not per section.

```
$ python3 scripts/bse.py check --run-dir examples/complete-run B005
B005 check FAIL (3/5 mechanical; 2 judgement predicates pending review)
  FAIL word_count within 15% of budget: word_count 570 outside 15% of 800 [680-920]
  ok   contains_headings [...]: all headings present
  ok   no_placeholders: no placeholders
  FAIL citation_tags: untagged numeric/year sentences: L48-51, L51-56
  ok   no_conclusion: no concluding language
```

This time the fix round was recorded explicitly, with the diagnosis written
down *before* the fix was made:

```
$ python3 scripts/bse.py record --run-dir examples/complete-run B005 --status fix \
    --note "check FAIL: final paragraph restates \$410,000/\$85,000/\$325,000 \
without fresh [S3] tags (writer assumed earlier tags in the section covered \
the restatement); also 570w is 30w under budget (skipped two-window/testing \
detail). Fix: tag every figure in the closing paragraph individually and \
expand the two-option paragraphs with the phased-rollout detail already in \
the brief."
B005 fix round 1/3 recorded
```

The fix: split the closing paragraph so each of the real-time and interim
figures got its own sentence with its own `[S3]` tag, and added the
phased-rollout rationale already present in the source memo but omitted
from the first draft.

```
$ python3 scripts/bse.py check --run-dir examples/complete-run B005
B005 check PASS (5/5 mechanical; 2 judgement predicates pending review)
  ok   word_count within 15% of budget: word_count 713 within 15% of 800 [680-920]
  ok   contains_headings [...]: all headings present
  ok   no_placeholders: no placeholders
  ok   citation_tags: all numeric claims tagged
  ok   no_conclusion: no concluding language
```

Reviewed (`reports/review-B005.md`, noting the fix round for the record)
and recorded done.

## 8. B006 — final body section, a third fix round

`batches/B006.md` (Section 5, three implementation options) also undershot
its word budget on the first draft (619 vs 900) by compressing each option
to a single thin paragraph. Recorded as an explicit fix round with the same
reasoning-before-fixing pattern as B005, then expanded with one additional
concrete consequence per option and a short paragraph on sequencing —
real content the brief already called for, not filler:

```
$ python3 scripts/bse.py check --run-dir examples/complete-run B006
B006 check PASS (5/5 mechanical; 2 judgement predicates pending review)
  ok   word_count within 15% of budget: word_count 769 within 15% of 900 [765-1035]
  ok   contains_headings [...]: all headings present
  ok   no_placeholders: no placeholders
  ok   citation_tags: all numeric claims tagged
  ok   no_conclusion: no concluding language
```

Reviewed (`reports/review-B006.md`) and recorded done:

```
$ python3 scripts/bse.py status --run-dir examples/complete-run
...
6 of 6 units done
```

Three of the six units (B003, B004, B005, B006 — four, in fact) hit a real
fix round before passing; that is reported here honestly rather than
smoothed over, because a run where every unit passes on the first try
would be a less credible demonstration of what the mechanical gate is
actually for.

## 9. Stitch

```
$ python3 scripts/bse.py stitch --run-dir examples/complete-run
stitched 6 units -> examples/complete-run/draft.md (3985 words, target 4200w, drift 5%)
  duplicates=0 terminology_violations=1 missing=0 front_matter=no back_matter=no
  report: examples/complete-run/reports/stitch.md
reminder: every unit is done but the seam pass has not run — front-matter.md
and back-matter.md contain no prose yet; write them (and final.md) by hand
after reading draft.md
```

`reports/stitch.md` reported the one real terminology violation (`fare
capping` in B002's heading — the locked wrong form for "fare cap") and zero
sentence-level duplicates (see `SEAM-PASS-NOTES.md` §1 for why the real
duplicate between B003 and B004 did not trip this mechanical check, and how
the human seam pass caught it anyway).

## 10. Seam pass

Full account in `SEAM-PASS-NOTES.md`. In summary: read `draft.md` against
the through-line (intact — see that file's §0); trimmed the one duplicated
clause (§1); fixed the one terminology violation (§2); confirmed the five
section transitions needed no repair and moved the source catalog to an
appendix (§3); confirmed register and pronoun consistency (§4); then, and
only then, wrote `front-matter.md` (Executive Summary, 441 words) and
`back-matter.md` (Conclusion and Recommendation, 555 words), and assembled
`final.md`.

```
$ python3 scripts/bse.py stitch --run-dir examples/complete-run
stitched 6 units -> examples/complete-run/draft.md (3985 words, target 4200w, drift 5%)
  duplicates=0 terminology_violations=1 missing=0 front_matter=yes back_matter=yes
  report: examples/complete-run/reports/stitch.md
```

(Re-running stitch after front-matter.md/back-matter.md were written
regenerates `draft.md` to include them, exactly as `bse.py stitch` is
documented to do; `final.md` is never touched by `stitch`.)

## 11. Final validation

```
$ python3 scripts/bse.py plan --run-dir examples/complete-run --validate
PLAN VALID: 6 units

$ python3 scripts/bse.py audit --run-dir examples/complete-run
audit: clean
```

`final.md` is 4,949 words (`bse.py`'s own `count_words`, which excludes
HTML comments and fenced code) — far longer than `front-matter.md` +
`back-matter.md` alone (441 + 555 = 996 words), and it differs meaningfully
from `draft.md` (4,981 words): a unified diff runs 55 removed / 46 added
lines, and a word-level `difflib.SequenceMatcher` ratio of 0.93 reflects
real edits (the moved appendix, the trimmed duplicate, the terminology fix,
the removed machine markers) layered on five of six sections that needed no
prose changes at all — which is the point of verifying each unit before it
is stitched, rather than editing everything at the end.

`final.md` reads start to finish as one document: an Executive Summary
that previews the argument, five sections that each build on the last
without repeating themselves (after the one fix), and a Conclusion that
states the recommendation once, supported entirely by evidence the reader
has already seen.
