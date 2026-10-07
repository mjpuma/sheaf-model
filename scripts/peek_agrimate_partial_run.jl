# Gate 0: score a still-running Agrimate run against the author output over
# the steps written so far. The NetCDF is rewritten whole after every 24-step
# chunk, so the completed prefix is already valid output.
#
#   cd /Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty
#   arch -x86_64 .../julia --project=. .../peek_agrimate_partial_run.jl <local.nc>
#
# Price index and stocks follow the definitions in
# compare_agrimate_julia_runs.jl, so the numbers are comparable with
# J4/J8/J9. Steps after the last written chunk are detected as all-zero
# transaction quantity and dropped from both series.
using NCDatasets, Dates, Printf, Statistics

const AUTHOR = "/Users/mjp38/GitHub/agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/" *
    "agrimate_baseline=2007-2009_export_restrictions=2007-2011_extra_regions=(Egypt=EGY)_" *
    "production_anomalies=FAOsince-2005_regions=AgrimateEU28_start=2000-01-01.nc"
const LOCAL = length(ARGS) >= 1 ? ARGS[1] :
    "/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/data_authorbase/netcdf/" *
    "agrimate_baseline=2007-2009_export_restrictions=2007-2011_extra_regions=(Egypt=EGY)_" *
    "production_anomalies=FAOsince-2005_regions=AgrimateEU28_start=2000-01-01.nc"

nz(x) = isnan(x) ? 0.0 : x

function load(path)
    ds = NCDataset(path)
    d = Dict{String,Any}()
    for k in keys(ds)
        x = Array(ds[k])
        if eltype(x) >: Missing && nonmissingtype(eltype(x)) <: AbstractFloat
            x = Float64.(coalesce.(x, NaN))
        end
        d[k] = x
    end
    close(ds)
    d["region"] = String.(d["region"])
    d
end

"Last step with any cross-border flow; the written prefix of a running job."
function written_steps(d)
    tq = nz.(d["transaction quantity"])
    T = size(tq, 1)
    last_t = 0
    for t in 1:T
        s = 0.0
        for c in 1:size(tq, 2), p in 1:size(tq, 3)
            p == c && continue
            s += tq[t, c, p]
        end
        s > 0 && (last_t = t)
    end
    last_t
end

"Monthly export-weighted mean cross-border transaction price over steps 1:T."
function wm_price_monthly(d, T)
    tq = nz.(d["transaction quantity"]); tp = nz.(d["transaction price"])
    R = size(tq, 2)
    ym = [(year(t), month(t)) for t in d["time"][1:T]]
    ks = unique(ym)
    out = Float64[]
    for k in ks
        v = 0.0; q = 0.0
        for t in findall(==(k), ym), c in 1:R, p in 1:R
            p == c && continue
            v += tq[t, c, p] * tp[t, c, p]; q += tq[t, c, p]
        end
        push!(out, v / q)
    end
    ks, out
end

window(ks, p, y0, m0, y1, m1) = begin
    sel = [(y, m) >= (y0, m0) && (y, m) <= (y1, m1) for (y, m) in ks]
    any(sel) ? mean(p[sel]) : NaN
end

L = load(LOCAL); A = load(AUTHOR)
T = written_steps(L)
@printf("steps written: %d of %d  (through %s)\n", T, length(L["time"]), L["time"][T])

kl, pl = wm_price_monthly(L, T)
ka, pa = wm_price_monthly(A, T)

# monthly series for plotting; J10_CSV sets the destination
if haskey(ENV, "J10_CSV")
    open(ENV["J10_CSV"], "w") do io
        println(io, "year,month,local,author")
        for i in 1:min(length(pl), length(pa))
            @printf(io, "%d,%d,%.6f,%.6f\n", kl[i][1], kl[i][2], pl[i], pa[i])
        end
    end
end

base_l = window(kl, pl, 2000, 1, 2005, 12)
base_a = window(ka, pa, 2000, 1, 2005, 12)
@printf("\n2000-2005 mean world price: local %.4f, author %.4f\n", base_l, base_a)

for (lab, y0, m0, y1, m1) in [("2007/08 (Jul 07 - Jun 08)", 2007, 7, 2008, 6),
                              ("2010/11 (Jul 10 - Jun 11)", 2010, 7, 2011, 6)]
    rl = window(kl, pl, y0, m0, y1, m1) / base_l
    ra = window(ka, pa, y0, m0, y1, m1) / base_a
    isnan(rl) && continue
    @printf("%s price ratio: local %.3f, author %.3f  (gap %+.3f)\n", lab, rl, ra, rl - ra)
end

n = min(length(pl), length(pa))
il = argmax(pl); ia = argmax(pa[1:n])
@printf("\npeak so far: local %.3f at %s, author %.3f at %s\n",
        pl[il], string(kl[il]), pa[ia], string(ka[ia]))
@printf("monthly price correlation over the written prefix: %.3f\n", cor(pl[1:n], pa[1:n]))

# stocks, year by year, over whole years inside the written prefix
yrs_l = year.(L["time"][1:T])
st_l = nz.(L["producer storage"]) .+ nz.(L["consumer storage"])
st_a = nz.(A["producer storage"]) .+ nz.(A["consumer storage"])
println("\nworld end-of-year stocks (Mt): year, local, author, gap %")
stock_rows = Tuple{Int,Float64,Float64}[]
for y in sort(unique(yrs_l))
    idx = findall(==(y), yrs_l)
    length(idx) == 24 || continue
    l = sum(st_l[idx[end], :]) / 1e3
    a = sum(st_a[idx[end], :]) / 1e3
    push!(stock_rows, (y, l, a))
    @printf("  %d  %8.1f  %8.1f  %+6.1f %%\n", y, l, a, 100 * (l / a - 1))
end

if haskey(ENV, "J10_STOCK_CSV")
    open(ENV["J10_STOCK_CSV"], "w") do io
        println(io, "year,local,author")
        for (y, l, a) in stock_rows
            @printf(io, "%d,%.4f,%.4f\n", y, l, a)
        end
    end
end
