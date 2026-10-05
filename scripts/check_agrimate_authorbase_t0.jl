# Gate 0 J10 verification, without the 312-step run.
#
#   cd /Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty
#   arch -x86_64 /Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia \
#       --project=. /Users/mjp38/GitHub/sheaf-model/scripts/check_agrimate_authorbase_t0.jl
#
# Three parts, all read-only on every input and output directory:
#
#  A. Input-derived quantities. Re-runs simulate()'s own input pipeline
#     (src/simulation.jl 59-124 and 189-274) on `data/agrimate_input_authorbase/`
#     with the paper's own functions and compares what it derives -- the annual
#     bilateral flow matrix and its marginals, the baseline harvests, the
#     realized 312-step harvest series, the aggregated export restrictions, and
#     the empirical parameters -- against the author's published arrays. This
#     covers `baseline harvest`, `harvest`, `baseline share foreign sales`,
#     `α domestic`, `ψ`, `A_d_star` and `A_c_star` without running the model.
#
#  B. Solver outputs. Compares the NetCDF written by a `t_max = 0` run (see
#     agrimate-2025/run_j10_authorbase_tmax0.jl) against the author's
#     `baseline price`, `baseline sales`, `baseline producer storage`,
#     `baseline demand`, `baseline consumer storage`, `baseline consumption`,
#     `baseline consumer price` and `baseline transaction quantity`. These are
#     the producer Nash equilibrium, the consumer baseline fixed point and the
#     baseline trade QP; they are not settable from the CSVs.
#
#  C. The same comparison for the J9 input set, as the before/after control.
#
# Set J10_T0 to the t_max = 0 NetCDF to run part B; it is skipped if absent.

using DrWatson
@quickactivate "Agrimate"
include(srcdir("simulation.jl"))
using NCDatasets, Printf, Statistics

const AUTHOR_NC = "/Users/mjp38/GitHub/agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/" *
    "agrimate_baseline=2007-2009_export_restrictions=2007-2011_extra_regions=(Egypt=EGY)_" *
    "production_anomalies=FAOsince-2005_regions=AgrimateEU28_start=2000-01-01.nc"
const T0_NC = get(ENV, "J10_T0",
    "/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/data_authorbase_t0/netcdf/" *
    "agrimate_baseline=2007-2009_extra_regions=(Egypt=EGY)_regions=AgrimateEU28_start=2000-01-01.nc")
const J9_T0 = get(ENV, "J10_J9_T0", "/Users/mjp38/GitHub/agrimate-2025/j8_author_params/tmax0_baseline.nc")

const T_MAX = 312

params = Params(
    crops = "wheat",
    baseline = "2007-2009",
    regions = "AgrimateEU28",
    extra_regions = Dict{String,Any}("Egypt" => "EGY"),
    start = Date(2000, 1, 1),
    production_anomalies = "FAOsince-2005",
    export_restrictions = "2007-2011",
)

# --------------------------------------------------------------------------
# author arrays
# --------------------------------------------------------------------------
ds = NCDataset(AUTHOR_NC)
AREG = String.(Array(ds["region"]))
getarr(name) = (x = Array(ds[name]); Float64.(coalesce.(x, NaN)))
A = Dict(v => getarr(v) for v in [
    "baseline harvest", "baseline sales", "baseline producer storage",
    "baseline demand", "baseline consumer storage", "baseline consumption",
    "baseline consumer price", "baseline price", "baseline transaction quantity",
    "harvest", "export restriction", "baseline share foreign sales",
    "α domestic", "ψ", "A_d_star", "A_c_star",
])
close(ds)
ridx = Dict(r => i for (i, r) in enumerate(AREG))

