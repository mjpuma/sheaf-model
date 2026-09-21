# T3 — Obtain-or-leave FAO-since-2005 + AgrimateEU28+Egypt

Labelled Fig. 4 *experiment* inputs. **Not adopted.** Not C.1.
Not `prepare_wheat`. Not a pin. Not L1–L8. Not an αI retune.
Do not invent an Egypt node. Do not copy Julia. Do not start G1.
`wheat_params()` stay αI=3.2, ζ=0,
N_for=3. Fig. 4 knobs stay on
`fig4_experiment_params()` (αI=3.5, ζ=1, N_for=6).
G1/G2 stay blocked. USDA stays the default. FBSH 5074 is ΔS,
never S.

## Obtain

| source | what | SHA / md5 | in-tree? | adopted? |
|---|---|---|---|---|
| GitLab paper repo | `https://gitlab.pik-potsdam.de/agrimate/agrimate` | `f2de96551857` | inspect `/tmp` | — |
| AgrimateEU28 YAML + Egypt=EGY extra | compact ISO map | labelled CSV | **yes** (`t3_fig4_inputs/`) | **no** |
| FAO wheat anomalies+trends (daily 2000–2020) | annual relative 2000–2011, since-2005 mask | daily md5 `1edc5878210a` / `20583d3d299b` | compact CSV only (not 4.7 MB daily) | **no** |
| GitLab `wheat_food_balance_fao.csv` | 1992–2020 cleaned FB | `14a87dd79a2d` | **no** | **no** |
| host reconstruction FB | 2006–11 | `ba213511d9e3` | yes (`data/food_balances/`) | **no** |
| this checkout `sheaf/agrimate/` | `*.jl` | — | 0 | — |

GitLab is public CC-BY-4.0. Daily FAO CSVs stay under `/tmp`
(4.7 MB × 2). Author `aggregate_areas` sums ISO3 days to the
region; relative = Σ anomaly / Σ trend; forcing = 1 + relative
(NaN → 1). Fig. 4 NetCDF label `FAOsince-2005` is this FAO
source with years before 2005 zeroed (start 2000). There is no
separate `source=FAOsince-2005` file.

S4 parallel ISO map was guessed from host AgrimateRegionsWheat.
T3 uses the sourced AgrimateEU28 YAML: EU-28 includes GBR, BLX,
CSK; Brazil stays inside Rest of South America; Egypt is the
`extra_regions` overlay (EGY out of Northern Africa), not a C.1
invention. NetCDF 27 names match.

## Verification protocol (CLAUDE.md)

1. **Claim.** Published Fig. 4 is AgrimateEU28+Egypt, FAO
   anomalies since 2005, start 2000, αI=3.5, ζ=1, N_for=6
   (`GATE0_DEPARTURES.md` A7; NetCDF `production_anomalies=
   FAOsince-2005`). Host C.1 is AgrimateRegionsWheat + USDA +
   αI=3.2. Knobs that *can* be set already live on
   `fig4_experiment_params()`.

2. **Implementation.** Compact extracts:
   `diagnostics/gate0_agrimate/t3_fig4_inputs/
   agrimate_eu28_egypt_iso3.csv` (256 ISO3; 27 names) and
   `fao_since_2005_annual_relative.csv` (324 region-years).
   `REGION_NAMES` still has Egypt=False,
   EU-28=False, EU-27=True, Brazil=True. `prepare_wheat` notes still USDA
   PSD, not FAOSTAT Food Balances. `fig4_experiment_region_path()`
   = `None`.

3. **Match (obtain).** Arrays needed to *label* a Fig. 4
   comparison exist. Egypt extra is EGY. EU-28 has GBR/BLX/CSK.
   FAO 124 ISO3 all map. Egypt 2004 `relative_since_2005` = 0 (masked); 2005 = 0.0974. Ukraine 2008
   relative = 0.3456.

4. **Counterexample (not adopted).** `"Egypt" in REGION_NAMES`
   is False. `wheat_params()` αI=3.2, ζ=0, N_for=3.
   `fig4_experiment_params()` still holds 3.5 / 1 / 6.
   Passing the extract folder to
   `fig4_experiment_region_path` still returns None (no FAO FB
   *and* EU28 WheatData pair). GitLab FB was left (md5 differs
   from the host reconstruction). FAO ΔS is not S.

5. **Correctness of not inventing Egypt / not wiring FAO.**
   Splitting EGY onto C.1 without also switching the live window
   to start 2000, old-demand-dynamics, and FAO Food Balances
   would silently replace the 14022004 wheat host with a mixed
   experiment. T3 labels the sourced arrays; it does not run
   them. USDA LOWESS H/H*−1 stays the host anomaly.

6. **Change.** Labelled obtain. No economics. No retune.
   T-queue exhausted. G0-P still **not accepted** (item 3
   last/first 1.444 vs 1.004; items 1–3 still fail).

## Still cannot-set (A7 remainder)

- AgrimateEU28+Egypt as live C.1 (arrays labelled; host still
  AgrimateRegionsWheat)
- FAO-since-2005 as `WheatData` / `prepare_wheat` anomalies
- FAO Food Balances as `prepare_wheat` default (A1; USDA stays;
  GitLab FB left, not bit-identical)
- start 2000-01-01 as the live window (Fig. 4 n_steps=312)
- git old-demand-dynamics executable
- Zenodo 14022004 Julia in `sheaf/agrimate/` (0 `*.jl`)
- Fig. 4 knobs as `wheat_params()` (they stay on the comparison
  object)

n_julia=0. freeze_q_oth on params=False.

**Next paste: stay not-accepted.** T3 obtained, not adopted.
Do not start G1. Do not invent Egypt. Do not retune αI.

