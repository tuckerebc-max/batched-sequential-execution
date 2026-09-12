# Failure modes

Each entry: the symptom as the user would see it, the mechanism producing it,
the guard that should catch it, and the recovery once it has already happened.

## From the SKILL.md table

| Failure | Symptom | Mechanism | Guard | Recovery |
|---|---|---|---|---|
| One-shotting | The whole deliverable comes back in one pass, quality visibly thinner toward the end | Executor given the full scope instead of one unit's brief | Plan gate; the executor receives only `briefs/<ID>.md` | Stop, run the CHARTER/PLAN moves properly, discard the one-shot output or salvage it as raw material for the first few units' inputs — never as a "unit" itself, since it was never verified. |
| False victory | Ledger or conversation claims a unit done; the artifact is thin, wrong, or missing | Something marked `done` without a passing check, or without a passing review where one is declared | `record` refuses `done` when mechanical checks failed, were never run, the artifact's hash doesn't match the last check, or — for a unit declaring `source:`/`charter:` predicates — no stored `review` verdict is a `pass` matching the current artifact | Run `bse.py audit` — it flags `DONE_WITHOUT_VERIFY` / `DONE_WITH_FAILING_VERIFY` / `HASH_MISMATCH` / `DONE_WITHOUT_REVIEW` / `DONE_WITH_FAILING_REVIEW`. Re-check (and, where declared, re-review) the unit; if it fails, re-open it as a normal `fix` round. |
| Re-doing completed work after a context reset | An agent re-executes units 1–8 after a compaction or new session | Conversational memory doesn't survive compaction; nothing told the new context what was already done | Ledger identity header + the resume rule | Read `LEDGER.md`'s first line, confirm the charter path, resume at the first unit without a `done` line — see [ledger-and-state.md](ledger-and-state.md#resume-rule). |
| Drift from the charter | Later units use different terms, tone, or scope than the charter specified | Charter wasn't in the brief, or terminology lock wasn't enforced | Charter included in every brief; terminology lock doubles as a `forbidden_phrases` predicate; `charter:` judgment predicates | Add the missing predicate to remaining units; for units already done, decide via the mid-run-goal-change procedure below whether they need re-opening. |
| Seam damage (repetition, tonal breaks) | The stitched draft reads like several documents taped together | Units executed independently, each blind to its neighbors' exact wording | carry.md's "do not repeat"; the stitch report's duplicate/seam lists; the seam pass | Run the seam-pass checklist in [stitching-and-seams.md](stitching-and-seams.md); if drift recurs unit after unit, tighten carry.md's "do not repeat" and "tone calibration note" going forward. |
| Premature conclusions mid-draft | A middle unit wraps up with "in conclusion" or a summary that contradicts what comes after | Executor treated its unit as a self-contained mini-essay | `no_conclusion` predicate on every non-final unit | Strip the concluding language, re-check, re-record; note the recurring pattern in carry.md so later units don't repeat it. |
| Thrash (fix rounds forever) | A unit cycles through fix attempts without converging | The unit is too big, or the predicate is unfalsifiable/miscalibrated | Cap of 3 fix rounds, then mandatory split or block | Look at *which* checks keep failing. If the same one, unchanged, across rounds — split the unit. If the predicate itself can't be satisfied as written (e.g., contradictory acceptance criteria), block and request a ruling. |
| Stall (no ledger advance in 2 units) | Two units in a row produce no `done` line | Sizing or specification is wrong at the plan level, not the execution level | Stall trigger: stop retrying, return to PLAN | See "stall vs. slow-but-real progress" below for how to tell these apart before invoking this guard. |
| Supervisor context bloat | The coordinating context grows huge, degrading its own judgment about what's next | Supervisor read batch text instead of paths, or accumulated status chatter | Supervisor reads only ledger/plan/status; artifacts move as file paths | Clear/compact the supervisor's context; it can always reconstruct everything it needs from `bse.py status` and `carry.md` — that's the point of the file-based state model. |
| Silent scope growth | The finished draft is much longer or shorter than the charter promised, discovered only at the end | Unit budgets crept without anyone re-checking the sum against the charter total | Budget-sum check at `plan --validate`, per denomination; and again at `stitch` (drift report), where a complete stitch outside ±20% now exits non-zero unless `--allow-drift` | See the over/under-target procedure in [stitching-and-seams.md](stitching-and-seams.md#a-stitched-draft-over-or-under-the-charter-target). |

## Additional failure modes identified in this design

| Failure | Symptom | Mechanism | Guard | Recovery |
|---|---|---|---|---|
| Verifier blind spot | A unit passes its declared checks but is clearly wrong in some way none of them cover | A unit can satisfy the ≥1-mechanical-verifier gate with a check that's technically present but weak (e.g., only `no_placeholders` on a data-heavy unit) | None enforced beyond "at least one" — this is a plan-authoring quality issue, not a tooling one | Add the missing predicate (see the [verification.md](verification.md) table by deliverable type) and re-check; treat a passed-but-wrong unit as a `fix` round even though the tool considered it done. |
| False-positive placeholder flag | `no_placeholders` fails on legitimate content | An angle-bracket span containing whitespace or placeholder vocabulary (`insert`, `your`, `name`, `title`, `date`, ...) that isn't a recognized HTML tag or autolink | A known HTML tag (`<br>`, `<sub>x</sub>`, closing tags) and an autolink (`<https://...>`, `<user@host>`) are both exempted already | Still possible for a genuinely unusual angle-bracket span (an uncommon tag, or prose that happens to contain one of the placeholder-vocabulary words inside `<...>`) to false-positive — rephrase around it rather than disabling the check. |
| Incomplete stitch mistaken for complete | `draft.md` is missing a unit's content and the seam pass proceeds as if the deliverable were whole | `stitch` refuses (exit 1) on any incomplete unit — `[P]` or not — unless `--partial` is passed explicitly | `stitch`'s refusal itself, and, if `--partial` was used deliberately, the prominent `WARNING: PARTIAL` line plus the `<!-- MISSING <ID> -->` markers and the "Missing units" section in `reports/stitch.md` | Never pass `--partial` as a default habit. If it was needed, grep `draft.md` for `MISSING` and finish those units before running the seam pass — a seam pass over a partial draft produces front/back matter that describes a deliverable that doesn't exist yet. |
| Budget-unit mismatch | `word_count` (or `slide_count`/`item_count`) fails with "no budget available to compare against" instead of a real result | The unit's own budget isn't in the verifier's unit (e.g., budget is `3files` but the check is `word_count within 15%` with no explicit base) | None — write the base explicitly | Rewrite the predicate as `within N% of <explicit number>` rather than relying on the unit's own budget. |
| Stale carry, unnoticed | Every unit's brief carries the same "Established facts" and "Do not repeat" list from three units ago | Nothing runs the carry-update prompt automatically — it is a deliberate step before every `record`, and skipping it produces no error at the time | `bse.py carry --check` (exits non-zero once ≥2 units are done and carry.md is still empty or the `init` scaffold); `audit`'s `CARRY_STALE` finding | Run the carry-update prompt ([prompts.md](prompts.md#carry-update-prompt)) against the just-finished unit's artifact and the previous carry.md, then `carry --set` (or `record --status done --carry FILE`), before briefing the next unit. |
| Execution starts on an empty or unvalidated plan | `bse.py next` (or a hand-run of the loop) starts dispatching units against a PLAN.md nobody actually checked | PLAN.md has no units yet, or has units but `plan --validate` was never run clean against them | `next` and `status` both refuse/flag it: `PLAN EMPTY` (no units parsed at all) or `PLAN NOT VALIDATED` (units exist but no clean `plan --validate` is stamped in `ledger.json`) | Write real units (replacing `init`'s single `SAMPLE` unit — `plan --validate` warns while it's still there) and run `bse.py plan --validate` until it's clean, before dispatching any executor. |
| Reviewed, then edited | A unit shows `review: pass` in an old note, but `bse.py status` now reports its review column as `stale` | The artifact was changed after the reviewer pass — a fix round, a hand edit — and the stored review's sha256 no longer matches | `record --status done` refuses (the review no longer matches); `status`'s review column; `audit`'s `DONE_WITHOUT_REVIEW` | Re-run the reviewer pass against the current artifact and record a fresh verdict with `bse.py review`; a stale review is not carried forward automatically, by design. |

## Mid-run charter and goal changes

**The charter turns out to be wrong mid-run.** Stop before writing another
brief. Decide whether it's a clarification or a fundamental change: if it only
sharpens something already ambiguous, amend CHARTER.md, log a `RULING` event
recording what changed and why, and continue — completed units don't need
revisiting. If it changes what already-completed units should have said,
treat it as the "goal changes mid-run" case below.

**A source turns out to contradict the plan.** Do not resolve it silently
during execution — that's exactly the kind of undocumented judgment call the
ledger exists to prevent. Mark the affected unit `blocked` with a `--note`
naming the contradiction and the charter clause it conflicts with, and surface
it. Resume only after a `RULING` event records the human's decision.

**The user changes the goal at unit 12 of 17.** Freeze new BRIEF/EXECUTE
work first. Then classify the change:

1. **Fits inside remaining budget, doesn't touch completed units** — amend
   CHARTER.md, log a `RULING`, resume the plan from unit 12 unchanged.
2. **Changes what completed units should have said** — do not un-mark them.
   Add new `revise`-type units downstream that depend on the affected units
   and correct them in place; the ledger keeps the honest history of both the
   original and the revision.
3. **Invalidates the plan's shape** (unit boundaries, ordering, or count no
   longer make sense) — this is the abandon-and-re-plan case.

## Abandoning and re-planning cleanly

1. Run `bse.py audit` and `bse.py status` to snapshot exactly what exists and
   what's verified.
2. For each `done` unit, decide against the *new* charter's acceptance
   criteria whether its artifact still qualifies. Units that still pass carry
   forward as pre-verified sources for the new plan (cited with a `[S#]`, not
   silently reused as if newly produced); units that don't must be redone.
3. Start a new run (new `run-id`, or a clearly re-charter'd CHARTER.md with a
   `RULING` marking the pivot point) and write a new PLAN.md from scratch
   against the current goal.
4. Run `plan --validate` before executing anything.
5. Never edit an existing run's ledger history to make it look like the old
   plan didn't happen — the point of the ledger is that it's honest even when
   the run pivoted.

## Telling a stall from slow-but-real progress

"No ledger advance in 2 units" is the trigger, but not every string of `fix`
events is a stall. Look at the fix-round detail lines in LEDGER.md between the
last `done` and now:

- **Slow-but-real:** the failing-check count is shrinking round over round
  (`fail(3/4)` → `fail(1/4)` → done), or different checks fail each round as
  earlier ones get fixed. Continue, but consider whether the unit should have
  been sized smaller from the start.
- **Actual stall:** the same check fails, with the same or worsening detail,
  across rounds — or two consecutive *different* units each burn through fix
  rounds without landing. This means the unit's specification (not the
  executor) is wrong. Stop retrying; return to the PLAN move and re-examine
  that unit's budget, inputs, or `done_when` before attempting it again.

## Related

- [Light mode](light-mode.md) — most of these guards don't exist there; know the trade before choosing it
- [Verification](verification.md) — predicate design and the fix-round/escalation path in full
- [Ledger and state](ledger-and-state.md) — `audit` findings and the resume rule
- [Stitching and seams](stitching-and-seams.md) — over/under-target recovery and the `[P]` stitch caveat
- [Composition](composition.md) — nesting and nesting-as-avoidance
