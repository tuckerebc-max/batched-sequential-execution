# CHARTER — <deliverable title>

<!--
This is the contract for one BSE run. Every batch reads this file. Keep it to
one page — every unit pays the reading cost. Nine sections below, all
required: eight are checked structurally by the tool (DESIGN.md §2.1);
Through-line is required by SKILL.md but not currently scaffolded or checked
by `bse.py` itself, so don't rely on `plan --validate` to catch a missing one
— check it yourself. `bse.py plan --validate` checks the budget-sum rule
against the "Total size" line and parses the terminology lock, so keep both
in one of the two shapes shown.
-->

## Deliverable
What: <one sentence: the finished thing>
Format: <markdown | docx | pptx | xlsx | pdf — rendered last via the format skill>
Total size: <n><unit>  <!-- e.g. 20000w, 80slides, 30files — bse.py reads this exact "Total size:" line to check budget drift. Name more than one denomination if the deliverable mixes types, e.g. "20000w, 12slides" — each is tracked and drift-checked separately. -->

## Through-line
<!-- One sentence: what the finished thing ARGUES or ESTABLISHES — not what
it covers. This is the one line that goes into every brief verbatim, and the
one thing the seam pass checks for before doing any local repair (see
stitching-and-seams.md step 0): a document assembled from N blind pieces can
pass every mechanical check and still not add up to anything, because no
single unit was ever responsible for the whole making its case. If you can't
state this in one sentence yet, the charter isn't ready to plan against. -->
<one sentence: what a reader should be able to say the finished thing established, that they couldn't say before reading it>

## Audience
<Who reads this, and what they already know. One or two sentences — this
governs register and how much you can assume without explaining.>

## Voice & register
<Two sentences: person (first/third), formality, tense, any house style to
imitate or avoid.>

## Non-negotiables
<!-- Numbered. Each one must be testable — a fact about the artifact you could
check, not a vibe. "Be professional" is not testable; "no first-person voice"
is. -->
1. <requirement, phrased so a stranger could check it>
2. <requirement>

## Terminology lock
<!-- The anti-drift dictionary: wrong form -> approved form. bse.py's own
`init` scaffold writes this as a bullet list, one pair per line — that's the
canonical shape and what's shown below. A markdown table is also accepted
(`| wrong | right |` rows, with a header row whose first cell is literally
"Wrong form" or similar — the parser skips that row rather than treating it
as a pair) if you'd rather read it that way; don't mix the two forms in one
charter. Either shape feeds a free mechanical verifier (forbidden_phrases)
and the stitch-time terminology check. -->
- <term as it tends to drift> -> <the one approved form>

## Sources of truth
<!-- Give every source an [S#] id. Units cite these ids; the citation_tags
verifier and any "source:" predicate rely on the id existing here. -->
- [S1] <path or URL> — <what it is, in a few words>

## Acceptance criteria
<!-- Numbered. Each one is a predicate — something a verifier or a reviewer
can find true or false against the finished draft, not an intention. Units'
"charter:" verify lines reference these numbers directly. -->
1. <criterion, phrased as a testable predicate>
2. <criterion>

## Out of scope
- <thing this deliverable explicitly does not cover, so no unit tries to>

---
## Example

# CHARTER — Q3 Infrastructure Reliability Report

## Deliverable
What: A 20,000-word internal report on Q3 infrastructure incidents and the
remediation plan.
Format: markdown, rendered last via the format skill (docx)
Total size: 20000w

## Through-line
Q3's incident pattern was concentrated in one root cause (the CDN migration),
not evenly distributed across systems, and the remediation plan should be
funded and sequenced accordingly.

## Audience
VP Engineering and the infra leads who will fund the remediation plan. They
know the systems; they do not know the incident timelines in detail.

## Voice & register
Third person, present tense for current state, past tense for incidents.
Plain, direct, no hedging language.

## Non-negotiables
1. Every incident date and duration figure carries a source citation.
2. No recommendation appears without a named owner and a quarter.

## Terminology lock
- downtime event -> incident
- SLA breach -> SLO violation

## Sources of truth
- [S1] incidents/2026-q3-log.csv — raw incident log, timestamps in UTC
- [S2] interviews/sre-notes.md — SRE lead interview notes, Aug 2026

## Acceptance criteria
1. Every incident in [S1] with severity >= 2 appears in the report body.
2. Total word count is within 20% of 20,000.
3. Every recommendation names an owning team and a target quarter.

## Out of scope
- Cost modeling for the remediation plan (tracked separately in FIN-118).
