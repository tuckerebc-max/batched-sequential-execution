# Verification

Nothing enters the ledger because the model says it's done (P6). Every unit
needs at least one **mechanical** predicate — checked by `bse.py check` with no
judgment involved — and may declare **judgment** predicates (`source:`,
`charter:`) that require a reviewer pass, recorded with `bse.py review`. This
file documents both gates, plus the fix-round/escalation path.

**Both gates are enforced by `record --status done`, not by convention.** A
unit with no judgment predicates only ever needed `check` to pass. A unit that
declares `source:` or `charter:` predicates additionally needs a stored
`review` verdict of `pass` for the artifact's *current* content — `record`
refuses otherwise (see "The review gate" below). This is current tool
behavior, not something that has always been true of every version of this
skill; if you're working from an older run directory or an older copy of
`bse.py`, check `bse.py review --help` exists before assuming the second gate
applies.

## The mechanical verifier catalogue

All defined in `scripts/bse.py`'s `VERIFIERS` registry. `text` is always the
artifact with fenced code blocks and HTML comments blanked out first (the same
rule `word_count` uses) — every verifier below operates on that "prose" view
unless noted.

| Verifier | Checks | Failure message names | Gotchas |
|---|---|---|---|
| `word_count <spec>` | Word count vs a numeric spec: `within N% of B`, `within N%` (B = unit's own budget), `>= N`, `<= N`, `N-M`, or bare `N` | The count, and the accepted range, e.g. `1740 outside 15% of 1380 [1173-1587]` | If the unit's budget isn't in words and the spec omits an explicit base, fails with "no budget available to compare against" — always write `within N% of B` explicitly unless the unit's own budget is in words. |
| `no_placeholders` | Regex sweep for `TBD`, `TODO`, `[insert`, `Lorem`, line-final `etc.`, `as described/above`, `XXX`, and any `<angle-bracket span>` that looks like a placeholder | Up to 8 hits, each `label 'match' Lnn` | Inline code spans (`` `...` ``) are exempted before the sweep runs. An angle-bracket span only counts as a placeholder when it contains whitespace or placeholder vocabulary (`insert`, `your`, `name`, `title`, `date`, `tbd`, `todo`, `xxx`, `placeholder`, `description`); a known HTML tag (`<br>`, `<sub>x</sub>`, closing tags) and an autolink (`<https://…>`, `<user@host>`) both pass. Hand-authored HTML and autolinks in prose are safe to declare this check alongside. |
| `contains_headings [..]` | Every named heading text exists, verbatim | Missing headings by exact string | Case- and punctuation-sensitive; must match the ATX heading text exactly, trailing `#`s stripped. |
| `max_heading_depth N` | No heading deeper than H*N* | Each offending heading's depth and line | |
| `citation_tags` | Every prose **sentence** containing a year or a "digit + unit" (`12%`, `$4`, `3 million`, `1200w`, …) carries an `[S#]` tag somewhere in it | Line (or line range) of each untagged sentence | Sentence-aware, not line-aware: a hard-wrapped sentence whose tag lands on the next physical line still counts as tagged, and a tag written after the terminal punctuation (`…12%. [S1]`) is treated as belonging to the sentence before it. It still tags the *sentence*, not the specific number — a sentence with two numeric claims and one tag passes. Split sentences if per-number precision matters. |
| `forbidden_phrases [..]` | None of the listed phrases appear (word-boundary match, case-insensitive) | Each hit as `'phrase' Lnn` | With no explicit list, defaults to the charter's terminology-lock *wrong forms* plus carry.md's "Do not repeat" bullets — free anti-drift enforcement. |
| `slide_count <spec>` | Slide count vs a numeric spec (same grammar as `word_count`) | Count and range, same format | A "slide" is an H1/H2 heading; if there are none, `---`/`***` separator lines + 1. Mixing heading-delimited and separator-delimited slides in one artifact undercounts. |
| `item_count <spec>` | Count of **top-level, unindented** `-`, `*`, or `N.` list lines | Count and range | Nested/indented list items are not counted — write feedback items as top-level bullets if this predicate matters. |
| `file_exists <path>` | Path exists, resolved relative to the run dir then cwd | `<path> exists/missing` | |
| `json_schema <path>` | Artifact (or its first ```` ```json ```` fence) parses and matches a tiny JSON-Schema subset (`type`, `required`, `properties`, `items`, `enum`, `min/maximum`, `min/maxLength`, `additionalProperties`) | Up to 8 schema violations, or a parse error | Stdlib-only subset — no `$ref`, `oneOf`, formats, etc. |
| `shell <cmd>` | Runs `<cmd>` in the run dir with `$BSE_ARTIFACT` set to the artifact path; exit 0 = pass | `exit N` plus the last 3 lines of stderr (or stdout) | 300-second timeout. This is the escape hatch for anything the other verifiers can't express — a test suite, a linter, a diff check. |
| `no_conclusion` | No "in conclusion / to summarize / in summary" anywhere, and no "overall," in the final paragraph | Each hit, with location | Only declare this on non-final units — see [stitching-and-seams.md](stitching-and-seams.md) on why front/back matter is written last. |

A verifier that throws an exception is always recorded as **failed** with the
exception text as the detail — a bug in a custom verifier can never
accidentally pass a unit.

## Writing a good judgment predicate

`source:` and `charter:` lines are never mechanically checked — `bse.py check`
surfaces them as "judgement pending" and the unit cannot be recorded done on
mechanical checks alone until a reviewer pass addresses them. Write them as a
claim a reviewer could adjudicate from the brief and the artifact alone:

- Bad: `charter: is faithful to the sources` (unfalsifiable — faithful how?)
- Good: `source: every numeric claim carries a [S#] tag present in inputs`
  (falsifiable by grep, reviewable by a person)
- Good: `charter: acceptance criteria 2, 5` (points at numbered, testable
  criteria already written in CHARTER.md — the predicate's content lives there,
  not invented at review time)

## The review gate

`bse.py review <ID> --verdict pass|fail --report <path>` stores a reviewer's
verdict, keyed to the sha256 of the artifact at the moment of review — not to
the unit. Consequences that follow directly from that keying:

- **Editing the artifact after review invalidates the review.** A stored
  verdict only counts for the exact bytes it was recorded against; the next
  `check` or `record` on a changed artifact sees a review with no matching
  sha and treats it as **stale**, not as pass carried forward.
- **`review` is a usage error (exit 2) on a unit with no judgment
  predicates.** There's nothing for a reviewer to adjudicate — `check` is
  that unit's only gate, and `bse.py review` says so and refuses.
- **`review` exits 1 on a `--verdict fail`**, the same convention `check`
  uses for a failing mechanical run, so a script chaining these commands can
  treat both the same way.
- **`--report <path>` must name a file that exists and is non-empty** — the
  reviewer's actual written findings, not a placeholder. `review` refuses
  otherwise.
- **`record --status done` refuses** when a unit declares judgment predicates
  and no *passing* review matches the artifact's current sha — whether
  because no review was ever recorded, the stored review is stale (artifact
  changed since), or the stored review is a `fail`. `--force` overrides, and
  stamps the ledger line `FORCED`.

`bse.py check`'s summary line reports both halves together once a unit
declares judgment predicates, e.g.:

```
PASS (4/4 mechanical; 2 judgement predicates pending review)
```

and after a passing review:

```
PASS (4/4 mechanical; 2 judgement predicates reviewed: pass)
```

`bse.py status` carries a `review` column (`-` when the unit declares no
judgment predicates, else `pending` / `stale` / `pass` / `fail`), and
`bse.py audit` reports `DONE_WITHOUT_REVIEW` (done, judgment predicates
declared, no matching review stored) and `DONE_WITH_FAILING_REVIEW` (done,
but the review matching the current artifact is a fail) — both signs that a
unit was force-recorded or that the artifact moved after review.

## Constructing a reviewer prompt that can't be gamed

Give the reviewer exactly three things: the **brief** (`briefs/<ID>.md`), the
**artifact** (`batches/<ID>.md`), and the **predicate text** from the unit's
`verify:` block. Nothing else. The reviewer's job ends by writing its verdict
to a report file and that report being recorded with `bse.py review <ID>
--verdict pass|fail --report <path>` — a verdict that exists only in the
conversation, never written to a report and stored, cannot satisfy `record`'s
review gate.

Exclude, deliberately:
- The full PLAN.md or other units' text — the reviewer should judge this unit
  against its own brief, not against a sense of the whole deliverable it was
  never given.
- Conversation history — a reviewer that saw the executor struggle will judge
  the *effort*, not the *artifact*.
- Any instruction resembling "don't flag X" or "go easy on Y." A pre-judgment
  about what the reviewer should overlook is not context, it's a thumb on the
  scale — it corrupts the one check meant to be independent of the work.

## The 3-fix-round rule and escalation

On a failing check: fix, re-check, up to **3** rounds (`MAX_FIX_ROUNDS`). A
round is counted **either** explicitly, via `bse.py record <ID> --status
fix` (which also stores your `--note`), **or automatically**: re-running
`bse.py check <ID>` on an artifact that changed since the last *failing*
check counts as a fix round on its own, even if nobody ran `record --status
fix` in between — the ledger line says so (`auto=check`). The two paths
don't double-count the same transition: an explicit `record --status fix`
answering a specific failing sha is consumed by the next `check` on the
repaired artifact rather than counted twice. Either way, a 4th round is
refused without `--force`. If the unit still fails after 3 rounds:

1. **Split** — the unit is too big for one predicate set to resolve; break it
   into `<ID>a` / `<ID>b` with narrower scope and re-plan those two units.
2. **Block** — `record <ID> --status blocked --note <reason>`; surface to the
   user rather than guessing. Appropriate when the failure is a genuine
   ambiguity (contradictory sources, an underspecified acceptance criterion),
   not a size problem.
3. **Ask for a ruling** — `record RULING --note <decision>` once a human has
   resolved the ambiguity; then resume the unit (or a split of it) against the
   ruling.

Never treat a 4th silent `--force` as an escalation path — `--force` stamps the
ledger `FORCED` precisely so `audit` and every later reader can see a predicate
was overridden, not satisfied.

## Why unanchored self-critique fails

A model reviewing its own prose against nothing but its own taste can make the
output *worse*, not better — self-correction without an external signal
degrades accuracy in controlled trials, and the gains attributed to
self-refinement elsewhere depend on exactly the oracle signal this skill
insists on (see [evidence.md §4](evidence.md#4-why-verification-must-be-externally-anchored)).
The design consequence: the halting condition is always a named, checkable
predicate — mechanical or a scoped reviewer pass — never "the model is
satisfied with it."

## Predicates worth declaring, by deliverable type

| Deliverable type | Predicates worth declaring |
|---|---|
| Report / manuscript section | `word_count`, `contains_headings`, `no_placeholders`, `citation_tags` (if it carries data), `forbidden_phrases`, `no_conclusion` (non-final units), `charter: acceptance criteria N` |
| Slide (created or edited) | `slide_count`, `no_placeholders`, `contains_headings` (if slides carry required titles), `charter:` for visual/brand consistency (judgment) |
| Code change / refactor slice | `shell` (run the test suite or a targeted subset), `file_exists`, `no_placeholders` (stray TODOs), `json_schema` for config/data files touched |
| Feedback-sweep item batch | `item_count`, `forbidden_phrases`, `source:` every item traceable to a specific feedback entry |
| Extraction / research batch | `item_count` or `word_count`, `citation_tags`, `source:` every extracted claim traces to a named input |
| Data / sheet unit | `json_schema` or `shell` (a validation script), `file_exists` |

## Related

- [Light mode](light-mode.md) — the version of verification that has no `check`/`review` gate at all
- [Batch sizing](batch-sizing.md) — sizing so one predicate set can resolve a unit
- [Ledger and state](ledger-and-state.md) — where `verify:` lines live in PLAN.md, and what `check`/`record` write
- [Stitching and seams](stitching-and-seams.md) — `no_conclusion` and why front matter is exempt
- [Failure modes](failure-modes.md) — thrash, false victory, and their guards
- [Evidence](evidence.md) — the research behind externally-anchored verification