nz(x) = isnan(x) ? 0.0 : x
function report(label, loc, aut; skipnan = true)
    @assert size(loc) == size(aut) "$label: size $(size(loc)) vs $(size(aut))"
    mask = skipnan ? .!isnan.(aut) : trues(size(aut))
    l = loc[mask]; a = aut[mask]
    bad = isnan.(l)
    if any(bad)
        @printf("| %-34s | %7d NaN where author is finite | | |\n", label, count(bad))
        l = l[.!bad]; a = a[.!bad]
    end
    isempty(a) && return (label, NaN, NaN)
    d = abs.(l .- a)
    scale = max(maximum(abs.(a)), eps())
    rel = maximum(d) / scale
    @printf("| %-34s | %6d | %12.3e | %11.3e |\n", label, length(a), maximum(d), rel)
    return (label, maximum(d), rel)
end

summary = Tuple{String,Float64,Float64}[]

# --------------------------------------------------------------------------
# PART A: everything simulate() derives from the CSVs
# --------------------------------------------------------------------------
function derive(inputroot)
    inputdir(p...) = joinpath(inputroot, p...)
    @unpack start, N_year, crops, baseline = params
    @unpack regions, extra_regions, flow_cutoff, production_cutoff = params
    crop = split(crops, ",")[1] |> string

    df_region = make_regions_dataframe(get_regions(regions), extra_regions)
    fb_non_agg = wload(inputdir(savename("food-balance", (; baseline, crop), "csv"; savename_kwargs...)))
    tf_non_agg = wload(inputdir(savename("trade-flows", (; baseline, crop), "csv"; savename_kwargs...)))
    df_hd = wload(inputdir(savename("harvest-distributions", (; crop), "csv"; savename_kwargs...)))
    df_hd = aggregate_harvest_distributions(df_hd, df_region;
        df_baseline_production = fb_non_agg[:, [:Area, :Production]])
    harvest_distributions = Dict(
        String(row[:Area]) => [isnan(val) ? 0.0 : val for val in row[Between("1", "365")]]
        for row in eachrow(df_hd))
    fb = aggregate_areas(fb_non_agg, df_region)
    tf = infer_trade_flows(aggregate_areas(tf_non_agg, df_region), fb)
    btf = Dict((String(row[:Origin]), String(row[:Destination])) => row["Trade Flow"] / N_year
               for row in eachrow(tf))
    bt = apply_cutoffs_to_trade_network(btf; flow_cutoff, production_cutoff)
    (bp, bc) = get_baseline_production_and_consumption(bt)
    bh = generate_baseline_harvests(bp, harvest_distributions; N_year)
    (bt, bp) = apply_filter_if_producer_not_exist(bt, bp, bh)

    # empirical parameters
    df_ep = wload(inputdir(savename("parameters", (; baseline, crop, source = "empirical"), "csv";
                                    savename_kwargs...)))
    ep = generate_empirical_params(params, df_ep, fb_non_agg[!, [:Area, :Consumption]], df_region)

    # realized harvest (simulate() 189-250), with N_hor from the model defaults
    N_hor = AgrimateParams().N_hor
    df_an = aggregate_areas(wload(inputdir(savename("harvest-anomalies",
        (; source = params.production_anomalies, crop), "csv"; savename_kwargs...))), df_region)
    df_tr = aggregate_areas(wload(inputdir(savename("harvest-trends",
        (; source = params.production_anomalies, crop), "csv"; savename_kwargs...))), df_region)
    date_start = timestep_to_datetime(0.5; start, N_year) |> Date
    date_end = timestep_to_datetime(T_MAX + N_hor + 0.5; start, N_year) |> Date
    (ys, ds_) = calculate_year_and_n(date_start; N_year = 365)
    (ye, de_) = calculate_year_and_n(date_end; N_year = 365)
    @assert "$ys-$ds_" in names(df_tr)
    if "$ye-$de_" in names(df_tr)
        columns = Between("$ys-$ds_", "$ye-$de_"); missing_days = 0
    else
        (ly, ld) = parse.(Int, split(names(df_tr)[end], "-"))
        columns = Between("$ys-$ds_", "$ly-$ld")
        missing_days = 365 * (ye - ly) + (de_ - ld)
    end
    an = Dict(String(row[:Area]) => [val for val in row[columns]] for row in eachrow(df_an))
    tr = Dict(String(row[:Area]) => [val for val in row[columns]] for row in eachrow(df_tr))
    forcings = Dict(area => vcat(
        replace(1 .+ an[area] ./ tr[area], NaN => 1., Inf => 1., -Inf => 1.),
        ones(missing_days)) for area in keys(tr))
    y_ts = date_to_fractional_year(date_start):(1/365):date_to_fractional_year(date_end) |> collect
    harvests = generate_harvests(params.production_anomalies, bp, bh, harvest_distributions,
        forcings, y_ts; start, t_max = T_MAX, N_year, N_hor)

    # aggregated export restrictions as the model sees them
    df_er = aggregate_export_restrictions(
        wload(inputdir(savename("export-restrictions",
            (; source = params.export_restrictions, crop), "csv"; savename_kwargs...))),
        df_region, tf_non_agg, tf)
    er = [String(row[:Exporter]) => Dict(:from => row[:From], :to => row[:To],
                                         :value => row[:Value]) for row in eachrow(df_er)]
    erdict = generate_export_restriction_dict(generate_export_restriction_intervals(er; start, N_year))

    return (; bt, bp, bc, bh, ep, harvests, erdict, missing_days)
