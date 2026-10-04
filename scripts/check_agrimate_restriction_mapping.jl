"""
Gate 0 J9: run the paper code's own export-restriction preprocessing on an
input directory and compare the per-region per-step result with the
`export restriction` variable of a NetCDF output. Read-only.

    cd /Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty
    arch -x86_64 /Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia \\
        --project=. /Users/mjp38/GitHub/sheaf-model/scripts/check_agrimate_restriction_mapping.jl \\
        <inputdir> <netcdf file>

The steps copy `simulate()` (src/simulation.jl lines 60-84 and 252-274):
region map, aggregated + inferred trade flows, `aggregate_export_restrictions`,
`generate_export_restriction_intervals`, `generate_export_restriction_dict`.
With `two_markets = true` the producer's `export_restriction` at step t is
`get(dict, (t, region), 0)` (agents/producer.jl lines 22-49, 277), and the
output rounds every value to 4 digits (simulation.jl line 296).
"""

using DrWatson
@quickactivate "Agrimate"
include(srcdir("simulation.jl"))

function restriction_matrix(inputroot, regions; T)
    params = Params(
        crops = "wheat", baseline = "2007-2009", regions = "AgrimateEU28",
        extra_regions = Dict{String,Any}("Egypt" => "EGY"),
        start = Date(2000, 1, 1), production_anomalies = "FAOsince-2005",
        export_restrictions = "2007-2011",
    )
    @unpack start, N_year, baseline, export_restrictions = params
    crop = "wheat"
    inputdir(path...) = joinpath(inputroot, path...)
    df_region = make_regions_dataframe(get_regions(params.regions), params.extra_regions)
    fb_non_agg = wload(inputdir(savename("food-balance", (;baseline, crop), "csv"; savename_kwargs...)))
    tf_non_agg = wload(inputdir(savename("trade-flows", (;baseline, crop), "csv"; savename_kwargs...)))
    fb = aggregate_areas(fb_non_agg, df_region)
    tf = infer_trade_flows(aggregate_areas(tf_non_agg, df_region), fb)
    df_er = wload(inputdir(savename("export-restrictions", (;source=export_restrictions, crop), "csv"; savename_kwargs...)))
    df_er = aggregate_export_restrictions(df_er, df_region, tf_non_agg, tf)
    println("aggregated intervals:")
    show(stdout, df_er; allrows = true); println()
    ers = [String(r[:Exporter]) => Dict(:from => r[:From], :to => r[:To], :value => r[:Value]) for r in eachrow(df_er)]
    dict = generate_export_restriction_dict(generate_export_restriction_intervals(ers; start, N_year))
    R = zeros(T, length(regions))
    for (j, reg) in enumerate(regions), t in 1:T
        R[t, j] = get(dict, (t, reg), 0.0)
    end
    return R
end

if abspath(PROGRAM_FILE) == @__FILE__
    inputroot, ncfile = ARGS[1], ARGS[2]
    ds = NCDataset(ncfile)
    regions = String.(Array(ds["region"]))
    tsteps = Array(ds["timestep"])
    var = ds["export restriction"]
    dims = dimnames(var)
    println("nc var dims = ", dims, "; timestep = ", first(tsteps), "..", last(tsteps))
    A = coalesce.(Array(var), 0.0)
    close(ds)
    A = dims[1] == "time" ? A : permutedims(A)
    T = length(tsteps)
    @assert tsteps == 1:T
    R = restriction_matrix(inputroot, regions; T)
    Rr = round.(R; digits = 4)
    println("max |raw - nc| = ", maximum(abs.(R .- A)))
    println("max |round4 - nc| = ", maximum(abs.(Rr .- A)))
    for (j, reg) in enumerate(regions)
        bad = findall(t -> Rr[t, j] != A[t, j], 1:T)
        on = count(>(0), A[:, j]); onr = count(>(0), Rr[:, j])
        (on == 0 && onr == 0) && continue
        println(rpad(reg, 26), " steps>0 nc/pre = ", on, "/", onr,
                "  max nc/pre = ", maximum(A[:, j]), "/", maximum(Rr[:, j]),
                "  max |raw - nc| = ", maximum(abs.(R[:, j] .- A[:, j])),
                "  mismatched steps = ", isempty(bad) ? "none" : string(bad))
    end
end
