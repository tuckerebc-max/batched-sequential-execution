# Light mode

Full mode exists to make a claim auditable: a ledger, a validator, external
predicates, a resume rule. Most jobs don't need that claim — they need the
other half of the benefit, which is just: don't try to write 6,000 words in
one pass. Light mode is that half, stripped to what fits in your own working
memory instead of a run directory.

There is no tool for this. No `.bse/`, no `ledger.json`, no `bse.py`. Four
small files, kept in the conversation or the working directory, and a loop
you run yourself.

## The loop

1. **Charter — half a page.** One sentence **through-line** (what the
   finished piece argues), a short **terminology lock** (wrong form →
   approved form), and numbered **sources** (`[S1]`, `[S2]`, …) if the piece
   cites anything. Nothing else — no audience/voice essay, no acceptance
   criteria list.
2. **Outline — numbered, with a word budget per item.** Each item is one
   pass's worth of work, sized the same way full mode sizes a unit (roughly
   800–1,200 words; see [batch-sizing.md](batch-sizing.md)).
3. **Execute one item at a time**, in order, each in a fresh pass. Read the
   charter and the carry note (below) before writing; write only that item.
4. **Carry note — five lines, replaced each time.** After finishing an item,
   write down: what's now established, what must not be repeated, and the
   tone to match. Five lines is the budget, not a minimum — shorter is fine.
5. **Finished list — plain text.** Append the item number and a word count
   once it's done. This is a note to yourself, not a gate — see the honesty
   note below.
6. **One seam pass at the end.** Read the whole assembled draft once. Fix
   any repeated sentence, any tonal jump at a join, any terminology-lock
   miss. Only now write the intro and the conclusion — the same reason full
   mode defers them: they make claims about a whole that doesn't exist yet.

No run directory. No validator. No subagents. No predicate beyond word count
and the terminology lock, both checked by eye (or a word-count tool if one
is handy) — not by an external script that refuses bad work.

## Worked example: a 6,000-word explainer in 6 units

**charter.md**

```
Through-line: adjustable-rate mortgages shifted risk to borrowers faster
than most disclosure rules kept up with.

Terminology lock:
- ARM -> adjustable-rate mortgage
- teaser rate -> introductory rate

Sources:
[S1] cfpb-arm-report-2024.pdf
[S2] fed-survey-notes.md
```

**outline.md**

```
1. What an ARM is and how the rate resets — 1000w
2. The introductory-rate period and why it's short — 900w
3. How resets are indexed and capped — 1100w
4. What disclosure rules require today [S1] — 1000w
5. Where borrowers are still under-informed [S1][S2] — 1000w
6. What a tighter disclosure rule would change — 1000w
```

**carry.md** (as it stood after finishing item 3, before starting item 4)

```
Established: rate resets to index + margin, within the cap [S1].
Don't repeat: the definition of "introductory rate" (done in item 2).
Tone: plain, second person ("you"), no jargon left undefined.
```

**finished.txt**

```
1  1020w
2   880w
3  1140w
4  1010w
5   970w
6  1030w
```

Total: 6,050w against a 6,000w target — no drift check beyond eyeballing
it. The seam pass then reads all six in order, fixes the item-3/item-4 join
(item 4 opened as if item 3 hadn't just defined "cap"), and writes a 150-word
intro and 150-word conclusion last.

That's the whole apparatus. It fits on one screen because it's supposed to.

## When to escalate to full mode

Move to full mode — the run directory, the validator, `bse.py`, the ledger —
the moment any of these becomes true. Check this list before you start, not
after light mode has already strained:

- [ ] The run will span multiple sessions, days, or a context reset.
- [ ] It's more than roughly 12 units — five lines of carry and a plain
      finished list stop being trustworthy well before that.
- [ ] More than one agent will touch it — light mode has no shared ledger,
      so two agents can silently duplicate or drop a unit.
- [ ] The result must be auditable — someone downstream will ask how a
      specific claim in the piece got there, and "I wrote it in order" is
      not an answer to that question.
- [ ] It's going to a client, a board, or publication.

## The honest limit

Full mode's whole point is that `bse.py record --status done` *refuses* to
accept a unit that hasn't passed a check. Light mode has no refusal
mechanism at all. The finished list is something you write, not something a
tool verifies against an artifact's hash — nothing stops a model (or you)
from appending "4 970w" to that list for an item that was never actually
written, or from claiming the seam pass happened when it didn't. Light
mode's guarantee is *lighter workload produces better output than one giant
pass*, which is real and worth having. It is not *nothing gets marked done
that isn't*. If you need that second guarantee — because the stakes justify
the machinery — that is exactly the case for full mode, not a reason to
add a checklist on top of light mode and call it the same thing.
