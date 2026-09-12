# PLAN — The Last Utility, Feedback Sweep

Units are grouped by manuscript region (chapter or sub-chapter section), not
by comment order, and run serially in reading order so `carry.md` can carry
forward decisions (a chosen term, a resolved ambiguity) the way a reader
moving through the book would encounter them. See WALKTHROUGH.md section 2
for why region-grouping beats comment-order grouping here.

## Units

- [x] B001 [revise] Front Matter feedback (items 1-7) — budget: 7items
- [x] B002 [revise] [dep:B001] Ch1 feedback (items 8-17) — budget: 10items
- [x] B003 [revise] [dep:B002] Ch2.1 feedback (items 18-24) — budget: 7items
- [x] B004 [revise] [dep:B003] Ch2.2 feedback (items 25-30) — budget: 6items
- [x] B005 [revise] [dep:B004] Ch3.1 feedback (items 31-38) — budget: 8items
- [x] B006 [revise] [dep:B005] Ch3.2 feedback (items 39-46) — budget: 8items
- [ ] B007 [revise] [dep:B006] Ch4 feedback (items 47-55) — budget: 9items
- [ ] B008 [revise] [dep:B007] Ch5.1 feedback (items 56-62) — budget: 7items
- [ ] B009 [revise] [dep:B008] Ch5.2 feedback (items 63-69) — budget: 7items
- [ ] B010 [revise] [dep:B009] Ch6.1 feedback (items 70-75) — budget: 6items
- [ ] B011 [revise] [dep:B010] Ch6.2 feedback (items 76-81) — budget: 6items
- [ ] B012 [revise] [dep:B011] Ch7.1 feedback (items 82-89) — budget: 8items
- [ ] B013 [revise] [dep:B012] Ch7.2 feedback (items 90-96) — budget: 7items
- [ ] B014 [revise] [dep:B013] Ch8 feedback (items 97-104) — budget: 8items
- [ ] B015 [revise] [dep:B014] Ch9/Conclusion feedback (items 105-114) — budget: 10items
- [ ] B016 [revise] [dep:B015] Back Matter feedback (items 115-120) — budget: 6items
- [ ] B017 [assemble] [dep:B001,B002,B003,B004,B005,B006,B007,B008,B009,B010,B011,B012,B013,B014,B015,B016] Final resolution log and reconciliation — budget: 1files

## Specs

### B001 — Front Matter feedback (items 1-7)
type: revise
budget: 7items
depends_on: []
inputs:
  - CHARTER.md
  - sources/reviewer-feedback-log.md#L1-7
  - sources/manuscript-ch1-9-excerpt.md
intent: |
  Resolve all seven feedback items on the Preface & Introduction: sharpen
  the opening hook, name the four case-study towns on first mention,
  ground the thesis in a concrete early figure, verify the electrification
  analogy isn't overstated, fix the "public works" italicization
  inconsistency, clarify the "four towns" framing, and note the
  school-bus-anecdote callback for whoever handles the conclusion (B015).
produces:
  - item: "resolution log, Front Matter, 7 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 7 items (#001-#007) show a logged resolution: applied (with what
  changed) or ruled out (with a one-line reason).

### B002 — Ch1 feedback (items 8-17)
type: revise
budget: 10items
depends_on: [B001]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L8-17
  - sources/manuscript-ch1-9-excerpt.md
intent: |
  Resolve the ten Chapter 1 items: fact-check the cooperative founding-era
  figures, tighten the historical section, define "cooperative" for lay
  readers, standardize "co-op"/"cooperative" per the terminology lock, fix
  the Chapter 2 preview error, add the plain-language summary and the
  forward-pointer to where the electrification analogy breaks down, fix
  the capitalization inconsistency, and trim the closing section's
  near-duplicate of the preface thesis (coordinate with B001's resolution
  so nothing is trimmed twice).
