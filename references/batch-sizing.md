# Batch sizing

The table in [SKILL.md](../SKILL.md#batch-sizing) gives defaults. This file gives the
reasoning, a procedure for unit types the table doesn't cover, and worked arithmetic.

## The table, with reasoning

| Unit type | Default | Ceiling | Shrink when | Why this band |
|---|---|---|---|---|
| Prose, new | 800–1,200w | 1,500 | dense citation, >3 sources, technical derivation | LongWriter's AgentWrite harness is the closest published analog — plan-then-write with a word budget per item — and it uses a 200–1,000-word band. That figure is a **prompt constant the paper never ablates for chunk size**, not a measured optimum (see [evidence.md §7](evidence.md#7-known-gaps)); LongWriter's *other* finding, that SFT output ceilings track training-data chunk size rather than architecture, supports staying inside *some* fixed band, not this specific one. 800–1,200 with a 1,500 ceiling is this skill's own calibrated default — comfortably inside AgentWrite's demonstrated range, sized against the decision procedure below (a batch a reviewer can check thoroughly in 5-10 minutes), not derived from an ablation that doesn't exist. Treat it as a starting point to calibrate away from (see "Calibrating on the first two units"), not as a finding. |
| Prose, revision to feedback | 6–10 items | 15 | items interact, or any item is structural | Each item is a small independent verification target (was it applied, does it still read correctly). Interacting items turn one predicate into a graph of predicates — the thing that makes verification unreliable. |
| Slides, created | 4–6 slides | 8 | heavy data or bespoke layout per slide | A slide is close to a paragraph in information density; data-dense or bespoke slides take a full judgment pass each, so the safe count per unit drops. |
| Slides, edited to spec | 8–12 slides | 20 | per-slide judgment required | Mechanical edits (apply a template field) verify cheaply in bulk; anything requiring per-slide judgment reduces to the "created" band's logic. |
| Code | 1 vertical slice, ~400 changed lines | — | crosses module boundaries | A vertical slice has one coherent behavior to test. Crossing a module boundary means the unit now owns two contracts, and a single `shell` predicate can no longer localize failure. |
| Data/sheets | 1 sheet or derived table | 2 | formula chains cross sheets | A sheet's formulas are checkable in isolation; a cross-sheet formula chain makes the correctness of unit N depend on unit N−1's exact cell layout, which breaks curated-context execution (P4). |
| Extraction/research | 5–8 sources | 12 | sources are long or conflicting | Each source needs to be read fully enough to extract faithfully. Conflicting sources turn extraction into arbitration, which is a different (heavier) operation type — see P10. |

## Decision procedure for a unit type not in the table

1. Identify the **verification unit** — the smallest thing one predicate set can
   check pass/fail without ambiguity (one paragraph, one slide, one test suite run,
   one row). This is almost never "however much the model can produce at once."
2. Ask how many verification units a competent human reviewer could check
   thoroughly in 5–10 minutes. That count is your starting default.
3. Set the ceiling at roughly 1.5–2x the default — the point past which a single
   failed check can no longer tell you *which part* is wrong.
4. Name at least one concrete "shrink when" condition: what property of the
   content (not the model) makes verification harder per unit.
5. Run the first unit at the default. If it passes clean on the first try, hold
   the size. If it takes 2+ fix rounds, halve it for the next unit of that type.

## Calibrating on the first two units

The table is a prior, not a commitment. After unit 1:
- Clean pass, well under the fix-round cap → the size is probably conservative;
  consider raising it one step for the same unit type, but only after unit 2 also
  passes clean — one data point is noise.
- 1 fix round, resolved on retry → hold the size.
- 2+ fix rounds, or blocked → shrink for every remaining unit of that type, not
  just the current one. Two verification failures on the same unit means the unit
  is too big — don't treat it as bad luck.

Record the calibration decision in `carry.md`'s tone/notes area or as a `RULING`
event so later units (and a resumed session) inherit it instead of re-learning it.

## Heterogeneous units

When a deliverable mixes types (a report with three data tables, a deck with two
appendix slides of raw numbers), size each unit by **its own** type's band, not the
deliverable's dominant type. Don't average bands across types — a "compose" unit
sized for prose and carrying an embedded table is really two verification units
glued together; split them so each gets its own predicate set. The plan's budget
sum check only sums units sharing the charter's total unit (see below), so mixed
units need the charter to state a total per unit kind if more than one is load-bearing.

## Budget and verifiability

A batch's budget is a control signal (P2) precisely because it is also the thing
a mechanical predicate can check. The relationship runs one direction: **shrink
the batch until the verification predicates for it are unambiguous**, not the
reverse. A model can competently produce a 3,000-word section in one pass — that
is not evidence the unit should be 3,000 words. If that section must carry a
`[S#]` tag on every numeric claim across five partially conflicting sources, no
single predicate set can catch a citation error buried at word 2,400 as reliably
as it catches one at word 400. Getting this wrong looks like: the unit passes
`citation_tags` and `word_count`, ships, and a source contradiction surfaces two
units later because the reviewer's attention (human or model) thinned out well
before the predicate did. The fix is not a better reviewer — it's an 800-word
unit with two sources instead of a 3,000-word unit with five.

## Worked sizing examples

**20,000-word report** — prose, new, band 800–1,200w. At 1,100w/unit: 20,000 / 1,100
≈ 18.2 → 18 units. 18 × 1,100 = 19,800w, drift 1% — comfortably inside the
±20% budget-sum gate.

[`examples/20k-word-report/`](../examples/20k-word-report/) works the same
target to a different, equally defensible number: 17 units total, 14 of them
body work (B002 through B015: twelve section-drafting units, one research
unit for an appendix, and the `revise` consistency/terminology audit that
closes the body out — everything except B001, the up-front source catalog,
and B016/B017, the executive summary and the assembled intro/conclusion,
which are infrastructure and front/back matter rather than "a section" of
the argument). Those 14 body units average closer to 1,250w each — nearer
the band's ceiling than its middle. Both decompositions are correct. This
section's 18-unit arithmetic picks the arithmetic midpoint of the band and
lets the remainder fall where it may; the worked example instead decomposed
by the report's actual argument structure first (problem statement, policy
landscape, three named subtopics, two case studies plus their comparison,
model legislation with its cost and timeline, a risk section, then an audit
pass) and let each unit's budget follow from how much that piece of the
argument needed, landing most of them near the band's upper end rather than
at a uniform 1,100w. Sizing by the content's own joints, not by dividing the
total evenly, is the better default in practice — this section's 18-unit
math is here to show the arithmetic, not to prescribe evenly-sized sections
over an outline that has its own natural structure.

