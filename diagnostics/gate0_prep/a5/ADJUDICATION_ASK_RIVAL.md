# Adjudication — does the sign condition pin `ask_rival`?

A5 finding 1 (category H) versus A2e/A2f. Resolved by locating the
crossing under both versions of the test.

| crop | floor | crossing, test as written | crossing, corrected test |
|---|---|---|---|
| maize | +0.00 | 0.755 | clears at 0.0 |
| wheat | +0.05 | clears at 0.0 | clears at 0.0 |
| rice | +0.05 | clears at 0.0 | clears at 0.0 |

## Margin at the shipped value

| crop | lift at ask_rival=0, corrected | lift at 0.80, corrected | floor |
|---|---|---|---|
| maize | +0.0467 | +0.3124 | +0.00 |
| wheat | +0.4876 | +0.9636 | +0.05 |
| rice | +0.1599 | +0.8318 | +0.05 |

## Resolution

If maize clears at 0.0 on the corrected test, then the sign
condition no longer selects 0.80 and A5 finding 1 cannot stand as
category H, however accurate it is about the test A5 was given. If
maize instead crosses somewhere in (0, 0.80), the condition still
constrains the parameter but no longer selects the shipped value,
and the honest reading is that the margin, not the sign, is the
open question. Either way the code comment as written is wrong.

