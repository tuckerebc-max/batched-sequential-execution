# Ledger and state

All state lives under `.bse/<run-id>/`. This file documents the exact formats
`scripts/bse.py` reads and writes, and how to keep the same discipline by hand.

## CHARTER.md

Nine sections, in this order (`bse.py init` scaffolds eight of them —
everything but Through-line, which SKILL.md requires but the tool doesn't
currently scaffold or check for structurally; nothing enforces section order
beyond convention either way):

| Section | Content |
|---|---|
| Deliverable | What, format, **Total size: `<n><unit>`** — the line the budget-sum check and `word_count`'s default base both key off. Must match the pattern `total size: <number><unit>` (case-insensitive), e.g. `Total size: 20000w`. A charter may name more than one denomination on this line (`Total size: 20000w, 40slides`), separated by `,`/`;`/`+`/`and`; each is tracked and drift-checked independently — see "Multi-denomination totals" below. |
| Through-line | One sentence: what the finished thing argues or establishes. Not one of the eight sections the tool's `CHARTER_SECTIONS` constant checks for structurally, but every brief should carry it verbatim — see the seam-pass step 0 in [stitching-and-seams.md](stitching-and-seams.md). |
| Audience | Who reads it, what they already know. |
| Voice & register | Tone, person, formality — two sentences. |
| Non-negotiables | Numbered, each independently testable. |
| Terminology lock | `wrong form -> approved form` lines (or a `\| wrong \| right \|` table row). Feeds `forbidden_phrases` for free. |
| Sources of truth | Paths/URLs with `[S#]` ids — the only inputs a brief may cite. |
| Acceptance criteria | Numbered predicates; a unit's `verify: charter` line references these by number. |
| Out of scope | What this deliverable does not do. |

### Multi-denomination totals

`Total size: 20000w, 40slides` declares two independent totals. Each unit's
own budget denomination (its `w`/`slides`/`files`/`items` suffix) is summed
separately and compared against whichever total shares that denomination;
`plan --validate` and `bse.py audit` both report drift per denomination, not
pooled. A denomination that appears in the plan's unit budgets but not in the
charter's `Total size` line is not an error — it's reported as an
**informational** finding (`budget denomination '<x>' has no charter total;
drift not checked` at plan time, `PLAN_BUDGET_UNCHECKED` at audit time) so a
mixed-type deliverable (a report with an appendix of slides, say) doesn't
force every denomination to be pre-declared.

## PLAN.md grammar

Two parts: a **units table** and one **spec block** per unit. This is the exact
grammar the parser (`parse_table_line` / `parse_spec_block` in `scripts/bse.py`)
accepts — deviate and `plan --validate` reports the line number and reason.

### Table line

```
- [ ] B003 [compose] [P] [dep:B001,B002] Section 3.2 — budget: 1200w (±15%)
```

- Leading `-` or `*`, then `[ ]` / `[x]` / `[X]` (case-insensitive done marker;
  tooling only ever writes it, never hand-edit it to `[x]`).
- ID: `B` + exactly 3 digits, optionally + one lowercase letter for a split unit
  (`B003a`, `B003b`).
- `[type]` immediately follows the ID: one of `research | compose | revise |
  transform | verify | assemble`.
- Then, in **either order**, optionally: `[P]` and `[dep:ID,ID,...]`. Both are
  parsed by repeatedly stripping whitespace and trying each in turn until
  neither matches.
- Everything up to the **last** occurrence of a dash-run followed by
  `budget:` (`-`, `–`, or `—`, one or more, case-insensitive) is the title —
  so a title may itself contain a hyphen as long as it isn't followed by
  `budget:`.
- Budget: `<digits><unit>` optionally followed by `(±N%)` — accepted units are
  normalized (`words`/`word`/`wds` → `w`, `slide`→`slides`, `file`→`files`,
  `item`→`items`; anything else passes through as typed, e.g. `files`, `lines`).

### Spec block

```
### B003 — Section 3.2
type: compose
budget: 1200w (±15%)
depends_on: [B002]
inputs:
  - path/to/source.md#L40-120
intent: |
  One paragraph a stranger could act on.
produces:
  - section: "3.2 Method"
verify:
  - mechanical: word_count within 15% of 1200
  - mechanical: no_placeholders
  - charter: acceptance criteria 2, 5
done_when: |
  One binary sentence.
waive: word_count — this unit's budget is nominal; see RULING 2026-09-01
```

