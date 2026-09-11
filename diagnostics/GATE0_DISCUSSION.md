# Gate 0 discussion — options after coauthor consultation

**Date:** 2026-08-31
**Status:** options to explore. Not a rewrite list. Not a freeze.
**Host:** `sheaf/dynamic_crop.py` (`_simulate_window`). 24-step crisis market.
**Not this host:** `sheaf.annual` (parked yearly SPE). Gate 1 / Gate 2 (paused).

Flow diagrams: [`figures/gate0_flows/`](../figures/gate0_flows/).
Organized writeup (plain language, economic language, then the figure):
[`overleaf/gate0_discussion/`](../overleaf/gate0_discussion/).
Captions also in [`GATE0_FLOWS.md`](GATE0_FLOWS.md).

This note is the document we use **before** writing Cursor prompts and
**before** changing equations. The sitting with Agrimate (Kuhla / Kubiczek /
Otto, 30 August 2026) produced questions about how SHEAF forms price, holds
grain, expects harvest, and trades. Those questions are about **our** Gate 0.
If we leave them half-answered and stack substitution and a restriction game
on top, the foundation is weak even if snapshot scores look fine.

Living queue: [`DEVELOPMENT.md`](DEVELOPMENT.md). Current parameter table:
[`GATE0_PARAMETERIZATION.md`](GATE0_PARAMETERIZATION.md). Snapshot scores:
`diagnostics/gate0_{wheat,maize,rice}_report.md`.

---

## 0. What “fully vetted” means here

A Gate 0 we will stand behind is not “corr ≈ 0.7 and asserts PASS.” Those
snapshots already exist. Vetted means:

1. **Every sitting question names an object in this code.** If a word from
   the notes (“baseline,” “DE,” “storage cost,” “sold to each market”) maps
   to more than one object, we say so and pick which object we mean.
2. **The paper language matches the code.** If we say “Agrimate-aligned
   agents with finite foresight,” the code must have those agents, or we
   stop saying it. `ARCHITECTURE.md` still claims suppliers/purchasers; the
   crisis loop is a sequential map. That mismatch is a documentation issue
   until we either change the sentence or change the model.
3. **Each design choice is a choice, not an accident.** For every cluster
   below we can say: we kept X, we rejected Y, for these reasons, against
   this complexity budget. Category D/E (simplification / philosophy) is
   allowed. Unnamed phenomenology that pretends to be a FOC is not.
4. **Identification still forbids crisis-by-crisis fit.** Opening the
   baseline does not license a 2008 dummy, a preferred \(\sigma^\star\), or
   retuning \(\kappa\) on one hike. A named change is re-scored as official
   vs sensitivity, shared across years.
5. **Known leftovers stay leftovers until a named change addresses them.**
   Wheat 2007/08 still high, consumption correlations negative, many
   exporters on the world safety floor, \(\tau\) cutting offers more than
   shipments — these are already disclosed. A new law that does not touch
   those mechanisms will not “fix” them. A new law that *does* touch them
   must not be tuned to make 2008 look nicer.

This file does **not** pick a winner in each cluster. It lays out the
options so we can decide with coauthors, then write prompts that
interrogate the current map (characterize first), then change only what
survives that interrogation.

---

## 1. How to use this file

For each cluster:

| Step | What we do | What we do not do |
|---|---|---|
| Current law | Cite the equation as coded | Paraphrase Agrimate’s paper as if it were ours |
| Colleague concern | Restate the sitting note as a question | Treat the note as a defect finding |
| Options | Keep / characterize / change, with budget | Jump to “clone Agrimate” or “revive the yearly QP” |
| Close the cluster | Named keep, or named change + re-score | Silent retune of `CropParams` |

Complexity budget (same axes as the constitution): scientific benefit,
computational cost, calibration burden, interpretability, new parameters,
new state, runtime, continuity with TWIST/Agrimate, publication benefit.
“More theoretically correct” is not sufficient on its own.

Classification if we later record a finding: **D** economic simplification,
**E** modeling philosophy, **G** documentation mismatch, **C** numerical,
**B** code ≠ claimed math. Do not call a disclosed reduced-form map a
coding bug.

---

## 2. The sitting questions, clustered

Handwritten notes from the sitting, cleaned. Slide 98 of the deck (naming /
method / substitution they never built / Gate 2) is a **different list**.
These twelve lines are what they actually asked.

