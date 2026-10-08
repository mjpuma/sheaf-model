# Gate 2 foundations: export-restriction decision rule

Companion to [`GAME_CLOCK.md`](GAME_CLOCK.md), which fixes who acts on which clock. This file covers why the decision rule has this form and how it fits the Agrimate storage layer. Gate 2 stays blocked until Gate 1 is accepted ([`DEVELOPMENT.md`](DEVELOPMENT.md)).

Notation: R is already stock, μ the stress trigger and ζ the revenue weight in earlier SHEAF notes; σ is the CES elasticity in the Agrimate code, so the logistic function is written Λ. Kuhla et al. (2025), Schewe et al. (2017) and Headey (2011) were checked against the published papers; verify the other references before citing them in a paper.

## Approach

Export restrictions in SHEAF come from a decision rule that each country applies every period. The rule combines two forces that shape restriction decisions in practice.

- **Reactive (contagion).** A country restricts when domestic prices rise, stocks fall, or enough trading partners have already restricted. This follows the threshold logic of Granovetter (1978) and of cascade models on networks (Watts, 2002). It describes the fast, sequential spread of restrictions seen in 2007/08 and 2010/11, when restrictions by one exporter raised the likelihood of restrictions by others and amplified world price increases (Giordani, Rocha and Ruta, 2016; Martin and Anderson, 2012).
- **Strategic.** Countries also pursue goals. They protect domestic consumers, try to keep export revenue, and the large players try to maintain leverage over importers. This is deliberate statecraft, and it often sharpens during crises rather than fading.

These are not two separate populations. Every country is subject to both forces in different proportions. Large exporters lean strategic and small ones lean reactive, but none is purely one or the other. The model therefore gives every country the same rule and lets a country-specific weight set the mix.

## Decision rule

Let x_{i,t} in [0, 1] be the export restriction intensity of country i at time t:

```
x_{i,t} = (1 - ω_i) · H_{i,t} + ω_i · G_{i,t}
```

**Reactive term H.** A smooth threshold (logistic function Λ) on observables from the previous period:

```
H_{i,t} = Λ( a_p (Δp_{i,t-1} - θ_p) + a_s (θ_s - s_{i,t-1}) + a_n (φ_{i,t-1} - θ_n) )
```

where Δp is the domestic price change, φ the trade-weighted share of partners restricting, θ the thresholds and a the sensitivities. The stock signal is calendar-matched, s_{i,t} = S_{i,t} / S^calm_{i,t}, where S^calm is the storage path of the undisturbed run at the same calendar step. Stocks fall before every harvest, so a raw stock threshold would fire every year; the ratio equals 1 in a normal year, so restrictions stay off unless the shortfall is unusual ([`GAME_CLOCK.md`](GAME_CLOCK.md), after Headey 2011). Which stocks enter S (purchaser, supplier, or both) is open.

**Types and actions.** Following [`GAME_CLOCK.md`](GAME_CLOCK.md), government parameters (ω_i, objective weights, price targets) are slow "types," fixed within a simulation at the beta stage. The restriction x_{i,t} is the fast "action," evaluated on Agrimate's 24-step clock and able to switch on and off within a year. GAME_CLOCK.md writes the action as τ_{i,t}; since τ is already the purchaser's restocking timescale in the Agrimate code, this section uses x. One symbol should be chosen for both documents.

**Strategic term G.** The country's best response to the current state of the world, including what other countries are doing:

```
G_{i,t} = argmax_x  U_i(x | x_{-i,t-1}, state_{t-1})
```

U_i trades off domestic price protection against lost export revenue, with leverage terms added in Gate 3. In Gate 2 this best response is myopic: each country responds to last period's actions by others and does not solve for what others will do. This is the standard best-response dynamic from the learning-in-games literature (Fudenberg and Levine, 1998).

**Blend weight ω_i in [0, 1].** Set per country (see "Fit with the storage layer" for its prior). ω only matters for countries with exports to restrict.

## Feedback

One country's restriction raises world prices and tightens supply. That feeds into every other country's reactive and strategic terms in the next period. Cascades emerge from this loop; they are not imposed.

## Fit with the storage layer

The Gate 0 host already has two storage holders in every region (Kuhla et al., 2025, Suppl. Sec. D):

- **Commercial storage holder (supplier):** farmers and commercial inventory holders. A risk-neutral, bounded-rational profit maximizer with adaptive expectations about other suppliers' sales. Its baseline storage follows purely economic reasoning. *Code: `Producer`, `sales_step!` and `communication_step!` in `agrimate_julia/src/AgrimateModel/src/agents/producer.jl`.*
- **Strategic storage holder (purchaser):** food processors, retailers and strategic government-owned food inventories. Its baseline stock-to-consumption ratio comes from observed regional stockholding policies. When its storage falls below the seasonal baseline in a crisis, it raises its budget share to restock. *Code: `Consumer`, `determine_extra_demand` in `agents/consumer.jl`.*

