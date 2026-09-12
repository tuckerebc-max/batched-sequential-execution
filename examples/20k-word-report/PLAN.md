# PLAN — Bridging the Interconnection Queue

## Units

- [x] B001 [research] Build the annotated source catalog — budget: 10items
- [x] B002 [compose] [dep:B001] Section 1: Problem statement — budget: 1100w
- [x] B003 [compose] [dep:B001] Section 2: Policy landscape overview — budget: 1200w
- [ ] B004 [compose] [dep:B001,B003] Section 3.1: Interconnection queue mechanics — budget: 1200w
- [ ] B005 [compose] [dep:B004] Section 3.2: Cost allocation methods — budget: 1200w
- [ ] B006 [compose] [dep:B004] Section 3.3: Technical standards (IEEE 1547) — budget: 1100w
- [ ] B007 [compose] [dep:B001] Section 4.1: Case study — shared-queue priority — budget: 1200w
- [ ] B008 [compose] [dep:B001] Section 4.2: Case study — hosting-capacity maps — budget: 1200w
- [ ] B009 [compose] [dep:B007,B008] Section 4.3: Comparative analysis — budget: 1300w
- [ ] B010 [compose] [dep:B005,B006] Section 5.1: Model legislation options — budget: 1300w
- [ ] B011 [compose] [dep:B005] Section 5.2: Rate design and cost recovery — budget: 1200w
- [ ] B012 [compose] [dep:B010,B011] Section 5.3: Implementation timeline — budget: 1000w
- [ ] B013 [compose] [dep:B009,B010] Section 6: Stakeholder risk analysis — budget: 1300w
- [ ] B014 [research] [dep:B001] Appendix A: Data tables and methodology notes — budget: 8items
- [ ] B015 [revise] [dep:B002,B003,B004,B005,B006,B007,B008,B009,B010,B011,B012,B013,B014] Consistency and terminology audit — budget: 1500w

## Specs

### B001 — Build the annotated source catalog
type: research
budget: 10items
depends_on: []
inputs:
  - sources/ferc-order-2222-summary.md
  - sources/state-survey-2026.md
  - sources/utility-interconnection-timelines.md
  - sources/case-studies-vermont-hawaii.md
  - sources/cost-benefit-model-notes.md