| Raw note (paraphrase) | Cluster below | Answered in `overleaf/gate0_discussion/` |
|---|---|---|
| How is price formed each step? Is it a differential equation? | §3 Price map | §3.5 eqs (12)–(14); §4.3 "How is the world price determined?" |
| Export prices each step? World vs export price? | §3 and §7 Trade / two prices | §3.4 eq (11); §4.4 "Who trades with whom, and at which price?" |
| Do we need an optimization principle? FAO / economists | §4 Optimization principle | §4.3 (three requests: agent optimisation, market clearing, principle already present) |
| What is the baseline? | §5 Baseline objects | §4.1 "Which object is 'the baseline'?" + Fig. 2 |
| Commercial hold / competitive storage / one agent | §6 Storage | §4.2 "Why is available surplus not fully offered each period?" + Fig. 3 |
| How much is sold to each market? | §7 Offers vs shares | §3.2 eqs (6)–(8); §4.4 (FAOSTAT supplies pattern only) |
| Linear demand? Industrial use? | §7 Demand objects | §3.1 eq (1); §4.5 "Is demand linear, and what counts as industrial use?" |
| Expectations: not 10-year foresight; adapt; stay close unless new info | §8 Expectations | §3.1 eq (2); §4.7 "What is the expectational horizon?" (§3.6 reference identity) |
| Slide 48 / storage cost; why not dump everything this step? | §6 and §9 Carrying cost | §4.2 (slide 48 = eq (11), not a cost of carry; no interest rate in eq (10)) |
| Glut should lower \(p\); annually? | §3 Scarcity symmetry | §4.6 "Should a surplus lower the price, and on what frequency?" |
| Too many parameters; hard bounds would give similar behavior | §9 Knobs vs bounds | §4.8 "Is the parameter count defensible?"; Table 2 classes; §5 ablation |

Equation and section numbers refer to the compiled `main.pdf` (17 pp.).
Every raw note has a named home; none is answered by "we will look at it."

Four words still collide. Until they are named, options talk past each other:

1. **“Baseline”** — SHEAF has four objects (§5). Agrimate may mean a fifth
   (annually-periodic Nash, 4-year spin-up).
   *Resolved in the note:* §4.1 names all four; scarcity uses the twin.
2. **“FRO and economics”** — we read **FAO and economists**. Confirm.
   *Open — a transcription question for the authors, not a model question.*
3. **“Slide 48 / storage cost”** — our deck 48 is the **ask update**, not a
   carrying-cost \(r\). Which did they mean?
   *Stated in the note:* §4.2 says slide 48 is eq (11) and flags the
   confirmation as still owed to them.
4. **“SHEAF is a DE”** — the crisis host is a **discrete sequential map**.
   The ask law is the only piece that looks like \(dq/dt\).
   *Resolved in the note:* §3 opens with the map; §4.3 says so explicitly.

---

## 3. Cluster: how \(p_t\) is formed

### Current law

Each fortnight \(t\) is arithmetic in order. Incoming: last world price
\(p\) and exporter asks \(q\). Outgoing: new \(p\), new \(q\). No inner
loop, no QP, no per-region NLP.

1. Demand \(d = C^{\mathrm{flex}}(p/p_0)^{\varepsilon}+C^{\mathrm{ind}}\)
   uses **incoming** \(p\) (last step).
2. Target \(T=L+s\), offers \(O=\max(0,\mathrm{avail}-d-T)(1-\tau)\),
   import demand \(D\) = food gap + \(\lambda\) rebuild.
3. Armington \(\mathrm{ship}=\min(O A,\,D\tilde S)\) plus residual pool.
   (\(\tilde S\) is the CES origin mix; destination-row \(\tilde A\) is a
   no-op.)
4. Consume, update stocks, soft-clip toward warehouse \(W\).
5. Asks: sold-out raises \(q\), leftover cuts \(q\), blockage marks up,
   pull toward \(p\):
   \[
   q\leftarrow (1-\beta)\,q\exp\bigl(\alpha(\mathrm{fill}-\theta)
   +\alpha_r b\cdot\mathbf{1}_{O>0}\bigr)+\beta p,
   \]
   clipped to \([0.45p_0,\,2.8p_0]\).