**80-slide deck** — slides created, band 4–6. At 5/unit: 80 / 5 = 16 units exactly,
no remainder to absorb. At the 6-slide default alternative: 80 / 6 ≈ 13.3 → 13
units of 6 plus one of 2, or flatten to 14 units of ~5.7 — prefer the exact 16×5
split when it divides cleanly.

**40-file refactor** — code, sized by vertical slice, not raw file count. If files
are largely independent (a mechanical rename or lint-fix), slices can be wide:
~5 files/slice → 8 units. If files share interfaces that must stay consistent
(a shared type threaded through call sites), slices must be narrow: ~3 files/slice
→ 40 / 3 ≈ 13.3 → 14 units, with the shared-interface unit executed first and
declared in every dependent unit's `depends_on`.

**200-item feedback sweep** — revision to feedback, band 6–10. At 8/unit: 200 / 8
= 25 units exactly. At the ceiling of 15 (only if items are simple and
non-interacting): 200 / 15 ≈ 13.3 → 14 units — but note the table's own guidance:
interacting items should pull you toward 6–8, not toward the ceiling.

## Related

- [Light mode](light-mode.md) — the same band, with just a numbered outline instead of PLAN.md
- [Ledger and state](ledger-and-state.md) — where budgets are declared and checked
- [Verification](verification.md) — the `word_count` / `slide_count` / `item_count` predicates that enforce these bands
- [Failure modes](failure-modes.md) — thrash and stall as symptoms of a wrong size