end

println("## A. Input-derived quantities, data/agrimate_input_authorbase\n")
D = derive(datadir("agrimate_input_authorbase"))
println("producers: ", length(D.bp), "  consumers: ", length(D.bc),
        "  pairs: ", length(D.bt), "  padded forcing days: ", D.missing_days)
missing_prod = [r for r in AREG if !haskey(D.bp, r)]
println("regions without a producer: ", missing_prod,
        " (author: ", [r for r in AREG if all(isnan, A["baseline harvest"][:, ridx[r]])], ")")

println("\n| quantity | cells | max abs diff | max rel diff |")
println("|---|---|---|---|")

# baseline harvest (24 x 28)
let loc = fill(NaN, 24, length(AREG))
    for (r, v) in D.bh
        loc[:, ridx[r]] = v
    end
    push!(summary, report("baseline harvest (24x28)", loc, A["baseline harvest"]))
end

# annual production / consumption marginals
let lp = fill(NaN, length(AREG)), lc = fill(NaN, length(AREG))
    for (r, v) in D.bp; lp[ridx[r]] = v * 24; end
    for (r, v) in D.bc; lc[ridx[r]] = v * 24; end
    ap = [sum(A["baseline harvest"][:, i]) for i in eachindex(AREG)]
    bd = [sum(A["baseline demand"][:, i]) for i in eachindex(AREG)]
    ac = bd .* (sum(filter(!isnan, ap)) / sum(filter(!isnan, bd)))
    push!(summary, report("annual production (28)", lp, ap))
    push!(summary, report("annual consumption (28)", lc, ac))
end

# share of foreign sales and α domestic, exactly as initialize_agents! forms them
let sf = fill(NaN, length(AREG)), ad = fill(NaN, length(AREG))
    tot = Dict(r => 0.0 for r in keys(D.bp))
    dom = Dict(r => 0.0 for r in keys(D.bp))
    frn = Dict(r => 0.0 for r in keys(D.bp))
    imp = Dict(r => 0.0 for r in keys(D.bp))
    for ((p, c), x) in D.bt
        tot[p] += x
        p == c ? (dom[p] += x) : (frn[p] += x)
        haskey(imp, c) && (imp[c] += x)
    end
    only_foreign = sum(values(frn))
    for r in keys(D.bp)
        sf[ridx[r]] = frn[r] / tot[r] > 0. ? frn[r] / tot[r] : 0.
        a = (dom[r] > 0 && frn[r] > 0) ?
            3.2 * imp[r] * frn[r] / (only_foreign * dom[r]) : 1.0
        ad[ridx[r]] = min(a, 1.0)
    end
    push!(summary, report("baseline share foreign sales (28)", sf, A["baseline share foreign sales"]))
    push!(summary, report("α domestic (28)", round.(ad; digits = 4), A["α domestic"]))
    @printf("world international trade: local %.4f kt, author off-diagonal output sum %.4f kt\n",
            only_foreign * 24, sum(filter(!isnan, A["baseline transaction quantity"])) -
            sum(filter(!isnan, [A["baseline transaction quantity"][n, i, i] for n in 1:24, i in eachindex(AREG)])))
