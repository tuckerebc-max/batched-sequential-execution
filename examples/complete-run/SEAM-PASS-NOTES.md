# Seam-pass notes — riverton-fare-cap

What the seam pass actually did to turn `draft.md` (the mechanical
concatenation of six checked, reviewed, recorded units) into `final.md` (the
deliverable). Every item below is a real change; the before/after text is
quoted from the actual files in this directory.

## 0. Through-line check (step 0 of the seam pass)

Read `draft.md` start to end against the charter's through-line: *RTA should
adopt an off-peak fare cap through a phased, corridor-first pilot.* The
argument is present and load-bearing across all five body sections — Section
1 establishes that peer agencies gained ridership without losing
full-fare-equivalent revenue, Section 2 shows RTA has the same spare
off-peak capacity those agencies had, Section 3 identifies the population a
phased, corridor-first design would reach that an enrollment-only or
system-wide design would not, Section 4 supplies the two technology paths a
phased design can sequence between, and Section 5 lays out that sequencing
as Option B among three options. No section states the recommendation
outright (each was checked by the `no_conclusion` mechanical verifier and,
for B006, by its own reviewer pass) — the through-line survives to the
Conclusion intact, which is the only place it is stated as a decision. This
was not a re-plan: no gap was found here.

## 1. Duplicate content removed

`bse.py stitch`'s mechanical dedup check reported **zero** duplicate
sentences (its sentence splitter treats semicolon-joined clauses as one
sentence, and the two units below phrased the repeated idea with different
terminal punctuation, so it fell through). The human read-through in step 0
caught it anyway, and it was already flagged in `reports/review-B004.md`'s
findings section during the unit's own review pass:

- `batches/B003.md` (Section 2) states: *"A rider who taps twice during the
  morning commute reaches the cap on the commute alone and then rides free
  for any trip later that day, including an evening or weekend trip; a
  rider whose only trips fall outside the morning commute never reaches the
  cap on those trips and pays full fare for each one."*
- `batches/B004.md` (Section 3) restated the same mechanic almost verbatim:
  *"a rider who taps twice during the morning commute reaches the cap on the
  commute alone and then rides free for any trip later that day, including
  an evening or weekend trip. A rider whose only trips are off-peak ...
  never reaches the cap on those trips and pays full fare for both taps."*

`final.md`'s Section 3 now reads: *"That design point matters here because
of how the all-day cap actually pays off, as Section 2 already established:
it rewards a peak-anchored commute, not a day made up only of off-peak
trips."* — the mechanic is referenced, not re-derived, and the paragraph
loses 27 words with no loss of content a reader needs at that point.

This is the one substantive lesson of this run's seam pass: **the mechanical
dedup check is not sufficient on its own** — it missed a real duplication
because of how it splits sentences, and only the required human read-through
against the through-line caught it. Treat its "0 duplicates" result as a
floor, not a guarantee.

## 2. Terminology fix

`reports/stitch.md` reported one real terminology-lock violation, exactly as
the mechanical check is supposed to catch:

```
## Terminology violations (1)
- B002 L1: 'fare capping' -> use 'fare cap'
```

`batches/B002.md`'s heading read *"1. How Off-Peak Fare Capping Works and
What Peer Agencies Found"* — "fare capping" is the locked wrong form for
"fare cap" (CHARTER.md, Terminology lock table). `final.md`'s Section 1
heading now reads *"1. How the Off-Peak Fare Cap Works and What Peer
Agencies Found."* No other locked wrong form ("smart card", "off-peak
discount", "transit agency", unhyphenated "low income") appears anywhere in
the six batches; this was the only fix needed.

## 3. Transitions

Every unit was drafted with a forward-pointing final sentence and the next
unit's carry was written to pick that thread up (see `carry.md`'s history
across `LEDGER.md`), so the five section boundaries needed no rewriting —
`reports/stitch.md`'s "Seams" listing was inspected boundary by boundary and
each read as a continuation, not a jump. One structural transition was
added rather than repaired: the source catalog (`batches/B001.md`) originally
opened `draft.md`, ahead of the report's own introduction, which is the
right place for it as an *input* to every unit but the wrong place for a
board reader. It is moved to the end of `final.md` as "Appendix A: Source
Catalog," re-labeled from a working document ("Feeds: B002...") to a
reader-facing citation list ("Underlies Section 1..."), after the
Conclusion.

## 4. Pronouns, antecedents, and register

Checked across all five section boundaries and the new front/back matter:
third-person, board-briefing register held throughout with no first-person
or rhetorical-question drift; "RTA" is used consistently rather than
alternating with "the authority" or "the agency"; no dangling "this" or "it"
crossing a section boundary without a clear antecedent. No changes needed.

## 5. Front matter and back matter — written last, per the skill

`front-matter.md` (Executive Summary) and `back-matter.md` (Conclusion and
Recommendation) were written only after the above steps, once Sections 1-5
existed in their corrected form. The Conclusion states the through-line's
recommendation — adopt an off-peak cap via Option B, the corridor-first
pilot — as the first and only place in the finished piece that recommendation
is stated outright, and every claim in it (the $410,000/$85,000 figures, the
33%-vs-19% equity figure, the 60-day union notice, the Access board-action
requirement, Ashford's awareness result) traces to a body section already
written; the Conclusion introduces no new figure or claim.

## 6. Net effect

`draft.md`: 4,981 words (`bse.py count_words`, comments/fences excluded).
`final.md`: 4,949 words. The two are close in length but differ meaningfully
in content and structure: front-matter.md (441w) and back-matter.md (555w)
are new; the catalog was moved and relabeled; the duplicate clause was cut;
the terminology fix was applied; all six `<!-- BSE B00X -->` machine markers
were removed since `final.md` is a document, not a stitched log. A word-level
diff (`difflib.SequenceMatcher`) puts the two files at 0.93 similarity — high,
because five of six units needed no prose changes at all, which is the point
of verifying each unit before it is stitched — but not identical, and the
unified `diff` between them runs 55 removed / 46 added lines.
