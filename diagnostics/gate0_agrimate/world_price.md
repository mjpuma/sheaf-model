# Gate 0 wheat — world-price recipe (R3)

Host `p_w` is the **XI-weighted mix of lagged D.7 offers**, then
`price_usd = p_w × p0`. It is **not** Eq. D.7 of world XI / XI*_world,
and it is **not** a 2006 pin. `wheat_params()` stay αI=3.2, ζ=0,
N_for=3. L1–L8 stay rejected. G1/G2 stay blocked.

Zenodo 14022004 Julia (`plot_wm_price_timeseries`) is **absent** from
this checkout. This note is a host identity plus a labelled gap, not a
bit-diff of author plotting code.

## Verification protocol (CLAUDE.md)

1. **Claim.** `methods.md` §1 said “D.7 × p0; not a calm pin.”
   `fig4.md` said author Fig. 4d is volume-weighted international
   transaction price, “not D.7 on world XI*,” and the host scores
   “D.7 × p0 / p0.” `GATE0_SPEC_MATRIX.md` already named the mix:
   “XI-weighted lagged D.7 offers × p0.” `GATE0_REDTEAM.md` Step 6
   classified the methods shorthand as **G**.

2. **Code.** `sheaf/agrimate/model.py`:
   - Each region’s offer is D.7 of `(XI_r + Q_{-r}) / XI*_world`
     (planned `xi_ship0`, not fulfilled `sold_i`).
   - Offers and fulfilled XI enter an `Ndel=2` queue.
   - `p_w = volume_weighted_offer_index(xi_lag, p_lag)` =
     `dot(xi_lag, p_lag) / sum(xi_lag)` (empty volume → last `p_w`,
     else 1.0 at t=0).
   - `price_usd = price_index * p0` with `p0` = 2006 Pink Sheet mean
     (`wheat_data.py`). Unit scale, not a path pin.
   - Author-side extractor in this repo:
     `fig4.world_market_price_index` drops the domestic diagonal of
     `(producer, consumer, time)` `q·p` and volume-weights the rest.
     That is a reconstruction of Fig. 4d from Zenodo 10688435 NetCDF,
     **not** a copy of `plot_wm_price_timeseries`.

3. **Match.** Spec-matrix row matches the code. methods.md’s “D.7 × p0”
   omitted the volume-weight and the lag (G; wording fixed here and in
   the methods generator). Economics unchanged.

4. **Counterexample to “a single D.7 of world XI*”.** Two exporters,
   `XI=(8,2)`, `Q_{-r}=(1,1)`, `XI*=10`: regional D.7 arguments are
   0.9 and 0.3; the XI-weighted mix is not `0.9^{-α}` or `1^{-α}`.
   Executable: `test_volume_weighted_offer_index_is_xi_mix_not_single_d7`
   and the 2006 harvest+AMIS path in
   `test_reported_pw_equals_lagged_xi_weighted_offers_not_world_d7`.
   Counterexample to “2006 pin”: that path’s mean index is not 1;
   `price_usd / p0` recovers the index (`test_host_index_is_usd_over_p0`
   on the committed three-scenario CSV).

5. **Correctness.** The mix is what `AgrimateSim.run` already computed.
   Extracting `volume_weighted_offer_index` / `lagged_offer_index` and
   storing `AgrimateResult.offer` does not change offers, XI, or `p_w`.
   Classification **H** for the host identity (95–100%, replayed on
   2006 harvest+AMIS). Classification **G** for the methods shorthand
   (fixed). Open **G/H** on author Julia vs host until 14022004
   `plot_wm_price_timeseries` is in-tree (40–60% as a reproduction
   blocker — unchanged). Do not pin 2006. Do not change
   `wheat_params()`.

## Zenodo 14022004 gap

Searched this VM for `plot.jl` / `plot_wm_price_timeseries` under
`agrimate/`, `vendor/agrimate`, `src/agrimate`, `/opt`, `/workspace`.
No Julia sources. `GATE0_DATA.md` already records that 14022004 was
retrieved 2026-09-16 as the executable specification and **not copied**.
R3 therefore cannot write a symbol-by-symbol Julia diff. The host-only
identity test is the substitute named in the prompt.

If a later session obtains the Julia, diff `plot_wm_price_timeseries`
against `fig4.world_market_price_index` **and** against
`volume_weighted_offer_index`. Do not vendor the Julia into
`wheat_params()`.

## Author Fig. 4 extractor vs host (in-tree only)

| piece | host | `fig4.world_market_price_index` |
|---|---|---|
| price | per-exporter D.7 offer | NetCDF `transaction price` |
| quantity | lagged fulfilled XI | bilateral `transaction quantity` |
| domestic | XI is already international | diagonal dropped |
| lag | `Ndel=2` delivery queue | contemporaneous NetCDF step |
| scale | × p0 for USD | index as stored |

They coincide when every destination pays the exporter offer. They
diverge if transaction prices are destination-specific. That is a
definition gap, not a retune.

## What this session did not do

- Pin the unforced world price to the 2006 mean.
- Change `wheat_params()` or adopt Fig. 4 knobs / Bai α_foreign=10.
- Restore L1–L8. Start G1 or G2. Re-run the three-scenario runner.
- Treat maize/rice as an acceptance target.
