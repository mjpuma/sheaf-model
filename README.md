# SHEAF Model

<p align="center">
  <img src="assets/SHEAF_Model_logo.png" width="260" alt="SHEAF Model logo — a wheat ear, rice panicle, and corn cob bound together in a green ring">
</p>

> **sheaf** &nbsp;/ʃiːf/&nbsp;
> — *(agriculture)* a bundle of cereal stalks bound together after the harvest;
> — *(mathematics)* a structure that consistently glues locally defined data into a coherent global whole (sheaf theory).
>
> Both senses describe the model. It **binds** several grains and heterogeneous agents into one
> trade network, and it **glues** each country's local supply, demand, and policy into a single,
> globally consistent market equilibrium.

**S**ubstitution, **H**eterogeneous agents, **E**quilibrium, **A**nd **F**ragility Model: a country-level,
multi-commodity, game-theoretic network model of global grain trade.

It sits in the TWIST → Agrimate lineage. Those models already do storage (and Agrimate
already does a trade network). SHEAF exists because two first-order pieces of crisis
dynamics are still missing:

1. **Strategy.** Exporters restrict in a crisis, and those restrictions move world
   prices. Agrimate takes the restriction schedule as given (AMIS). SHEAF's destination
   is an *endogenous* export-restriction game among governments — who restricts, how
   much, and whether cooperation changes the outcome. Gate 0 first isolates that
   contribution with AMIS prescribed, one crop at a time.
2. **Substitution.** Wheat, rice, and maize are linked on the demand side, so a shock
   to one grain spills into the others. Single-commodity models wall each grain off;
   that overstates own-grain spikes and misses the other markets. In SHEAF the
   no-substitution case is a *special limit* (`σ = 0`), not the model.

Both sit on a **trade network** cleared each **fortnight** (Gate 0: 24
steps/year). Crisis papers keep substitution and the game as separate
switches: Gate 0 is both off (AMIS diary); Gate 1 is substitution on,
game off; the crisis game is types slow / actions on that same 24-step
clock (`diagnostics/GAME_CLOCK.md`). Headey (2011) is the guiding
account of why those actions have dates, not marketing years.

The annual SPE (Takayama–Judge QP + year-Nash) is **parked** in
[`sheaf/annual/`](sheaf/annual/README.md) so it can be imported later as a
slow outer loop. It is not the default API and **not** the 2007/08 object.

![harvest shocks versus export restrictions, 2006–11](figures/fig1_gate0_prices.png)

*Gate 0, 2006–11, one crop at a time (Pink Sheet in real 2010 \$). Harvest anomalies
alone miss the 2008 rice spike and understate 2007/08 wheat; adding observed export
restrictions (AMIS) produces both. That is why SHEAF has a strategic layer —
restrictions are first-order, not a residual. Agrimate takes those restrictions as
given; SHEAF's next step is to let exporters choose them **on that same
two-week clock**. Characteristic government types (how much they care
about domestic food) can be sticky; the decision is not. Substitution is
the other missing piece, and is still off in this figure. Gate 0 does
not need to be re-run to say that.

## Mathematical formulation

Crisis work uses the **24-step Gate 0 spine** (`sheaf/dynamic_crop.py`,
§8 below). The baseline market is open to revision after colleague
consultation; existing `diagnostics/gate0_*_report.md` scores are
snapshots, not a freeze.

The **annual SPE** (linear demand, yearly QP, lagged-price storage,
$/t Nash) is parked in [`sheaf/annual/README.md`](sheaf/annual/README.md).
Pull it in with `from sheaf.annual import SheafModel`. Do not treat it as
the crisis heartbeat.

### 7. From data to parameters

**Gate 0 wheat spine (§8):** USDA PSD country production, consumption, and ending
stocks (`sheaf/data_usda.py`); FAOSTAT bilateral E0 **share pattern**
(`sheaf/data_faostat.py`) — E0 magnitudes are unit-agnostic and are never
used as tonnes; only row/column shares $A,S$ enter the spine; AMIS
export-restriction schedules; harvest calendars in `data/crop_calendars/`;
monthly Pink Sheet prices for scoring.