6. World target \(p^\star=\omega p^{\mathrm{tr}}+(1-\omega)p^{\mathrm{scar}}\),
   then \(p\leftarrow\rho p+(1-\rho)p^\star\), clipped to \([60,1200]\).

Scarcity term (twin-relative free cover, unmet anomaly, preferred-source
blockage):

\[
p^{\mathrm{scar}}=p_0\,r^{\eta}(1+\kappa_u\Delta u+\kappa_b b),\quad
r=\frac{\mathrm{free}^{\mathrm{twin}}+f}{\mathrm{free}+f}.
\]

Calm identity: if free, unmet, and blockage match the twin, \(p^\star=p_0\)
exactly. \(\eta\) is **symmetric** (a glut must cheapen flex demand). Code:
`_simulate_window` around the demand / ask / `p_star` block.

The ask law is a discrete analogue of \(\mathrm{d}q/\mathrm{d}t\propto
(\mathrm{fill}-\theta)q\). **World \(p\) is not that law.** It is a blend
plus an AR(1) smoother (\(\rho=0.65\)).

### Colleague concern

They heard a DE, or an export-price process, and asked how a single number
\(p_t\) is justified. Agrimate does not have a world price as a primitive;
prices come out of supplier / consumer / purchaser programs.

### Options (not ranked as a decision yet)

| ID | Option | What it is | Buys | Costs | Likely leftover impact |
|---|---|---|---|---|---|
| P0 | **Keep the map.** Honest writeup: reduced-form ask/scarcity, not Agrimate agents. | Documentation + `ARCHITECTURE.md` sentence | Stops overclaiming. Zero score risk | Does not shrink knobs. FAO/econ may still want a principle | None |
| P1 | **Characterize only.** Is \(p^{\mathrm{scar}}\) already inverse demand? Is the ask law already a markup FOC? | Read-only math on the current update | If yes, we already have a principle. If no, we know what is phenomenological | None | None |
| P2 | **Same-step consistency.** This step’s \(d\) uses this step’s \(p\) (1-D root or one Jacobi iteration) | Demand and price share an information set | Closes “last fortnight’s \(p\) on this fortnight’s curve” | Medium score movement. New numerical object (root, tolerance) | May move monthly \(p\); will not by itself fix exporter floors |
| P3 | **Ask FOC only.** Replace the exponential fill law with a one-line exporter markup; keep world \(p\) as inverse demand | One behavioral equation for \(q_i\) | May collapse \(\alpha,\theta,\beta\). Still a map | Medium. Must not be fit to 2008 peaks | Asks and \(\omega\)-blend move; wheat 2008 is restriction-led, so maybe |
| P4 | **Agrimate clone.** Per-region supplier / consumer / purchaser NLPs each step | Their commercial layer | Lineage match. Domestic vs export price | High: Julia-class solves, CES, horizon, discount. Loses “Python map.” New model | High — new hindcast, not a retune |
| P5 | **Yearly SPE as heartbeat.** Takayama–Judge QP every crisis step or every year | The parked `sheaf.annual` object | True market-clearing \(p\) | Wrong clock. Annual wheat 2008 had the wrong hike sign on that host | High and previously failed as 2007/08 heartbeat |
| P6 | **Continuous-time DE.** Write the map as ODEs and integrate | Literal reading of “it is a DE” | None that P0/P1 do not already give | Fake precision. Same reduced-form gains | None |

**Do not treat P4 or P5 as the default “more scientific” move.** Agrimate’s
NLPs are a different model. The yearly QP is an optimization principle that
already failed as the crisis host. P0 and P1 have no score risk and should
happen before P2–P3 are even coded.

### What would close this cluster

- P0 done: paper and `ARCHITECTURE.md` say “24-step ask/scarcity map,” not
  “Agrimate agents.”
- P1 done: a short note that either exhibits a potential whose FOC *is* the
  current update, or states that \(\eta,\omega,\kappa,\alpha\) are not FOCs.
- Only then: a **named** P2 or P3 as sensitivity beside the current map,
  not a silent replacement of Gate 0.

---

## 4. Cluster: do we need an optimization principle?

This is the FAO / economist sitting remark, split from §3 because three
different objects get bundled as one request.

