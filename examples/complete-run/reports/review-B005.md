# Reviewer report — B005 — Section 4: Operational and Technical Feasibility

Reviewer inputs: briefs/B005.md and batches/B005.md (the version recorded
after fix round 1/3 — see LEDGER.md), cross-checked against
sources/farebox-tech-memo.md [S3]. No other unit's text was read.

## Predicates

PREDICATE: source: the cost, timeline, and mechanism described for both the
real-time and interim options match [S3] exactly
VERDICT: PASS
EVIDENCE: "quoted at $410,000 and a nine-month delivery timeline from
contract signature" and the breakdown "two months of vendor development,
three months of RTA-side integration testing... and a recommended
four-month phased rollout across RTA's roughly 340 buses and 22 light-rail
vehicles" matches [S3] exactly. "$85,000 and three months, because it
changes only the batch job's refund rule" matches [S3]. The batch-versus-
real-time mechanism — "the batch job only reconciles a rider's cumulative
daily taps after the fact — it has no way of knowing, at the moment a given
tap happens, whether that tap falls inside or outside the off-peak window"
— correctly restates [S3]'s explanation without simplifying away the actual
constraint.

PREDICATE: charter: acceptance criteria 4
VERDICT: PASS
EVIDENCE: Criterion 4 requires the section to distinguish the real-time and
interim options with their respective costs and timelines; both are stated
individually with figures and neither is recommended over the other — the
section ends by naming the choice as "a question of implementation choices,
not fare-system capability" rather than answering it.

## Findings

FINDING: none remaining. Note for the record: the first drafted version of
this artifact failed `bse.py check` on two grounds — three closing-paragraph
figures ($410,000 / $85,000 / $325,000) restated without their own [S#] tags,
and the section running 570 words against an 800w budget — and was corrected
in fix round 1/3 (see LEDGER.md and reports/B005.md) before this review. The
corrected artifact under review here has no outstanding citation gaps.
SEVERITY: Minor
EVIDENCE: reports/B005.md shows the mechanical result as PASS (5/5) on the
artifact reviewed.

Summary: 0 Critical, 0 Important findings. Both predicates PASS.