`waive:` is optional, a scalar or list of `<rule> — <reason>` entries
(`—`, `–`, `--`, `-`, or `:` all work as the separator), and only these three
rule names are recognized: `word_count`, `citation_tags`, `no_conclusion` —
see "Predicate-adequacy rules" below. Anything else in `waive:` is a parse
error, not a silent no-op.

- Heading: `### <ID>` then an optional separator (`—`, `–`, `-`, or `:`) and a
  title; the separator is optional, so `### B003 Section 3.2` also parses.
- Fields are `key: value` lines read until the next heading. Three value shapes:
  - **Block scalar** — value is exactly `|`, `>`, `|-`, or `>-`; every following
    line that is blank or indented becomes the field's text, common indentation
    stripped, trailing blank lines dropped.
  - **List** — value is empty or `[]`; following `- item` lines (blank lines
    tolerated) become a list, until a non-list, non-blank line.
  - **Inline list** — value starts with `[` and ends with `]` on the same line;
    parsed as JSON if it looks like JSON, else comma-split.
  - Anything else is a plain scalar string; a trailing `  # comment` (space
    before `#`) is stripped.
- `verify:` list items are `kind: expression`; `kind` other than `mechanical`
  (typically `source` or `charter`) is never checked by the script — it becomes
  a "judgement pending" entry for a reviewer pass. See
  [verification.md](verification.md).

### Validation gate (`bse.py plan --validate`)

Fails the run (exit 1) on any of: duplicate ID; unparsable table line; missing
`### ID` spec block; table/spec mismatch on `type`, `budget`, or `depends_on`;
missing `intent`, `done_when`, `inputs`, or `produces`; zero `mechanical:`
verifiers, or one naming an unregistered verifier; a dependency on an unknown
or self-referential unit; a dependency cycle; two `[P]` units sharing a
`produces` target; a `PLAN_PLACEHOLDER` string (`TBD`, `etc.`, `similar to`,
`as above`, `...`/`…`) anywhere in a spec block; no `Total size` in CHARTER.md;
the sum of same-denomination budgets drifting more than 20% from the
matching charter total (checked per denomination — see "Multi-denomination
totals" above); or a failed **predicate-adequacy rule** (below). Fewer than 5
units is a **warning**, not an error. A pass stamps `plan_validated` into
`ledger.json` — `bse.py next` and `status` both refuse to proceed on a plan
that has never passed this gate (`PLAN NOT VALIDATED`), and on a plan with no
units at all (`PLAN EMPTY`).

### Predicate-adequacy rules

Three rules, checked per unit, each waivable with a `waive: <rule> —
<reason>` line in that unit's spec block (waivers are echoed in the
validator's output so they're visible, not silent):

| Rule | Triggers when | Satisfied by |
|---|---|---|
| `word_count` | The unit's budget denomination is `w` | A `- mechanical: word_count …` verifier |
| `citation_tags` | The unit's `inputs:` name a real source — anything beyond `CHARTER.md`, `carry.md`, or a prior unit's own `batches/<ID>.md` (already verified when it was recorded) | A `- mechanical: citation_tags` verifier, or any `source:` judgment predicate |
| `no_conclusion` | The unit's `type` is `compose` and it is **not** the plan's last unit | A `- mechanical: no_conclusion` verifier |

A numeric verifier (`word_count`/`slide_count`/`item_count`) that implicitly
compares against "the unit's own budget" (an empty spec, or `within N%`
with no explicit base) must count the same denomination the budget is
expressed in — declaring `word_count within 15%` on a unit budgeted in
`slides` is a validation error; give an explicit base (`word_count within
15% of 900`) instead.

## LEDGER.md

First line, written once by `init`, never changed except by the tooling that
also rewrites `ledger.json`:

```
# BSE ledger — run: <run-id> — charter: <absolute path to CHARTER.md> — created: <iso>
```

Every subsequent line is one event, append-only, fixed-width-ish for human
scanning. Exact forms the script emits:

```
B003 done     2026-09-12T18:44Z  artifact=batches/B003.md  words=1187  verify=pass(4/4)  sha=ab12cd3
B004 fix 1/3  2026-09-12T18:51Z  verify=fail(2/4): word_count 1740 outside 15% of 1380 [1173-1587]; placeholders: TBD 'TBD' L22
B004 fix 2/3  2026-09-12T18:55Z  verify=fail(1/4): ...  auto=check (artifact changed after a failing check)
B004 blocked  2026-09-12T19:04Z  reason=source contradicts charter NN-3; needs human ruling
RULING        2026-09-12T19:20Z  use 2025 figures, not 2024
B005 review pass  2026-09-12T19:25Z  predicates=2  report=reports/B005-review.md  sha=9f2a1b4
SEAM  B001-B006 2026-09-12T19:30Z  dedup=2 found; terminology drift=0
```