| Object | Who has it | Gate 0 today |
|---|---|---|
| **Agents maximize** (FOCs: store vs sell, export price as a decision) | Agrimate: supplier profit, consumer CES, purchaser CES | No |
| **Markets clear** (equilibrium: \(p\) is a multiplier on balance) | Parked annual SPE | No. Architecture locked disequilibrium adjustment |
| **The map is a gradient of a potential** | Partial: \(p^{\mathrm{scar}}\propto r^{\eta}\) is inverse-demand flavored; asks and the \(\omega\)-blend are not | Unproven. That is P1 |

Their claim: an objective would **improve the model** and be **more
acceptable**. Those are two tests.

**Improve the model.** Wheat 2008 still high (restriction-led), consumption
corr negative (mean flex + \(\varepsilon<0\)), exporters on the safety
floor (one world STU). An exporter NLP does not obviously fix those. Risk:
retuning a new objective to 2008 and calling it theory.

**Acceptability.** For Wright–Williams / Takayama–Judge referees: yes, if
the FOC is genuine. Wrapping the current map in an \(\arg\max\) of a
constructed potential is documentation theater. For Ecological Economics /
ABM (Agrimate’s venue): a disclosed reduced-form map on Agrimate’s clock
and data is already in-family with TWIST’s stylised price–supply curve.
TWIST did not solve a storage Euler either.

### Options

| ID | Option | Acceptability | Scientific | Do before code? |
|---|---|---|---|---|
| O0 | Honest language only (same as P0) | Medium — referees who wanted FOCs still want FOCs; referees who wanted honesty get it | Stops a false claim | Yes |
| O1 | Prove/falsify current map as FOC (same as P1) | High *if* it is a FOC; honest *if* it is not | Identification | Yes |
| O2 | Same-step inverse demand (P2) | “This step’s \(p\) sits on this step’s demand” | Consistency, not Agrimate | Only as labeled sensitivity |
| O3 | One exporter markup FOC (P3) | Partial — \(q_i\) has a principle; world \(p\) still blended | Fewer ask knobs | Only if O1 shows the current law is not already that FOC |
| O4 | Full agent NLPs (P4) | Highest for “it is Agrimate” referees | That *is* Agrimate | No for Gate 0 |
| O5 | Revive SPE (P5) | Highest for spatial-equilibrium referees | Wrong object for 2007/08 | No |

**Working stance (not a freeze):** we do **not** need an optimization under
\(p\) in order to *have* a Gate 0. We may need O0+O1 in order to *stand
behind* Gate 0 in front of FAO/econ. O2–O3 are later, named, and only if
O1 fails to find a principle already in the map. O4–O5 fail the complexity
budget as a Gate 0 move.

---

## 5. Cluster: what is the baseline?

The notes did not say which object. SHEAF has four. Scarcity (the price
residual) uses the **twin**.

| Object | What it is | Role in Gate 0 |
|---|---|---|
| \(p_0\) | Start-year mean real Pink Sheet (wheat 213.5 $/t) | Numeraire. Calm \(p^\star=p_0\) |
| \(H^{\mathrm{seas}}\) | Score-window mean PSD production × calendar triangle | Climatology harvest. Twin uses this |
| **Twin** | Same map, \(H^{\mathrm{seas}}\), mean flex, \(C^{\mathrm{ind}}=0\), \(\tau\equiv 0\), same opening stock | `free_twin`, `unmet_twin` for the scarcity ratio. Not a different model |
| **Spin-up** | 2005 PSD stocks, clipped, then 2 years of climatology / mean flex / no AMIS | Opening \(S\) for both twin and treatment. Agrimate uses ~4 years |

Official score split (Agrimate Figs. 3–4 style): climatology baseline;
production anomalies only; harvest + AMIS (mean flex; USA maize industrial
on). Year-by-year food/feed is a **sensitivity**, not the headline.

### Colleague concern

“What is the baseline?” may mean \(p_0\), the twin, spin-up length, or
Agrimate’s annually-periodic Nash rest. If we talk past each other, every
later option (storage, price) is ill-posed.

### Options

| ID | Option | Notes |
|---|---|---|
| B0 | **Name the four** in every Gate 0 writeup. Scarcity uses the twin. \(p_0\) is the numeraire | Documentation. Do now |
| B1 | **Keep 2-year spin-up** | Continuity with current snapshots. Agrimate uses ~4 |
| B2 | **4-year spin-up** (Agrimate length) as a **named sensitivity** | May move opening stocks and 2006 levels. Do not retune \(\eta\) to compensate |
| B3 | **Annually-periodic Nash / SPE rest** as the “baseline” | That is the parked annual object, or Agrimate’s rest. Not the current twin. Would be a new baseline object, not a rename |
| B4 | Change twin harvest (realized vs seasonal) or twin demand (year-by-year flex) | Identification change. `twin_harvest` and `use_demand` already exist as switches. Official split stays unless we relabel |

