# Walkthrough — Meridian Grid Robotics Q3 2026 Investor Update

A real run of `scripts/bse.py` in wave mode. All commands below were
actually executed with `--run-dir examples/80-slide-deck`, and every output
block is what the tool actually printed.

**`next` refuses to run on a plan that has never passed `--validate`** — in
this run the plan was validated (section 1) before `next` was ever called
(section 2), so that refusal never fired here; see the 20k-word-report
example's walkthrough for the actual refusal message, reproduced there
against a disposable copy of that run.

## 1. Init and plan validation

```
$ python3 scripts/bse.py init --run-dir examples/80-slide-deck --run-id investor-deck-q3 \
    --title "Meridian Grid Robotics Q3 2026 Investor Update" --total 80slides
initialised run investor-deck-q3 at examples/80-slide-deck
  edit CHARTER.md and PLAN.md, then: bse.py plan --validate
```

CHARTER.md and PLAN.md were then written by hand (9 units: eight `[P]`
transform units of 10 slides each, plus one non-`[P]` reconciliation unit),
and validated on the first try:

```
$ python3 scripts/bse.py plan --run-dir examples/80-slide-deck --validate
PLAN VALID: 9 units
```

## 1a. A later validator update: four units needed a tracing predicate

Some time after that first validation and after B001 was executed (section
3), `plan --validate` gained a predicate-adequacy rule: a unit that reads a
named source beyond the charter must declare `citation_tags` or a `source:`
predicate, or a waiver. Four of this plan's nine units read
`sources/rebrand-styleguide.md` — the naming, color, and figure-sourcing
rules every wave edits against — without declaring any of the three:

```
$ python3 scripts/bse.py plan --run-dir examples/80-slide-deck --validate
PLAN INVALID: 9 units
  error: L45: B002 [citation_tags] reads 2 input(s) beyond the charter (sources/rebrand-styleguide.md, ...) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L94: B004 [citation_tags] reads 2 input(s) beyond the charter (sources/rebrand-styleguide.md, ...) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L117: B005 [citation_tags] reads 2 input(s) beyond the charter (sources/rebrand-styleguide.md, ...) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  error: L222: B009 [citation_tags] reads 1 input(s) beyond the charter (sources/rebrand-styleguide.md) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>' (or add 'waive: citation_tags — <reason>' to the spec block)
  warning: budget denomination 'items' (sum 10items across B009) has no charter total; drift not checked
```

Note that B001, B003, B006, B007, B008 are *not* flagged even though several
of them also read the style guide — they already declare `citation_tags`
(their edit logs cite `[S1]`/`[S2]` inline for every renamed hex or dollar
figure). B002/B004/B005 are pure rename-and-recolor waves with no numeric
claims at all, so a per-sentence tag check is the wrong shape; B009 is a
cross-wave checklist, not cited prose. A judgement `source:` predicate fits
all four better than mechanical `citation_tags` would — each was added,
naming exactly what must trace to `[S1]`:

```diff
  produces:
    - section: "Slides 11-20 edited"
  verify:
    - mechanical: forbidden_phrases
    - mechanical: no_placeholders
+   - source: every product-name rename and the flagged screenshot-asset slide match the naming rule in [S1]
```

(and similarly for B004, B005, and B009 — see PLAN.md for the exact
wording each was given). Re-validating:

```
$ python3 scripts/bse.py plan --run-dir examples/80-slide-deck --validate
PLAN VALID: 9 units
  warning: budget denomination 'items' (sum 10items across B009) has no charter total; drift not checked
```

Declaring a `source:` predicate means B002, B004, B005 and B009 cannot be
recorded `done` until a reviewer pass verdicts them — the same judgement
gate as the 20k-word-report example's B002/B003, just not yet exercised
here since none of the four is executed in this example (section 4). This
already shows up in `bse.py status`'s `review` column, which is new: `-`
for a unit with no judgement predicate, else `pending` / `stale` / `pass` /
`fail` once an artifact exists:

```
$ python3 scripts/bse.py status --run-dir examples/80-slide-deck
# BSE ledger — run: investor-deck-q3 — charter: /home/claude/bse/examples/80-slide-deck/CHARTER.md — created: 2026-09-12T21:36:18Z
id     type       status   att   budget     words  review   title
B001   transform  done       2   10slides     538  -        Slides 1-10: Title & overview
B002   transform  pending    0   10slides       -  pending  Slides 11-20: Market & product
B003   transform  pending    0   10slides       -  -        Slides 21-30: Financials
B004   transform  pending    0   10slides       -  pending  Slides 31-40: Customer case studies
B005   transform  pending    0   10slides       -  pending  Slides 41-50: Technology roadmap
B006   transform  pending    0   10slides       -  -        Slides 51-60: Go-to-market & partnerships
B007   transform  pending    0   10slides       -  -        Slides 61-70: Team & operations
B008   transform  pending    0   10slides       -  -        Slides 71-80: Appendix & financial detail
B009   verify     pending    0   10items        -  pending  Cross-wave reconciliation pass
1 of 9 units done
```

