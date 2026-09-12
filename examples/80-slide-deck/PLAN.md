# PLAN — Meridian Grid Robotics Q3 2026 Investor Update

## Units

- [x] B001 [transform] [P] Slides 1-10: Title & overview — budget: 10slides
- [ ] B002 [transform] [P] Slides 11-20: Market & product — budget: 10slides
- [ ] B003 [transform] [P] Slides 21-30: Financials — budget: 10slides
- [ ] B004 [transform] [P] Slides 31-40: Customer case studies — budget: 10slides
- [ ] B005 [transform] [P] Slides 41-50: Technology roadmap — budget: 10slides
- [ ] B006 [transform] [P] Slides 51-60: Go-to-market & partnerships — budget: 10slides
- [ ] B007 [transform] [P] Slides 61-70: Team & operations — budget: 10slides
- [ ] B008 [transform] [P] Slides 71-80: Appendix & financial detail — budget: 10slides
- [ ] B009 [verify] [dep:B001,B002,B003,B004,B005,B006,B007,B008] Cross-wave reconciliation pass — budget: 10items

## Specs

### B001 — Slides 1-10: Title & overview
type: transform
budget: 10slides
depends_on: []
inputs:
  - CHARTER.md
  - sources/rebrand-styleguide.md
  - sources/q3-2026-actuals.md
  - sources/original-deck-outline.md#L14-24
intent: |
  Edit slides 1-10 (Title & overview section) against the rebrand style
  guide and Q3 2026 actuals: rename the company/ticker/product everywhere
  they appear, update the Q3 headline metrics and stock chart description
  to Q3 2026 figures, and swap chart/divider colors to the new palette.
  Slides with no dependency (e.g. mission statement, team photo slides) are
  left unchanged and noted as such. This unit cannot see any other wave; do
  not assume slides 11+ have been touched yet.
produces:
  - section: "Slides 1-10 edited"
verify:
  - mechanical: forbidden_phrases
  - mechanical: citation_tags
  - mechanical: no_placeholders
