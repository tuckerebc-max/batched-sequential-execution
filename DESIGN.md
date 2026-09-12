# DESIGN SPEC — batched-sequential-execution (BSE)

Internal build spec. Subagents: this is your source of truth. Do not invent
behavior outside it; if something is underspecified, choose the simplest option
and note it in your report.

## 0. One-line purpose

A skill that converts a deliverable too large for one reliable pass (20k-word
manuscripts, 80-slide decks, multi-step builds, large feedback sweeps) into an
ordered series of small, budgeted, independently verified batches — executed one
at a time against a durable file ledger, then stitched into one coherent final
artifact.

## 1. Design principles (each traceable to evidence; see references/evidence.md)

P1. **Plan granularity is the dominant quality lever.** Deeper plans beat better
    drafting (DOC: +22.5% coherence from outline depth alone). Spend compute on
    the plan.
P2. **Every unit carries an explicit budget.** Word/slide/file counts are control
    signals, not suggestions (AgentWrite: +21.3 length adherence, -0.2 quality).
P3. **Serial with a passed baton beats parallel fan-out** (-2% vs -6% coherence).
    Parallel is allowed only for independent units and only with a mandatory
    reconciliation pass (STORM pays for parallelism with cross-section dedup).
P4. **Curated context, not accumulated transcript.** Same task, same answer:
    near-perfect at 300 tokens, degraded at 113k (LongMemEval). Prior batches in
    full are distractors, not free information.
P5. **Every verification must bind to an external checkable predicate.**
    Unanchored self-critique can lose up to 37.7 points (Huang et al. 2023).
    The model's own satisfaction is never a halting condition.
P6. **Only verified work enters persistent state** (LongHorizon-Harness).
    The ledger records verified reality, not claimed reality.
P7. **State lives in files, not in the conversation.** Compaction destroys
    conversational memory; the most expensive observed failure is re-doing
    completed work (superpowers).
P8. **Per-step accuracy decays, it does not merely compound.** Errors in context
    make further errors likelier (self-conditioning). Fresh context per batch is
    the mitigation.
P9. **Allow decomposition at execution time.** A batch may split itself when it
    discovers it is too big (WriteHERE: interleaved planning beat fixed plans,
    margin widening with length).
P10. **Type your units.** Labeling a unit's operation type mattered more in
    ablation (-67%) than the decomposition structure itself (-49%).

## 2. Run directory (the state model)

Created under `<workdir>/.bse/<run-id>/` by default; user may name it.

```
.bse/<run-id>/
  CHARTER.md          # written once. The contract. <= 1 page. Read by EVERY batch.
  PLAN.md             # ordered unit table + per-unit spec blocks
  LEDGER.md           # append-only human-readable progress log (identity header first line)
  ledger.json         # machine mirror, authoritative for tooling
  carry.md            # the baton: <= 400 words of rolling carryforward
  briefs/<ID>.md      # generated self-contained brief for one batch
  batches/<ID>.md     # the batch output artifact (lightweight: markdown/json)
  reports/<ID>.md     # verification report for that batch
  front-matter.md     # introduction / executive summary — written BY HAND in the seam pass
  back-matter.md      # conclusion — written BY HAND in the seam pass
  draft.md            # machine output of `stitch` (regenerated on every stitch, never hand-edited)
  final.md            # the seam-passed deliverable. NEVER written by the tool.
```

Rule: **artifacts move as file paths, never as pasted inline text.**

`init` scaffolds `front-matter.md` and `back-matter.md` as comment-only files
(no prose); `stitch` prepends/appends them by default once they contain prose
(`--no-front-matter` suppresses; `--include-front-matter` is a deprecated
no-op alias for one version). `stitch` refuses `--out final.md`; `audit`
checks that `final.md` exists once every unit is done and is newer than
`draft.md`.

### 2.1 CHARTER.md (template)
Sections, all required: `Deliverable` (what, format, total size — one count
per denomination the plan budgets in, e.g. `Total size: 20000w, 40slides`), `Audience`,
`Voice & register`, `Non-negotiables` (numbered, each testable),
`Terminology lock` (term -> approved form; the anti-drift dictionary),
`Sources of truth` (paths/URLs with ids), `Acceptance criteria` (numbered,
each a predicate), `Out of scope`.