B002/B004/B005/B009 show `pending` in the `review` column already, even
before any of them has an artifact — that column reflects what the *plan*
declares, not just what's been checked. B001 shows `-` (no judgement
predicate at all — it was never in the four flagged above) and B003,
B006-B008 also show `-` here even though they read the style guide too,
because they satisfy the predicate-adequacy rule with mechanical
`citation_tags` instead of a `source:` predicate (section 1a).

## 2. Why this deck uses wave mode, not the serial baton

DESIGN.md reserves wave mode for units that are "genuinely independent...
and touch no shared file/section" — and explicitly warns it "never" for
prose that must flow (SKILL.md, Modes). This deck qualifies on both counts,
for reasons the 20k-word-report example does not:

- **No narrative dependency between slide ranges.** Section 3.2 of the
  report genuinely depends on terms Section 3.1 defined first; slide 47
  (manufacturing capacity) does not depend on anything decided while
  editing slide 12 (product overview). Each wave's unit spec says exactly
  this in its `intent`: "this unit cannot see any other wave; do not
  assume slides 11+ have been touched yet."
- **Editing against a fixed, already-written spec, not composing new
  prose.** Every change in every unit is dictated by the rebrand style
  guide and the Q3 2026 actuals — there is no voice, argument, or
  carryover of "established facts" a baton needs to hand forward. `carry.md`
  for this run stays at its untouched template state for exactly that
  reason (nothing in this task needs a baton).
- **The failure mode wave mode trades for speed — cross-wave drift — is
  real and specific here, not hypothetical.** Six of the eight waves touch
  the same footer wordmark string, three touch the same divider palette,
  and two touch the same TOC section names, all edited by units that
  cannot see each other. That is exactly what the mandatory reconciliation
  pass (B009) exists to catch.

`bse.py next --all` is the wave-mode dispatch primitive — it returns every
currently unblocked unit at once, not just the first one, so a supervisor
can hand all eight to concurrent subagents in one step:

```
$ python3 scripts/bse.py next --run-dir examples/80-slide-deck --all
B001 [P]
B002 [P]
B003 [P]
B004 [P]
B005 [P]
B006 [P]
B007 [P]
B008 [P]
```

B009 does not appear — its `[dep:B001,...,B008]` keeps it blocked until all
eight waves are recorded done, which `unblocked_units()` enforces
mechanically, not by convention.

## 3. One wave, executed for real, including a real failure

B001 covers slides 1-10. Its brief was assembled the same way as any other
unit:

```
$ python3 scripts/bse.py brief --run-dir examples/80-slide-deck B001
brief written: examples/80-slide-deck/briefs/B001.md (1257 words)
```

The first draft of `batches/B001.md` failed its check for real:

```
$ python3 scripts/bse.py check --run-dir examples/80-slide-deck B001
B001 check FAIL (2/3 mechanical)
  FAIL forbidden_phrases: forbidden: 'battery packs' L8
  ok   citation_tags: all numeric claims tagged
  ok   no_placeholders: no placeholders
  report: examples/80-slide-deck/reports/B001.md
```

The edit log's own description of the change had written `replaced
"battery packs" with "energy modules"` — quoting the forbidden old term to
describe what was replaced. `forbidden_phrases` does a plain word-boundary
search; it does not understand "this is the before-text in a diff
description" as a mitigating context, and it shouldn't have to. The fix was
to describe the change without repeating the retired term:

```diff
- Company overview: replaced the old company name and replaced "battery packs"
- with "energy modules" in the description sentence; ...
+ Company overview: replaced the old company name and replaced the old
+ product-name term with "energy modules" in the description sentence; ...
```

Re-checking the fixed artifact shows something new: `check` itself now
counts a fix round automatically. No `bse.py record --status fix` was ever
called here — the tool noticed the artifact's sha256 changed after a
failing check and counted the round on its own (capped at the same 3
rounds an explicit `record --status fix` would be):

```
$ python3 scripts/bse.py check --run-dir examples/80-slide-deck B001
B001 check PASS (3/3 mechanical)
  fix round 1/3 counted (artifact changed after a failing check)
  ok   forbidden_phrases: no forbidden phrases
  ok   citation_tags: all numeric claims tagged
  ok   no_placeholders: no placeholders
  report: examples/80-slide-deck/reports/B001.md

$ python3 scripts/bse.py record --run-dir examples/80-slide-deck B001 --status done
B001 done (538w, verify=pass(3/3)) — 1 of 9 units

