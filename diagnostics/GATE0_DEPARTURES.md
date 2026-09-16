# Gate 0 departure register

Statuses: proposed | approved | implemented | validated | rejected | deferred.

## D0 — Rebuild Gate 0 as Agrimate (approved, implemented)

Rewrite approved by the 16 Sep 2026 assignment. Historical Fig. 4 match
**not** claimed.

## Legacy mechanisms removed

L1 fill-target 0.70; L2 calm-price pin; L3 trade/scarcity blend; L4 ask_rival;
L5 prescribed buffer; L6 scarcity-ratio floor as economics; L7 residual ν;
L8 AR(1) smoother. Rejected for baseline. Worse Pink-Sheet fit is not a reason
to restore them.

## Data adaptations (not economic departures)

A1 USDA PSD not FAOSTAT Food Balances; A2 E0 shares rescaled; A3 A_d not E.30
(Egypt 0.17); A4 A_c income-group proxies; A5 restriction weights inside
multi-country regions; A6 inverse-demand floor 0.05 (numerical).

## Proposed extensions (not implemented)

E1 cross-crop substitution (≠ origin CES). E2 government restriction game
(≠ supplier oligopoly). Need user approval before code.