### 2.2 PLAN.md schema
A units table plus one spec block per unit.

Table line format (spec-kit-derived, extended):
```
- [ ] B003 [type] [P?] [dep:B001,B002] <title> — budget: <n><unit>
```
- ID: `B` + 3 digits, sequential **in execution order**.
- type: one of `research | compose | revise | transform | verify | assemble`
  (P10 — the executor is told what kind of operation this is).
- `[P]` present only if the unit is genuinely independent of every incomplete
  unit AND touches no shared file/section.
- budget: `1200w`, `6slides`, `3files`, `10items`.
- `[X]` replaces `[ ]` only via tooling, only after verification passes.

Spec block per unit (all fields required, no placeholders):
```
### B003 — <title>
type: compose
budget: 1200w (±15%)
depends_on: [B002]
inputs:
  - path/to/source.md#L40-120        # explicit slices, not "the repo"
  - CHARTER.md
intent: |
  One paragraph. What this unit must accomplish, in terms a stranger could act on.
produces:            # interfaces/artifacts later units may rely on
  - term: "capacity ledger" defined
  - section: "3.2 Method"
verify:              # the external predicate(s). At least one MECHANICAL.
  - mechanical: word_count within 15% of 1200
  - mechanical: contains_headings ["3.2 Method"]
  - mechanical: no_placeholders
  - source: every numeric claim carries a [S#] tag present in inputs
  - charter: acceptance criteria 2, 5
waive: citation_tags — every figure is in a table verified by json_schema   # optional, see below
done_when: |
  One sentence, binary.
```

`mechanical:` predicates are decided by `bse.py check`. `source:` and
`charter:` are **judgement predicates**, decided by a reviewer pass and
recorded with `bse.py review ID --verdict pass|fail --report PATH`. Both are
gates: a unit that declares judgement predicates cannot be recorded `done`
without a stored `pass` review whose sha256 matches the artifact as it is now.

Plan validation gate (`bse.py plan --validate`), must pass before any execution:
unique IDs; every unit has budget, intent, >=1 mechanical verifier, done_when;
no placeholder strings (`TBD`, `etc.`, `similar to`, `as above`, `...`);
dependencies exist and are acyclic; `[P]` units share no `produces` targets;
a numeric verifier (`word_count`, `slide_count`, `item_count`) whose base is the
unit budget (`within N%`, `within N% of budget`, or no spec) counts the same
denomination the budget is expressed in (an explicit literal base is always
legal); sum of budgets within ±20% of the charter's total, checked per
denomination — a denomination budgeted in the plan but absent from the charter
total is reported as a warning, not silently ignored.

**Predicate adequacy** (also enforced at `--validate`; each error names the
unit, the rule in brackets, and the one-line fix):
- `[word_count]` — a unit whose budget denomination is words must declare a
  `word_count` mechanical verifier.
- `[citation_tags]` — a unit whose `inputs` name a *source* (anything other
  than `CHARTER.md`, `carry.md` and the run's own `batches/<ID>.md`, which
  were verified when they were recorded) must declare `citation_tags` or at
  least one `source:` predicate.
- `[no_conclusion]` — a `compose` unit that is not the last unit in the plan
  must declare `no_conclusion`.

Escape hatch: `waive: <rule> — <reason>` in the spec block (scalar, or a list
under `waive:`). A waiver needs a reason and must name one of the three rules;
`plan --validate` prints every waiver (`waiver: B004 citation_tags — ...`) and
returns them in `--json` under `waivers`, so an opt-out is visible, never
silent.

A plan with zero units is `PLAN EMPTY` (validate exit 1; `next` exit 1;
`status` prints `PLAN EMPTY`). A successful `--validate` stamps
`plan_validated` into `ledger.json`; `next` refuses (`PLAN NOT VALIDATED`,
exit 1) until that has happened once. `init` writes one real, uncommented
sample unit per charter denomination, sized to the charter total and titled
`SAMPLE unit — replace with your first real unit`, so the first `--validate`
passes; the validator warns while the sample is still present.

