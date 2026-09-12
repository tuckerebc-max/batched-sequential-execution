# carry.md — the baton (max 400 words; each unit REPLACES this file)

<!--
carry.md is not a log — it does not accumulate. Every completed unit writes
a brand-new carry.md that replaces the previous one in full (`bse.py carry
--set FILE`, enforced against the 400-word cap). Keep only what the next
fresh-context unit actually needs; everything else is a distractor. The five
section headings below are fixed — do not rename, merge, or drop any of them,
even when a section has nothing to say (write "(none yet)" or "(none)").
-->

## Established facts
<!-- Bullets, each citing a [S#] source id where the fact came from a source. -->
- <fact the next unit can rely on as settled> [S#]

## Interfaces/terms now defined
<!-- Terms or interfaces earlier units introduced that later units must reuse
verbatim — this is how term drift gets caught before it starts. -->
- <term> — <its definition, one line>

## Open threads for later units
<!-- Anything decided to defer, so a later unit does not have to rediscover it. -->
- <thread or open question, and which unit should pick it up>

## Do not repeat
<!-- Topics/claims already fully covered. This list is fed straight into the
forbidden_phrases mechanical verifier for later units — keep entries short
and literal (a phrase, not a paragraph). -->
- <topic or phrase already covered in an earlier unit>

## Tone calibration note
<!-- <= 2 sentences. Whatever a fresh executor needs to match voice/register
without re-reading every prior batch. -->
<one or two sentences>

---
## Example

# carry.md — the baton (max 400 words; each unit REPLACES this file)

## Established facts
- Q3 had 14 severity>=2 incidents, 9 of them network-related [S1]
- SRE lead attributes the Aug spike to the CDN migration [S2]

## Interfaces/terms now defined
- "capacity ledger" — the running per-region headroom table introduced in 3.2;
  later sections reference it by this name only, never "headroom sheet"

## Open threads for later units
- Cost figures for the remediation plan are out of scope (see charter) but
  B007 should still name which team owns each recommendation

## Do not repeat
- The CDN migration timeline (fully covered in 3.1 — do not re-narrate it)
- The definition of "incident" vs "SLO violation" (locked in 3.2)

## Tone calibration note
Keep it plain and declarative, as in 3.1-3.2 — short sentences, no hedging
("may have," "it seems") anywhere a source figure is available instead.
