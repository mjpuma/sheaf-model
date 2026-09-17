# Agrimate sitting — cleaned questions and Cursor prompts

**For:** Kuhla / Kubiczek / Otto (Agrimate).
**From:** SHEAF sitting, 30 August 2026.
**What this is:** the handwritten notes from the conversation, interrogated, then turned into paste-ready Cursor prompts. One prompt at a time. Do not retune anything. Do not redesign SHEAF.

The five discussion questions on deck slide 98 are **not** this list. Slide 98 mixed naming, method, substitution they never built, and Gate 2 design. These prompts ask you to **locate objects in Agrimate** first. Design opinions come after the objects are named.

---

## Covering note (send this)

We took the sitting notes as twelve overlapping remarks about price, storage, expectations, and trade. Four words still need a yes/no from you before we treat an answer as locked:

1. **“Baseline”** — which object? SHEAF has four (reference price \(p_0\), climatology harvest, no-shock twin, opening-stock spin-up). Which one were you asking about, or is yours a fifth (annually-periodic Nash, 4-year spin-up, …)?
2. **“FRO and economics”** — we read this as **FAO and economists**. Correct?
3. **“Slide 48 / storage cost”** — our deck 48 is the ask-price update (fill rate + blockage), not a carrying-cost term. Were you asking about Agrimate’s supplier carrying cost, or about that ask update?
4. **“SHEAF is a differential equation”** — Gate 0 is a **discrete sequential map**: incoming world price and exporter asks enter demand and trade; the step writes next asks and next price. There is no inner solve and no DE. Is that the object you meant?

SHEAF-side answers in short, so you are not blocked on a clone:

| Your question | SHEAF crisis host (`sheaf/dynamic_crop.py`) |
|---|---|
| How is price formed? | One world \(p_t\) per crop: blend of shipment-weighted asks and a twin-relative scarcity term, then AR(1) smoother. Exporter asks \(q_{i,t}\) move with fill and blockage. Not a QP, not a DE. |
| What is the baseline? | Say which. Default twin = climatology harvest, mean food/feed, no industrial, \(\tau\equiv 0\). \(p_0\) = start-year Pink Sheet mean. |
| Commercial / competitive storage? | No separate commercial agent. Target stock \(T=L+s\), rebuild \(\lambda=0.08\), soft warehouse drain. No carrying cost \(r\). Gate 2 `gov_stu` is a Headey trigger, not Agrimate procurement. |
| Export offer vs demand share | Offers \(O\) from surplus above food and \(T\), cut by \(\tau\). Import demand \(D\) = food gap + rebuild. FAOSTAT \(A,S\) are **shares**; tonnes come from \(O,D\). |
| Linear demand / industrial | Crisis host is isoelastic food/feed. Industrial is inelastic USA maize FSI residual only. Linear Slutsky \(D=a-Mp\) is the leftover annual host in `core.py`, not 2007/08. |
| World vs export price | One world \(p\) plus exporter asks \(q_i\). A ban does not create a cheaper domestic CPI. |
| Too many parameters | Agreed as a concern. Literature vs reduced-form is tabled in the deck (CropParams). We are not retuning to 2008. |

Please run **P1–P6** in the Agrimate repo (Cursor, Agent mode, one prompt per chat or sequential). If you clone SHEAF, **S1–S4** locate the corresponding SHEAF objects. Return file:line, equation, unit, and **same / cousin / different** versus the SHEAF belief in each prompt.

Do not: retune CropParams or \(\sigma\); unpause SHEAF `dynamic_grains.py`; re-score 2008 as who-restricts; graft annual \(M_i\) onto the 24-step spine.

---

## What was messy (so we do not send the raw notes)

The notes mixed three jobs in one paragraph: (a) you explaining Agrimate, (b) you asking how SHEAF works, (c) a shared worry about parameters and an optimization principle for FAO/economists.

Specific collisions:

- **Q-price and Q-export-price** are the same cluster. Split into “which price objects exist” vs “which program produces them.”
- **Commercial hold vs competitive storage.** Agrimate’s paper splits **commercial** vs **strategic**. “Competitive storage” here is Williams–Wright-style commercial storage, not a third agent. “More freedom to produce” would be acreage; neither model has endogenous acreage (SHEAF slide 6, category E).
- **“Storage simplification in Agrimate: production and commercial storage, one agent.”** That is your architecture, not a SHEAF claim. P1 asks you to confirm it from code.
- **Sold-to-each-market** may be the **purchaser** CES, not the supplier. The notes attributed it to competitive storage; P3 asks who actually allocates.
- **Deck Q1 and Q5** (slide 98) were the same question twice (object vs method). These prompts separate agent set, price object, and method.
- **Deck Q3** (Jacobi isoelastic vs nested CES/AIDS) asks you to design cross-grain substitution you never built. Not in P1–P6. Optional after objects are named.
- **Deck Q4** (Headey \(S/S^{\mathrm{calm}}\)) asks you to design SHEAF Gate 2. Agrimate has no endogenous restriction. P6 only asks how **exogenous** AMIS enters.