### 2.3 LEDGER.md
First line is the identity header — the resume anchor:
```
# BSE ledger — run: <run-id> — charter: <abs path to CHARTER.md> — created: <iso>
```
Then append-only lines, one per event:
```
B003 done     2026-09-12T18:44:10Z  artifact=batches/B003.md  words=1187  verify=pass(3/3)  sha=ab12cd3
B004 fix 1/3  2026-09-12T18:51:02Z  verify=fail(2/3): word_count 1740 outside 15% of 1200 [1020-1380]; placeholders: TBD 'TBD' L22  auto=check (artifact changed after a failing check)
B004 review pass  2026-09-12T18:57:01Z  predicates=2  report=reports/B004-review.md  sha=77f0e91
B004 done     2026-09-12T18:58:40Z  artifact=batches/B004.md  words=1240  verify=pass(3/3)  review=pass  sha=77f0e91
B005 blocked  2026-09-12T19:04:15Z  reason=source contradicts charter NN-3; needs human ruling
RULING        2026-09-12T19:20:33Z  unit=B005  use 2025 figures, not 2024 — matches audience expectation — cost if wrong: restate 2 charts
SEAM  B001-B006 2026-09-12T19:30:00Z  dedup=2 found; terminology drift=0
```
`verify=pass(n/n)` counts MECHANICAL predicates only (the §2.2 example unit has
three); judgement predicates (`source:`, `charter:`) are listed in
`reports/<ID>.md` and decided by the reviewer pass, whose verdict is its own
`review pass|fail` line keyed to the artifact sha. A `done` line for a unit
with judgement predicates carries `review=pass` (or `review=none`/`fail` with
`FORCED`). A `fix` line is written either by `record --status fix` (with its
`note=`) or by `check` itself (`auto=check`) when check is re-run on a changed
artifact after a failing check — so the 3-round cap cannot be evaded by
skipping `record --status fix`; an explicit fix record answering the same
failing artifact is consumed by the next check and is not counted twice. The
SEAM line reports what stitch FOUND — stitch never removes or rewrites
anything; dedup is the seam pass's job. `RULING` takes an optional `unit=<ID>`
(from `record RULING --unit ID`, validated against PLAN.md); unit-less rulings
stay legal. A partial stitch appends `; PARTIAL missing=<n> (<ids>)`.

**Resume rule (state verbatim in SKILL.md):** read LEDGER.md. If its first line
names this run's charter, every unit with a `done` line is COMPLETE — do not
re-execute it. Resume at the first unit without one.

### 2.4 ledger.json
```json
{"run_id":"...","charter":"...","created":"...","plan_validated":{"ts":"...","units":["B001",...]},
"units":{"B003":{"status":"done",
"artifact":"batches/B003.md","sha256":"...","words":1187,"verify":{"passed":3,"failed":0,
"checks":[...]},"attempts":2,"fix_rounds":1,"fix_recorded_for":null,"updated":"...",
"reviews":[{"verdict":"pass","sha256":"...","artifact":"batches/B003.md","report":"reports/B003-review.md",
            "predicates":["source: ...","charter: ..."],"note":null,"ts":"..."}],
"history":[{"status":"blocked","timestamp":"...","note":"source contradicts NN-3"},
           {"status":"done","timestamp":"...","note":null}]}},
"events":[{"ts":"...","kind":"ruling","unit":"B003","note":"...","line":"RULING ..."}, ...]}
```
`status` is the CURRENT state; `history` is appended on every status change
(blocked / fix / done), so ledger.json alone shows that a unit was once blocked
or failed even after it resumed to done. `reviews` is append-only; the review
that counts is the latest one whose `sha256` equals the artifact's current
hash — an edit after review makes it stale exactly as it stales `check`.
`fix_recorded_for` holds the failing sha an explicit `record --status fix`
answered, so the next `check` does not count that round again. Ledgers written
before these fields existed load unchanged (missing keys default).
`bse.py` writes both files atomically (write temp, os.replace). ledger.json is
authoritative; LEDGER.md is regenerated-append for humans.

