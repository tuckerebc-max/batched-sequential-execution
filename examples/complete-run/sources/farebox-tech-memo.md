# Technical memo — RiverPass fare system capability for time-of-day capping

Prepared by RTA IT/Fare Systems, 2026-07, in response to a Planning
department request to scope what a time-of-day (off-peak-specific) fare cap
would require of the existing fare system.

## Current system

RTA's fare system, branded RiverPass, is an account-based tap card and phone
app installed in 2020 and last upgraded in 2023. Fare validation at the
farebox is real-time (a tap is authorized or declined in under one second),
but cap accounting — deciding whether a rider has reached a cap and should
ride free — currently runs as a nightly batch job, not in real time. In
practice this means a rider who has already reached the all-day cap can still
be charged at the farebox for a tap that happens later the same day; RTA
credits the overcharge back to the rider's account the following morning
once the batch job runs. RTA data shows roughly 4% of all-day-cap-eligible
taps are overcharged and refunded this way in an average week.

## What a time-of-day cap would require

A cap that behaves differently depending on the time of the tap (for
example, a lower or zero fare after a rider's second off-peak tap, while
still charging peak fare the same day) cannot be evaluated correctly by the
current nightly batch process, because the batch job does not know at tap
time whether a given tap falls inside or outside the off-peak window relative
to the rider's other taps that day — it only reconciles cumulative daily
taps after the fact. RiverPass would need a software change to move cap
evaluation into the real-time authorization path so that the farebox knows,
at the moment of the tap, both the time of day and the rider's cap status.

RTA's fare-system vendor quoted this change at $410,000 and a 9-month
delivery timeline from contract signature, based on a scoping call in June
2026; the quote has not been through RTA procurement review and is not a
binding bid. The 9 months includes 2 months of vendor development, 3 months
of RTA-side integration testing against the existing farebox hardware
(unchanged since 2020), and a recommended 4-month phased rollout across
RTA's approximately 340 buses and 22 light-rail vehicles rather than a single
cutover, to catch hardware-specific validation bugs before they affect the
whole fleet.

## Interim option

RTA's fare-system vendor also described a lower-cost interim path: keep cap
evaluation in the nightly batch job, but change only the refund logic so
that any rider whose batch reconciliation shows they qualified for an
off-peak cap that day receives an automatic same-week account credit rather
than riding free at the farebox in real time. This interim option was quoted
at $85,000 and 3 months, because it changes only the batch job's refund
rule, not the real-time authorization path. Its tradeoff, as the vendor's
scoping notes state directly, is that a rider does not experience "riding
free" at the point of travel — they pay full fare at the farebox and see the
credit on their account days later, which RTA's own product staff flagged in
the scoping call as a meaningfully worse rider experience than real-time
capping, even though the two options are intended to produce the same net
fare outcome.

## Hardware note

The farebox hardware itself (installed 2020) supports both paths without
replacement; the vendor's quote in both cases is software-only. RTA's IT
department has no other planned RiverPass changes competing for 2027
engineering capacity as of this memo's writing.