$ python3 scripts/bse.py next --run-dir examples/80-slide-deck
B002
```

`LEDGER.md` records the auto-counted round exactly as an explicit one would
be, just tagged `auto=check`:

```
B001 fix 1/3  2026-09-12T22:29:56Z  verify=fail(1/3): forbidden: 'battery packs' L8  auto=check (artifact changed after a failing check)
B001 done     2026-09-12T22:29:56Z  artifact=batches/B001.md  words=538  verify=pass(3/3)  sha=89ee605
```

## 4. The batch artifact: a markdown table, per slide

`batches/B001.md` (the full file is in this directory) is the answer to
"what does a per-slide edit look like as a batch artifact": a markdown
table with exactly the three columns the task calls for — slide number,
change made, verification evidence — plus a short "notes for the
reconciliation pass" section flagging the two cross-wave risks this unit
noticed (the shared footer string, and a judgment call on slide 7 about
whether historical data should be restated). That second section is what
lets B009 do its job without re-reading all eight full logs from scratch —
each wave surfaces what the reconciliation pass specifically needs to
check.

The remaining seven waves (B002-B008) and the reconciliation pass (B009)
were not executed in this example for the same reason B004-B017 were not
executed in the 20k-word-report example: the mechanical loop is fully
demonstrated by B001, and running all nine units would mean pasting an
entire investor deck's worth of edit-log tables into a documentation
example. Every unit's spec block is complete, real, and already passed
`plan --validate`.

## 5. What the mandatory reconciliation pass actually checks

B009's spec block (in PLAN.md) is explicit about this because "wave mode
worked" is not, on its own, a checkable predicate. It checks:

1. All 80 slide numbers appear exactly once across the eight edit logs —
   no gap, no duplicate (DESIGN.md's "seam damage" failure mode, applied to
   slides instead of prose).
2. Every wave used identical replacement text for elements more than one
   wave touches — the footer wordmark, the TOC labels, the palette hex
   values — since two waves independently choosing "Meridian Grid
   Robotics" vs. "Meridian Grid Robotics, Inc." would be exactly the kind
   of drift parallel execution risks and serial execution would not.
3. No wave invented a figure absent from `sources/q3-2026-actuals.md` —
   parallel units can't cross-check each other's arithmetic in the moment,
   so this is checked once, centrally, after the fact.
4. Both slides flagged as out-of-scope design-asset issues (the
   screenshot with the embedded old logo, the IR email domain) are still
   flagged in the combined view, not silently dropped by whichever wave
   didn't own them.

This is a real editing pass, not a rubber stamp — it is why B009 is typed
`verify` and depends on all eight waves rather than being folded into
`bse.py stitch`'s automatic seam pass, which only catches duplicate prose
sentences and terminology-lock violations, not slide-numbering or
cross-wave figure invention.

## 6. What this run actually produces, and what `stitch` cannot do here

Worth stating plainly: this run's deliverable, per the charter, is nine
markdown edit logs (eight per-slide-range logs plus the reconciliation
memo) — a **verified change set**, not the `.pptx` itself. The charter says
so explicitly ("this run never touches the real .pptx; the format skill
applies the approved edits to the actual file afterward") and "Out of
scope" repeats it ("Producing the final .pptx file — batches here are the
edit log only"). That means `bse.py stitch` is not the right tool for this
run's last mile the way it is for the 20k-word-report example: `stitch`
concatenates `batches/*.md` in plan order into `draft.md`, but concatenating
nine edit-log tables is not "the deck" in any sense a reader could open and
present — it would just be nine tables end to end, and there is no
front-matter/back-matter prose to write in a seam pass either, because
there is no prose narrative here to seam. The seventh move (STITCH -> SEAM)
is built for an assembled *document*; an edit-log run's real "seventh move"
is a separate, human (or tooled) **apply step** — someone (or some other
script) reads the nine verified, `[S#]`-tagged edit logs and B009's
reconciliation memo, and applies each logged change to the actual `.pptx`
file, slide by slide. `bse.py` verifies that the change set is internally
consistent and complete (every slide accounted for, no invented figures,
no leftover old branding); it does not — and per this charter, should
not — touch the `.pptx` itself.

## Design feedback surfaced by building this example

- **`forbidden_phrases` cannot tell "the new text" from "a description of
  the old text."** This is almost certainly the right behavior for the
  final deck (a reader should never see the retired name anywhere), but it
  means an edit-log artifact that describes its own diffs has to be
  written carefully — "replaced X with Y" fails if X is a locked-out term.
  An executor prompt for this kind of unit should say so explicitly, the
  way this walkthrough had to discover it by hitting the failure.
- **`slide_count` was not the right verifier for this unit shape.** The
  budget is denominated in slides (so it sums correctly against the
  charter's `80slides` total), but the artifact is an edit log, not
  rendered slide content, so `slide_count`'s heading-counting heuristic
  does not apply. `forbidden_phrases` / `citation_tags` / `no_placeholders`
  turned out to be the right predicates for an edit-log unit; a reader
  building a similar plan should not assume the unit's budget denomination
  dictates which verifier to use — the two are independent, and the
  mechanical registry's numeric comparator (`parse_number_spec`) happily
  accepts a literal number instead of `budget` when the two need to differ.