A `done` line is only ever written by `record --status done` after a stored
check has zero failures and a matching sha256, **and**, if the unit declares
judgment predicates, a stored `review` verdict of `pass` matching that same
sha256 — or with `--force`, in which case the line carries a trailing
`FORCED` marker; never trust a `FORCED` line as clean. `fix` lines increment a
per-unit counter capped at 3 (`MAX_FIX_ROUNDS`); a 4th `fix` is refused
without `--force`. A `fix` line may be written explicitly (`record --status
fix`) or automatically — re-running `check` on an artifact that changed after
a failing check counts a round on its own, marked `auto=check` — the two
never double-count the same transition. A `review` line records one
reviewer verdict, keyed to the artifact's sha256 at review time; a later
edit to the artifact makes that stored review **stale** without a new
ledger line — `status` and `audit` both surface staleness by re-comparing
sha256, not by an event.

## ledger.json

Authoritative for tooling; LEDGER.md is a human-readable append log derived
from the same events, not the other way around.

```json
{
  "run_id": "report-2026", "title": "...", "charter": "/abs/path/CHARTER.md",
  "created": "2026-09-12T...Z", "total": "20000w",
  "plan_validated": {"ts": "2026-09-12T18:00:00Z", "units": ["B001", "B002", "..."]},
  "units": {
    "B003": {"status": "done", "artifact": "batches/B003.md", "sha256": "...",
              "words": 1187, "verify": {"passed": 4, "failed": 0, "checks": [...]},
              "attempts": 1, "fix_rounds": 0, "updated": "...",
              "history": [{"status": "fix", "timestamp": "...", "note": null},
                          {"status": "done", "timestamp": "...", "note": null}],
              "reviews": [{"verdict": "pass", "sha256": "...", "artifact": "batches/B003.md",
                           "report": "reports/B003-review.md", "predicates": ["charter: ..."],
                           "note": null, "ts": "..."}]}
  },
  "events": [{"ts": "...", "line": "B003 done ...", "unit": "B003", "kind": "done", "forced": false}]
}
```

`status` is one of `pending | done | blocked | fix`. `history` is an
append-only record of every status this unit has passed through — so
`ledger.json` alone shows the fix/blocked/done sequence, not just the
latest state. `reviews` is every stored reviewer verdict for this unit, most
recent last; only the most recent verdict **matching the current artifact's
sha256** counts for `record`'s review gate (`review_for_sha` — an older
review for a since-edited artifact is stale, not consulted). `plan_validated`
is stamped by a clean `plan --validate` and is what `next`/`status` check
before allowing execution to proceed. Written via temp-file + `os.replace`
(atomic on POSIX and Windows) — a crash mid-write leaves the old file intact,
never a half-written one.

## carry.md — the baton

Five fixed sections, in order: **Established facts**, **Interfaces/terms now
defined**, **Open threads for later units**, **Do not repeat**, **Tone
calibration note**. Hard cap: 400 words, counted the same way `word_count`
counts everything (fenced code and HTML comments excluded). `bse.py carry --set
FILE` refuses to install a file over the cap; a file under cap but missing a
section is installed with a warning, not refused. Each unit **replaces**
carry.md wholesale (`record --status done --carry FILE`, or `carry --set`
directly) — it is not an append log.

