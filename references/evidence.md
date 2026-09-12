# Evidence

Every design choice in this skill traces to something published. Where a source is
industry research rather than peer-reviewed, it is marked. Where a number is
widely repeated but unverified, it is marked too.

## 1. Why one big pass fails

**Output length is bounded by training, not architecture.** LongWriter
([arXiv:2408.07055](https://arxiv.org/abs/2408.07055), ICLR 2025) shows models
"consistently fail to produce outputs beyond 2,000 words" and traces the ceiling
to SFT data: restrict training outputs to 500 / 1,000 / 2,000 words and the
resulting models top out near 600 / 900 / 1,800. The ceiling moves with the data,
which is why a harness that stays under it works.

**Long context degrades non-uniformly.** *Lost in the Middle*
([arXiv:2307.03172](https://arxiv.org/abs/2307.03172), TACL 2024): with 20
documents, GPT-3.5 accuracy runs 75.8% when the answer is first, 53.8% in the
middle, 63.2% at the end — and the middle case falls *below* the 56.1% closed-book
baseline. Supplying the right material in the wrong place is worse than supplying
nothing. Bigger windows did not fix it: 4K and 16K performance curves were
"nearly superimposed" on inputs that fit both.

**Context rot.** Chroma's [context rot report](https://www.trychroma.com/research/context-rot)
(2025, 18 models; industry research, not peer-reviewed) finds reliability falls
with input length even on tasks with zero reasoning content — models asked merely
to replicate repeated words under-generate, hallucinate, and refuse as length
grows. On LongMemEval, the *same* question with the *same* answer is near-perfect
in a 300-token prompt and materially degraded at 113k. Distractors compound:
irrelevant prior material is not neutral padding.

Anthropic frames the same effect as a finite
[attention budget](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
depleted by every token: "as the number of tokens in the context window increases,
the model's ability to accurately recall information from that context decreases."

**Errors self-condition.** *The Illusion of Diminishing Returns*
([arXiv:2509.09677](https://arxiv.org/abs/2509.09677), ICLR 2026) isolates
execution from reasoning by handing the model both the knowledge and the plan, and
finds long-task failure is execution failure. Per-step accuracy does not stay
constant — it *decays*, because a model's own prior errors in context make further
errors likelier. Qwen3-32B has near-perfect single-step accuracy yet falls below
50% within 15 turns. Injecting artificial errors at 0% / 20% / 50% monotonically
degrades turn-100 accuracy, and scale does not fix it.

→ **Design consequence:** fresh context per unit (SKILL.md move 4), and curated
briefs rather than accumulated transcript (move 3).

## 2. Why planning carries the quality

**Outline depth outperforms better drafting.** DOC
([arXiv:2212.10077](https://arxiv.org/abs/2212.10077), ACL 2023) adds a detailed
hierarchical outliner plus a controller that enforces it, and beats the Re3
baseline by +22.5% plot coherence, +28.2% outline relevance, +20.7%
interestingness on human evaluation — from planning, not from drafting.

**Explicit budgets are the control signal.** AgentWrite (the harness inside
LongWriter) plans paragraph-by-paragraph with a word count attached to each item,
then writes them in sequence. On LongBench-Write, GPT-4o goes 78.6 → 89.1 overall,
with length adherence 65.3 → 86.6, at a quality cost of 0.2 points.

**Type your units.** WriteHERE
([arXiv:2503.08275](https://arxiv.org/abs/2503.08275); an EMNLP 2025 listing
exists but the venue could not be confirmed from the arXiv record) labels tasks
as retrieval / reasoning / composition. In its ablation — overall score on the
TELL ME A STORY set with a GPT-4o backbone, a single dataset and a single
backbone — removing task typing dropped the score from 2.143 to 0.717 (-67%) and
removing recursive decomposition dropped it to 1.100 (-49%). On that evidence,
telling the executor what *kind* of operation it is doing mattered more than the
decomposition structure. Generalizing it beyond long-form narrative writing is an
inference, not a finding.

**Allow decomposition during execution.** The same work interleaves planning with
execution rather than planning to completion first, and its margin over
fixed-workflow baselines *widens* with length (beating Agents' Room on >50% of
8,000-word samples). Hence: a unit that discovers it is too big should split
rather than push through.

→ **Design consequence:** the plan schema (budget, type, produces, done_when), the
plan validation gate, and the "stop and split" instruction to executors.

## 3. Why serial with a baton, and what parallel costs

AgentWrite's ablation, with its baselines named precisely, because the two
numbers have different denominators: AgentWrite (serial, each chunk seeing the
prior text) versus direct single-pass generation improves breadth and depth by
about 5% while costing about 2% on coherence and clarity. The `+Parallel`
variant — chunks generated without the prior text — then costs a further **6% of
coherence relative to serial AgentWrite**. The comparison that matters for this
skill is the second one: naive fan-out costs roughly six points of coherence
against the serial baton, not against a single pass.

STORM ([arXiv:2402.14207](https://arxiv.org/abs/2402.14207), NAACL 2024) does
parallelize sections — and pays for it with an explicit cross-section
deduplication pass plus a lead section written last, after everything else exists.
Its gains concentrate in outline metrics (heading soft recall 86.26 vs 73.59) far
more than in article metrics, which is the planning lesson again.

Chain of Agents ([arXiv:2406.02818](https://arxiv.org/abs/2406.02818), NeurIPS
2024) is the reading-side mirror: workers process consecutive chunks, each
receiving the previous worker's free-form "communication unit". Up to 10% over
RAG and full-context baselines across nine datasets, with the advantage *growing*
at length — on BookSum, a reported improvement around 100% beyond 400k tokens
versus a 200k full-context baseline. (That figure comes from the abstract and
Google's research blog; the per-dataset tables could not be independently
verified, so treat the direction as well-supported and the magnitude as
indicative.) Chunking is not only a workaround for small windows.

→ **Design consequence:** serial by default with a bounded 400-word carry
(the baton); wave mode restricted to independent units and gated on a mandatory
reconciliation pass; front and back matter written last.

## 4. Why verification must be externally anchored

Reflexion ([arXiv:2303.11366](https://arxiv.org/abs/2303.11366)) reaches 91%
pass@1 on HumanEval with verbal self-reflection stored in an episodic buffer.
Self-Refine ([arXiv:2303.17651](https://arxiv.org/abs/2303.17651)) reports ~20%
average absolute improvement across seven tasks.

But *LLMs Cannot Self-Correct Reasoning Yet*
([arXiv:2310.01798](https://arxiv.org/abs/2310.01798), ICLR 2024, Google DeepMind)
shows those gains depend on an external signal. Intrinsic self-correction
**degrades** performance: GPT-3.5 on CommonSenseQA falls 75.8 → 38.1 after one
round; GPT-4 on GSM8K falls 95.5 → 89.0 without oracle feedback, but rises to 97.5
with it. The oracle's real contribution is telling the model *when to stop*.

Reflexion works because HumanEval has unit tests. Self-Refine works on tasks with
checkable rubrics. There is no free lunch in "now critique your own prose".

**Error correction at the unit level is cheap relative to its payoff.** MAKER
([arXiv:2511.09030](https://arxiv.org/abs/2511.09030)) completes a 1,048,575-step
task with zero errors by decomposing to one step per agent and voting
first-to-ahead-by-k; the required k grows as Θ(ln s) in the number of steps —
logarithmic, not linear. Monolithic agents on the same task derail within a few
hundred steps. The task is Towers of Hanoi — a synthetic, mechanically checkable
sequence, about as far from prose composition as a task can be. It is cited here
for one transferable point only: the *cost curve* of per-unit error correction is
logarithmic in run length, which is why a verification gate on every unit remains
affordable as runs get long. It is not evidence about writing quality.

→ **Design consequence:** at least one mechanical predicate per unit; reviewer
prompts that carry the predicates and nothing else; a hard cap of 3 fix rounds;
and the rule that the model's own satisfaction is never the halting condition.

## 5. Why state lives in files

Anthropic's
[Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
describes an initializer agent that writes a feature list as a JSON state machine
(every item marked failing), a progress file, and a baseline commit — after which
each session begins with a fixed orientation ritual: read the git log and progress
file, review the feature list, run end-to-end tests *before* new work. It names the
failure modes directly: one-shotting, false victory, undocumented state, premature
completion. Its central operational rule: "work on only one feature at a time…
this incremental approach turned out to be critical to addressing the agent's
tendency to do too much at once." And on context management alone: "compaction
isn't sufficient."

Anthropic's context engineering post adds the three long-horizon techniques this
skill uses: **compaction**, **structured note-taking** persisted outside the
context window, and **sub-agent architectures** where each subagent explores
widely but returns a condensed 1,000–2,000 token summary.

Microsoft's Magentic-One (in
[AutoGen](https://microsoft.github.io/autogen/stable//user-guide/agentchat-user-guide/magentic-one.html))
contributes the vocabulary and the split this skill's CHARTER/LEDGER pair follows:
an outer loop maintaining a **task ledger** of facts and plan, an inner loop
maintaining a **progress ledger**, and re-planning — not retrying — when progress
stalls.

→ **Design consequence:** the run directory, the append-only ledger with an
identity header, the resume rule, `audit`, and the stall trigger.

## 6. Field-tested harnesses this design borrows from

| Source | Borrowed |
|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) (`subagent-driven-development`) | The ledger with an identity header and the resume-rule pattern (read the ledger, treat what it marks done as done, resume at the first gap); the "never pass a subagent" list; artifacts passed as file paths; explicit model tiering; capped fix rounds. Its stated justification is the best argument for ledgers in the wild: conversation memory does not survive compaction, and controllers that lost their place have re-dispatched entire completed task sequences. |
| [github/spec-kit](https://github.com/github/spec-kit) | A task-line schema derived from spec-kit's `tasks.md` (`- [ ] T001 [P] description`), IDs sequential in execution order, `[P]` only for genuinely independent units, a write-back checkbox as the resume marker, halt-on-failure. Its [complex features guide](https://github.github.com/spec-kit/concepts/complex-features.html) prescribes batching by task range or phase precisely to avoid context exhaustion. |
| [AMAP-ML/LongHorizon-Harness](https://github.com/AMAP-ML/LongHorizon-Harness) | The load-bearing invariant: only results that pass independent verification enter persistent task state. Manager / Executor / Auditor separation, fresh context per round. |
| [THUDM/LongWriter](https://github.com/THUDM/LongWriter) (AgentWrite prompts) | Word budgets per plan item; the 200–1,000 word band; and the instruction that a chunk must not write a conclusion because the work is ongoing. |
| [stanford-oval/storm](https://github.com/stanford-oval/storm) | Per-unit retrieval slices with a hard cap; parallel sections paid for with a dedup pass; the lead section generated last. |
| [Roo Code Boomerang tasks](https://roocodeinc.github.io/Roo-Code/features/boomerang-tasks/) | The isolation contract stated plainly: a subtask does not inherit the parent's context, so the dispatch message is the entire context budget. |
| [eyaltoledano/claude-task-master](https://github.com/eyaltoledano/claude-task-master) | A queryable next-unit primitive rather than a readable list; complexity analysis driving how far to expand a task. |
| [Claude Code subagents](https://code.claude.com/docs/en/sub-agents) | The precise context boundary — a subagent does not receive conversation history, and does not receive files the main conversation already read. Per-agent model and turn budgets. |
| [Cline memory bank](https://github.com/cline/prompts/blob/main/.clinerules/memory-bank.md) | Files as the only link across resets — with the caveat that a six-file mandatory read is a context tax, which is why this skill uses one charter, one plan, one ledger, and one bounded carry. |

## 7. Known gaps

- The 200–1,000 word chunk band from LongWriter is a prompt constant, not an
  ablated optimum; the paper offers no chunk-size study. Treat the sizing tables
  as calibrated defaults, not findings.
- Chain of Agents' per-dataset deltas could not be verified from the abstract and
  blog alone.
- MAKER reports no dollar cost for the million-step run.
- "One story per context window" is community canon around BMAD-METHOD but is not
  verifiable in its first-party docs; the weaker documented form is "start a new
  chat for each major workflow".
- METR's horizon doubling (~7 months,
  [arXiv:2503.14499](https://arxiv.org/abs/2503.14499)) is measured at 50% success;
  the 80% horizon is substantially shorter. Sizing here targets reliability, not
  the 50% frontier.