---

## How to run a prompt

1. Open the Agrimate repository in Cursor.
2. New agent chat. Paste **one** `P#` block (from the horizontal rules through the return checklist).
3. Do not modify Agrimate source. Locate, quote, classify.
4. Send back the checklist, not a redesign.

---

## P1 — Supplier / commercial storage agent

```
You are answering a lineage question from the SHEAF team (Kuhla et al. 2025 successor). Work ONLY in this Agrimate repository. Do not modify code. Do not retune. Do not propose a SHEAF redesign.

SHEAF currently believes, from Kuhla et al. 2025 §3.2 and the ODD:
- Each region has a SUPPLIER agent that lumps domestic production and commercial storage into one stock.
- Each step the supplier solves a finite-horizon expected-profit problem (domestic sales + export sales − storage costs), “similar to competitive storage (Williams and Wright, 1991), with three major differences.”
- Process order is Harvest → Policy update (export restrictions) → Sales (commercial storage, using the CURRENT harvest) → Expectation formation → … → Procurement (strategic refill).
- Strategic storage is a different agent: partial-adjustment refill (ODD Eq. D.31a), not the commercial FOC.
- There is no endogenous acreage.

Please locate in THIS repo:
1. The supplier / commercial-storage agent class and the function that is called every time step.
2. The objective (write the equation as coded, with symbols and units).
3. The decision variables (store vs sell? domestic vs export split? destination mix?).
4. The information set at decision time: does it see this step’s harvest? this step’s export restrictions?
5. Confirm or correct the process order above, with file:line for each box.
6. Confirm that “competitive storage” in conversation = this commercial supplier, not a third class, and that production is not a decision (no acreage).

Return exactly:
- file:line for objective, decisions, and process schedule
- equation + units (quantity: tonnes or kt; price: which deflator/base)
- classification vs SHEAF’s belief: SAME / COUSIN / DIFFERENT, one sentence why
- any conversation word that does not match the code (“commercial hold”, “competitive storage”, “one agent”)
```

---

## P2 — Price formation each step

```
You are answering a lineage question from the SHEAF team. Work ONLY in this Agrimate repository. Do not modify code.

SHEAF currently believes:
- Agrimate does NOT have a single world price as a primitive. Prices come out of per-region optimizations: supplier (offer / export price), consumer (CES utility under budget and quantity cap), purchaser (CES allocation across suppliers).
- That is why the model is Julia: each region, each step, solves constrained problems (Kuhla et al. 2025 §3.2.1–§3.2.3).
- SHEAF Gate 0 is a different object: one world p_t per crop (real 2010 $/t), plus exporter asks q_i,t that adjust with fill and blockage. The step is an explicit NumPy map, not a solve. A ban withholds offers; it does not create a cheaper domestic CPI.

Please locate in THIS repo:
1. Every price object that exists at a time step (supplier, consumer, purchaser, regional, world index, CIF/FOB, …). Name them as in the code.
2. For each: which program produces it (objective + constraints), or if it is an accounting average after trade.
3. Units and deflator (nominal? real? which base year?).
4. How a published “world price” for the 2007/08 and 2010/11 figures is constructed from those objects.
5. Whether a domestic price can diverge from an export price when an export restriction is on.

Return exactly:
- table: price object | produced by (file:line / FOC of which program) | unit
- how the paper’s world-price series is aggregated (file:line)
- SAME / COUSIN / DIFFERENT vs SHEAF’s “one world p + asks”
- one sentence: is SHEAF’s closed-form map a fair cousin of this commercial layer, or a different object that should not inherit the name “Agrimate-aligned market”?
```

---

## P3 — Who decides how much is sold to each market