The carry does **not** maintain itself. It is a file, and nothing runs the
carry-update prompt ([prompts.md](prompts.md#carry-update-prompt))
automatically before a `record` — that step has to be taken deliberately,
every unit, or the next brief inherits a stale baton. `bse.py carry --check`
exits non-zero once **two or more units are done** and carry.md is still
empty or byte-identical to the `init` scaffold (line-ending differences
normalized) — the point at which "the baton was never written" stops being
plausibly fine and starts being the run's most common silent failure.
`bse.py audit` reports the same condition as `CARRY_STALE`.

## front-matter.md, back-matter.md, final.md — the seam pass's files

Three more files at the run root, none of them written by any command before
the seam pass:

| File | Written by | `stitch` behavior |
|---|---|---|
| `front-matter.md` | Hand, in the seam pass, after every unit is done | Prepended to `draft.md` **by default** once it contains any prose; `--no-front-matter` suppresses front/back matter entirely; `--include-front-matter` is a **deprecated no-op** kept only so an old invocation doesn't break — it will be removed. |
| `back-matter.md` | Hand, in the seam pass | Appended to `draft.md` the same way, under the same flags. |
| `final.md` | Hand, in the seam pass — **never** by the tool | `stitch --out final.md` is refused outright (exit 2): `draft.md` is machine output, `final.md` is the deliverable, and the tool will not let the two collapse into one file. |

`init` scaffolds `front-matter.md` and `back-matter.md` as HTML-comment-only
placeholders (no prose, so `stitch` treats them as "not yet written," not as
empty front matter); it does not create `final.md` at all. `bse.py audit`
reports `SEAM_PASS_MISSING` when every unit is done but `final.md` still
doesn't exist, and `FINAL_STALE` when `final.md` is older than a `draft.md`
that was re-stitched after it — the sign that a unit was re-opened and
re-stitched after the seam pass ran, and the seam pass needs to be redone on
the new draft.

## `bse.py status`'s table

```
id     type       status   att   budget     words   review    title
B003   compose    done       1   1200w       1187   pass      Section 3.2 — capacity model
B004   compose    fix        2   1200w       1740   -         Section 3.3
```

The `review` column reads `-` for a unit that declares no judgment
predicates (only `check` gates it), `pending` (never reviewed),
`stale` (a review exists but not for the current artifact), `pass`, or
`fail`. The footer also reports the count of units awaiting review, and, when
applicable, `PLAN EMPTY` or `PLAN NOT VALIDATED` in place of (or alongside)
the done/total count — both of which also make `bse.py next` refuse to
return a unit until fixed.

## Resume rule

> Read `LEDGER.md`. If its first line names this run's charter, every unit
> with a `done` line is COMPLETE — do not re-execute it. Resume at the first
> unit without one.

### Resume walkthrough after a context reset

1. Locate the run directory: `bse.py status --run-dir .bse/<run-id>` (or let it
   default to the most recently touched run under `./.bse`).
2. Read `LEDGER.md`'s first line; confirm the charter path matches the
   CHARTER.md you're about to trust.
3. Run `bse.py audit`. Do not proceed on unresolved findings — see below.
4. Run `bse.py status` to see the full id/type/status/attempts/budget/words
   table in one screen.
5. Run `bse.py next` for the first unblocked, not-done unit.
6. Read `carry.md` (`bse.py carry --show`) — it, not conversation memory, is
   what "resuming" actually restores.
7. Continue the loop at BRIEF for that unit.

## What `audit` detects, and what to do

Every finding carries a **level**: `error` (default) or `info`. Only `error`
findings make `audit` exit non-zero — an `info` finding is worth reading but
does not by itself mean the run is broken (e.g. a mixed-denomination plan
where one denomination has no charter total to check against).

| Finding | Level | Meaning | Action |
|---|---|---|---|
| `LEDGER_MD_MISSING` / `LEDGER_HEADER_MISMATCH` | error | LEDGER.md absent, or its first line doesn't match ledger.json | Treat ledger.json as authoritative; regenerate LEDGER.md's header, or investigate why two run dirs' state got merged. |
| `PHANTOM_COMPLETE` | error | PLAN.md shows `[x]` but ledger has no `done` record (or a non-done status) | Do not trust the `[x]`. Re-run `check` on the unit's artifact; only `record` can legitimately re-set it. |
| `ARTIFACT_MISSING` / `ARTIFACT_EMPTY` | error | Ledger says done, file isn't there or is 0 bytes | The unit is not actually done. Re-execute it from BRIEF. |
| `HASH_MISMATCH` | error | Artifact changed since it was recorded | Something edited a batch file after verification. Re-run `check`; if it now fails, treat as a fresh `fix` round. |
| `DONE_WITHOUT_VERIFY` | error | Done with no stored verify record | Almost certainly a `--force` or manual ledger edit. Re-check before trusting it downstream. |
| `DONE_WITH_FAILING_VERIFY` | error | Stored check itself shows failures | The unit was force-recorded or the ledger is stale. Re-check. |
| `DONE_WITHOUT_REVIEW` | error | Unit declares judgment predicates; done, but no stored review matches the recorded artifact's sha | Force-recorded, or reviewed then edited. Run the reviewer pass and `bse.py review`. |
| `DONE_WITH_FAILING_REVIEW` | error | Done, but the review matching the current artifact is a `fail` | Force-recorded over a failing review. Fix the artifact, re-check, re-review. |
| `PLAN_NOT_MARKED` | error | Ledger says done, PLAN.md line is still `[ ]` | Cosmetic but confusing — `record` should have flipped it; re-run `record` or hand-edit the checkbox only. |
| `BUDGET_DRIFT` | error | A done unit's word count is >20% off its own budget | Not a hard failure by itself; check whether the unit should have been split, or the budget was wrong. |
| `UNKNOWN_UNIT` / `UNKNOWN_UNIT_EVENT` | error | Ledger references an ID not in the current PLAN.md | The plan was edited after execution started. Reconcile which is authoritative before continuing. |
| `CARRY_OVER_CAP` | error | carry.md exceeds 400 words | Someone bypassed `carry --set`. Trim it back under cap by hand. |
| `CARRY_STALE` | error | ≥2 units done, carry.md is still empty or the `init` scaffold | The baton was never written. Write it now with the carry-update prompt before continuing. |
| `SEAM_PASS_MISSING` | error once every unit is done, `info` before that | `final.md` doesn't exist yet | Run the seam pass: read `draft.md`, write `front-matter.md`, `back-matter.md`, and `final.md` by hand. |
| `SEAM_PASS_INCOMPLETE` | info | `final.md` exists, but front-matter.md or back-matter.md still carries no prose | Finish the seam pass's step of writing front/back matter. |
| `FINAL_STALE` | error once every unit is done, `info` before that | `final.md` is older than `draft.md` — the draft was re-stitched after the seam pass ran | Redo the seam pass against the new `draft.md`; the old `final.md` no longer reflects the current units. |
| `BLOCK_WITHOUT_RULING` | info | A unit was blocked, then later moved past `blocked` (fix/done) with no `RULING` event recorded in between | Not necessarily wrong, but worth confirming the resolution was a deliberate decision, not a silent retry. |
| `PLAN_BUDGET_DRIFT` | error | Plan's total budget sum drifts >20% from the charter target, for a denomination the charter declares | Scope has grown or shrunk silently since planning. Re-open PLAN move. |
| `PLAN_BUDGET_UNCHECKED` | info | Plan budgets sum to a denomination the charter's `Total size` line never declared | Not an error by itself — a mixed-type deliverable's secondary denomination may be intentionally undeclared — but confirm it's not a missed `Total size` entry. |

## Doing this without the script

The four files are the entire contract; the script is bookkeeping convenience.
By hand:

1. Write CHARTER.md and PLAN.md exactly to the formats above; check them
   yourself against the validation-gate list before starting.
2. Before executing a unit, assemble its brief manually: paste CHARTER.md +
   that unit's spec block + current carry.md + named input slices into a
   single file. Nothing else.
3. After the executor writes its artifact, check each `mechanical:` predicate
   by hand (word count, headings present, no placeholder strings) and write a
   one-line pass/fail note. If the unit also declares a `source:`/`charter:`
   judgment predicate, run a separate reviewer pass against the brief and
   artifact only, and write its verdict down before step 4 — do not treat a
   passing mechanical check alone as license to record a unit with judgment
   predicates.
4. Only if every mechanical check passes, and any judgment predicate's
   reviewer verdict is a pass, append one ledger line in the exact format
   above, then flip that unit's `[ ]` to `[x]` in PLAN.md.
5. Before that ledger line — using the carry-update prompt
   ([prompts.md](prompts.md#carry-update-prompt)) — replace carry.md's five
   sections with the updated baton, counting words by hand (any word
   processor's count, minus code-fence content). Do this every unit; a carry
   that still reads like the scaffold after two units is the single most
   common silent failure in this loop.
6. To stitch: concatenate batch files in plan order into draft.md; scan
   adjacent boundaries for duplicated sentences and tone breaks yourself.
   Then, and only once every unit is done, do the seam pass by hand: read the
   whole draft against the charter's through-line, fix what the boundary scan
   found, and only then write front-matter.md, back-matter.md, and finally
   final.md — draft.md itself is never the deliverable.

The discipline is the skill; the script only makes it cheap to keep.

## Related

- [Light mode](light-mode.md) — the same discipline with none of these files
- [Batch sizing](batch-sizing.md) — how budgets are chosen before they're written into PLAN.md
- [Verification](verification.md) — what `mechanical:` and judgment predicates check
- [Stitching and seams](stitching-and-seams.md) — what happens to these files at assembly
- [Failure modes](failure-modes.md) — recovery when the ledger and reality disagree
