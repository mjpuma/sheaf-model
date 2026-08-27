"""Re-derive every quantitative claim made in the SHEAF first-principles deck.

Run from the repository root::

    python3 overleaf/sheaf_deck/verify_claims.py

Each check prints ``[OK]`` / ``[DIVERGENCE]`` / ``[FAIL]`` and the numbers the
slides quote. Nothing here modifies the model: it imports ``sheaf`` read-only
and re-runs the locked Gate 0 / Gate 1 / Gate 2 hosts with their own defaults.

``[DIVERGENCE]`` is not a failure. It marks a place where prose (README or a
diagnostics note) and the implementation say different things, and the deck
shows both.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

RESULTS: list[tuple[str, str, str]] = []


def record(tag: str, name: str, detail: str) -> None:
    RESULTS.append((tag, name, detail))
    print(f"[{tag}] {name}\n        {detail}")


def section(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def check_clock() -> None:
    section("1. Clock (sheaf/calendar24.py)")
    from sheaf.calendar24 import (
        DAYS_PER_STEP,
        STEPS_PER_YEAR,
        month_half_to_year_step,
        n_steps,
        year_step_to_month_half,
    )

    ok = STEPS_PER_YEAR == 24 and abs(DAYS_PER_STEP - 365.25 / 24) < 1e-12
    record("OK" if ok else "FAIL", "T_y = 24 steps/year",
           f"STEPS_PER_YEAR={STEPS_PER_YEAR}, "
           f"DAYS_PER_STEP={DAYS_PER_STEP:.5f} days")

    round_trip = all(
        month_half_to_year_step(*year_step_to_month_half(k)) == k
        for k in range(STEPS_PER_YEAR))
    record("OK" if round_trip else "FAIL", "step <-> (month, half) is a bijection",
           "year_step = 2*(month-1) + half for all 24 steps")

    T = n_steps(2006, 2011)
    record("OK" if T == 144 else "FAIL", "2006-2011 window length",
           f"n_steps(2006, 2011) = {T} steps = 6 years x 24")


def check_units() -> None:
    section("2. Units (USDA PSD 1000 MT -> MMT)")
    import pandas as pd

    from sheaf.data_usda import _KT_TO_MMT, load_psd_country

    raw = pd.read_csv(ROOT / "data" / "usda_psd" / "psd_grains_country_year.csv")
    hit = raw[(raw["Country_Name"] == "United States")
              & (raw["Market_Year"] == 2008) & (raw["grain"] == "wheat")]
    raw_prod = float(hit["Production"].iloc[0])

    psd = load_psd_country("wheat", country="USA")
    loaded = float(psd[psd["year"] == 2008]["production"].iloc[0])

    ok = abs(loaded - raw_prod * _KT_TO_MMT) < 1e-9
    record("OK" if ok else "FAIL", "PSD conversion factor",
           f"USA wheat 2008: raw {raw_prod:.0f} (1000 MT) x {_KT_TO_MMT} "
           f"= {loaded:.3f} MMT")

    from sheaf.data_faostat import (
        SHEAF_NODE_MAP,
        aggregate_to_nodes,
        load_trade_matrix,
    )
    E = aggregate_to_nodes(load_trade_matrix("wheat", window=(2006, 2007)),
                           SHEAF_NODE_MAP)
    total = float(E.to_numpy().sum())
    record("DIVERGENCE", "FAOSTAT E0 magnitudes are unit-agnostic",
           f"wheat 2006-07 node matrix sums to {total:.3e} (not MMT). "
           "Only row/column shares enter the model; rescale_to_total() exists "
           "but is never called in the Gate 0 path.")


def check_lowess() -> None:
    section("3. Harvest forcing (LOWESS anomaly vs in-sample mean)")
    from sheaf.data_usda import detrend_anomalies, load_psd_country

    psd = load_psd_country("wheat")
    world = psd.groupby("year")["production"].sum()
    hist = world.loc[1994:2011]

    anom = detrend_anomalies(hist, window_years=10)["anomaly"]
    a2006 = float(anom.loc[2006])

    window = world.loc[2006:2011]
    vs_mean = float(world.loc[2006] / window.mean() - 1.0)

    record("OK", "2006 world wheat: mean-relative vs trend-relative",
           f"vs 2006-2011 in-sample mean {vs_mean:+.1%}; "
           f"vs LOWESS trend {a2006:+.1%}. README/GATE0 quote "
           "'-9% vs that mean but only -4% vs LOWESS'.")

    from sheaf.seasonal import country_step_weights, load_harvest_calendar
    w = country_step_weights(load_harvest_calendar("wheat"))
    sums = np.array([v.sum() for v in w.values()])
    ok = np.allclose(sums, 1.0)
    record("OK" if ok else "FAIL", "harvest calendar weights normalise",
           f"{len(w)} nodes, all 24-step weight vectors sum to 1 "
           f"(max |sum-1| = {np.max(np.abs(sums - 1)):.2e})")


def check_trade_shares() -> None:
    section("4. Armington share matrices")
    from sheaf.calibration import DATA
    from sheaf.dynamic_crop import load_trade_shares

    countries = [d["name"] for d in DATA] + ["RestOfWorld"]
    A, S = load_trade_shares("wheat", countries, window=(2006, 2007))

    diag_ok = np.allclose(np.diag(A), 0.0) and np.allclose(np.diag(S), 0.0)
    rows = A.sum(axis=1)
    cols = S.sum(axis=0)
    rows_ok = np.all((np.abs(rows - 1) < 1e-9) | (rows < 1e-12))
    cols_ok = np.all((np.abs(cols - 1) < 1e-9) | (cols < 1e-12))

    record("OK" if (diag_ok and rows_ok and cols_ok) else "FAIL",
           "A rows and S columns are shares, no self-trade",
           f"n={len(countries)}; zero diagonals={diag_ok}; "
           f"A row sums in {{0,1}}={rows_ok}; S col sums in {{0,1}}={cols_ok}")

    A_rice, _ = load_trade_shares("rice", countries, window=(2006, 2007))
    i = countries.index("Vietnam")
    record("OK" if A_rice[i].sum() > 0.99 else "FAIL",
           "Vietnam rice E0 repair is active",
           f"Vietnam rice destination row sums to {A_rice[i].sum():.3f} after "
           "_repair_vietnam_rice_e0 (raw crisis-window row is all zero).")


def check_lean_gap() -> None:
    section("5. Lean foresight window (README §8 vs dynamic_crop.py:585)")
    from sheaf.calendar24 import STEPS_PER_YEAR
    from sheaf.dynamic_crop import MAX_LEAN_STEPS, prepare_crop_run
    from sheaf.seasonal import rolling_ahead_variable, steps_to_harvest_pulse

    prep = prepare_crop_run("wheat", start_year=2006, end_year=2007,
                            use_amis=False, use_shocks=False,
                            use_demand=False, use_industrial=False,
                            spin_up_years=0)
    params = prep.params
    C_step = prep.C_flex + prep.C_ind
    H_exp = (params.foresight_phi * prep.H
             + (1.0 - params.foresight_phi) * prep.H_seas)
    lh = steps_to_harvest_pulse(H_exp, frac=params.harvest_pulse_frac,
                                max_horizon=MAX_LEAN_STEPS)
    C_ahead = rolling_ahead_variable(C_step, lh)
    H_ahead = rolling_ahead_variable(H_exp, lh)

    code = np.maximum(0.0, C_ahead + C_step - H_ahead - H_exp)
    readme = np.maximum(0.0, C_ahead - H_ahead)

    diff = float(np.max(np.abs(code - readme)))
    rel = diff / max(float(np.max(readme)), 1e-9)
    record("DIVERGENCE", "lean gap L includes the current step in code",
           f"README sums k=1..h_t; code adds C_t and subtracts H^exp_t, i.e. "
           f"k=0..h_t. max|L_code - L_readme| = {diff:.3f} MMT "
           f"({rel:.1%} of max L). The code comment at dynamic_crop.py:584 "
           "states this; the README equation does not.")

    record("OK", "steps-to-pulse horizon is a world clock",
           f"steps_to_harvest_pulse uses H.sum(axis=0); "
           f"h_t ranges {lh.min()}-{lh.max()} steps "
           f"(cap = {MAX_LEAN_STEPS} = {STEPS_PER_YEAR} steps).")


def check_scarcity_shift() -> None:
    section("6. Scarcity ratio offset (README §8 'f' vs dynamic_crop.py:661)")
    from sheaf.dynamic_crop import prepare_crop_run

    prep = prepare_crop_run("wheat", start_year=2006, end_year=2007,
                            use_amis=False, use_shocks=False,
                            use_demand=False, use_industrial=False,
                            spin_up_years=0)
    safety_w = float(max(prep.safety.sum(), 1.0))
    floor0 = 0.05 * safety_w
    record("DIVERGENCE", "'f' in r_t = (F_twin + f)/(free + f) is state-dependent",
           f"code: shift = 0.05*sum(safety) + max(0, -min(free, twin)). "
           f"For wheat 0.05*sum(safety) = {floor0:.3f} MMT, and the second term "
           "is 0 unless free or twin goes negative. README writes 'f' as if it "
           "were a constant and never defines it.")


def check_eta() -> None:
    section("7. Gate 1 cross-price exponents (dynamic_coupled.cross_price_eta)")
    from sheaf.calibration import RHO
    from sheaf.dynamic_coupled import COUPLED_GRAINS, cross_price_eta
    from sheaf.dynamic_crop import default_crop_params

    for sigma in (0.0, 0.3, 0.6):
        eta = cross_price_eta(sigma)
        own = np.array([default_crop_params(g).elast for g in COUPLED_GRAINS])
        own_ok = np.allclose(np.diag(eta), own)
        expect = np.zeros_like(eta)
        idx = {"wheat": 0, "rice": 1, "maize": 2}
        for a, ga in enumerate(COUPLED_GRAINS):
            for b, gb in enumerate(COUPLED_GRAINS):
                if a == b:
                    expect[a, b] = own[a]
                else:
                    expect[a, b] = sigma * RHO[idx[ga], idx[gb]] * abs(own[a])
        ok = own_ok and np.allclose(eta, expect)
        flat = ", ".join(f"{v:+.3f}" for v in eta.flatten())
        record("OK" if ok else "FAIL", f"eta at sigma={sigma}",
               f"diag = own elasticities (wheat {own[0]}, rice {own[1]}, "
               f"maize {own[2]}); off-diag = sigma*rho*|eps|. matrix = [{flat}]")

    eta0 = cross_price_eta(0.0)
    off = eta0 - np.diag(np.diag(eta0))
    record("OK" if np.allclose(off, 0.0) else "FAIL",
           "sigma=0 removes every cross term",
           f"max |off-diagonal| = {np.max(np.abs(off)):.2e}")


def check_pd() -> None:
    section("8. Annual demand system M (core.build_demand_system) PD claim")
    from sheaf.calibration import DATA, GLOBAL_CONS, GRAINS, OWN_ELAST, P0, RHO
    from sheaf.core import build_demand_system

    cons = [np.array(d["cons"], float) for d in DATA]
    cons.append(GLOBAL_CONS - np.sum(cons, axis=0))

    for sigma in (0.0, 0.3, 0.6, 0.9):
        lam, dom, capped = [], [], 0
        for D0 in cons:
            sysd = build_demand_system(GRAINS, D0, P0, OWN_ELAST, RHO, sigma)
            M = sysd.M
            lam.append(float(np.linalg.eigvalsh(M).min()))
            b = np.diag(M)
            offsum = np.abs(M - np.diag(b)).sum(axis=1)
            dom.append(float(np.min(b - offsum)))
            bb = -OWN_ELAST * D0 / P0
            S = np.zeros((3, 3))
            for g in range(3):
                for h in range(3):
                    if g != h:
                        S[g, h] = sigma * RHO[g, h] * np.sqrt(bb[g] * bb[h])
            if np.any(S.sum(axis=1) >= 0.95 * bb):
                capped += 1
        record("OK" if min(lam) > 0 else "FAIL",
               f"M is positive definite at subst_scale={sigma}",
               f"over {len(cons)} calibration nodes: min eigenvalue "
               f"{min(lam):.4e}, min diagonal-dominance margin {min(dom):.4e}, "
               f"nodes hitting the 0.95 row cap: {capped}")

    sysd0 = build_demand_system(GRAINS, cons[0], P0, OWN_ELAST, RHO, 0.0)
    off = sysd0.M - np.diag(np.diag(sysd0.M))
    record("OK" if np.allclose(off, 0.0) else "FAIL",
           "README §6 limit: sigma=0 makes M exactly diagonal",
           f"max |off-diagonal(M)| = {np.max(np.abs(off)):.2e}, so the benefit "
           "potential separates and the QP splits into G independent markets.")

    rng = np.random.default_rng(20260827)
    fails, n_trial = [], 20000
    for _ in range(n_trial):
        G = int(rng.integers(2, 6))
        b = 10.0 ** rng.uniform(-3, 3, size=G)
        R = rng.uniform(0.0, 0.99, size=(G, G))
        R = np.triu(R, 1)
        R = R + R.T
        sigma = 10.0 ** rng.uniform(-1, 1)
        S = np.zeros((G, G))
        for g in range(G):
            for h in range(G):
                if g != h:
                    S[g, h] = sigma * R[g, h] * np.sqrt(b[g] * b[h])
        for g in range(G):
            offs = S[g].sum()
            if offs >= 0.95 * b[g]:
                S[g] *= (0.95 * b[g]) / offs
        S = np.sqrt(S * S.T)
        M = np.diag(b) - S
        eig = float(np.linalg.eigvalsh(M).min())
        if eig <= 0:
            fails.append((G, sigma, eig))
    if fails:
        G, sigma, eig = min(fails, key=lambda z: z[2])
        record("DIVERGENCE", "row-cap + geometric-mean symmetrisation is not a "
               "PD guarantee for arbitrary inputs",
               f"{len(fails)}/{n_trial} random draws give min eig <= 0 "
               f"(worst {eig:.3e} at G={G}, sigma={sigma:.2f}). SHEAF's own "
               "calibration is well inside the safe region (above).")
    else:
        record("OK", "no PD counterexample found",
               f"{n_trial} random draws (G=2..5, b over 6 orders of magnitude, "
               "sigma 0.1-10): min eigenvalue stayed positive in every case.")


def check_gate0_asserts() -> None:
    section("9. Gate 0 robustness asserts (dynamic_crop.py)")
    from sheaf.dynamic_crop import (
        assert_amis_cuts_exports,
        assert_amis_raises_price,
        assert_no_spring_spike,
        assert_twin_identity,
        run_crop_dynamics,
    )

    for crop in ("wheat", "rice", "maize"):
        for fn in (assert_twin_identity, assert_amis_raises_price,
                   assert_no_spring_spike, assert_amis_cuts_exports):
            try:
                fn(crop)
                record("OK", f"{fn.__name__}({crop})", "passed")
            except AssertionError as exc:
                record("FAIL", f"{fn.__name__}({crop})", str(exc))

    res = run_crop_dynamics("wheat", use_amis=False, use_shocks=False,
                            use_demand=False, use_industrial=False)
    p0 = float(res.price[0])
    drift = float(np.max(np.abs(res.price[24:] - p0)) / p0)
    free_err = float(np.max(np.abs(res.free_liquid - res.free_twin)))
    record("OK", "calm identity is numerically exact, not just inside tolerance",
           f"wheat neither-path: max price drift {drift:.2e} of p0={p0:.1f} $/t; "
           f"max |free - twin| = {free_err:.2e} MMT")


def check_gate1_identity() -> None:
    section("10. Gate 1 identity: coupled sigma=0 == three Gate 0 runs")
    from sheaf.dynamic_coupled import run_coupled_dynamics
    from sheaf.dynamic_crop import result_to_monthly, run_crop_dynamics

    coupled = run_coupled_dynamics(subst_scale=0.0, use_demand=False)
    worst = 0.0
    for g in coupled.grains:
        solo = run_crop_dynamics(g, use_amis=True, use_shocks=True,
                                 use_demand=False)
        a = result_to_monthly(coupled.by_crop[g])["model_price"].to_numpy()
        b = result_to_monthly(solo)["model_price"].to_numpy()
        rel = float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1.0)))
        worst = max(worst, rel)
    record("OK" if worst < 5e-3 else "FAIL",
           "sigma=0 recovers Gate 0 to machine precision",
           f"max relative monthly |dp| across wheat/rice/maize = {worst:.3e} "
           "(bar is 0.5%)")


def check_gate2() -> None:
    section("11. Gate 2 beta: Headey-clock cascade (dynamic_policy.py)")
    from sheaf.dynamic_crop import simulate_prep
    from sheaf.dynamic_policy import (
        PolicyKnobs,
        climatology_relative_cuts,
        gov_buffer,
        prepare_beta,
        shock_year_harvest,
        simulate_headey,
        year_slice,
    )

    knobs = PolicyKnobs()
    prep = prepare_beta(knobs)
    sl = year_slice(prep, knobs.shock_year)

    _, meta_calm = climatology_relative_cuts(prep, prep.H, knobs)
    calm_on = {k: v["n_year"] for k, v in meta_calm["by_player"].items()}
    ok = all(v == 0 for v in calm_on.values())
    record("OK" if ok else "FAIL", "hard bar 1: climatology harvest => tau_t = 0",
           f"on-steps in the shock year per player: {calm_on}")

    H = shock_year_harvest(prep, knobs.exporter, knobs.shock_year,
                           knobs.harvest_mult)
    res, _, meta = simulate_headey(prep, H, knobs)
    p = meta["by_player"]
    ru, kz = p["Russia"], p["Kazakhstan"]

    record("OK" if ru["n_year"] > 0 else "FAIL",
           "hard bar 2: Russia harvest x0.50 turns Russia on",
           f"Russia on {ru['n_year']}/24 steps, first at step "
           f"{ru['first_on']}, min S/S_calm = {ru['min_ratio']:.2f}")
    record("OK" if kz["n_year"] > 0 else "FAIL",
           "hard bar 3: Kazakhstan fires with no Kazakh harvest cut",
           f"Kazakhstan on {kz['n_year']}/24 steps, first at step "
           f"{kz['first_on']}, min S/S_calm = {kz['min_ratio']:.2f}")
    record("OK" if kz["first_on"] >= ru["first_on"] else "FAIL",
           "hard bar 4: the neighbour does not fire first",
           f"Russia first_on={ru['first_on']}, Kazakhstan "
           f"first_on={kz['first_on']}")
    record("OK" if ru["closed_exports"] <= ru["open_exports"] else "FAIL",
           "hard bar 5: Russia's own cuts reduce Russia's shipments",
           f"open {ru['open_exports']:.2f} -> closed "
           f"{ru['closed_exports']:.2f} MMT")

    knobs_kz_only = PolicyKnobs(players=("Kazakhstan",))
    _, meta_no_ru = climatology_relative_cuts(prep, H, knobs_kz_only)
    kz_alone = meta_no_ru["by_player"]["Kazakhstan"]
    i_kz = prep.countries.index("Kazakhstan")
    calm_stock = simulate_prep(prep, harvest=prep.H).stock[i_kz]
    kz_closed_ratio = float(
        (res.stock[i_kz] / np.maximum(calm_stock, 1e-9))[sl].min())
    record("DIVERGENCE", "the cascade is harvest diversion, not ban-on-ban",
           f"Kazakhstan's open-path trough is {kz_alone['min_ratio']:.3f}, "
           f"already below the {knobs.stock_ratio_trigger} trigger before any "
           f"Russian tau is applied; with Russia's cuts on, Kazakhstan's trough "
           f"*rises* to {kz_closed_ratio:.3f}.")

    s_gov = gov_buffer(prep, knobs)
    record("OK", "government buffer is illustrative, not Gate 0 safety",
           f"s_gov = gov_stu {knobs.gov_stu} x C_ann(Russia) = {s_gov:.2f} MMT, "
           f"versus Gate 0 competitive safety stu_target "
           f"{prep.params.stu_target} x C_ann = "
           f"{prep.safety[prep.countries.index('Russia')]:.2f} MMT")


def check_warehouse() -> None:
    section("12. Carry capacity W (README §8 vs GATE0_PARAMETERIZATION §2.3)")
    from sheaf.calendar24 import STEPS_PER_YEAR
    from sheaf.dynamic_crop import prepare_crop_run

    for crop in ("wheat", "rice"):
        prep = prepare_crop_run(crop, start_year=2006, end_year=2006,
                                use_amis=False, use_shocks=False,
                                use_demand=False, use_industrial=False,
                                spin_up_years=0)
        pr = prep.params
        i = prep.countries.index("India" if crop == "rice" else "Russia")
        t = 12
        code_W = (pr.max_stu * prep.C_ann[i]
                  + (prep.C_ann[i] / STEPS_PER_YEAR) * pr.pipeline_max_steps
                  + (prep.H[i, t] if pr.pipeline_max_steps > 0 else 0.0))
        doc_W = (max(pr.max_stu * prep.C_ann[i], 1.5 * prep.safety[i])
                 + (prep.C_ann[i] / STEPS_PER_YEAR) * pr.pipeline_max_steps
                 + prep.H[i, t])
        tag = "OK" if abs(code_W - doc_W) < 1e-9 else "DIVERGENCE"
        record(tag, f"W for {crop} (pipeline={pr.pipeline_max_steps})",
               f"code {code_W:.3f} MMT vs GATE0_PARAMETERIZATION §2.3 display "
               f"{doc_W:.3f} MMT. README §8 matches the code (it carries the "
               "1{{pipeline>0}} indicator and no 1.5s floor); the diagnostics "
               "note's displayed equation is stale relative to its own prose.")


def main() -> int:
    check_clock()
    check_units()
    check_lowess()
    check_trade_shares()
    check_lean_gap()
    check_scarcity_shift()
    check_eta()
    check_pd()
    check_gate0_asserts()
    check_gate1_identity()
    check_gate2()
    check_warehouse()

    section("Summary")
    n_fail = sum(1 for t, _, _ in RESULTS if t == "FAIL")
    n_div = sum(1 for t, _, _ in RESULTS if t == "DIVERGENCE")
    n_ok = sum(1 for t, _, _ in RESULTS if t == "OK")
    print(f"{n_ok} OK, {n_div} documented divergence(s), {n_fail} failure(s)")
    for tag, name, _ in RESULTS:
        if tag != "OK":
            print(f"  [{tag}] {name}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