**Annual SPE prototype (parked):** `sheaf.annual.SheafModel` still uses the
illustrative table in `sheaf/calibration.py` (optionally overlaid with USDA
quantities). See [`sheaf/annual/README.md`](sheaf/annual/README.md).

### 8. Gate 0 sub-annual crop spine (Agrimate-aligned)

Implementation: `sheaf/dynamic_crop.py` (wheat wrap: `sheaf/dynamic_wheat.py`).
Clock: $T_y=24$ steps per year
($\Delta t \approx 15.2$ days). Quantities in million tonnes (MMT); prices in
real \$/tonne (Pink Sheet deflator). **One crop at a time** until Gate 0 is green
for wheat, maize, and rice (`diagnostics/GATE0_PER_CROP_PLAN.md`).

#### Notation

| Symbol | Meaning | Default / source |
|---|---|---|
| $i,j$ | SHEAF nodes (17 named + Rest-of-World) | `calibration.DATA` |
| $t$ | sub-annual step index | $24$ per calendar year |
| $H_{i,t}$ | harvest inflow (MMT/step) | climatology × LOWESS anomaly × calendar |
| $C_{i,t}$ | baseline food/feed use (MMT/step) | official P1: mean-flex $/24$ |
| $S_{i,t}$ | end-of-step stocks (MMT) | state variable |
| $\mathrm{avail}_{i,t}$ | $S_{i,t}+H_{i,t}$ | identity, every step |
| $p_t$ | world price (\$/t) | state; smoothed |
| $p_0$ | reference price | mean real Pink Sheet in start year |
| $\varepsilon$ | food demand price elasticity | crop-specific (`CropParams.elast`) |
| $\tau_{i,t}\in[0,1]$ | AMIS export quantity cut | ban $0.95$, tax $0.50$, … |
| $A_{ij}$ | destination share of $i$'s exports to $j$ | FAOSTAT E0 **row shares** (diag $0$; E0 is not tonnes) |
| $S_{ij}$ | source share of $j$'s imports from $i$ | FAOSTAT E0 **column shares** (diag $0$) |
| $q_{i,t}$ | exporter **ask** price (\$/t) | adapts to fill rates |
| $\lambda$ | stock-rebuild speed per step | $0.08$ |
| $\phi$ | weight on realized harvest in foresight | $0.55$ (maize $0.40$) |
| $\eta$ | scarcity-price inverse elasticity | $\approx 1.0$ (`inv_eta`) |
| $\mathrm{shift}_t$ | scarcity-ratio floor | $0.05\sum_i s_i$ plus a non-negativity pad |
| $\rho$ | price smoothing toward $p^\star$ | $0.65$ |
| $\kappa_u,\kappa_b$ | unmet-anomaly and preferred-block weights | crop-specific |
| $\alpha,\theta$ | ask-adjustment speed and target fill | $0.15$, $0.70$ |
| $\alpha_r$ | rival-block ask markup | $0.80$ |
| $\gamma$ | ask competitiveness exponent | $1.25$ |
| $\omega$ | weight on trade-weighted ask in $p^\star$ | $\approx 0.65$–$0.72$ |
| $\beta$ | ask mean-reversion weight toward $p_t$ | $0.18$ |
| $\nu$ | residual-substitution share after Armington | $0.15$ |
| $s_i$ | safety stock | $\mathtt{stu\_target}\cdot C_i^{\mathrm{ann}}$ |
| $C^{\mathrm{flex}},C^{\mathrm{ind}}$ | price-elastic use vs inelastic industrial | USA maize: FSI excess vs 2000–04 |

