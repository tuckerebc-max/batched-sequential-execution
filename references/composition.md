# Composition

This skill is an execution wrapper, not a content authority. It has an opinion
about cadence and verification and none at all about what "good" means for any
particular domain — that division is what lets it compose.

## The three-layer division

| Layer | Decides | Example |
|---|---|---|
| Domain skill / workbench | What good looks like: voice, method, standards, what counts as correct | A research-writing skill's house style; a codebase's lint rules and test conventions; a brand's slide template |
| **This skill (BSE)** | How much work happens at once, in what order, and what must be true before it counts | Unit sizing, the plan gate, briefs, fix-round caps, the ledger |
| Format skill | Renders the finished, verified markdown into its final shape | docx/pptx/xlsx/pdf skills |

BSE never decides whether a paragraph is well-argued or whether code follows
house style — those are charter content the calling layer supplies. BSE
decides whether that paragraph's unit is the right size to verify reliably,
and whether it actually got verified before it was recorded.

## The handoff contract

A calling skill supplies, to start a run:

| Field | Goes into |
|---|---|
| The deliverable and its target size | CHARTER.md `Deliverable` (the `Total size:` line the budget-sum check reads) |
| Audience and voice/register, if the domain skill has house style | CHARTER.md `Audience` / `Voice & register` |
| Non-negotiables and acceptance criteria the domain skill already knows | CHARTER.md `Non-negotiables` / `Acceptance criteria` — these become `charter:` predicates units can cite by number |
| Authoritative sources, with ids | CHARTER.md `Sources of truth` — the only things a brief may cite as `[S#]` |
| Terminology the domain skill enforces | CHARTER.md `Terminology lock` — doubles as a free `forbidden_phrases` predicate |
| Preferred mode and model tiering, if the caller has a preference | Run configuration (§3.2/3.3 of the loop) — otherwise BSE's defaults apply |

BSE returns, when the run completes:

| Field | What it is |
|---|---|
| `final.md` | The stitched, seam-passed markdown — the thing to hand to a format skill or return directly. (`draft.md` is the intermediate machine assembly the seam pass starts from; it is never the return value.) |
| `ledger.json` / `LEDGER.md` | The full audit trail: what was produced, when, against which predicates, with how many fix rounds |
| `reports/stitch.md` | Word-count drift, duplicate content, terminology violations — worth surfacing to the caller even on a clean run |
| The run directory itself | Everything is inspectable after the fact; nothing needed for the deliverable lived only in conversation |

## Worked integration sketches

**(a) A research/writing workbench producing a long report.** The workbench's
research phase already knows its sources; it hands them straight into
`Sources of truth` with `[S#]` ids rather than BSE re-deriving them. The
workbench's editorial standards (citation format, banned words) become the
terminology lock and a `citation_tags` predicate on every unit that carries
data. BSE runs CHARTER → PLAN → the batch loop → STITCH → the seam pass; the
workbench takes `final.md` back for its own further editorial read before
sending it onward (that read is domain judgment layered on top of BSE's own
seam pass, not a substitute for it).

**(b) A deck-production workflow.** The deck skill owns the visual template
and brand rules; those become `Voice & register` and `Non-negotiables` in the
charter (e.g., "every slide uses the two-column layout for data slides"). BSE
sizes and batches slide creation per [batch-sizing.md](batch-sizing.md)'s
slide bands, using `wave` mode for independent sections of the deck (each
section is a `[P]` unit) with the mandatory reconciliation pass catching any
duplicate slide numbering or repeated agenda slides. The pptx skill renders
only after stitch and the seam pass — never per-unit.

**(c) A codebase refactor.** The dev-standards skill supplies lint config and
the test command as a `shell` predicate every unit declares. BSE sequences
vertical slices, each depending on the ones that define shared interfaces it
touches. Wave mode is legitimate only for genuinely independent modules with
no shared file in either's `produces:` — the plan validator already refuses
`[P]` units that collide there.

**(d) A coordination layer assigning work to agents.** Here PLAN.md *is* the
assignment queue and `bse.py next` / `brief` / `check` / `record` are the
shared API a fleet of agents uses instead of each agent inventing its own
notion of "what's next." The coordination layer's job shrinks to picking which
agent executes the unit `next` returns; the ledger is the single source of
truth that prevents two agents from claiming the same unit, and `audit`
catches an agent that crashed mid-unit without a clean `blocked`/`fix` record.

## Skipping the plan move

If the caller already has a plan — a workbench's own outline, a coordination
layer's task graph — don't re-derive one. Translate it into PLAN.md's schema
(table line + spec block per item, per [ledger-and-state.md](ledger-and-state.md))
and run `bse.py plan --validate` directly. Skipping PLAN means skipping the
authoring effort, never the validation gate — an imported plan is exactly as
likely to have a missing budget or a placeholder as a newly written one.

## Nesting

A unit whose own scope turns out to warrant its own charter, plan, and ledger
is a legitimate nested BSE run — for example, one "chapter" unit inside a
book-level plan that, once briefed, is clearly a 15-unit job in its own right.
The nested run must terminate in a single artifact that satisfies the *parent*
unit's own `verify:` predicates; the parent's ledger records that one
`done` line, not the child run's internal history (the child run directory
stays as its own audit trail, referenced but not flattened in).

Nesting is a mistake when it's used to dodge BSE's own discipline at the
current level: splitting a 6-unit plan into six nested one-unit "runs" to avoid
writing real budgets, or using a nested run to route around the 5-unit
overhead threshold. If a unit needs its own plan, that's a sign the *parent*
plan under-decomposed it — reconsider the parent plan before nesting.

## Subagents vs. inline, and model tiering

Delegated mode (the default) dispatches a fresh subagent per unit because
context isolation is the mechanism, not a preference (P4, P7) — an inline pass
only approximates it if the context is actually cleared between units, which
is why inline execution is restricted to `solo` mode under roughly 8 units,
where one operator can enforce that discipline by hand.

Assign models explicitly per role, never by inheritance from whatever model is
running the supervisor:

| Role | Tier |
|---|---|
| Mechanical / transform units | fast, cheap |
| Compose / revise units | mid |
| Reviewer pass (judgment predicates) | mid or higher — it must be capable enough to catch what the executor might have missed |
| Plan authoring, seam pass, final review, any ruling | most capable available |

## Related

- [Ledger and state](ledger-and-state.md) — the file formats a calling skill hands off through
- [Batch sizing](batch-sizing.md) — sizing units per the domain's own operation types
- [Stitching and seams](stitching-and-seams.md) — what a format skill receives, and what it must not receive earlier
- [Failure modes](failure-modes.md) — what happens when a caller changes the charter mid-run