**Close this cluster** when every coauthor uses the same word for the same
object, and when any spin-up / twin change is a named sensitivity with the
official split still defined.

---

## 6. Cluster: storage — commercial agent, target stock, carrying cost

### Current law

Gate 0 has **no** commercial storage agent and **no** store-vs-sell
optimization. Production is not a decision (no acreage — same as Agrimate).
Harvest is added to stock; then a partition:

| Bucket | Rule | Decision? |
|---|---|---|
| Eat | \(d=C^{\mathrm{flex}}(p/p_0)^{\varepsilon}+C^{\mathrm{ind}}\), then \(C_{\mathrm{used}}=\min(d,\mathrm{avail}-X+R)\) | No — isoelastic + min |
| Hold as cover | \(T=L+s\), \(L\) = lean gap to next world harvest pulse, \(s=\mathtt{stu\_target}\cdot C^{\mathrm{ann}}\) | No — target-stock rule |
| Offer for export | \(O=\max(0,\mathrm{avail}-d-T)(1-\tau)\) | No — residual surplus, then AMIS cut |
| Warehouse overflow | After trade, drain \(\lambda_W\) of \(\max(0,S-W)\) | No — soft clip, not a $ cost |

`stu_target` is **one world STU**. That is why many exporter nodes sit on
the safety floor in the snapshots (USA/Canada/Australia wheat ~×0.2). A
country-specific price-responsive hold was tried and **rejected**: it helped
USA wheat and fattened China maize ~×3.

Agrimate: one supplier per region gets the harvest and chooses how much to
sell vs store from finite-horizon expected profit, **after** policy is
known. Strategic storage is a different agent (partial-adjustment refill).
SHEAF Gate 2 `gov_stu` is a Headey trigger, not that procurement agent.

**Carrying cost \(r\):** Gate 0 has none. Deck slide 48 is the ask update.
They do not dump the harvest this step because offers are only surplus
above \(d+T\), not because an Euler says \(E[p_{t+1}]>(1+r)p_t\).

Warehouse \(W\) and ask clips are **hard-ish bounds**. Colleagues’ remark:
if you have a lot of constraints you get similar behavior even with thin
expectations. That is a fair reading of what \(T\) and \(W\) are doing.

### Colleague concern

Williams–Wright / competitive storage is the economist’s default “why hold.”
Agrimate already simplified that to one commercial supplier. SHEAF simplified
further to a target. Is that one step too far for a foundation?

### Options

| ID | Option | Lineage | New params | Leftover stocks | Budget |
|---|---|---|---|---|---|
| S0 | **Keep \(T=L+s\).** Disclose: cover rule, not a storage Euler | TWIST-like stylised hold; not Agrimate commercial | 0 | Exporter floor remains a disclosed leftover | Default until S1–S2 are characterized |
| S1 | **Add an explicit \(r\)** without an agent (tax on \(S\) or on overflow) | Accounting, not Wright–Williams | 1+ (\(r\), maybe crop-specific) | Unclear — may dump more, worsening floors, or drain China | Low compute; high identification risk |
| S2 | **One-line store-vs-sell:** offer extra iff expected price rise beats \(r\), with \(E[p]\) from last \(\Delta p\) or from \(\phi\)-harvest | Cousin of competitive storage, not Agrimate NLP | \(r\), expectation rule | Directly aimed at “why not dump” | Medium. Must not be 2008-fit |
| S3 | **Country STU / price-responsive hold** | Already tried | Country vector | Helped USA wheat, China maize ~×3 — **rejected** | Do not revive without a new structural story |
| S4 | **Agrimate supplier NLP** | Their commercial layer | Horizon, discount, CES weights, storage cost | New model (same as P4) | No for Gate 0 |
| S5 | **Deaton–Laroque RE storage** | Canonical, not claimed, not TWIST/Agrimate | Rational expectations apparatus | Wrong lineage test | No |