```
You are answering a lineage question from the SHEAF team. Work ONLY in this Agrimate repository. Do not modify code.

Conversation note (messy): “how does the competitive storage decide how much is sold to each of the markets?”

SHEAF currently believes this may have been attributed to the wrong agent:
- Agrimate’s PURCHASER (not the supplier) allocates next-step demand across suppliers with a CES (Kuhla et al. 2025 §3.2.3).
- Export restrictions change that choice set or the feasible export quantity (SHEAF called this “edge shutdown”; that name may be wrong).
- SHEAF Gate 0 instead: destination shares A from FAOSTAT, reweighted by asks (Ã ∝ A (p0/q)^γ), then ship = min(O Ã, D S), leftover pool with ν=0.15. Tonnes come from USDA-derived offers O and demand D; FAOSTAT is shares only.

Please locate in THIS repo:
1. Who chooses the destination / source mix each step: supplier, purchaser, both, or a residual pool?
2. The CES (or other) formula as coded: elasticity, budget, quantity cap, preference weights.
3. How an AMIS export prohibition / tax / quota changes that allocation. Be precise: zero an edge, drop a supplier from the CES choice set, cap export quantity, add a tax to delivered cost, or something else.
4. After preferred links, is there a residual / spot pool?

Return exactly:
- agent that allocates | equation | file:line | unit
- AMIS mechanism in one sentence with file:line (do not use SHEAF’s phrase “edge shutdown” unless the code really zeros an edge)
- SAME / COUSIN / DIFFERENT vs SHEAF Armington min-clear
```

---

## P4 — Expectation formation

```
You are answering a lineage question from the SHEAF team. Work ONLY in this Agrimate repository. Do not modify code.

Conversation notes:
- “You don’t have perfect foresight over the next 10 years, but you need to form expectations and adapt… stay close to equilibrium unless you have new info.”
- “If you have more than one harvest per year, we need expectation formation.”
- “If you have a complex model, the expectation model needs to be quite simple… can’t do it on country level.”
- “We could think about new markets.”

SHEAF currently believes:
- Agrimate suppliers use finite-horizon expected profit with ADAPTIVE expectations, not rational expectations and not 10-year perfect foresight.
- SHEAF Gate 0 harvest expectation is a reduced-form blend: H^exp = φ H + (1-φ) H^seas, with φ = 0.55 wheat/rice and 0.50 maize. Price entering demand is last step’s world p. No RE. Lean horizon h_t is a world harvest-pulse clock, shared by all countries.

Please locate in THIS repo:
1. What is expected: price, harvest, demand, or a combination?
2. Horizon in time steps (and in days/months).
3. The adaptation law (write the coded update).
4. At what spatial grain: 28 regions, country, or world?
5. Why more than one harvest per year forces this (calendar / Southern Hemisphere / multiple pulses).
6. What “can’t do it on country level” and “new markets” refer to in the code or paper, if anything. If they were sitting remarks not in the model, say so.

Return exactly:
- expectation object | update law | horizon | spatial grain | file:line
- SAME / COUSIN / DIFFERENT vs SHEAF’s φ-blend + lagged p
- confirm: not 10-year perfect foresight, not Deaton–Laroque RE
```

---

## P5 — Why hold grain (carrying cost; why not sell everything now)

```
You are answering a lineage question from the SHEAF team. Work ONLY in this Agrimate repository. Do not modify code.

Conversation notes:
- “If there’s more harvest globally, the price goes down… BUT unclear in Agrimate: why not sell everything now?”
- “Slide 48: how is the cost of storage taken into account? Store more / store longer → greater costs.”
- “Market dynamics is like expectation formation… if you have a lot of constraints you’d get similar behavior… too many parameters… what hard boundary can be replaced?”

SHEAF currently believes:
- Agrimate’s commercial supplier has an explicit carrying / storage-cost term in the expected-profit objective, so holding is an interior FOC, not only a warehouse clip.
- Constraints (warehouse, quantity cap, budget) also bind and can mimic storage even without a rich expectation.
- SHEAF Gate 0 has NO carrying cost r. Holding is a target-stock rule T = lean gap + safety, plus rebuild λ = 0.08 and a soft warehouse drain λ_W. SHEAF deck slide 48 is the ASK update (fill and blockage), not storage cost — we think you were pointing at your supplier cost term, not that slide.

Please locate in THIS repo:
1. The storage-cost / carrying-cost term as coded (equation, unit, per-step or per-year).
2. The first-order condition (or KKT) that says “do not dump the harvest this step.” Quote it.
3. Warehouse / capacity / quantity-cap constraints that would hold grain even if the cost term were zero. Which of those are doing the work in the 2007/08 hindcast, if you know?
4. Strategic-storage refill (purchaser / government buffer): is it a cost FOC or a partial-adjustment rule?

Return exactly:
- carrying-cost term | file:line | unit
- why-not-dump FOC | file:line
- constraints that substitute for the FOC
- SAME / COUSIN / DIFFERENT vs SHEAF’s target-stock rule with no r
- one sentence on “too many parameters / hard boundaries”: which Agrimate bounds are structural vs calibrated
```

---

## P6 — Baseline, spin-up, and how AMIS enters

