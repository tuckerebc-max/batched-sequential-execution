# BSE worked examples

Four real runs of `scripts/bse.py`, each a different shape of "too big for
one pass" from DESIGN.md's list. Every state file in each directory — every
`CHARTER.md`, `PLAN.md`, `LEDGER.md`, `ledger.json`, brief, batch, and
verification report — was produced by actually running the tool against
this repo's checkout, not written by hand to look like tool output. Where a
command failed for real (a plan-validation error, a failing mechanical
check), the failure and the fix are both shown, because that is the part of
the loop most worth seeing.

[`complete-run/`](complete-run/) is the one to read first: it is executed
start to finish — six units, a real failure and fix round, reviewer verdicts,
`stitch`, a hand-written seam pass producing `front-matter.md`,
`back-matter.md` and `final.md`, and a clean closing audit. It is deliberately
small (~5,000 words) so the whole run fits in one sitting, and
`SEAM-PASS-NOTES.md` records exactly what the seam pass changed — including a
duplicate the mechanical check missed and the read-through caught.

The other three runs are not executed start to finish — each executes a real,
representative slice (the first few units, including at least one genuine
failure or escalation) and leaves the remaining units fully specified and
plan-validated but not run. Running the rest is the same loop, repeated;
pasting a full 20,000-word report or an 80-slide deck into a documentation
example would not make the mechanics any clearer.

## The examples

### [`20k-word-report/`](20k-word-report/) — long-document composition

A policy research report (charter total 15,800w of body sections), broken
into 15 serial units (the flagship example — the full unit list is written
out, not abbreviated). Shows the default `delegated` mode: research a
source catalog, compose section by section with a carry-forward baton, and
a consistency-audit unit before the seam pass. Front matter (executive
summary) and back matter (introduction/conclusion) are no longer plan
units — they are `front-matter.md`/`back-matter.md`, written by hand in the
seam pass and included by `stitch` automatically. Includes a genuine
mechanical-check failure (a budget miscalibration in the first unit) and
its fix, a real judgement-predicate review (with a written reviewer report,
not a rubber stamp) for the two composed sections, a real `carry.md` baton
after three units, and a `WALKTHROUGH.md` narrating every command run,
including a later validator update that required re-shaping the plan.

### [`80-slide-deck/`](80-slide-deck/) — wave-mode editing

An 80-slide investor deck getting a post-merger rebrand and figures
refresh, edited in `wave` mode: eight `[P]` units of 10 slides each, run in
parallel (no unit can see another), followed by a mandatory, non-parallel
reconciliation pass. Shows why this deliverable qualifies for wave mode
when the other two do not (no narrative flow, no baton needed, a concrete
cross-wave drift risk the reconciliation pass exists to catch), a batch
artifact as a markdown table of slide/change/evidence, a real
`forbidden_phrases` failure caused by an edit log describing its own diff
in banned terminology, and `check` automatically counting that failure's
fix round. Also spells out plainly what this kind of run actually produces
(a verified change set of edit logs) versus the separate, human apply step
that turns it into the real `.pptx`.

### [`feedback-sweep/`](feedback-sweep/) — large revision sweep

120 reviewer comments (developmental edit, beta reads, fact-check,
copyedit) applied to an existing 30,000-word nonfiction manuscript, grouped
into 17 units of 6-10 items each **by manuscript region, not by the order
comments arrived in** — with the grouping logic and its rationale spelled
out. Includes the case every real feedback sweep eventually hits: a
reviewer comment that contradicts the charter (an attribution
non-negotiable), which the executor correctly refuses to resolve on its
own, escalating through a real `blocked` ledger entry and a real `RULING`
entry before the unit resumes and completes; a real judgement-predicate
review of all six executed units, added after a later validator update
required every unit to trace its resolutions back to the reviewer-feedback
log; and a real `carry.md` baton written after those six units, fixing a
genuine `CARRY_STALE` finding. Also spells out what this run actually
produces (a verified resolution log, not a revised manuscript) and the
separate apply step that would produce one.

## How to run these yourself

Every command below is run from the repo root. Each example passes its own
`--run-dir`, so the three never share state and never touch `./.bse`.

```bash
# See the current state of any run
python3 scripts/bse.py status --run-dir examples/20k-word-report

# Validate a plan from scratch
python3 scripts/bse.py plan --run-dir examples/80-slide-deck --validate

# Read the ledger's identity header and resume point
python3 scripts/bse.py next --run-dir examples/feedback-sweep

# Re-run the mechanical checks already recorded
python3 scripts/bse.py check --run-dir examples/20k-word-report B002

# Confirm ledger/filesystem consistency (phantom-complete detector)
python3 scripts/bse.py audit --run-dir examples/feedback-sweep
```

To continue any of the three runs past where this repo stops: `bse.py next
--run-dir <dir>` (or `--all` for the wave-mode deck) names the next
unblocked unit; `bse.py brief <ID>` assembles its brief; write
`batches/<ID>.md`; `bse.py check <ID>`; `bse.py record <ID> --status done`.
That loop, repeated, is the entire tool.

Tested against Python 3.11; the tool itself targets 3.9+, standard library
only.

## Design feedback from building these

Each example's `WALKTHROUGH.md` ends with a short "design feedback" section
noting places the tool's actual behavior was sharper, stricter, or more
surprising than its one-line docstring suggested — worth reading if you are
extending `scripts/bse.py` or writing unit specs of your own. In short:

- `citation_tags` joins a paragraph's or list item's wrapped lines into one
  chunk before checking for a `[S#]` tag, so a hard-wrapped sentence whose
  number and tag land on different physical lines still passes — an
  earlier draft of one walkthrough claimed otherwise, based on an older
  tool version, and has been corrected in place.
- `forbidden_phrases` does a plain word-boundary search with no concept of
  "this is describing the old text as part of a diff" — an edit log has to
  avoid ever spelling out a retired term, even to say what it was replaced
  with.
- A unit's budget denomination (words, slides, items, files) and the
  mechanical verifier used to check it are independent choices; nothing
  requires `slide_count` for a `slides`-budgeted unit, and picking a
  different, more meaningful verifier is expected when the artifact shape
  doesn't match the budget's unit.
- `record RULING --unit ID` links a ruling to the specific unit it
  resolves, and `bse.py audit`'s `BLOCK_WITHOUT_RULING` check already flags
  a unit that went `blocked` -> `done`/`fix` with no RULING (linked or
  unit-less) recorded in between — an earlier draft of one walkthrough
  claimed neither existed; both do, and the feedback-sweep walkthrough now
  demonstrates the check firing against a disposable copy of its ledger.
- `plan --validate` now enforces predicate adequacy (a word-budgeted unit
  needs `word_count`; a unit reading a named source needs `citation_tags`
  or a `source:` predicate; a non-final `compose` unit needs
  `no_conclusion`; each waivable) and `next` refuses to run on a plan that
  has never passed `--validate`. All three plans in this directory needed
  real changes to satisfy this once it shipped — see each `WALKTHROUGH.md`
  for the specific fix and, where a predicate was added to an already-`done`
  unit, the real reviewer pass that followed.
- `bse.py status` now has a `review` column (`-`/`pending`/`stale`/`pass`/
  `fail`), and `bse.py check`, re-run on an artifact that changed after a
  failing check, counts a fix round on its own — both shown live in these
  walkthroughs, not just described.
