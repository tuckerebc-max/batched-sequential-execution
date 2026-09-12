# PLAN

<!--
This is the ordered unit plan for one BSE run: a table (execution order) plus
one "### <ID> — <title>" spec block per table row. `bse.py plan --validate`
enforces this shape — see the checklist at the bottom before you run it.

Known mechanical verifier names (use exactly one of these as the first word
after "mechanical:"): word_count, no_placeholders, contains_headings,
max_heading_depth, citation_tags, forbidden_phrases, slide_count, item_count,
file_exists, json_schema, shell, no_conclusion. Non-mechanical predicate kinds
(any other word before the colon, e.g. "source:" or "charter:") are judgement
predicates routed to the reviewer pass — write them as free text.

`plan --validate` also enforces three predicate-adequacy rules per unit, each
waivable with a `waive: <rule> — <reason>` line in the spec block (see the
sample unit and the `waive:` example below):
- a unit budgeted in words needs a `word_count` mechanical verifier;
- a unit whose `inputs` name a real source (anything beyond CHARTER.md,
  carry.md, or a prior unit's own batches/<ID>.md) needs `citation_tags` or a
  `source:` predicate;
- a non-final `compose` unit needs `no_conclusion`.
-->

## Units
<!--
Table line syntax (one per unit, in execution order):
  - [ ] <ID> [<type>] [P] [dep:<ID>,<ID>] <title> — budget: <n><unit>

- ID: B + 3 digits, sequential in execution order (B001, B002, ...). A split
  unit becomes <ID>a / <ID>b (e.g. B004a).
- type: one of research | compose | revise | transform | verify | assemble.
- [P] — include only if this unit is genuinely independent of every
  incomplete unit and shares no `produces` target with another [P] unit.
- [dep:...] — comma-separated IDs this unit depends on; omit if none.
- budget: an integer + unit with no space — 1200w, 6slides, 3files, 10items.
- Leave the checkbox "[ ]"; tooling flips it to "[x]" on verified completion.

`bse.py init` writes exactly ONE real, uncommented unit below — marked
SAMPLE — and nothing else. Its budget is deliberately set to the charter's
ENTIRE declared total (here, `init`'s own default `--total 20000w`), not a
realistic per-unit size in the band — that's what makes the very first
`plan --validate` pass with zero budget-sum drift on a fresh run, before
you've written any real units. Replace both the unit and its budget with
your real first unit, sized per [batch-sizing.md](batch-sizing.md);
`plan --validate` warns while SAMPLE is still there. This template shows
the exact scaffold `init` produces so you can recognize it before
overwriting it.
-->
- [ ] B001 [compose] SAMPLE unit — replace with your first real unit — budget: 20000w

## Specs
<!--
One "### <ID> — <title>" block per table row, in any order, all fields
required, no placeholders left unfilled (no "TBD", "etc.", "similar to",
"as above", "..."). The sample block below is what `init` actually writes;
the two worked examples further down show a filled, real block of each kind.
-->
### B001 — SAMPLE unit — replace with your first real unit
type: compose
budget: 20000w (±15%)
depends_on: []
inputs:
  - CHARTER.md
intent: |
  This is the scaffold's sample unit. It exists so that `bse.py plan
  --validate` passes on a fresh run. Replace it with the real first unit:
  one paragraph a stranger could act on, a real budget in the band, and the
  input slices it needs.
produces:
  - section: "Sample section"
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: no_placeholders
  - mechanical: no_conclusion
done_when: |
  The sample unit has been replaced by real units and this block is gone.

---
## Example

Two worked spec blocks, one `compose` and one `revise`, each exercising every
field and all three verify-predicate kinds (`mechanical`, `source`, `charter`).
Their table lines:

```
- [ ] B002 [compose] [dep:B001] Section 3.2 — capacity model — budget: 1200w
- [ ] B006 [revise] [dep:B005] Apply reviewer feedback batch 2 — budget: 8items
```

### B002 — Section 3.2 — capacity model
type: compose
budget: 1200w (±15%)
depends_on: [B001]
inputs:
  - research/capacity-notes.md#L40-120
  - CHARTER.md
intent: |
  Write section 3.2, "Method", explaining the capacity model introduced in
  B001's glossary. Define "capacity ledger" on first use and carry the term
  forward exactly as locked in the charter. End mid-argument — do not
  summarize or conclude; later sections build on this one.
produces:
  - term: "capacity ledger" defined
  - section: "3.2 Method"
verify:
  - mechanical: word_count within 15% of 1200
  - mechanical: contains_headings ["3.2 Method"]
  - mechanical: no_placeholders
  - source: every numeric claim carries a [S#] tag present in CHARTER.md's sources
  - charter: acceptance criteria 2, 5
done_when: |
  Section 3.2 exists, defines "capacity ledger", and every mechanical check
  above passes.

### B006 — Apply reviewer feedback batch 2
type: revise
budget: 8items (±15%)
depends_on: [B005]
inputs:
  - reports/feedback-round2.md#L1-40
  - batches/B003.md
  - CHARTER.md
intent: |
  Apply feedback items 9-16 from reports/feedback-round2.md to batches/B003.md
  and write the revised section to batches/B006.md. Fix only what the listed
  items name; do not rewrite passing material or restate carry's "do not
  repeat" topics.
produces:
  - section: "3.2 Method" (revised)
verify:
  - mechanical: item_count within 15% of 8
  - mechanical: no_placeholders
  - mechanical: forbidden_phrases []
  - source: every applied fix traces to a numbered feedback item in the input
  - charter: acceptance criteria 1
done_when: |
  All 8 listed feedback items are resolved in batches/B006.md and every
  mechanical check above passes.

### Waiving a predicate-adequacy rule

A third worked unit, showing `waive:` — used only when a rule's premise
genuinely doesn't hold for this unit, not as a way to skip writing a
predicate that should exist. `inputs` here names a real file beyond
CHARTER.md/carry.md/a prior batch, so the validator would otherwise demand
`citation_tags` or a `source:` predicate — but this unit's input is a style
reference, not a source of any claim the section makes:

```
- [ ] B009 [compose] Section 3.4 — house-style pass — budget: 900w
```

### B009 — Section 3.4 — house-style pass
type: compose
budget: 900w (±15%)
depends_on: [B002]
inputs:
  - style/report-house-style.md
  - CHARTER.md
intent: |
  Write section 3.4, restating the capacity model's implications in the
  house style guide's plain-language register. Introduces no new fact or
  figure — style/report-house-style.md is a writing-style reference, not a
  source any claim traces to.
produces:
  - section: "3.4 Plain-language summary"
verify:
  - mechanical: word_count within 15% of 900
  - mechanical: no_placeholders
  - mechanical: no_conclusion
done_when: |
  Section 3.4 exists and every mechanical check above passes.
waive: citation_tags — the named input is a style reference, not a source of any claim