intent: |
  Read all five source files and produce a one-page annotated catalog: for
  each source, its [S#] tag, a one-line description of what it is, and a
  one-line note on which planned sections will rely on it. This catalog is
  the only unit that reads every source file in full; every later unit reads
  only the slices it needs plus this catalog.
produces:
  - section: "Source Catalog"
  - term: "source catalog" defined
verify:
  - mechanical: item_count within 20% of budget
  - mechanical: no_placeholders
  - mechanical: citation_tags
done_when: |
  The catalog lists all five sources, each with its [S#] tag, a description,
  and at least one downstream section it feeds.

### B002 — Section 1: Problem statement
type: compose
budget: 1100w
depends_on: [B001]
inputs:
  - CHARTER.md
  - batches/B001.md
  - sources/state-survey-2026.md
intent: |
  Write Section 1, framing why state interconnection queues for battery
  storage have become a policy problem worth a report: growing queues,
  uneven state practice, and the pressure Federal Order 2222-B adds. Ground
  every claim in the survey data; do not yet discuss remedies (that is
  Sections 3 and 5).
produces:
  - section: "1. Problem Statement"
  - term: "interconnection queue" defined for report use
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["1. Problem Statement"]
  - mechanical: no_placeholders
  - mechanical: citation_tags
  - mechanical: no_conclusion
  - source: every statistic traces to [S2] or [S1]
  - charter: acceptance criteria 1
done_when: |
  Section 1 states the problem with at least three [S#]-tagged statistics
  from the 2026 survey and ends on an open question, not a conclusion.

### B003 — Section 2: Policy landscape overview
type: compose
budget: 1200w
depends_on: [B001]
inputs:
  - CHARTER.md
  - batches/B001.md
  - sources/ferc-order-2222-summary.md
intent: |
  Write Section 2, orienting the reader in the current policy landscape:
  what Federal Order 2222-B does and does not touch, and the resulting
  division of authority between federal wholesale-market rules and state
  retail-interconnection rules. This section sets up Sections 3-6 without
  pre-empting their content.
produces:
  - section: "2. Policy Landscape"
  - term: "retail interconnection authority" defined
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["2. Policy Landscape"]
  - mechanical: no_placeholders
  - mechanical: citation_tags
  - mechanical: no_conclusion
  - source: the federal/state authority split matches [S1] exactly
  - charter: acceptance criteria 1
done_when: |
  Section 2 correctly states what Federal Order 2222-B does and does not
  govern, tagged [S1], without discussing specific state remedies.

### B004 — Section 3.1: Interconnection queue mechanics
type: compose
budget: 1200w
depends_on: [B001, B003]
inputs:
  - CHARTER.md
  - batches/B001.md
  - batches/B003.md
  - sources/state-survey-2026.md
  - sources/utility-interconnection-timelines.md
intent: |
  Explain, mechanically, how a battery interconnection application moves
  through a state queue: fast-track screening, supplemental review triggers,
  and where utility-reported queue data shows time actually accumulates.
  This is descriptive, not prescriptive — remedies come in Section 5.
produces:
  - section: "3.1 Interconnection Queue Mechanics"
  - term: "supplemental review" defined
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["3.1 Interconnection Queue Mechanics"]
  - mechanical: no_placeholders
  - mechanical: citation_tags
  - mechanical: no_conclusion
  - source: queue-stage claims traceable to [S2] or [S3]
  - charter: acceptance criteria 2
done_when: |
  The section names every queue stage and cites the utility-reported time
  data ([S3]) for the stage that adds the most delay.

### B005 — Section 3.2: Cost allocation methods
type: compose
budget: 1200w
depends_on: [B004]
inputs:
  - CHARTER.md
  - batches/B004.md
  - sources/cost-benefit-model-notes.md
intent: |
  Describe the three cost-allocation methods (applicant-pays,
  socialized-through-rates, hybrid threshold) at the level of mechanics only:
  who pays what, when. Clearly separate the illustrative modeling
  assumptions in the source memo from any observed data, per charter
  non-negotiable 4.
produces:
  - section: "3.2 Cost Allocation Methods"
  - term: "hybrid threshold" defined
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["3.2 Cost Allocation Methods"]
  - mechanical: no_placeholders
  - mechanical: citation_tags
  - mechanical: no_conclusion
  - source: every dollar figure from [S5] is flagged as an illustrative
    modeling assumption, not fact
  - charter: acceptance criteria 4
done_when: |
  All three cost-allocation methods are named and explained, and every
  [S5]-sourced figure is explicitly marked illustrative.

### B006 — Section 3.3: Technical standards (IEEE 1547)
type: compose
budget: 1100w
depends_on: [B004]
inputs:
  - CHARTER.md
  - batches/B004.md
  - sources/ferc-order-2222-summary.md
intent: |
  Explain how technical interconnection standards (referencing IEEE 1547 as
  the governing standard family) interact with queue processing time:
  certified equipment fast paths, and where non-certified or novel
  configurations trigger the supplemental review described in 3.1.
produces:
  - section: "3.3 Technical Standards"
  - term: "certified equipment fast path" defined
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["3.3 Technical Standards"]
  - mechanical: no_placeholders
  - mechanical: citation_tags
  - mechanical: no_conclusion
  - charter: acceptance criteria 2
done_when: |
  The section explains the certified-equipment fast path and how it
  connects back to the supplemental-review concept from Section 3.1.

### B007 — Section 4.1: Case study — shared-queue priority
type: compose
budget: 1200w
depends_on: [B001]
inputs:
  - CHARTER.md
  - batches/B001.md
  - sources/case-studies-vermont-hawaii.md
intent: |
  Present the shared-savings queue-priority composite case study: what the
  state did, the 18-month results, and the cross-subsidy tradeoff. State the
  tradeoff plainly per charter non-negotiable 5; do not editorialize about
  whether the tradeoff was worth it.
produces:
  - section: "4.1 Case Study: Shared-Queue Priority"
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["4.1 Case Study: Shared-Queue Priority"]
  - mechanical: no_placeholders
  - mechanical: citation_tags
  - mechanical: no_conclusion
  - source: all figures traceable to [S4]
  - charter: acceptance criteria 3
done_when: |
  The case study states the 18-month results and the cross-subsidy tradeoff,
  both tagged [S4].

### B008 — Section 4.2: Case study — hosting-capacity maps
type: compose
budget: 1200w
depends_on: [B001]
inputs:
  - CHARTER.md
  - batches/B001.md
  - sources/case-studies-vermont-hawaii.md
intent: |
  Present the hosting-capacity-map composite case study: what the state
  required, the reduction in withdrawn applications and queue time, and the
  rate-case delay tradeoff before the map went live.
produces:
  - section: "4.2 Case Study: Hosting-Capacity Maps"
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["4.2 Case Study: Hosting-Capacity Maps"]
  - mechanical: no_placeholders
  - mechanical: citation_tags
  - mechanical: no_conclusion
  - source: all figures traceable to [S4]
  - charter: acceptance criteria 3
done_when: |
  The case study states the withdrawal/queue-time improvement and the
  rate-case delay tradeoff, both tagged [S4].

### B009 — Section 4.3: Comparative analysis
type: compose
budget: 1300w
depends_on: [B007, B008]
inputs:
  - CHARTER.md
  - batches/B007.md
  - batches/B008.md
intent: |
  Compare the two case studies directly: which problem each solves best,
  what they cost to build, and under what state conditions (utility
  structure, existing data infrastructure) one approach fits better than the
  other. This section may reference figures already stated in 4.1/4.2
  without re-deriving them.
produces:
  - section: "4.3 Comparative Analysis"
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["4.3 Comparative Analysis"]
  - mechanical: no_placeholders
  - mechanical: no_conclusion
  - charter: acceptance criteria 3
done_when: |
  The section names at least one condition favoring each approach and does
  not restate the case study narratives at length.

### B010 — Section 5.1: Model legislation options
type: compose
budget: 1300w
depends_on: [B005, B006]
inputs:
  - CHARTER.md
  - batches/B005.md
  - batches/B006.md
intent: |
  Draft plain-language descriptions of model legislative options covering
  cost allocation and technical fast-track thresholds, framed strictly as
  options a legislature could choose among, per charter non-negotiable 3 —
  never as a recommendation.
produces:
  - section: "5.1 Model Legislation Options"
  - term: "model legislation option" defined
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["5.1 Model Legislation Options"]
  - mechanical: no_placeholders
  - mechanical: no_conclusion
  - mechanical: forbidden_phrases ["we recommend", "states should adopt", "the best option"]
  - charter: acceptance criteria 4
done_when: |
  At least three model legislative options are described as options, with no
  option framed as the report's recommendation.

### B011 — Section 5.2: Rate design and cost recovery
type: compose
budget: 1200w
depends_on: [B005]
inputs:
  - CHARTER.md
  - batches/B005.md
  - sources/cost-benefit-model-notes.md
intent: |
  Explain how each cost-allocation method interacts with rate design and
  ratepayer cost recovery, separating observed program costs (from the
  Vermont-style case in [S4]) from the illustrative [S5] modeling figures.
produces:
  - section: "5.2 Rate Design and Cost Recovery"
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["5.2 Rate Design and Cost Recovery"]
  - mechanical: no_placeholders
  - mechanical: citation_tags
  - mechanical: no_conclusion
  - charter: acceptance criteria 4
done_when: |
  The section distinguishes observed program costs from illustrative
  modeling figures explicitly, each correctly tagged.

### B012 — Section 5.3: Implementation timeline
type: compose
budget: 1000w
depends_on: [B010, B011]
inputs:
  - CHARTER.md
  - batches/B010.md
  - batches/B011.md
intent: |
  Lay out a realistic multi-year implementation timeline for a state
  adopting one of the model legislation options, including the rate-case and
  system-build lead times documented in the case studies.
produces:
  - section: "5.3 Implementation Timeline"
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["5.3 Implementation Timeline"]
  - mechanical: no_placeholders
  - mechanical: no_conclusion
  - charter: acceptance criteria 4
done_when: |
  The timeline names at least three sequential phases with approximate
  durations grounded in the case-study lead times.

### B013 — Section 6: Stakeholder risk analysis
type: compose
budget: 1300w
depends_on: [B009, B010]
inputs:
  - CHARTER.md
  - batches/B009.md
  - batches/B010.md
intent: |
  Analyze how each stakeholder group (distribution utilities, applicants,
  ratepayers not participating, state regulators) is affected by the model
  legislation options, naming risks each group would raise.
produces:
  - section: "6. Stakeholder Risk Analysis"
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["6. Stakeholder Risk Analysis"]
  - mechanical: no_placeholders
  - mechanical: no_conclusion
  - charter: acceptance criteria 4
done_when: |
  Each of the four stakeholder groups has at least one named risk tied to a
  specific model legislation option.

### B014 — Appendix A: Data tables and methodology notes
type: research
budget: 8items
depends_on: [B001]
inputs:
  - sources/state-survey-2026.md
  - sources/utility-interconnection-timelines.md
  - sources/cost-benefit-model-notes.md
intent: |
  Compile the appendix: the underlying data tables referenced across the
  report and a short methodology note on how the survey and utility data
  were gathered, so a reader can check any figure back to its source table.
produces:
  - section: "Appendix A"
verify:
  - mechanical: item_count within 20% of budget
  - mechanical: no_placeholders
  - source: every reproduced data table is captioned with the [S#] source file it was reproduced from
done_when: |
  The appendix reproduces every data table cited in Sections 3-5 and states
  the survey methodology in one paragraph.

### B015 — Consistency and terminology audit
type: revise
budget: 1500w
depends_on: [B002, B003, B004, B005, B006, B007, B008, B009, B010, B011, B012, B013, B014]
inputs:
  - CHARTER.md
  - carry.md
  - batches/B002.md
  - batches/B003.md
  - batches/B004.md
  - batches/B005.md
  - batches/B006.md
  - batches/B007.md
  - batches/B008.md
  - batches/B009.md
  - batches/B010.md
  - batches/B011.md
  - batches/B012.md
  - batches/B013.md
  - batches/B014.md
intent: |
  Read every body section end to end and produce a consistency memo: every
  terminology-lock violation found (file and line), every place two sections
  repeat the same statistic or claim at length, and any numeric
  contradiction between sections. This memo drives the seam pass at stitch
  time; it does not edit the sections itself.
produces:
  - section: "Consistency Audit Memo"
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: no_placeholders
  - mechanical: forbidden_phrases
done_when: |
  The memo lists every terminology-lock violation found across B002-B014
  with a file and line reference, or states plainly that none were found.

<!-- There is no B016/B017 unit for the executive summary or the
     introduction/conclusion. Front matter (executive summary) and back
     matter (introduction + conclusion) are no longer planned, budgeted
     units in this tool version — they are front-matter.md / back-matter.md,
     written by hand in the seam pass after every body unit is done and
     `stitch` has produced draft.md (SKILL.md move 7, step 5), then included
     by `stitch` automatically on the next run. See WALKTHROUGH.md section 2
     for why this plan no longer carries B016/B017. -->
