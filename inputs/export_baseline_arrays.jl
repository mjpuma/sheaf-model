# Gate 0 J10: dump the calibrated baseline state, the realized harvest and the
# export-restriction series out of an Agrimate output NetCDF into plain CSVs.
# Read-only on the NetCDF. Used for the author's published wheat file and, as a
# control, for our own local runs.
#
#   cd /Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty
#   arch -x86_64 /Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia \
#       --project=. /Users/mjp38/GitHub/sheaf-model/inputs/export_baseline_arrays.jl \
#       [<netcdf path> <output dir>]
#
# Defaults to the author's wheat harvest+restrictions file and
# /Users/mjp38/GitHub/agrimate-2025/j10_author_base/ (outside both repos, not
# committed).
#
# Output files:
#   baseline_region.csv        Region,psi,A_d_star,A_c_star,share_foreign_sales,alpha_domestic
#   baseline_step.csv          Region,variable,n,value   (the seven 24-step baseline arrays)
#   baseline_price.csv         n,value
#   baseline_transactions.csv  Consumer,Producer,n,value  (see the dim note below)
#   baseline_trade_annual.csv  Consumer,Producer,annual
#   harvest.csv                Region,t,value            (312x28 realized harvest)
#   export_restriction.csv     Region,t,value            (312x28, absent in baseline runs)
#   dims.txt                   variable dimension + global attribute report
#
# DIM NOTE. src/io.jl declares "baseline transaction quantity" as
# (inner_annual_timestep, region, region) and fills it by sorting the long
# frame on [:n, :producer, :consumer] and then
# `reshape(values, N, N, 24)` -> `permutedims(_, [3,1,2])`. Julia's reshape is
# column-major, so the fastest-varying sort key (consumer) lands on the first
# reshaped axis. The stored layout is therefore (n, consumer, producer), not
# (n, producer, consumer). This script writes the axes out under their true
# meaning and asserts the identity that pins it down (row sums match baseline
# demand, column sums match baseline sales).

using DrWatson
@quickactivate "Agrimate"
using NCDatasets, Printf

const DEFAULT_NC = "/Users/mjp38/GitHub/agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/" *
    "agrimate_baseline=2007-2009_export_restrictions=2007-2011_extra_regions=(Egypt=EGY)_" *
    "production_anomalies=FAOsince-2005_regions=AgrimateEU28_start=2000-01-01.nc"
const DEFAULT_OUT = "/Users/mjp38/GitHub/agrimate-2025/j10_author_base/"

ncpath = length(ARGS) >= 1 ? ARGS[1] : DEFAULT_NC
outdir = length(ARGS) >= 2 ? ARGS[2] : DEFAULT_OUT

mkpath(outdir)
ds = NCDataset(ncpath)
regions = String.(Array(ds["region"]))
println("file    : ", ncpath)
println("regions : ", length(regions))

open(joinpath(outdir, "dims.txt"), "w") do io
    println(io, "source: ", ncpath)
    for (name, var) in ds
        println(io, name, "  dims=", dimnames(var), "  size=", size(var))
    end
    println(io, "\nglobal attributes:")
    for (k, v) in ds.attrib
        println(io, "  ", k, " = ", v)
    end
end

mis(x) = ismissing(x) || (x isa AbstractFloat && isnan(x)) ? "" : @sprintf("%.12g", Float64(x))

const SCALARS = ["ψ", "A_d_star", "A_c_star", "baseline share foreign sales", "α domestic"]
open(joinpath(outdir, "baseline_region.csv"), "w") do io
    println(io, "Region,psi,A_d_star,A_c_star,share_foreign_sales,alpha_domestic")
    cols = [Array(ds[v]) for v in SCALARS]
    for (i, r) in enumerate(regions)
        println(io, "\"", r, "\",", join([mis(c[i]) for c in cols], ","))
    end
end

const STEPVARS = [
    "baseline harvest", "baseline sales", "baseline producer storage",
    "baseline demand", "baseline consumer storage", "baseline consumption",
    "baseline consumer price",
]
step_arrays = Dict{String,Array{Union{Missing,Float64},2}}()
open(joinpath(outdir, "baseline_step.csv"), "w") do io
    println(io, "Region,variable,n,value")
    for v in STEPVARS
        a = Array(ds[v])
        @assert size(a) == (24, length(regions)) "unexpected size for $v: $(size(a))"
        step_arrays[v] = a
        for (i, r) in enumerate(regions), n in 1:24
            println(io, "\"", r, "\",\"", v, "\",", n, ",", mis(a[n, i]))
        end
    end