S3 is not an open option unless new evidence overturns the China-maize
result. S4–S5 fail the budget as Gate 0. The live question is **S0 vs S2**
(and whether S1 is a cheap way to answer “slide 48” that still is not an
Euler).

### What would close this cluster

- A sentence we will print: “Gate 0 holds grain because of a lean+safety
  target, not because of a storage Euler. Agrimate’s commercial supplier is
  a different object.”
- If that sentence is unacceptable to coauthors, S2 as a **named
  sensitivity**, scored without retuning \(\eta,\omega,\kappa\).
- Warehouse soft-clip stays a disclosed reduced-form drain unless S2 makes
  overflow a priced decision.

---

## 7. Cluster: trade objects, two prices, demand shape

### Current objects

| Symbol | Object | Unit |
|---|---|---|
| \(O\) | Export offers: surplus above food and \(T\), times \((1-\tau)\) | MMT/step |
| \(D\) | Purchase / import demand: food gap + \(\lambda\) rebuild toward \(T\) | MMT/step |
| \(A\) | Destination shares (FAOSTAT). Dest-row reweight \(\tilde A\) is the identity (`_ask_reweight_dest`) | dimensionless |
| \(S,\tilde S\) | Source shares (FAOSTAT, then CES origin mix \(\tilde S\propto S(p_0/q)^{\gamma}\); `_ask_reweight_src`) | dimensionless |
| \(d\) | Desired use: isoelastic flex + inelastic industrial | MMT/step |
| \(C^{\mathrm{ind}}\) | USA maize FSI minus 2000–04 mean; else 0 | MMT/step |
| \(p\) | One world price per crop, real 2010 $/t | $/t |
| \(q_i\) | Exporter ask (“export price”) | $/t |

Tonnes come from \(O\) and \(D\). FAOSTAT E0 is a **pattern**. \(\tau\)
cuts **offers**; cleared shipments are demand-constrained (Russia wheat
Aug–Dec 2010 offers ×0.11, ships ×0.79 vs harvest-only). A ban does **not**
create a cheaper domestic CPI: there is no domestic price object.

Linear \(D=a-Mp\) is the parked annual host, not Gate 0. Official scores use
window-mean flex / 24, not year-by-year food/feed.

### Colleague concern

“Sold to each market” was attributed to competitive storage; in Agrimate it
is likely the **purchaser** CES. “World vs export price” asks whether a
restriction can split the two. Linear vs isoelastic, and what “industrial”
means, were mixed into the same breath.

### Options

| ID | Option | What changes | Why someone wants it | Cost |
|---|---|---|---|---|
| T0 | **Keep** one world \(p\), asks \(q_i\), Armington min-clear, isoelastic flex, USA maize FSI residual | Writeup only | Honest; matches current snapshots | Ban cannot cheapen a local CPI (Gate 2 welfare on world \(p\) is the later pain) |
| T1 | **Domestic vs export price** when \(\tau>0\) (two \(p\)’s per exporter) | New state | Food-security welfare; economist “ban creates a wedge” | New identification. Gate 2 benefit, not a Gate 0 hindcast requirement |
| T2 | **Nested CES purchaser** (budget + origins) instead of origin-mix \(\tilde S\) | Allocation rule | Full Agrimate purchaser. Origin-share CES already ships; dest-row \(\tilde A\) is a no-op | Nested elasticity; FAOSTAT \(S\) already preference weights |
| T3 | **\(\tau\) cuts shipments not offers** (or both) | Quantity accounting | Shipment signs vs AMIS | Changes the disclosed leftover; must not be a 2008 knob |
| T4 | **Year-by-year flex as official demand** | Score protocol | Match PSD consumption path | Official split today is mean flex (Agrimate-matched). Would relabel Gate 0 |
| T5 | **Linear demand on the 24-step host** | Demand system | Match parked README §1 | Wrong object; isoelastic is the crisis claim |

T1 is the option that later layers most want, and the one Gate 0 least
needs for Pink Sheet world prices. Do not smuggle it in as a “small”
price-law tweak.

**Close this cluster** when (a) offer vs share vs ask vs world \(p\) are
never used as synonyms, (b) we have an explicit yes/no on a domestic price
in Gate 0, (c) the official demand split stays mean flex unless we
re-announce the split.

---

## 8. Cluster: expectations

### Current law