### 2.5 carry.md (the baton) — max 400 words, hard-enforced
Fixed sections: `Established facts` (bullets, with [S#]), `Interfaces/terms now
defined`, `Open threads for later units`, `Do not repeat` (topics already
covered), `Tone calibration note` (<=2 sentences). Each unit REPLACES carry.md
with an updated version; it does not append forever.

## 3. The loop (seven moves)

CHARTER -> PLAN -> [ BRIEF -> EXECUTE -> VERIFY -> RECORD ] * N -> STITCH -> SEAM

1. **CHARTER** — negotiate and write the contract. Ask the user the minimum set
   of questions needed to make every acceptance criterion testable. One pass.
2. **PLAN** — produce the unit table + spec blocks, validate, and show the user
   the plan and the cadence estimate before executing. This is the only
   approval gate in the normal path.
3. **BRIEF** — generate `briefs/<ID>.md` = CHARTER + this unit's spec block +
   current carry.md + the named input slices. Nothing else.
4. **EXECUTE** — fresh context. Either a delegated subagent (preferred) or an
   inline pass after clearing. Input is the brief FILE PATH. Output is written
   to `batches/<ID>.md` by the executor. Forbidden to the executor: the full
   plan, other batches' text, the conversation history, pre-judgments about
   what the verifier should ignore.
5. **VERIFY** — two gates. `bse.py check <ID>` runs the mechanical predicates
   and reports both halves (`B003 check PASS (4/4 mechanical; 2 judgement
   predicates pending review)`). Where the unit declares source/charter
   predicates, a reviewer pass whose prompt contains the brief, the artifact,
   and the predicates ONLY decides them, and its verdict is recorded with
   `bse.py review <ID> --verdict pass|fail --report <path>` (a usage error for
   a unit with no judgement predicates). Fail -> fix round (max 3; `check`
   counts a round itself whenever it is re-run on a changed artifact after a
   failing check) -> if still failing, shrink the unit (split into
   <ID>a/<ID>b) or mark blocked and surface to the user. Never mark done on a
   failing predicate.
6. **RECORD** — `bse.py record` appends ledger + updates carry.md. It refuses
   `done` when the check failed, was never run, is stale, or a declared
   judgement predicate has no matching passing review; `--force` overrides and
   stamps `FORCED`. Only now is the unit `[X]` in PLAN.md. `audit` reports
   `CARRY_STALE` (error) when two or more units are done and carry.md is still
   the init scaffold or empty; `carry --check` exits 1 in that state.
7. **STITCH, then SEAM** — `bse.py stitch` concatenates in plan order into
   `draft.md` (machine output; prepends `front-matter.md` and appends
   `back-matter.md` when they contain prose; exits 1 on a complete stitch more
   than ±20% off the charter target unless `--allow-drift`; reminds you when
   every unit is done and the seam-pass files are still empty). Then the SEAM
   PASS runs by hand: read the draft against the through-line, cross-unit
   dedup, transition repair, terminology conformance against the charter lock
   list, and only then `front-matter.md` / `back-matter.md` (intro, executive
   summary, conclusion) which are always written LAST because they depend on
   everything — and finally `final.md`, the deliverable, which the tool never
   generates. `audit` reports `SEAM_PASS_MISSING` (error once every unit is
   done; info after a partial stitch) and `FINAL_STALE` when `final.md` is
   older than `draft.md`. Hand `final.md` to the format skill
   (docx/pptx/xlsx/pdf) for rendering. **Batches never write the final binary
   format.**

### 3.1 Cadence / reporting contract
Default: report to the user after every batch with one line —
`B004 done (1,240w, 4/4 checks, review pass) — 4 of 17 units, ~38 min remaining`. Optionally
deliver the interim markdown. Configurable to every N batches for long runs.
Target 5-10 minutes of agent work per batch.

### 3.2 Modes
- `solo` — one session, clear/compact between batches. Cheapest. Use <8 units.
- `delegated` (DEFAULT) — supervisor holds only ledger + plan; a fresh subagent
  per batch; a separate reviewer subagent for judgment predicates.
- `wave` — parallel batch of `[P]` units, max 4 concurrent, mandatory
  reconciliation pass after each wave. Only for independent, non-narrative units
  (e.g. 80 slides of per-slide edits, per-file refactors). Never for prose that
  must flow.
- `relay` — run spans sessions/days; each new session bootstraps from the ledger
  identity header. Nothing else is assumed.

### 3.3 Model tiering (state explicitly, never inherit)
mechanical/transform units -> fast cheap model; compose/revise -> mid;
plan authoring, seam pass, final review, any ruling -> most capable.

## 4. Batch sizing (the tables SKILL.md must carry)

| Unit type | Default batch | Hard ceiling | Shrink when |
|---|---|---|---|
| Prose (new) | 800–1,200 finished words | 1,500 | dense citation, >3 sources, technical derivation |
| Prose (revision to feedback) | 6–10 discrete feedback items | 15 | items interact, or any item is structural |
| Slides (create) | 4–6 slides | 8 | heavy data per slide, or bespoke layouts |
| Slides (edit to spec) | 8–12 slides | 20 | per-slide judgment required |
| Code | 1 vertical slice / feature | ~400 changed lines | crosses module boundaries |
| Data/sheets | 1 sheet or 1 derived table | 2 | formula chains cross sheets |
| Extraction/research | 5–8 sources | 12 | sources are long or conflicting |

Universal rules:
- A batch must fit comfortably in one context with room to spare: never plan a
  unit whose brief + inputs + expected output exceeds ~40% of the executor's
  usable window.
- Two consecutive verification failures on a unit = the unit is too big. Split it.
- Never size by "how much can the model do" — size by "how much can be verified
  in one predicate set."
- Total units should be >= 5. If a deliverable decomposes into fewer than 5
  units, BSE is overhead; say so and do it directly.

## 5. Failure modes and their guards (must appear in SKILL.md)

| Failure | Guard |
|---|---|
| One-shotting (tries everything at once) | Plan gate; executor receives ONE unit's brief |
| False victory (claims done, isn't) | P6 — only work passing mechanical checks AND any declared review is recorded |
| Stale baton (every unit gets the same carry) | `audit` CARRY_STALE / `carry --check` after the second done unit |
| Empty plan mistaken for a finished one | `next`/`status` say PLAN EMPTY; `next` refuses a never-validated plan |
| Re-doing completed work after compaction | Ledger identity header + resume rule |
| Drift from charter | Charter in every brief; terminology lock; charter predicates |
| Seam damage (repetition, tonal breaks) | carry.md "do not repeat" + seam pass + no mid-work conclusions |
| Premature conclusions mid-draft | Executor instruction: never write concluding/summarizing language; the work is ongoing |
| Thrash (fix rounds forever) | Max 3 fix rounds, counted by `check` itself, then split or block |
| Stall (no ledger advance in 2 units) | Re-plan trigger: return to PLAN, do not retry |
| Context bloat in supervisor | Supervisor reads only ledger/plan/status; artifacts by path |
| Silent scope growth | Budget sum check vs charter at plan validate; stitch exits 1 beyond ±20% unless --allow-drift |
| Shipping draft.md as the deliverable | final.md is written by hand; stitch refuses to write it; audit flags a missing or stale final.md |

## 6. `scripts/bse.py` — CLI contract (Python 3.9+, **stdlib only**)

Single file. No third-party imports. Must run on Windows and POSIX.
Exit 0 on success, 1 on validation/verification failure, 2 on usage error.
Every command supports `--run-dir PATH` (default: `./.bse/<most recent>`)
and `--json` for machine-readable output.

```
bse.py init --run-id ID [--title T] [--total "20000w, 40slides"]  # scaffold run dir + templates + one SAMPLE unit
bse.py plan --validate                                     # schema + placeholder + dep + budget + predicate-adequacy checks; lists waivers
bse.py status                                              # table: id, type, status, attempts, budget, words, review; PLAN EMPTY / NOT VALIDATED
bse.py next [--all]                                        # next unblocked unit ID; exit 1 on an empty or never-validated plan
bse.py brief ID [--out PATH]                               # assemble self-contained brief file
bse.py check ID [--artifact PATH] [--force]                # mechanical verifiers -> reports/ID.md; counts fix rounds (cap 3)
bse.py review ID --verdict pass|fail --report PATH [--note N]   # reviewer verdict on judgement predicates, keyed to artifact sha
bse.py record ID --status done|blocked|fix [--artifact P] [--carry F] [--note N] [--force]
bse.py record RULING --note N [--unit ID]                  # human ruling, optionally linked to a unit
bse.py carry --set FILE | --show | --check                 # replace/print/test the baton (400-word cap; --check exits 1 when stale)
bse.py stitch [--out draft.md] [--partial] [--no-front-matter] [--allow-drift]   # ordered assembly + report; never final.md
bse.py audit                                               # ledger vs filesystem consistency; phantom-complete, stale carry, seam pass
```

`review` exits 0 on a `pass` verdict and 1 on `fail` (like `check`); it is a
usage error (2) for a unit that declares no judgement predicates, or when
`--report` does not name an existing, non-empty file.

### 6.1 Mechanical verifiers (implement all; extensible registry)
- `word_count within N% of B` — a word is a whitespace-delimited token
  containing at least one letter or digit, counted over every prose line
  (headings and list text included); fenced code blocks and HTML comments are
  EXCLUDED. `B` may be a literal or `budget` (the default when omitted).
- `no_placeholders` — regex list: `\bTBD\b`, `\bTODO\b`, `\[insert`, `\bLorem`,
  `\betc\.`(only when line-final), `as (described|above)`, `XXX`, plus
  angle-bracket placeholders in prose: a `<...>` span counts only when it
  contains whitespace or placeholder vocabulary (insert, your, name, title,
  date, tbd, todo, xxx, placeholder, description); known HTML tags (`<br>`,
  `<sub>`), closing tags (`</sub>`) and autolinks (anything containing `://`
  or `@`) are never flagged. Code spans and comments are excluded.
- `contains_headings [..]` — exact heading text present.
- `max_heading_depth N`
- `citation_tags` — every SENTENCE containing a digit-with-unit or a year must
  carry a `[S\d+]` tag, when the unit declares it. Physical lines within a
  paragraph (or a list item and its continuation lines) are joined before
  splitting on terminal punctuation, so hard-wrapped prose with the tag on the
  next line counts as tagged; a tag written after the period (`12%. [S1]`)
  belongs to the sentence it follows. Headings and fenced code are exempt.
- `forbidden_phrases [..]` — from charter terminology lock (wrong forms) and
  from carry.md "do not repeat".
- `slide_count`, `item_count`, `file_exists`, `json_schema` (stdlib json only),
  `shell` (run a command, non-zero = fail) — opt-in per unit.
- `no_conclusion` — flags concluding language (`in conclusion`, `to summarize`,
  `overall,` at final paragraph) in non-final units.

### 6.2 `stitch` behavior
- Order strictly by PLAN unit order; refuse to stitch if ANY unit (`[P]` or
  not) is incomplete — not `done`, or `done` with a missing artifact — unless
  `--partial` is given. With `--partial`: insert `<!-- MISSING B00X -->`, list
  every missing unit in `reports/stitch.md` under "Missing units", stamp the
  SEAM ledger line `PARTIAL missing=<n>`, exit 0, and print a clear
  `WARNING: PARTIAL stitch` line.
- Emit `draft.md` plus `reports/stitch.md` containing: per-unit word counts,
  total vs charter target, **duplicate-content report** (normalized sentence
  hashing; report any sentence >=12 words appearing in 2+ units), terminology
  violations, and a seam list (adjacent unit boundaries with the last/first 30
  words, for the seam pass to inspect).
- Never modify batch files. Never write `final.md` (`--out final.md` is a
  usage error).
- Front/back matter: prepend `front-matter.md` and append `back-matter.md`
  by default when they contain prose (the commented `init` scaffold does
  not count); otherwise insert a `<!-- FRONT MATTER: ... not yet written -->`
  marker. `--no-front-matter` suppresses both. When every unit is done and
  either file has no prose, print a reminder that the seam pass has not run.
- Budget gate: on a complete (non-partial) stitch, total words more than
  ±20% from the charter target prints `WARNING: BUDGET DRIFT` and exits 1
  unless `--allow-drift`; the draft and report are still written. Partial
  stitches are under budget by construction and are exempt.

### 6.3 `audit`
Detects: units marked done whose artifact is missing/empty/hash-mismatched;
units done with a failing stored verify record; units done with judgement
predicates but no stored `pass` review for the recorded sha
(`DONE_WITHOUT_REVIEW` / `DONE_WITH_FAILING_REVIEW`); plan units absent from
ledger; ledger entries for unknown units; carry.md over cap; `CARRY_STALE` —
two or more units done and carry.md still the init scaffold or empty;
`SEAM_PASS_MISSING` — every unit done and no `final.md`; `FINAL_STALE` —
`final.md` older than `draft.md` once every unit is done; budget drift >20%
(per denomination, against the charter's totals). Informational findings
(reported with `level: info`, never a failure / exit 1): `BLOCK_WITHOUT_RULING`
— a unit whose history shows a block later resolved (fix/done) with no RULING
event (unit-linked or unit-less) recorded in between; `PLAN_BUDGET_UNCHECKED`
— a denomination budgeted in the plan with no charter total to compare
against; `SEAM_PASS_MISSING` / `FINAL_STALE` while units are still incomplete
(only reported once a draft.md exists); `SEAM_PASS_INCOMPLETE` — final.md
exists but front- or back-matter.md still has no prose.

## 7. Tests (`tests/test_bse.py`, stdlib `unittest`, no network)
Must cover, at minimum: init scaffolding; plan validation happy path + each
failure (dup id, cycle, missing budget, placeholder, budget drift);
next/dependency resolution incl. `[P]`; brief assembly contains charter+spec+carry
and nothing else; each mechanical verifier pass and fail; record refuses `done`
when checks failed; resume (ledger replay after simulated context loss);
stitch ordering + duplicate detection + partial mode; audit catches phantom
complete and hash mismatch; carry word cap; atomic write leaves no temp files;
Windows path handling (use pathlib, no hardcoded `/`); the review gate
(usage error without judgement predicates, refusal without a matching pass,
stale after an edit, --force stamps FORCED, status/check report the halves);
seam-pass files (init scaffold, stitch inclusion/suppression, final.md never
written, SEAM_PASS_MISSING/FINAL_STALE levels); CARRY_STALE and `carry
--check`; each predicate-adequacy rule and waiver listing; fix rounds counted
by `check` without double-counting explicit records, capped at 3; empty and
never-validated plans; the init sample unit validating per denomination; the
stitch drift gate; the item-denominated charter total; the CI examples job.
Target: >=35 test cases, all passing via `python -m unittest discover tests`
(currently 127).

## 8. Repo layout (final)
```
batched-sequential-execution/
  SKILL.md                     # the skill itself (root = drop-in skill dir)
  README.md                    # what/why/install/quickstart/evidence summary
  LICENSE                      # MIT, Eric Tucker
  DESIGN.md                    # this file (kept, trimmed, as contributor doc)
  .claude-plugin/plugin.json   # plugin manifest
  .claude-plugin/marketplace.json
  scripts/bse.py
  references/
    batch-sizing.md  ledger-and-state.md  verification.md  stitching-and-seams.md
    composition.md   failure-modes.md     evidence.md      prompts.md
  templates/
    CHARTER.md  PLAN.md  LEDGER.md  carry.md  brief.md  executor-prompt.md
    reviewer-prompt.md
  examples/
    20k-word-report/  80-slide-deck/  feedback-sweep/
  tests/test_bse.py
  .github/workflows/test.yml   # py_compile + unittest on push (3.9-3.13), then plan --validate /
                               # status / audit against every examples/*/ run dir (non-zero exit fails)
```

## 9. SKILL.md constraints
- YAML frontmatter: `name`, `description` (third person, trigger-rich, <1024
  chars, names the triggers: long document, many slides, multi-step build,
  large feedback sweep, "chunked", "batched", "too big for one pass").
- Body <= ~500 lines; everything else lives in references/ and is loaded
  on demand (progressive disclosure).
- Must contain: when to use / when NOT to use, the seven moves, the sizing
  tables, the resume rule verbatim, the executor "never pass" list, the
  verification discipline, the composition contract with other skills, and
  the CLI quick reference.
