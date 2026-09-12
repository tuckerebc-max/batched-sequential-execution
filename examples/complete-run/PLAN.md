# PLAN — Off-Peak Fare Capping at Riverton Transit Authority

## Units

- [x] B001 [research] Build the source catalog — budget: 5items
- [x] B002 [compose] [dep:B001] Section 1: How Off-Peak Fare Capping Works and What Peer Agencies Found — budget: 850w
- [x] B003 [compose] [dep:B001] Section 2: RTA Ridership and Revenue by Time of Day — budget: 850w
- [x] B004 [compose] [dep:B001,B003] Section 3: Equity and Access Implications — budget: 800w
- [x] B005 [compose] [dep:B001,B003] Section 4: Operational and Technical Feasibility — budget: 800w
- [x] B006 [compose] [dep:B003,B004,B005] Section 5: Implementation Options and Tradeoffs — budget: 900w

## Specs

### B001 — Build the source catalog
type: research
budget: 5items (±15%)
depends_on: []
inputs:
  - sources/peer-program-outcomes.md
  - sources/riverton-ridership-data.md
  - sources/farebox-tech-memo.md
  - sources/equity-analysis-notes.md
  - sources/stakeholder-interview-notes.md
intent: |
  Read all five source files in full and produce a one-page annotated
  catalog: for each source, its [S#] tag, a one-line description of what it
  is and covers, and a one-line note on which planned body sections
  (B002-B006) will rely on it. This catalog is the only unit that reads
  every source file in full; every later unit reads only the catalog plus
  the specific source slices its own section needs.
produces:
  - section: "Source Catalog"
  - term: "source catalog" defined
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - mechanical: citation_tags
done_when: |
  The catalog lists all five sources, each with its [S#] tag, a one-line
  description, and at least one downstream section (B002-B006) it feeds.

### B002 — Section 1: How Off-Peak Fare Capping Works and What Peer Agencies Found
type: compose
budget: 850w (±15%)
depends_on: [B001]
inputs:
  - CHARTER.md
  - batches/B001.md
  - sources/peer-program-outcomes.md
intent: |
  Write Section 1. Explain what an off-peak fare cap is and how it differs
  from RTA's current all-day cap in one short framing paragraph, then
  summarize what the three peer agencies (Meridian Transit, Cedar Falls
  Regional Transit, Ashford Regional Transit) actually found when they
  implemented one: the ridership and revenue effects, what each cost and
  took to build, and the one tradeoff each agency's own report names. Do not
  yet discuss RTA's own ridership data (Section 2) or make any
  recommendation about what RTA should do.
produces:
  - section: "1. How Off-Peak Fare Capping Works and What Peer Agencies Found"
  - term: "off-peak fare cap" defined for report use
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["1. How Off-Peak Fare Capping Works and What Peer Agencies Found"]
  - mechanical: no_placeholders
  - mechanical: citation_tags
  - mechanical: no_conclusion
  - source: every ridership, revenue, cost, and date figure attributed to Meridian, Cedar Falls, or Ashford matches [S1] exactly, with no figure invented or altered
  - charter: acceptance criteria 1
done_when: |
  Section 1 defines "off-peak fare cap", states each peer agency's
  ridership/revenue result and one named tradeoff tagged [S1], and does not
  discuss RTA's own data or recommend a course of action.

### B003 — Section 2: RTA Ridership and Revenue by Time of Day
type: compose
budget: 850w (±15%)
depends_on: [B001]
inputs:
  - CHARTER.md
  - batches/B001.md
  - sources/riverton-ridership-data.md
intent: |
  Write Section 2. Describe RTA's current all-day cap mechanics and exactly
  which riders benefit from it (peak-anchored multi-trip riders), then
  present RTA's own day-part ridership and revenue breakdown (AM peak,
  daytime, off-peak) and the spare off-peak seat capacity the system already
  carries. Ground every figure in RTA's FY2026 data. Do not yet discuss
  equity implications (Section 3) or technical feasibility (Section 4).
produces:
  - section: "2. RTA Ridership and Revenue by Time of Day"
  - term: "day-part" defined for report use (AM peak / daytime / off-peak)
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["2. RTA Ridership and Revenue by Time of Day"]
  - mechanical: no_placeholders
  - mechanical: citation_tags
  - mechanical: no_conclusion
  - source: every boardings, revenue, and occupancy figure matches [S2] exactly, and the mechanics of the current all-day cap are described correctly
  - charter: acceptance criteria 2
done_when: |
  Section 2 states the three day-part boardings/revenue figures, explains
  why the current all-day cap mechanically favors peak-anchored riders, and
  states the off-peak seat-occupancy figure, all tagged [S2].

### B004 — Section 3: Equity and Access Implications
type: compose
budget: 800w (±15%)
depends_on: [B001, B003]
inputs:
  - CHARTER.md
  - batches/B001.md
  - batches/B003.md
  - sources/equity-analysis-notes.md
intent: |
  Write Section 3. Using the Equity & Access office's analysis, state who
  is riding off-peak today (reduced-fare/low-income riders at roughly twice
  their system-wide share), why the current all-day cap structurally
  underserves a rider whose only trips are off-peak, and the corridor
  concentration finding. Name the Equity office's own caution about
  non-enrolled-but-eligible riders. Reference Section 2's day-part framing
  without restating its specific boardings and revenue figures verbatim.
  Do not yet discuss technical feasibility or implementation phasing.
produces:
  - section: "3. Equity and Access Implications"
  - term: "reduced-fare rider" defined for report use
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["3. Equity and Access Implications"]
  - mechanical: no_placeholders
  - mechanical: citation_tags
  - mechanical: no_conclusion
  - source: the enrollment share, the off-peak share, and the corridor concentration figures match [S4] exactly, and the office's own caution about unenrolled-eligible riders is preserved, not dropped
  - charter: acceptance criteria 3, 4
done_when: |
  Section 3 states the reduced-fare off-peak share, explains structurally
  why the all-day cap underserves off-peak-only riders, names the four
  concentrated corridors, and carries forward the Equity office's caution
  about unenrolled-eligible riders, all tagged [S4].

### B005 — Section 4: Operational and Technical Feasibility
type: compose
budget: 800w (±15%)
depends_on: [B001, B003]
inputs:
  - CHARTER.md
  - batches/B001.md
  - batches/B003.md
  - sources/farebox-tech-memo.md
intent: |
  Write Section 4. Explain how RTA's RiverPass fare system currently
  evaluates the all-day cap (nightly batch, not real time) and why a
  time-of-day cap needs cap evaluation moved into the real-time
  authorization path. Present both options the fare-system vendor scoped —
  the real-time option and the lower-cost interim batch-credit option — with
  each one's cost, timeline, and rider-experience tradeoff, and note that
  spare off-peak capacity (Section 2) removes crowding as a constraint. Do
  not yet discuss implementation phasing or sequencing (Section 5).
produces:
  - section: "4. Operational and Technical Feasibility"
  - term: "real-time authorization path" defined for report use
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["4. Operational and Technical Feasibility"]
  - mechanical: no_placeholders
  - mechanical: citation_tags
  - mechanical: no_conclusion
  - source: the cost, timeline, and mechanism described for both the real-time and interim options match [S3] exactly
  - charter: acceptance criteria 4
done_when: |
  Section 4 explains the current batch-versus-real-time constraint and
  states both options' cost and timeline figures, tagged [S3], without
  recommending which option RTA should choose.

### B006 — Section 5: Implementation Options and Tradeoffs
type: compose
budget: 900w (±15%)
depends_on: [B003, B004, B005]
inputs:
  - CHARTER.md
  - batches/B004.md
  - batches/B005.md
  - sources/stakeholder-interview-notes.md
intent: |
  Write Section 5, the final body section. Lay out at least two concrete
  phasing options for how RTA could roll out an off-peak cap — for example,
  a system-wide launch versus a corridor-first pilot targeting the highest
  reduced-fare-concentration corridors from Section 3 — and fold in what the
  driver union, RTA Access, and Finance said: the union's advance-notice
  requirement, the Access boundary question, and Finance's preference for
  testing the revenue assumption before the full technology spend. Present
  the options as options the Board could choose among; do not state which
  one RTA should adopt or use any concluding language — the recommendation
  belongs to the conclusion, written separately in the seam pass.
produces:
  - section: "5. Implementation Options and Tradeoffs"
  - term: "corridor-first pilot" named as one implementation option
verify:
  - mechanical: word_count within 15% of budget
  - mechanical: contains_headings ["5. Implementation Options and Tradeoffs"]
  - mechanical: no_placeholders
  - mechanical: citation_tags
  - mechanical: no_conclusion
  - source: the union's notice requirement, the Access boundary point, and Finance's phasing preference are each attributed correctly to [S5] and not merged or misattributed
  - charter: acceptance criteria 5
done_when: |
  Section 5 names at least two phasing options, attributes each
  stakeholder's position correctly to [S5], and does not declare either
  option RTA's decision.