end

# empirical parameters
for (sym, name) in [(:ψ, "ψ"), (:A_d_star, "A_d_star"), (:A_c_star, "A_c_star")]
    loc = fill(NaN, length(AREG))
    for (r, v) in D.ep[sym]; loc[ridx[r]] = v; end
    push!(summary, report("$name (28)", loc, A[name]))
end

# realized harvest (312 x 28)
let loc = fill(NaN, T_MAX, length(AREG))
    for (r, v) in D.harvests
        loc[:, ridx[r]] = v[1:T_MAX]
    end
    push!(summary, report("harvest (312x28)", round.(loc; digits = 4), A["harvest"]))
end

# export restrictions (312 x 28), as export_restriction_step! would read them
let loc = zeros(T_MAX, length(AREG))
    for t in 1:T_MAX, r in AREG
        loc[t, ridx[r]] = round(get(D.erdict, (t, r), 0.0); digits = 4)
    end
    aut = nz.(A["export restriction"])
    push!(summary, report("export restriction (312x28)", loc, aut; skipnan = false))
    d = abs.(loc .- aut)
    println()
    println("| region | steps>0 L | steps>0 A | max L | max A | max abs diff | differing steps |")
    println("|---|---|---|---|---|---|---|")
    for i in eachindex(AREG)
        (any(loc[:, i] .> 0) || any(aut[:, i] .> 0)) || continue
        @printf("| %s | %d | %d | %.4f | %.4f | %.4f | %d |\n", AREG[i],
                count(>(0), loc[:, i]), count(>(0), aut[:, i]),
                maximum(loc[:, i]), maximum(aut[:, i]), maximum(d[:, i]), count(>(0), d[:, i]))
    end
end

# --------------------------------------------------------------------------
# PART B / C: solver outputs from a t_max = 0 run
# --------------------------------------------------------------------------
const SOLVER_VARS = ["baseline price", "baseline sales", "baseline producer storage",
    "baseline demand", "baseline consumer storage", "baseline consumption",
    "baseline consumer price", "baseline transaction quantity"]

function compare_t0(path, title)
    if !isfile(path)
        println("\n## $title: $path not found, skipped\n")
        return Tuple{String,Float64,Float64}[]
    end
    d = NCDataset(path)
    reg = String.(Array(d["region"]))
    out = Tuple{String,Float64,Float64}[]
    println("\n## $title\n")
    println("file: ", path)
    println("same region order as author: ", reg == AREG)
    println("\n| quantity | cells | max abs diff | max rel diff |")
    println("|---|---|---|---|")
    perm = [findfirst(==(r), reg) for r in AREG]
    for v in SOLVER_VARS
        haskey(d, v) || continue
        x = Float64.(coalesce.(Array(d[v]), NaN))
        y = A[v]
        if ndims(x) == 1 && length(x) == length(reg)
            x = x[perm]
        elseif ndims(x) == 2 && size(x, 2) == length(reg)
            x = x[:, perm]
        elseif ndims(x) == 3
            x = x[:, perm, perm]
        end
        push!(out, report(v, x, y))
    end
    close(d)
    return out
end

append!(summary, compare_t0(T0_NC, "B. Solver outputs, J10 author-baseline inputs (t_max = 0)"))
append!(summary, compare_t0(J9_T0, "C. Solver outputs, J8/J9 inputs (t_max = 0 control)"))

println("\n## Worst differences, part A\n")
for (lab, ab, rl) in summary
    @printf("%-36s abs %-12.3e rel %-12.3e\n", lab, ab, rl)
end