end

open(joinpath(outdir, "baseline_price.csv"), "w") do io
    println(io, "n,value")
    a = Array(ds["baseline price"])
    @assert length(a) == 24
    for n in 1:24
        println(io, n, ",", mis(a[n]))
    end
end

# baseline transaction quantity, written as (n, consumer, producer) -- see DIM NOTE
btq = Array(ds["baseline transaction quantity"])
@assert size(btq) == (24, length(regions), length(regions))
nzsum(v) = sum(Float64(x) for x in v if !ismissing(x) && !isnan(x); init = 0.0)
open(joinpath(outdir, "baseline_transactions.csv"), "w") do io
    println(io, "Consumer,Producer,n,value")
    for (ic, c) in enumerate(regions), (ip, p) in enumerate(regions)
        col = [btq[n, ic, ip] for n in 1:24]
        all(x -> ismissing(x) || (x isa AbstractFloat && isnan(x)), col) && continue
        for n in 1:24
            println(io, "\"", c, "\",\"", p, "\",", n, ",", mis(col[n]))
        end
    end
end
open(joinpath(outdir, "baseline_trade_annual.csv"), "w") do io
    println(io, "Consumer,Producer,annual")
    for (ic, c) in enumerate(regions), (ip, p) in enumerate(regions)
        col = [btq[n, ic, ip] for n in 1:24]
        all(x -> ismissing(x) || (x isa AbstractFloat && isnan(x)), col) && continue
        println(io, "\"", c, "\",\"", p, "\",", @sprintf("%.12g", nzsum(col)))
    end
end

# Axis-orientation check: summing over the producer axis must track baseline
# demand, summing over the consumer axis must track baseline sales. The QP that
# produces the matrix is solved to eps=baseline_tol and its negative entries are
# then clipped to zero, so these marginals are only approximate -- the check is
# that the *correct* pairing is much closer than the transposed one.
let bd = step_arrays["baseline demand"], bs = step_arrays["baseline sales"]
    worst_d = 0.0; worst_s = 0.0
    rel(a, b) = b == 0 ? abs(a) : abs(a - b) / b
    for (i, r) in enumerate(regions)
        over_prod = nzsum(vec(btq[:, i, :]))          # all producers selling into r
        over_cons = nzsum(vec(btq[:, :, i]))          # all consumers buying from r
        d = nzsum(bd[:, i]); s = nzsum(bs[:, i])
        # Only regions whose demand and sales differ materially can discriminate
        # between the two axis orders.
        if d > 0 && abs(d - s) / d > 0.02
            @assert rel(over_prod, d) < rel(over_cons, d) "axis order ambiguous at $r"
        end
        d > 0 && (worst_d = max(worst_d, rel(over_prod, d)))
        s > 0 && (worst_s = max(worst_s, rel(over_cons, s)))
    end
    println("axis orientation (n, consumer, producer) confirmed for all regions")
    @printf("  worst |rowsum/baseline demand - 1| = %.3e\n", worst_d)
    @printf("  worst |colsum/baseline sales  - 1| = %.3e   (QP tolerance + sign clipping)\n", worst_s)
end

if haskey(ds, "harvest")
    h = Array(ds["harvest"])
    open(joinpath(outdir, "harvest.csv"), "w") do io
        println(io, "Region,t,value")
        for (i, r) in enumerate(regions), t in 1:size(h, 1)
            println(io, "\"", r, "\",", t, ",", mis(h[t, i]))
        end
    end
    println("harvest : ", size(h))
end

if haskey(ds, "export restriction")
    e = Array(ds["export restriction"])
    open(joinpath(outdir, "export_restriction.csv"), "w") do io
        println(io, "Region,t,value")
        for (i, r) in enumerate(regions), t in 1:size(e, 1)
            println(io, "\"", r, "\",", t, ",", mis(e[t, i]))
        end
    end
    println("export restriction : ", size(e))
end

close(ds)
println("wrote ", outdir)