```
You are answering a lineage question from the SHEAF team. Work ONLY in this Agrimate repository. Do not modify code.

Conversation note: “what is the baseline…” (unspecified). SHEAF will not guess.

SHEAF currently believes, from the paper and ODD:
- Clock: 24 steps per year (~15 days), not 26 fortnights (Kuhla et al. 2025 §4.1).
- Spin-up on the order of 4 years (96 steps) before the scored window.
- Seasonal / annually-periodic Nash (or equivalent rest) is the no-crisis baseline; crises are anomalies around that.
- Export restrictions are EXOGENOUS from AMIS. Bans ≈ 95% quantity cut, taxes ≈ 50%. No endogenous who-restricts.
- Harvest forcing: LOWESS (window ~10 years) then calendar-spread; mid-season concentration.

Please locate in THIS repo:
1. Name every object a reader might call “baseline” (spin-up path, climatology harvest, no-restriction counterfactual, Nash rest prices, …). For each: definition, file:line, unit.
2. STEPS_PER_YEAR and the stated reason for 24 not 26, if any exists in code or docs.
3. Spin-up length and what is on during spin-up (restrictions? shocks?).
4. The AMIS → model map: policy label → what changes in the supplier/purchaser problem. Confirm or correct ban≈0.95 and tax≈0.50.
5. Detrending: LOWESS window, robust iterations or not, vs in-sample mean.

Return exactly:
- table of baseline objects
- clock and spin-up
- AMIS mechanism (this must match P3; if they disagree, say so)
- SAME / COUSIN / DIFFERENT vs SHEAF: 24-step clock, 2-year spin-up, AMIS as offer-cut τ ∈ [0,1], LOWESS window_years=10 hand-rolled
```

---

## Optional: if you clone SHEAF

Run these in the SHEAF repository, Agent mode, read-only. Do not modify `sheaf/*.py`. Crisis host is `sheaf/dynamic_crop.py` (24-step). Ignore `sheaf/core.py` unless a prompt names it; that is the leftover annual SPE, not 2007/08.

### S1 — Price is a map, not a differential equation

```
Read-only. Crisis host only (sheaf/dynamic_crop.py, README §8).

A visitor described SHEAF’s step price as “a differential equation.” Locate the actual update.

1. In _simulate_window, list incoming (p, q) and outgoing (p, q') with line numbers.
2. Write p^tr, r, p^scar, p*, p_t as coded. Units: real 2010 $/t.
3. Confirm there is no cvxpy / CLARABEL / root-find inside this file (imports).
4. Confirm the calm identity: no shock and no AMIS ⇒ p_t = p0 (assert_twin_identity).
5. One sentence: this is a discrete map, not a DE and not Agrimate’s per-step optimizations.

Return file:line and the equations. Do not retune CropParams.
```

### S2 — Four things named “baseline”

```
Read-only. sheaf/dynamic_crop.py prepare_crop_run, README §8.

Name and locate:
1. p0 — start-year mean real Pink Sheet.
2. H^seas — score-window mean production × calendar weights.
3. Twin run — climatology H, mean flex, C_ind=0, τ≡0.
4. Opening stocks — PSD seed year 2005, clip, spin_up_years=2.

Do not call core.py SpatialEquilibrium a crisis baseline. Return a four-row table: object | formula | file:line | unit.
```

### S3 — Export offer vs demand share vs industrial

```
Read-only. sheaf/dynamic_crop.py _simulate_window and _bilateral_clear.

1. Offers O = max(0, avail − d − T) (1−τ). τ cuts offers, not shipments.
2. Import demand D = food gap + λ·rebuild.
3. A, S are FAOSTAT shares; ship = min(O Ã, D S) then residual pool ν.
4. Food/feed is isoelastic in p/p0, not linear. Industrial is USA maize FSI residual only.

Return each identity with file:line. Note if anyone reading README §1 linear D=a−Mp would be on the leftover host.
```

### S4 — Storage without carrying cost

```
Read-only. sheaf/dynamic_crop.py lean gap, target T, warehouse W, soft clip.

1. T = L + s, s = stu_target × C^ann. No r, no storage Euler.
2. Rebuild λ and warehouse_lambda (both 0.08). Soft clip toward W, not a hard incineration.
3. No commercial vs strategic split on Gate 0. dynamic_policy.gov_stu is Gate 2 Headey, not Agrimate procurement.
4. Compare in one sentence to Agrimate’s commercial expected-profit storage (do not “fix” SHEAF).

Return identities with file:line. Classification: different object (reduced-form target stock), not a failed Williams–Wright FOC.
```

---

## After P1–P6 come back

Then, and only then, we can sit the slide-98 design questions on named objects:

1. Fair cousin vs different object (now with your price table from P2).
2. Offer-cut τ vs whatever AMIS actually does in your code (P3/P6).
3. Cross-grain substitution — optional; you never built it.
4. Headey trigger vs importer procurement — optional; you have no endogenous ban.

Until the objects are named, those four are naming fights, not science.