done_when: |
  Every slide 1-10 that the style guide or actuals touch is edited and
  logged in a table (slide #, change made, verification evidence); every
  slide left unchanged states why.

### B002 — Slides 11-20: Market & product
type: transform
budget: 10slides
depends_on: []
inputs:
  - CHARTER.md
  - sources/rebrand-styleguide.md
  - sources/original-deck-outline.md#L26-39
intent: |
  Edit slides 11-20 (Market & product section): rename the product
  ("battery pack" -> "energy module") wherever it appears in slide text,
  swap chart colors to the new palette, and flag (but do not attempt to
  fix in this text-only pass) the one slide whose screenshot asset embeds
  the old logo in the UI chrome — that is a design-asset fix, not a text
  edit, and is out of scope for this unit.
produces:
  - section: "Slides 11-20 edited"
verify:
  - mechanical: forbidden_phrases
  - mechanical: no_placeholders
  - source: every product-name rename and the flagged screenshot-asset slide match the naming rule in [S1]
done_when: |
  Every text occurrence of the old product name in slides 11-20 is
  replaced, chart colors are logged as updated, and the screenshot-asset
  slide is flagged for design rather than silently left inconsistent.

### B003 — Slides 21-30: Financials
type: transform
budget: 10slides
depends_on: []
inputs:
  - CHARTER.md
  - sources/q3-2026-actuals.md
  - sources/original-deck-outline.md#L41-51
intent: |
  This is the highest figure-density wave: nine consecutive metric-trend
  charts (revenue, margin, units shipped, services revenue, cash, headcount,
  backlog, ASP, R&D%) that all end at a Q3 2025 data point and need a Q3
  2026 point appended, each [S2]-tagged, plus a palette swap on every
  chart. Do not alter the historical data points already shown.
produces:
  - section: "Slides 21-30 edited"
verify:
  - mechanical: citation_tags
  - mechanical: no_placeholders
  - mechanical: forbidden_phrases
done_when: |
  All nine metric charts show an added Q3 2026 data point sourced to [S2]
  and the new palette; the section-divider slide's color is also updated.

### B004 — Slides 31-40: Customer case studies
type: transform
budget: 10slides
depends_on: []
inputs:
  - CHARTER.md
  - sources/rebrand-styleguide.md
  - sources/original-deck-outline.md#L53-59
intent: |
  Edit the three customer case studies (slides 31-40): rename the product
  wherever named, and update the intro slide's framing sentence, which
  currently names the pre-merger company. Case-study-specific dollar
  figures (e.g. a customer's site cost) are not company financials and are
  left unchanged — do not confuse them with Q3 2026 actuals.
produces:
  - section: "Slides 31-40 edited"
verify:
  - mechanical: forbidden_phrases
  - mechanical: no_placeholders
  - source: every renamed company or product-name occurrence in slides 31-40 matches [S1] exactly, and no case-study-specific dollar figure is altered
done_when: |
  The section intro and all three case studies use the new company and
  product names; no case-study-specific dollar figure is altered.

### B005 — Slides 41-50: Technology roadmap
type: transform
budget: 10slides
depends_on: []
inputs:
  - CHARTER.md
  - sources/rebrand-styleguide.md
  - sources/original-deck-outline.md#L61-70
intent: |
  Edit the roadmap section: rename the product on the next-gen preview
  slide, remove the old-company footnote citation on the patent-portfolio
  slide, and swap the section divider and manufacturing-capacity chart to
  the new palette. Most slides in this range (roadmap timelines, R&D
  facility photo, supply chain, certifications) have no rebrand dependency
  and are logged as unchanged.
produces:
  - section: "Slides 41-50 edited"
verify:
  - mechanical: forbidden_phrases
  - mechanical: no_placeholders
  - source: the product rename, the footnote removal, and the palette swap all match [S1] exactly
done_when: |
  The product name and the patent-portfolio footnote are corrected, the
  divider and capacity chart use the new palette, and every unaffected
  slide is explicitly logged as unchanged rather than silently skipped.

### B006 — Slides 51-60: Go-to-market & partnerships
type: transform
budget: 10slides
depends_on: []
inputs:
  - CHARTER.md
  - sources/rebrand-styleguide.md
  - sources/q3-2026-actuals.md
  - sources/original-deck-outline.md#L72-80
intent: |
  Edit the go-to-market section: update the utility-partnership count to
  the Q3 2026 cumulative figure (23 total, 7 new this quarter, both
  [S2]-tagged), rename the company on the analyst-coverage and
  press-mentions slides, replace the ticker, and swap the section divider
  color.
produces:
  - section: "Slides 51-60 edited"
verify:
  - mechanical: citation_tags
  - mechanical: forbidden_phrases
  - mechanical: no_placeholders
done_when: |
  Both partnership figures are updated and [S2]-tagged, every company-name
  and ticker occurrence in this range is corrected, and the divider color
  is updated.

### B007 — Slides 61-70: Team & operations
type: transform
budget: 10slides
depends_on: []
inputs:
  - CHARTER.md
  - sources/q3-2026-actuals.md
  - sources/original-deck-outline.md#L82-91
intent: |
  Edit the team & operations section: update the org-chart and
  hiring-plan headcount figures to the Q3 2026 actual (1,340, [S2]-tagged),
  swap the hiring-plan chart's palette, and note that the operational-KPIs
  slide's one dollar figure (facilities cost) is not present in
  sources/q3-2026-actuals.md and must be flagged, not invented.
produces:
  - section: "Slides 61-70 edited"
verify:
  - mechanical: citation_tags
  - mechanical: no_placeholders
  - mechanical: forbidden_phrases
done_when: |
  Both headcount figures are updated and [S2]-tagged, the hiring chart
  uses the new palette, and the unsourced facilities-cost figure is
  explicitly flagged rather than silently left or guessed at.

### B008 — Slides 71-80: Appendix & financial detail
type: transform
budget: 10slides
depends_on: []
inputs:
  - CHARTER.md
  - sources/rebrand-styleguide.md
  - sources/q3-2026-actuals.md
  - sources/original-deck-outline.md#L93-104
intent: |
  This is the second-highest figure-density wave: the full income
  statement, balance sheet, cash flow, and non-GAAP reconciliation detail
  slides all need a complete Q3 2026 refresh from [S2], each figure
  [S#]-tagged. The two risk-factor slides and the glossary and closing
  slide need company/ticker/product-name corrections. The IR contact
  slide's old email domain is flagged for the IR team, not edited here (it
  is not a text substitution this pass is scoped to make).
produces:
  - section: "Slides 71-80 edited"
verify:
  - mechanical: citation_tags
  - mechanical: forbidden_phrases
  - mechanical: no_placeholders
done_when: |
  All four detail-statement slides are refreshed to Q3 2026 figures with
  [S2] tags, every remaining Voltane/VOLT/battery pack occurrence in
  slides 71-80 is corrected, and the IR-email issue is flagged rather than
  silently edited.

### B009 — Cross-wave reconciliation pass
type: verify
budget: 10items
depends_on: [B001, B002, B003, B004, B005, B006, B007, B008]
inputs:
  - CHARTER.md
  - sources/rebrand-styleguide.md
  - batches/B001.md
  - batches/B002.md
  - batches/B003.md
  - batches/B004.md
  - batches/B005.md
  - batches/B006.md
  - batches/B007.md
  - batches/B008.md
intent: |
  The eight waves above ran in parallel and could not see each other; this
  is the mandatory reconciliation pass DESIGN.md requires after any wave.
  Check, across all eight edit logs together: (1) no slide number is
  missing or duplicated (80 total, 1-80 exactly once each); (2) every wave
  used identical replacement text for shared recurring elements (the
  footer wordmark, the TOC section names, the divider palette hex); (3) no
  wave silently invented a figure not present in sources/q3-2026-actuals.md;
  (4) the two flagged design-asset issues (the screenshot logo, the IR
  email domain) are both still flagged, not dropped. Produce a single
  reconciliation memo as a checklist of these items.
produces:
  - section: "Reconciliation memo"
verify:
  - mechanical: item_count within 20% of budget
  - mechanical: no_placeholders
  - source: every color-hex and terminology cross-check in the memo matches [S1] exactly
  - charter: acceptance criteria 3, 4
done_when: |
  The memo confirms all 80 slide numbers appear exactly once across the
  eight logs, confirms identical replacement text for every shared
  recurring element, and lists both flagged design-asset issues as still
  open.