Full parameterization, classes (structural / literature / reduced-form), and
economic defensibility: [`diagnostics/GATE0_PARAMETERIZATION.md`](diagnostics/GATE0_PARAMETERIZATION.md).
Defaults live in `sheaf.dynamic_crop.default_crop_params`.

#### Harvest calendars and why we detrend

The twin / climatology path is the score-window **mean** seasonal harvest
(country calendar weights in `sheaf/seasonal.py`). Treatment harvest is **not**
raw PSD year totals laid on that calendar. It is
$$
H_{i,y}^{\mathrm{ann}}=\overline{H}_i\cdot(1+a_{i,y}),
\qquad
a_{i,y}=\frac{Y_{i,y}-\hat Y_{i,y}}{\hat Y_{i,y}},
$$
where \(\hat Y\) is a per-country LOWESS trend on a padded PSD history
(`detrend_anomalies` in `sheaf/data_usda.py`, Agrimate's method) and the
annual total is then spread with triangular month weights.

**Calendar weights.** For a harvest window of $N$ months with peak index
$i_{\mathrm{peak}}$ along that window,
$$
w_m \propto \max\bigl(N-|i_m-i_{\mathrm{peak}}|,1\bigr)
$$
on months in the window and $0$ elsewhere; then each month is split
equally across its two half-month steps so $\sum_t w_{i,t}=1$ over a year
(`harvest_month_weights`, `step_weights_from_months`).

**Why this matters.** An in-sample 2006–11 *mean* is contaminated by post-2008
trend growth. World wheat 2006 is about **−9% vs that mean** but only **−4% vs
LOWESS**. The model then treats 2006/07 as a crash (false May spike) and
under-weights 2010 (Russia drought sits near a boom-inflated mean). The same
bias made 2008 maize look scarce when it is on-trend, and dumped 2008–11 rice
growth into stocks. Signed anomalies vs trend keep the twin balanced with mean
flex demand and isolate *shocks*, not secular yield growth.

Official P1 still uses year-by-year AMIS and (for USA maize) industrial use;
only the harvest *level* is climatology × anomaly. `shock_mode=full` keeps
surpluses as well as shortfalls.

Rice calendars are multi-crop (kharif + rabi / early + late) except Vietnam,
whose autumn pulse is kept so the 2008 ban still hits offers.

**Availability.** At the start of every step,
$$\mathrm{avail}_{i,t}=S_{i,t}+H_{i,t}.$$

**Official P1 step demand.** Year-by-year flex is a sensitivity
(`use_demand=True`). The locked score uses **mean flex**, split uniformly:
$$
\overline{C}^{\mathrm{flex}}_i=\frac{1}{Y}\sum_y C^{\mathrm{flex}}_{i,y},
\qquad
C^{\mathrm{flex}}_{i,t}=\overline{C}^{\mathrm{flex}}_i/24.
$$
Industrial (USA maize FSI excess) is year-by-year when
`use_industrial=True`, then $/24$. Pipeline food used in $W$ is
$C_i^{\mathrm{ann}}/24$, not the shocked flex path.

#### Lean foresight and targets

Let $h_t$ be steps to the next global harvest pulse: the smallest $h\ge 1$
such that cumulative **world** harvest ahead reaches $12\%$ of mean annual
world $H$ (cap $24$; `steps_to_harvest_pulse`),
$$
h_t=\min\Bigl\{h\ge 1:\ \sum_{k=1}^{h} H^{\mathrm{world}}_{t+k}
\ge 0.12\,\overline{H}^{\mathrm{world}}\Bigr\}.
$$
All countries share this clock. Expected harvest for foresight is the blend
$$H^{\mathrm{exp}}_{i,t}=\phi\,H_{i,t}+(1-\phi)\,H^{\mathrm{seas}}_{i,t},$$
where $H^{\mathrm{seas}}$ is the mean-year seasonal path. The lean gap
**includes the current step** ($k=0$ through $h_t$):
$$
L_{i,t}=\max\Bigl(0,\ \sum_{k=0}^{h_t} C_{i,t+k}-\sum_{k=0}^{h_t} H^{\mathrm{exp}}_{i,t+k}\Bigr),
\qquad
T_{i,t}=L_{i,t}+s_i.
$$
(`rolling_ahead_variable` sums $t+1,\ldots,t+h_t$; `_simulate_window`
adds $C_{i,t}$ and $H^{\mathrm{exp}}_{i,t}$.)

#### Demand, offers, and AMIS

$$
d_{i,t}=C^{\mathrm{flex}}_{i,t}\,(p_t/p_0)^{\varepsilon}+C^{\mathrm{ind}}_{i,t},
$$
$$
D_{i,t}=\max(0,d_{i,t}-\mathrm{avail}_{i,t})
+\lambda\max\bigl(0,\,T_{i,t}-\max(0,\mathrm{avail}_{i,t}-d_{i,t})\bigr),
$$
$$
O_{i,t}=\max(0,\mathrm{avail}_{i,t}-d_{i,t}-T_{i,t})\,(1-\tau_{i,t}).
$$
Carry capacity is
$$
W_{i,t}=\mathtt{max\_stu}\,C_i^{\mathrm{ann}}
+\mathtt{pipeline\_max\_steps}\cdot C_i^{\mathrm{ann}}/24
+\mathbf{1}_{\{\mathtt{pipeline}>0\}}H_{i,t}.
$$
Pulse crops (wheat/maize, `pipeline_max_steps=12`) pad \(W\) with same-step
harvest so a pulse is not incinerated on intake. Rice (`pipeline=0`) clips
toward carry: padding \(W\) with every monsoon step stored harvest as silos.
Overflow is soft-clipped at `warehouse_lambda` (default = rebuild \(\lambda\)).

**Stock scoring (nodes, not groupings).** USDA PSD ending stocks are *local
marketing-year* carry. World wheat is scored in May (×1.02 vs PSD) and maize in
August (×1.08). Rice is August (×1.05), not calendar December — December is the
post-kharif peak and was the old ×1.63 “fat STU.” Each SHEAF node is then
scored at its own USDA MY-end month (`sheaf/marketing_years.py`). Do not
aggregate into Agrimate’s 28 regions. World tightness is also scored
FAO/AMIS-style: the same MY-end month **with and without China** (rice: also
without India). Wheat ×1.09 and rice ×1.14 excluding China sit next to the
including-China world bar; maize ×1.49 is leftover (China MY is September,
world bar is August, and local-MY China maize is fat). China remains a named
node; its stock *levels* are estimated state reserves and are not a Gate 0 fail.

**Consumption scoring (P1 expansion, not Agrimate Fig. 4).** World calendar-year
use vs **country-sum** PSD (not `load_crop_world`, which omits the EU): wheat
×0.92, maize ×0.92, rice ×0.86. Official matched is mean flex + isoelastic, so
the model path is flat/down while PSD use rises (wheat corr −0.17, maize −0.64,
rice −0.74). Median country-year ratio is a sanity print, not the bar.
Year-by-year food/feed is a sensitivity. Agrimate Fig. 4 scored supply Δ and
stock Δ, not consumption levels.

**AMIS shipment signs (P1 expansion).** Official matched vs harvest-only, not
the isolated-τ assert. τ cuts offers; shipments are demand-constrained.
Russia Aug–Dec 2010 offers ×0.11, ships ×0.79. Argentina May 2007 offers
×0.30, ships ×0.99. Rice Oct–Dec 2007 ban+harvest signs are right; the
scored Vietnam window is a 2008 tax. Not FAOSTAT bilateral crisis volumes.

#### Adaptive ask prices and Armington clear

Destination shares are ask-reweighted,
$$\tilde A_{ij}\propto A_{ij}\,(p_0/q_{i,t})^{\gamma}\quad(\text{rows renormed}),$$
then preferred links clear as
$$\mathrm{ship}^0_{ij}=\min\bigl(O_{i,t}\tilde A_{ij},\,D_{j,t}S_{ij}\bigr).$$
Leftover offers and leftover demand form a residual pool that can fill at
most fraction $\nu$ of leftover demand (`_bilateral_clear`):
$$
\mathrm{offer}^{\mathrm{left}}_i=\max\bigl(0,O_{i,t}-\textstyle\sum_j\mathrm{ship}^0_{ij}\bigr),
\quad
\mathrm{demand}^{\mathrm{left}}_j=\max\bigl(0,D_{j,t}-\textstyle\sum_i\mathrm{ship}^0_{ij}\bigr),
$$
$$
\mathrm{take}_j=\nu\,\mathrm{demand}^{\mathrm{left}}_j,
\qquad
\mathrm{fill}=\min\Bigl(1,\;
\frac{\sum_i\mathrm{offer}^{\mathrm{left}}_i}{\sum_j\mathrm{take}_j}\Bigr),
$$
leftover offers are allocated by leftover-demand weights
$w_j\propto\mathrm{take}_j\cdot\mathrm{fill}$, and columns are clipped so
no importer receives more than that cap. $\mathrm{ship}=\mathrm{ship}^0+\mathrm{ship}^1$.
E0 never supplies the tonnes; $O$ and $D$ do.
Fill rates update asks (sold-out $\Rightarrow$ raise ask; leftover $\Rightarrow$ cut):
$$
q_{i,t+1}
=\bigl[(1-\beta)\,q_{i,t}\exp\bigl(\alpha(\mathrm{fill}_{i,t}-\theta)
+\alpha_r b_t\cdot\mathbf{1}_{O_{i,t}>0}\bigr)
+\beta\,p_t\bigr],
\qquad
\mathrm{fill}_{i,t}=\frac{\sum_j\mathrm{ship}_{ij}}{\max(O_{i,t},\epsilon)},
$$
with mean-reversion weight $\beta=0.18$, rival markup \(\alpha_r=0.80\),
clipped to $[0.45\,p_0,\,2.8\,p_0]$. \(b_t\) is the preferred-source block
fraction; \(\alpha_r=0\) recovers the own-fill law.

#### World price

After trade, physical cover is \(\sum_i S_{i,t+1}-\sum_i L_{i,t}\). Surplus
sitting behind an export cut is not world-market accessible:
\(\mathrm{locked}_t=\sum_i \tau_{i,t}\max(0,S_{i,t+1}-T_{i,t})\),
\(\mathrm{free}_t=\sum_i S_{i,t+1}-\sum_i L_{i,t}-\mathrm{locked}_t\).
Let $F^{\mathrm{twin}}_t$ and $u^{\mathrm{twin}}_t$ be free stocks and unmet fractions
from a **path-matched twin** (mean flex $C$, mean-year $H$, no industrial, $\tau\equiv 0$). Define
$$
u_t=1-\frac{\sum_i\mathrm{received}_{i,t}}{\max(\sum_i D_{i,t},\epsilon)},
\quad
b_t=\frac{\sum_{i,j} S_{ij}\,\tau_{i,t}\,D_{j,t}}{\max(\sum_j D_{j,t},\epsilon)},
\quad
\Delta u_t=\max(0,u_t-u^{\mathrm{twin}}_t).
$$
Trade-weighted ask
$$
p^{\mathrm{tr}}_t=\frac{\sum_i q_{i,t}\,\mathrm{shipped}_{i,t}}{\sum_i\mathrm{shipped}_{i,t}}
$$
(or the incoming $p_t$ if no trade). The scarcity ratio uses a
**state-dependent floor**, not a free constant $f$:
$$
\mathrm{shift}_t=0.05\sum_i s_i+\max\bigl(0,\,-\min(\mathrm{free}_t,F^{\mathrm{twin}}_t)\bigr),
\qquad
r_t=\frac{F^{\mathrm{twin}}_t+\mathrm{shift}_t}{\mathrm{free}_t+\mathrm{shift}_t}.
$$
The $0.05\sum s_i$ term keeps $r_t$ defined when free cover is small; the
second term is zero unless free or twin goes negative. Scarcity signal
$$
p^{\mathrm{scar}}_t=p_0\cdot r_t^{\eta_{\mathrm{eff}}}
\cdot\bigl(1+\kappa_u\Delta u_t+\kappa_b b_t\bigr),
$$
with $\eta_{\mathrm{eff}}=\eta$ (symmetric in surplus and shortage). Then
$$
p^\star_t=\omega\,p^{\mathrm{tr}}_t+(1-\omega)\,p^{\mathrm{scar}}_t,
\qquad
p_t=\rho\,p_{t-1}+(1-\rho)\,p^\star_t.
$$
If the path matches the twin (calm), $p^\star_t=p_0$ by construction
(`assert_twin_identity`).

**Opening stocks.** PSD ending stocks in `stock_seed_year` (default 2005)
are clipped to carry,
$$
S_{i,0}=\min\bigl(R^{\mathrm{end}}_{i,\mathrm{seed}},\,
\max(\mathtt{max\_stu}\,C_i^{\mathrm{ann}},\,1.5 s_i)\bigr),
$$
then optionally spun up `spin_up_years=2` on climatology harvest, mean
flex, no industrial, no AMIS. The $1.5s$ floor is an **opening** clip
only; warehouse $W$ uses $\mathtt{max\_stu}\,C$ with no $1.5s$ term.

#### Method of solution

The crisis host does **not** solve a spatial price equilibrium, a
complementarity problem, or a market-clearing root each step.
`_simulate_window` evaluates an **explicit sequential map**
$t=0,\ldots,T-1$. Lean horizons and rolling sums are computed once
before the loop. Inside the step:

1. $\mathrm{avail}_{i,t}=S_{i,t}+H_{i,t}$
2. $d,L,T,D,O$ from closed-form algebra (isoelastic $d$ uses the
   **incoming** $p_{t-1}$; $q_{i,t}$ is the ask inherited from $t-1$)
3. $\tilde A$, Armington $\min$, residual pool (dense $n\times n$)
4. consumption, stock update, soft warehouse clip
5. ask update $\to q_{i,t+1}$
6. $p^{\mathrm{tr}}$, $\mathrm{shift}$, $r$, $p^{\mathrm{scar}}$,
   $p^\star$, then $p_t=\rho\,p_{t-1}+(1-\rho)\,p^\star_t$

There is no inner iteration to a within-step fixed point. The
path-matched twin is a **second** forward pass of the same map
(mean-flex $C$, seasonal $H$, $\tau\equiv 0$). Complexity is
$O(Tn^2)$ per crop ($n=18$). Implementation is NumPy; `cvxpy` is not
imported on this path. **SHEAF stays in Python.** Agrimate's Julia is
because they solve per-step agent optimizations, not because the same
map is faster in Julia. The same map would be the same algorithm in
either language.

**Gate 1.** One Jacobi factor $\mathrm{fac}=\exp(\eta\log(p/p_0))$ from
the three *start-of-step* world prices, then $G$ independent Gate 0
maps. Not a simultaneous three-crop fixed point and not Gauss–Seidel.

**Gate 2.** Three forward passes of the Gate 0 map (climatology, open
shocked harvest, then shocked harvest with $\tau_t$). The ratio rule is
a threshold, not an optimization. Nested-year grid BR is a leftover
diagnostic for $\tau^{\mathrm{on}}$.

**LOWESS** (prepare time only): tricube local linear, one $2\times 2$
weighted least-squares solve per sample point (`data_usda._lowess`).

**Parked annual host** (`sheaf.annual`): concave QP via cvxpy
(CLARABEL → SCS → OSQP) and year-IBR. Not the crisis object.

Agrimate (Kuhla et al. 2025) is a different object: each region’s
supplier, consumer, and purchaser solve constrained optimizations every
step (finite-horizon expected profit; CES under budget). That is why
their model is Julia (optional MPI). SHEAF’s crisis host does not solve
those agent problems.

#### Robustness asserts

`assert_twin_identity`, `assert_amis_raises_price`, `assert_amis_cuts_exports`,
`assert_no_spring_spike` — run by `scripts/score_subannual_crop.py --crop …`.
Questions the model might answer (hindcast, substitution, who restricts,
club, tipping, network) — not a queue of papers:
`diagnostics/PAPER_STACK.md`. Clock: `diagnostics/GAME_CLOCK.md`.
Agrimate-style figures: `python scripts/make_agrimate_comparison.py`.

### References

*Spatial price equilibrium (market layer).*

- Enke, S. (1951). Equilibrium among spatially separated markets: solution by electric analogue. *Econometrica*, 19(1), 40–47. https://www.jstor.org/stable/1907907
- Samuelson, P. A. (1952). Spatial price equilibrium and linear programming. *American Economic Review*, 42, 283–303.
- Takayama, T., & Judge, G. G. (1971). *Spatial and Temporal Price and Allocation Models*. Amsterdam: North-Holland.

*Competitive storage (storage layer).*

- Wright, B. D., & Williams, J. C. (1982). The economic role of commodity storage. *The Economic Journal*, 92(367), 596–614. https://doi.org/10.2307/2232552
- Williams, J. C., & Wright, B. D. (1991). *Storage and Commodity Markets*. Cambridge: Cambridge University Press.
- Deaton, A., & Laroque, G. (1992). On the behaviour of commodity prices. *The Review of Economic Studies*, 59(1), 1–23. https://doi.org/10.2307/2297923

*Export restrictions and price insulation (strategic layer).*

- Headey, D. (2011). Rethinking the global food crisis: The role of trade shocks. *Food Policy*, 36(2), 136–146. https://doi.org/10.1016/j.foodpol.2010.10.003
- Martin, W., & Anderson, K. (2012). Export restrictions and price insulation during commodity price booms. *American Journal of Agricultural Economics*, 94(2), 422–427. https://doi.org/10.1093/ajae/aar105

*Food-trade networks and the crisis-modelling lineage (single-commodity predecessors SHEAF generalises).*

- Puma, M. J., Bose, S., Chon, S. Y., & Cook, B. I. (2015). Assessing the evolving fragility of the global food system. *Environmental Research Letters*, 10(2), 024007. https://doi.org/10.1088/1748-9326/10/2/024007
- Schewe, J., Otto, C., & Frieler, K. (2017). The role of storage dynamics in annual wheat prices. *Environmental Research Letters*, 12(5), 054005. — introduces the Trade With Storage (**TWIST**) model.
- Falkendal, T., Otto, C., Schewe, J., Jägermeyr, J., Konar, M., Kummu, M., Watkins, B., & Puma, M. J. (2021). Grain export restrictions during COVID-19 risk food insecurity in many low- and middle-income countries. *Nature Food*, 2(1), 11–14. https://doi.org/10.1038/s43016-020-00211-7
- Kuhla, K., Kubiczek, P., & Otto, C. (2025). Understanding agricultural market dynamics in times of crisis: the dynamic agent-based network model Agrimate. *Ecological Economics*, 231, 108546. https://doi.org/10.1016/j.ecolecon.2025.108546

*Note on the TWIST/Agrimate lineage.* TWIST (Trade With Storage; Schewe et al. 2017, applied in Falkendal et al. 2021) reproduces annual world wheat prices from a stylised price–supply curve but does not resolve the trade network or export restrictions. Agrimate (Kuhla et al. 2025) adds a dynamic agent-based network with commercial and strategic stockholding and hindcasts 2007/08 and 2010/11, taking export restrictions as an exogenous AMIS schedule. Both are single-commodity. SHEAF exists to put **endogenous strategy** (governments choose restrictions) and **cross-grain substitution** on that network. Headey (2011) is the account of *when* those restrictions and import surges happen — months, not years — so the crisis game belongs on Agrimate’s 24-step clock, not on TWIST’s annual SPE. Gate 0 is why restrictions are first-order, with AMIS still prescribed; Gate 1’s $\sigma=0$ identity is the zero-substitution limit on the live host. The annual $\sigma=0$ proposition lives in `sheaf/annual/README.md`.

## Quick start

```bash
pip install -r requirements.txt
python scripts/score_subannual_crop.py --crop wheat
```

That is the crisis smoke test (Gate 0 wheat, 24-step map). Official reports:
`diagnostics/gate0_*_report.md`. Substitution band: `scripts/score_gate1.py`.
Policy beta: `scripts/score_gate2_beta.py`.

The parked annual SPE (Black Sea shock on the yearly QP):

```bash
python scripts/annual/demo.py
```

Minimal crisis use in code:

```python
from sheaf import run_crop_dynamics

result = run_crop_dynamics("wheat", start_year=2006, end_year=2011)
```

Annual prototype (only when you want the yearly QP):

```python
from sheaf.annual import build_countries, SheafModel

countries, transport, grains, freight = build_countries(substitution=True)
model = SheafModel(countries, transport, grains, freight_mult=freight)
df = model.run(periods=12, shocks={5: shock_matrix, 6: shock_matrix})
```

## Layout

```
sheaf/
  dynamic_crop.py     # Gate 0 24-step market (crisis heartbeat)
  dynamic_coupled.py  # Gate 1 isoelastic substitution on that spine
  dynamic_policy.py   # Gate 2: slow types, Headey-clock τ_t
  annual/             # parked yearly SPE + year-Nash (import sheaf.annual)
  calibration.py      # node names, GRAINS, RHO, illustrative DATA
  core.py             # ImportError shim → sheaf.annual
scripts/score_subannual_crop.py  # crisis smoke test / official P1
scripts/score_gate1.py
scripts/score_gate2_beta.py
scripts/annual/demo.py           # Black Sea shock on the parked annual host
diagnostics/GAME_CLOCK.md
```

## Extending it

- **Grains** — append to `GRAINS`, `P0`, and `RHO` in `sheaf/calibration.py` for
  Gate 1; Gate 0 `CropParams` is per-crop.
- **Real data** — crisis quantities already come from USDA PSD / FAOSTAT E0
  shares / AMIS / Pink Sheet. The illustrative `DATA` table is node names plus
  the parked annual prototype.
- **Annual outer loop** — `from sheaf.annual import SheafModel` when you want
  a year-scale diagnostic or slow types. Do not mix that clock into
  `dynamic_crop._simulate_window`.
- **Chokepoints / terms-of-trade** — those knobs live on the parked annual QP
  (`sheaf/annual/README.md`), not on the 24-step map.

## Caveats

This is a **prototype**. Gate 0 (`sheaf/dynamic_crop.py`) runs 2006–11
per-crop hindcasts against Pink Sheet with AMIS restrictions prescribed
(`diagnostics/gate0_*_report.md`). Those scores are snapshots of the current
baseline; the market is open to revision after colleague consultation.
Do not silently fit 2008 (no crisis dummies, no hidden $\sigma^\star$).
Gate 1 puts substitution on that spine (`diagnostics/gate1_report.md`).
The annual SPE in `sheaf/annual/` is illustrative — linear demand, inelastic
within-year production, discretised Nash on a tax grid. It is not the
2007/08 game. On the crisis spine, types are illustrative; actions `τ_t`
are state-contingent and not scored against who banned in 2008.

## License

MIT — see `LICENSE`.
