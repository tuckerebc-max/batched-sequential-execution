# BSE per-run record

Copy for each actual use; leave unknown measurements as `unavailable` with a reason. This blank template records no completed use or trial. Refer to [EVALUATION.md](EVALUATION.md) for the rubric.

- Run/task ID, date, task class, and authorization reference:
- Executor account/seat and session ID; artifact and record paths:
- Status (running / completed / blocked / abandoned), with acceptance evidence:
- Natural unit count; suitability/exclusions checked; light/full mode and trigger:
- Pilot number (first three suitable authorized uses are pilots; otherwise later use):
- Shared completion count before/after; deduplicated completion sequence (one task, not batches):
- Package commit; method revision and what changed:
- Frozen brief, source packet/version or hashes, requirement IDs, acceptance criteria:
- Output budget; model/version/settings and tools actually observable (unknowns stated):
- Upfront correction and time allowances; practical comparison target:
- First submitted and final artifact paths/hashes; light notes or full ledger/check/review evidence:
- Mode deviations, failed checks, blocked units, approval denials, and unresolved findings:

Use the protocol's 0/1/2 anchors for fidelity, completeness, and coherence. Record evidence and denominators, not just scores. Include unit and seam repairs in effort.

| Dimension | First submitted | Final | Evidence / counts / limits |
|---|---|---|---|
| Source/requirement fidelity | | | Supported/checked claims; deviations; sampling rule |
| Completeness | | | Met/total criteria; missing IDs |
| Cross-batch coherence | | | Defects/seams inspected; conflict locations |
| Correction effort | | | Rounds, affected units, measured repair minutes, unresolved findings |
| Time/token overhead | | | UTC start/end, elapsed, non-overlapping active phases and waits; tokens if measured |

- Usage/cost telemetry source and coverage; input/output/cached/reasoning tokens if exposed; actual cost if supplied, otherwise `unavailable` (no inferred subscription cost):
- Timing coverage/gaps; authoring versus coordination, checking, correction and evaluation costs; allowance exceeded and why:
- Assessor account/seat, separate commissioned-session ID, report path, and artifact hashes reviewed:
- Assessor authored either artifact? Independent assessment complete or pending, with reason. Same author's self-review is not independent, even if labeled a reviewer pass.

**Matched comparison checkpoint:** recommend a comparison at every third completed suitable use and after a meaningful method revision. Comparisons must fit task authorization and available capacity; otherwise mark pending. Preserve failed or abandoned pairs.

- Trigger (completion 3/6/9… or meaningful revision); recommendation/date:
- Comparison ID and status (not due / recommended, pending / running / completed):
- Authorized bounded safe subtask; natural unit count (at least five for BSE), capacity/time cap:
- Same frozen brief, source packet, output budget, model/settings, acceptance and review criteria for both arms; list any mismatch:
- Arm A/B mapping: BSE mode versus ordinary unbatched workflow; fresh sessions, execution order, session IDs, and prevention of cross-arm artifact exposure:
- Predeclared target and stop rule; first submitted/final output paths and hashes for both arms:
- Non-author assessor in a separate commissioned-seat session; blind A/B labels where practical; report/session ID:

| Paired result | BSE | Ordinary baseline | Difference and evidence |
|---|---|---|---|
| Fidelity / completeness / coherence | | | |
| Repair rounds / minutes / unresolved findings | | | |
| Elapsed / active / waiting / method and evaluation time | | | |
| Measured tokens / cost, or unavailable | | | |

- Missing authorization, capacity, matching, or independent assessment: record **pending**, reason, and next authorized opportunity. Do not call a self-reviewed pair an independently completed comparison.
- Completed comparison requires both arms, matched conditions, acceptance results (including failures), measured records, and the independent report. Unavailable usage/cost may remain unavailable.
- Decision: retain / narrow / revise / pause for this task class; evidence, tradeoffs, and next change:
- Limits: first three uses are pilots; small selected samples, order effects, reviewer variation and model drift constrain inference. No automatic superiority claim. No polling heartbeat or uncommissioned dispatch follows this record.