This continues the TWIST lineage. TWIST has one producer-side and one consumer-side storage holder, and folds government strategic reserves into the consumer side rather than modeling public and private storage separately, because their objectives differ (Schewe et al., 2017). Agrimate names that consumer-side holder strategic and regionalizes it.

Gate 2 is built to fit this structure rather than duplicate it.

1. **One strategic stock, one government decision.** The purchaser already holds the strategic stock, so Gate 2 adds no second stockholder. A thin government layer per region reads state from the region's supplier (export revenue) and purchaser (storage, consumer price) and outputs x_{i,t}. It replaces the export restrictions that Agrimate takes as exogenous decisions of the regional government. A later extension can let the same layer shift the purchaser's storage target, which is the lever TWIST adjusted by hand for China's stock drawdown and later restocking.
2. **The strategic term mirrors the supplier's logic.** The supplier already optimizes against adaptive expectations of what other suppliers will sell. G applies the same myopic best-response structure to the government's objective.
3. **Prior for ω from observed stockholding.** The regional balance between strategic (purchaser) and commercial (supplier) stocks reflects stockholding policy and is a principled prior for ω_i. Whether large strategic stocks go with strategic restriction behavior is a hypothesis, tested against the AMIS restriction histories in `data/amis_policies/`.
4. **Both sides of the panic.** The purchaser's crisis restocking is import-side hoarding. The reactive term H is its export-side mirror. Together they close the feedback loop without a new mechanism.

## Where Nash fits

A Nash equilibrium is the state in which every country's strategic term is a best response to every other country's action at the same time. If the myopic best responses in G are iterated to convergence within a period, they reach that equilibrium. So Nash is not excluded from SHEAF. It is a limiting case of the strategic term.

We do not use Nash as the default, for three reasons.

1. **Crisis episodes do not look like an equilibrium.** The 2007/08 and 2010/11 waves were sequential and reactive, under incomplete information and domestic political pressure. A simultaneous fixed point is a poor description of that process across dozens of exporters.
2. **The standard assumptions are weakest when the model matters most.** Nash assumes rational players, common knowledge of rationality and known payoffs. In a fat-tailed crisis none of these hold well (Taleb, 2018, 2020).
3. **Countries live along one path.** Under multiplicative risk, the ensemble average can differ sharply from what a single country experiences over time (Peters, 2019). Crisis behavior should be evaluated along paths, not only in expectation.

The case for Nash is stronger for a small set of major powers (for example the US, Russia, China, Brazil, the EU and India) acting on a longer timescale. These are few players with real analytic capacity who model one another. Gate 3 tests this by solving the strategic term to equilibrium within that block only, while all other countries keep the myopic blended rule.

## Nesting

- ω_i = 0 for all i: pure threshold cascade.
- ω_i = 1 for all i: pure myopic best response.
- ω_i = 1 with best responses iterated to convergence: Nash equilibrium.
- x set to the observed AMIS restriction path instead of the rule: Gate 1 as run with historical restrictions; with cross-price terms also zero, this reproduces the accepted Gate 0 runs, which used the authors' exogenous restrictions.
- All cross-price terms zero: Gate 0, the single-commodity TWIST/Agrimate limit.

Prior models sit at corners of this space. The contribution is the interior.

## What the model claims

SHEAF does not predict a single equilibrium. The blend weights and thresholds are uncertain, and the model treats that uncertainty as the object of study. The main output is a fragility map: how likely a restriction cascade is, as a function of shock size and the mix of reactive and strategic behavior. The question is not where the system settles but how easily it tips.

## References

- Fudenberg, D., and Levine, D. K. (1998). *The Theory of Learning in Games.* MIT Press.
- Giordani, P. E., Rocha, N., and Ruta, M. (2016). Food prices and the multiplier effect of trade policy. *Journal of International Economics*, 101, 55–69.
- Granovetter, M. (1978). Threshold models of collective behavior. *American Journal of Sociology*, 83(6), 1420–1443.
- Headey, D. (2011). Rethinking the global food crisis: The role of trade shocks. *Food Policy*, 36, 136–146.
- Kuhla, K., Kubiczek, P., and Otto, C. (2025). Understanding agricultural market dynamics in times of crisis: The dynamic agent-based network model Agrimate. *Ecological Economics*, 231, 108546.
- Martin, W., and Anderson, K. (2012). Export restrictions and price insulation during commodity price booms. *American Journal of Agricultural Economics*, 94(2), 422–427.
- Peters, O. (2019). The ergodicity problem in economics. *Nature Physics*, 15, 1216–1221.
- Schewe, J., Otto, C., and Frieler, K. (2017). The role of storage dynamics in annual wheat prices. *Environmental Research Letters*, 12, 054005.
- Taleb, N. N. (2018). *Skin in the Game.* Random House.
- Taleb, N. N. (2020). *Statistical Consequences of Fat Tails.* STEM Academic Press.
- Watts, D. J. (2002). A simple model of global cascades on random networks. *PNAS*, 99(9), 5766–5771.