produces:
  - item: "resolution log, Ch1, 10 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - mechanical: forbidden_phrases
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 10 items (#008-#017) show a logged resolution, and the terminology
  lock's "co-op -> cooperative" form is applied everywhere in this chapter.

### B003 — Ch2.1 feedback (items 18-24)
type: revise
budget: 7items
depends_on: [B002]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L18-24
intent: |
  Resolve the seven items on 2.1 (incumbent-response origins): add a date
  anchor, soften the "uniformly opposed" overstatement per the
  fact-checker, add a concrete incumbent quote or filing excerpt, vary the
  incumbent noun/adjective repetition, smooth the transition from Chapter
  1, confirm the lobbying-tactics claim is attributed to reporting (not
  asserted), and decide whether the section needs one more example.
produces:
  - item: "resolution log, Ch2.1, 7 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 7 items (#018-#024) show a logged resolution, and the
  attribution-vs-assertion fact-check (#023) is resolved with a specific
  citation or a specific rewording, not a general assurance.

### B004 — Ch2.2 feedback (items 25-30)
type: revise
budget: 6items
depends_on: [B003]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L25-30
intent: |
  Resolve the six items on 2.2 (the statehouse floor fight): clarify early
  momentum, verify the vote-margin figure, consider a present-tense pass
  for immediacy, standardize "statehouse" per the terminology lock, state
  the vote's outcome unambiguously, and weigh trimming 2.1 or 2.2 for
  Chapter 2's overall length relative to Chapter 1.
produces:
  - item: "resolution log, Ch2.2, 6 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - mechanical: forbidden_phrases
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 6 items (#025-#030) show a logged resolution, and the vote's outcome
  is stated in one unambiguous sentence in the chapter text.

### B005 — Ch3.1 feedback (items 31-38)
type: revise
budget: 8items
depends_on: [B004]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L31-38
  - sources/manuscript-ch1-9-excerpt.md
intent: |
  Resolve the eight items on 3.1 (Harlow County's founding): add the
  one-sentence recap, verify the board-vote year, explain what "pivot into
  fiber" involved operationally, add an internal-obstacle beat so the
  section is not uncritically positive, standardize "build-out"
  hyphenation, clarify the fiber subsidiary's legal-entity status, and
  mark the membership-count figure as approximate if uncited.
produces:
  - item: "resolution log, Ch3.1, 8 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 8 items (#031-#038) show a logged resolution, including a specific
  internal-obstacle addition (#034) rather than a note that none exists.

### B006 — Ch3.2 feedback (items 39-46)
type: revise
budget: 8items
depends_on: [B005]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L39-46
  - sources/manuscript-ch1-9-excerpt.md
intent: |
  Resolve the eight items on 3.2 (financing and attribution). Item #043 is
  a legal beta reader's request to anonymize the cooperative's former
  finance director given a since-arisen litigation risk. This directly
  contradicts charter non-negotiable 2 (named, on-the-record sources keep
  full attribution) and is not this unit's call to make: if execution
  reaches #043, stop, do not apply or silently reject it, and record the
  unit `blocked` with the conflict stated plainly so a human can issue a
  RULING. The other seven items (financing-before-names ordering, the
  bond-financing fact-check, a lay-reader summary, the
  financing/funding-distinction copyedit, keeping the interview material,
  the build-out cost fact-check, and the Chapter 4 bridge) can and should
  be resolved independently of #043's outcome.
produces:
  - item: "resolution log, Ch3.2, 8 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  Items #039-#042 and #044-#046 show a logged resolution; #043 shows
  either a resolution consistent with a recorded RULING, or a `blocked`
  ledger entry naming the charter conflict if no RULING has issued yet.

### B007 — Ch4 feedback (items 47-55)
type: revise
budget: 9items
depends_on: [B006]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L47-55
intent: |
  Resolve the nine items on Chapter 4 (Cedar Bend's failed bond measure):
  add the explicit contrast to Harlow County's outcome, verify the vote
  margin, explain what the bond would have funded, standardize
  "referendum" vs. "ballot measure," name what Cedar Bend might have done
  differently, weigh adding a resident perspective, verify the
  counter-campaign spending figure, add the Chapter 6 forward pointer, and
  fix the title/running-head punctuation mismatch.
produces:
  - item: "resolution log, Ch4, 9 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 9 items (#047-#055) show a logged resolution, and the Harlow
  County / Cedar Bend contrast is stated in the chapter's opening, not
  only implied.

### B008 — Ch5.1 feedback (items 56-62)
type: revise
budget: 7items
depends_on: [B007]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L56-62
intent: |
  Resolve the seven items on 5.1 (the Rural Connectivity Fund): introduce
  the program's stated purpose before its mechanics, verify the
  award-range figures, reformat the application process as a numbered
  list, fix the inconsistent abbreviation, decide whether a fifth
  contrasting (denied-applicant) town is added, verify the
  application-to-award timeline against Chapter 3's figure for
  consistency, and confirm the transition into 5.2 still reads well
  however the fifth-town question is resolved.
produces:
  - item: "resolution log, Ch5.1, 7 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - mechanical: forbidden_phrases
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 7 items (#056-#062) show a logged resolution, and the fifth-town
  decision (add or don't) is stated explicitly so B009 does not
  independently guess the same question for 5.2.

### B009 — Ch5.2 feedback (items 63-69)
type: revise
budget: 7items
depends_on: [B008]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L63-69
intent: |
  Resolve the seven items on 5.2 (state matching funds): state which
  states require matching funds up front, verify the "typical" matching
  percentage, add the one-sentence reminder of 5.1's terms, standardize
  "matching funds" per the terminology lock, apply the same fifth-town
  decision B008 recorded (do not re-decide it), verify the
  "within two years" timing claim, and confirm the two sections balance.
produces:
  - item: "resolution log, Ch5.2, 7 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - mechanical: forbidden_phrases
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 7 items (#063-#069) show a logged resolution, consistent with
  whatever B008 decided about the fifth-town addition.

### B010 — Ch6.1 feedback (items 70-75)
type: revise
budget: 6items
depends_on: [B009]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L70-75
intent: |
  Resolve the six items on 6.1 (rate-design fights): explain up front why
  a fiber utility's rate design differs from an electric utility's, verify
  the composite rate figures, define "ratepayer" on first use, standardize
  "rate design" per the terminology lock, add a concrete household-bill
  figure, and verify the cross-subsidy claim or mark it as characterized
  rather than established.
produces:
  - item: "resolution log, Ch6.1, 6 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - mechanical: forbidden_phrases
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 6 items (#070-#075) show a logged resolution, and "ratepayer" is
  defined on its first use in this chapter.

### B011 — Ch6.2 feedback (items 76-81)
type: revise
budget: 6items
depends_on: [B010]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L76-81
intent: |
  Resolve the six items on 6.2 (public-meeting backlash): trim one of the
  three composite meetings for pacing, check the scenes don't read as
  dismissive of residents, mark attendance figures as illustrative per the
  case-notes convention, standardize "public meeting" per the terminology
  lock, add a supportive resident quote to avoid one-sided framing, and
  confirm the bridge into Chapter 7 still works after the trim.
produces:
  - item: "resolution log, Ch6.2, 6 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - mechanical: forbidden_phrases
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 6 items (#076-#081) show a logged resolution, and the trim decision
  from #076 is reflected consistently in how #081's bridge is evaluated.

### B012 — Ch7.1 feedback (items 82-89)
type: revise
budget: 8items
depends_on: [B011]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L82-89
intent: |
  Resolve the eight items on 7.1 (Fenwick Falls' takeover vote): open with
  the specific motivating problem, verify the acquisition price, explain
  what "municipal takeover" means operationally, fix the hyphenation
  inconsistency, cross-check the vote-margin figure against the
  introduction if repeated there, verify the incumbent's stated
  divestment reason, preserve this section's length per the beta reader's
  note, and add the forward-pointing sentence into 7.2.
produces:
  - item: "resolution log, Ch7.1, 8 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 8 items (#082-#089) show a logged resolution, and the vote-margin
  cross-check (#086) explicitly states whether the introduction repeats
  the figure and, if so, that both instances now agree.

### B013 — Ch7.2 feedback (items 90-96)
type: revise
budget: 7items
depends_on: [B012]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L90-96
intent: |
  Resolve the seven items on 7.2 (aftermath): open with a concrete
  first-week detail, verify the complaint figures, add an acknowledgment
  of transition service hiccups, standardize "eighteen months" per house
  style, soften the closing line's editorializing to match the book's
  register, verify the post-takeover rate figure against Chapter 6, and
  confirm nothing further is needed given the beta reader called this the
  strongest case study.
produces:
  - item: "resolution log, Ch7.2, 7 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 7 items (#090-#096) show a logged resolution, and the rate-figure
  cross-check (#095) confirms agreement with Chapter 6 or flags the
  discrepancy for the reconciliation pass.

### B014 — Ch8 feedback (items 97-104)
type: revise
budget: 8items
depends_on: [B013]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L97-104
intent: |
  Resolve the eight items on Chapter 8 (post-grant sustainability): name
  the chapter's guiding question explicitly, verify the grant-duration
  claim, add a concrete example to balance the academic register,
  standardize "post-grant" hyphenation, reference all four case-study
  towns by name, cross-check Fenwick Falls' operating-cost figures against
  Chapter 7, consider a fifth "did not achieve sustainability" example,
  and confirm the chapter still sets up Chapter 9.
produces:
  - item: "resolution log, Ch8, 8 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 8 items (#097-#104) show a logged resolution, and all four
  case-study towns are confirmed named at least once in this chapter.

### B015 — Ch9/Conclusion feedback (items 105-114)
type: revise
budget: 10items
depends_on: [B014]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L105-114
intent: |
  Resolve the ten items on Chapter 9/Conclusion: return to the preface's
  school-bus anecdote (coordinating with what B001 logged about it), keep
  the conclusion free of new factual claims not established earlier,
  state the intended audience for the "lessons" framing, verify all four
  town names are spelled consistently with their first use, resolve the
  new-claim-about-legislative-trends issue by cutting it or relocating its
  support, keep the strong closing paragraph, verify any summary-statistics
  table against per-chapter figures, consider the town-council
  practical-takeaways list, and align "next decade" vs. "coming decade."
produces:
  - item: "resolution log, Ch9/Conclusion, 10 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - mechanical: forbidden_phrases
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 10 items (#105-#114) show a logged resolution, and the school-bus
  callback (#105) is confirmed consistent with B001's Front Matter
  resolution rather than independently reinvented.

### B016 — Back Matter feedback (items 115-120)
type: revise
budget: 6items
depends_on: [B015]
inputs:
  - CHARTER.md
  - carry.md
  - sources/reviewer-feedback-log.md#L115-120
intent: |
  Resolve the six Back Matter items: thank interview subjects by name
  consistent with the in-chapter attribution standard (cross-referencing
  whatever B006 decided about item #043), standardize the interview-list
  formatting, cross-check the interview list against every subject named
  in the chapters, weigh moving the methodology note earlier, and align
  the appendix citation format with the in-chapter [S#] convention.
produces:
  - item: "resolution log, Back Matter, 6 items"
verify:
  - mechanical: item_count within 15% of budget
  - mechanical: no_placeholders
  - source: each resolution's stated action, checked against its numbered item's exact text in sources/reviewer-feedback-log.md, accurately reflects what that item asked for
done_when: |
  All 6 items (#115-#120) show a logged resolution, and the
  interview-subject cross-check (#117) explicitly states whether the
  finance director from #043 is named or handled per that item's eventual
  RULING.

### B017 — Final resolution log and reconciliation
type: assemble
budget: 1files
depends_on: [B001, B002, B003, B004, B005, B006, B007, B008, B009, B010, B011, B012, B013, B014, B015, B016]
inputs:
  - CHARTER.md
  - batches/B001.md
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
  - batches/B015.md
  - batches/B016.md
intent: |
  Concatenate all sixteen per-region resolution logs into one combined
  resolution log (120 items total), and reconcile cross-region decisions
  that depended on each other: the fifth-town question (B008/B009), the
  vote-margin and rate-figure cross-checks (B012/B013 vs. earlier
  chapters), the school-bus callback (B001/B015), and the finance-director
  attribution outcome (B006/B016). Confirm the combined log accounts for
  all 120 items with no gap and no duplicate item number.
produces:
  - file: "resolution-log.md"
verify:
  - mechanical: file_exists resolution-log.md
  - mechanical: no_placeholders
  - charter: acceptance criteria 1, 3, 5
done_when: |
  resolution-log.md exists, lists items #001-#120 exactly once each with a
  resolution, and states the outcome of every cross-region decision named
  above.
