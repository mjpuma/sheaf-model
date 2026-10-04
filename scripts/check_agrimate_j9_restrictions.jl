# Gate 0 J9 check: did the author's export-restriction series survive the
# input rebuild and the simulation? Compares the `export restriction`
# variable written by the J9 run with the same variable in the author
# NetCDF, per region and overall.
#
# Run read-only from the paper project (uses its NCDatasets):
#   cd /Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty
#   arch -x86_64 /Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia \
#       --project=. /Users/mjp38/GitHub/sheaf-model/scripts/check_agrimate_j9_restrictions.jl
#
# Both files store the aggregated input value per (step, region), rounded to
# 4 digits (src/simulation.jl line 296), so an exact copy should give 0.

using NCDatasets, Dates, Printf

const FILE = "agrimate_baseline=2007-2009_export_restrictions=2007-2011_" *
             "extra_regions=(Egypt=EGY)_production_anomalies=FAOsince-2005_" *
             "regions=AgrimateEU28_start=2000-01-01.nc"
const LOCAL = get(ENV, "J9_LOCAL",
    "/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/data_authorrestr/netcdf/" * FILE)
const AUTHOR = get(ENV, "J9_AUTHOR",
    "/Users/mjp38/GitHub/agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/" * FILE)

nz(x) = isnan(x) ? 0.0 : x

function restrictions(path)
    ds = NCDataset(path)
    x = Array(ds["export restriction"])
    x = eltype(x) >: Missing ? Float64.(coalesce.(x, NaN)) : Float64.(x)
    regions = String.(Array(ds["region"]))
    times = Array(ds["time"])
    close(ds)
    nz.(x), regions, times
end

L, RL, TL = restrictions(LOCAL)
A, RA, TA = restrictions(AUTHOR)

println("local:  ", LOCAL)
println("author: ", AUTHOR)
println("same region order: ", RL == RA, "; same time axis: ", TL == TA,
        "; shape local ", size(L), " author ", size(A))
@assert RL == RA && TL == TA && size(L) == size(A)

d = abs.(L .- A)
println("\n## Realized export restriction, J9 local vs author\n")
println("| region | steps>0 L | steps>0 A | max L | max A | max abs diff | steps differing |")
println("|---|---|---|---|---|---|---|")
for i in eachindex(RL)
    el = L[:, i]; ea = A[:, i]
    (any(el .> 0) || any(ea .> 0)) || continue
    @printf("| %s | %d | %d | %.4f | %.4f | %.4f | %d |\n", RL[i], count(>(0), el),
            count(>(0), ea), maximum(el), maximum(ea), maximum(d[:, i]), count(>(0), d[:, i]))
end

k = argmax(d)
@printf("\noverall max abs diff = %.4f (region %s, step %d, %s): local %.4f, author %.4f\n",
        d[k], RL[k[2]], k[1], Dates.format(TL[k[1]], "yyyy-mm-dd"), L[k], A[k])
@printf("total differing (step, region) cells = %d of %d\n", count(>(0), d), length(d))
others = [i for i in eachindex(RL) if i != k[2]]
@printf("max abs diff excluding %s = %.4g\n", RL[k[2]], maximum(d[:, others]))