- **Harvest:** \(H^{\mathrm{exp}}=\phi H+(1-\phi)H^{\mathrm{seas}}\).
  Wheat/rice \(\phi=0.55\), maize \(0.50\). Enters the **lean gap only**.
  Not a 10-year path. Not rational expectations. A country only partly sees
  its own bad year.
- **Price:** demand uses last fortnight’s \(p\). Asks adapt to this step’s
  fill. No \(E[p]\) over future years. No country-level price expectation.
- **Lean clock:** \(h_t\) is **world-wide** (until 12% of annual world
  harvest arrives). Shared by every country.
- **Calm:** no shock and no AMIS \(\Rightarrow p=p_0\). That is “stay close
  to equilibrium unless new info.”

Agrimate sitting: you don’t have perfect foresight over 10 years, but you
need to form expectations and adapt. Country-level vs world-level was in
the notes; SHEAF’s lean horizon is already not country-level. “New markets”
is not an object in the code.

### Options

| ID | Option | vs sitting | Cost |
|---|---|---|---|
| E0 | **Keep \(\phi\)-blend + last-\(p\) demand.** Disclose thin expectations | Matches “not 10-year foresight.” Does not match Agrimate’s expectation module | 0 |
| E1 | Same-step \(p\) in demand (identical to P2) | Price expectation = this step’s clearing | See P2 |
| E2 | **Country lean clock** (pulse defined on \(i\)’s calendar, not world) | Answers “country-level” | Changes \(T_i\) and offers; harvest calendars already exist |
| E3 | **Agrimate-style expectation formation** (their module, adaptive toward seasonal Nash) | Closest to the sitting sentence | Need their exact object first; new state |
| E4 | **10-year / RE foresight** | Opposite of what they said | No |

E4 is not on the table. E0 vs E2 is a real modeling choice (world hungry
season vs national crop calendar). E3 waits until Agrimate’s expectation
object is named in *their* code, not guessed from the notes.

---

## 9. Cluster: too many knobs vs hard bounds

### Current classification (from `GATE0_PARAMETERIZATION.md`)

| Class | Examples | Fit to 2008? |
|---|---|---|
| Literature | \(\varepsilon\), `stu_target`, `max_stu` | Only inside published ranges |
| Structural | 24-step clock, AMIS→\(\tau\), pipeline, \(\nu\), pulse 0.12, USA maize industrial | No — redesign if changed |
| Reduced-form | \(\lambda,\lambda_W,\eta,\rho,\omega,\kappa_u,\kappa_b,\alpha,\theta,\gamma,\beta,\alpha_r,\phi\) | No — shared across years, not crisis-by-crisis |

Hard-ish bounds: warehouse \(W\), ask clips \([0.45p_0,2.8p_0]\), price
clips \([60,1200]\), AMIS \(\tau\), Armington min. These already do work a
FOC would do (capacity, no infinite ask, no infinite \(p\)).

Colleague remark: too many parameters; hard constraints would produce
similar behavior. That can be read as (i) a request to **cut knobs**, or
(ii) a claim that **\(T\) and \(W\) already are** the model, and the
reduced-form price map is extra.

### Options

| ID | Option | Knob count | Risk |
|---|---|---|---|
| K0 | **Keep the table.** Document class of every number. No 2008-only values | Same | FAO still sees a long table |
| K1 | **Freeze a subset to 0 or 1** where P1 shows they are not identified (e.g. \(\alpha_r=0\) recovers own-fill; \(\omega=1\) is asks-only; \(\omega=0\) is scarcity-only) | Down | Those are **sensitivities already worth scoring**, not necessarily a new official map |
| K2 | **Replace a block of knobs with one FOC** (P3 or S2) | Down if the FOC is real | New params of the FOC; 2008-fit temptation |
| K3 | **More hard bounds, fewer gains** (hard warehouse, hard offer floor, drop \(\kappa_u,\kappa_b\)) | Down | May be the sitting’s “constraints ⇒ similar behavior.” Score risk on 2010 blockage channel |
| K4 | Fit reduced-form knobs to 2007/08 | Down on paper, dishonest | Forbidden |

K1 is the cheapest empirical answer to “too many parameters”: isolated
\(\omega\in\{0,1\}\), \(\alpha_r=0\), \(\kappa_b=0\), etc., already tell us
which channels carry 2008 vs 2010. That is interrogation, not a redesign.

---

## 10. Snapshot leftovers — what a redesign can and cannot eat

From the current official P1 split. These are **not** a to-do list for
knobs. They are tests for whether an option in §§3–9 is even aimed at the
right leftover.

| Leftover | Mechanism in the current map | Options that could touch it | Options that will not |
|---|---|---|---|
| Wheat 2007/08 still high (×2.27 vs ×1.82); restriction-led | \(\tau\) on offers + \(\alpha_r\) / \(\kappa_b\) blockage | P3, T1, T3, K1 (\(\alpha_r,\kappa_b\)) | S0 language; B0 naming; E0 |
| Wheat 2010 production-led after LOWESS | Harvest forcing, not a price-law bug | Not a \(p\)-map rewrite | Price FOCs |
| Consumption corr negative vs PSD | Official mean flex + \(\varepsilon<0\) | T4 (relabel official demand) | Storage Euler |
| Exporter stocks on world safety floor | One world `stu_target`; \(O\) sells surplus above \(T\) | S2, T1; **not** S3 without new evidence | P0 writeup |
| \(\tau\) cuts offers more than shipments | Demand-constrained Armington | T3 | Ask FOC alone |
| Maize 2010/11 a bit high | Harvest-only ~flat; residual elsewhere | K1 isolations first | Clone Agrimate first |
| Vietnam rice stocks fat in **2006** | Data / calendar, not 2008 ban | Not a sitting-cluster rewrite | AMIS \(\tau\) |

A change that improves wheat 2008 by fitting \(\kappa_b\) is **not**
vetting. A change that improves wheat 2008 because \(\tau\) now means the
same thing in offers and in shipments, scored with knobs held, **is** a
candidate.

---

## 11. What stays off the table while we vet

- Crisis dummies; 2008-only \(\kappa\); picking \(\sigma^\star\)
- Mixing `sheaf.annual` into `_simulate_window` (parked; pull in only for a
  year-scale outer loop we actually want)
- Unpausing `dynamic_grains.py` to chase Gate 0
- Running Gate 2 as if Headey required a new `CropParams`
- Cloning Agrimate’s Julia layer and calling it SHEAF Gate 0
- Deaton–Laroque as the storage test (lineage is TWIST → Agrimate → SHEAF)

Continuity test for any surviving option: does it move us **toward** a
disclosed 24-step stock–trade–ask system on Agrimate’s clock and data, or
toward a second Agrimate, or back toward a yearly QP that already failed?

---

## 12. How a cluster is closed (decision protocol)

Same order as the verification protocol, applied to a **design option**
rather than a suspected bug:

1. **Locate the sitting claim** (this file’s “colleague concern”).
2. **Locate the implementation** (`dynamic_crop.py` line block above).
3. **Match or mismatch** with what we print (`ARCHITECTURE.md`, README §8,
   `GATE0_PARAMETERIZATION.md`).
4. **Characterize the current law** (P1 / O1): is it already the FOC /
   baseline / storage object they asked for?
5. **If we change:** one named option ID, complexity-budget paragraph,
   official vs sensitivity, re-score wheat/maize/rice, update the parameter
   table in the same commit.
6. **If we keep:** one sentence we will stand behind in the paper.

Skipping to step 5 without step 4 is how the foundation stays weak.

---

## 13. Suggested order of discussion (not of coding)

1. **Names** — baseline objects (B0), offer vs share vs ask vs \(p\) (T0),
   “DE” vs map (P0). Zero code. If coauthors do not share names, later
   clusters are noise.
2. **Honesty** — `ARCHITECTURE.md` agent sentence; reduced-form vs FOC
   (O0/O1, P1). Still zero code unless characterization is a short note.
3. **Storage principle** — S0 vs S2 (and confirm slide 48 ≠ \(r\)). This is
   the sitting’s sharpest “your commercial layer is missing” point.
4. **Price principle** — keep map vs P2 vs P3. Only after (2) and (3),
   because a markup FOC on asks while \(T\) is still a cover rule is a
   mixed object; say so if we do it.
5. **Knob isolations** — K1 on \(\omega,\alpha_r,\kappa_b\) as
   interrogation, not as a new official map.
6. **Then** write in-repo Cursor prompts that force steps 1–4 of §12 on
   each surviving option. Prompts come **after** this discussion, not
   instead of it.

Gate 1 and Gate 2 stay paused until this list has closed enough that we
would print Gate 0 as the market we believe.
