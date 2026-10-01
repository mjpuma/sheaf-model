# Gate 0 J4: compare local runs of the published Agrimate code with the
# author NetCDF in Zenodo data v3 (hindcasting_analysis/raw_data).
#
# Run read-only from the paper project (uses its NCDatasets):
#   cd /Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty
#   arch -x86_64 /Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia \
#       --project=. /Users/mjp38/GitHub/sheaf-model/scripts/compare_agrimate_julia_runs.jl
#
# Aggregation follows the paper's src/plot.jl: harvest and consumption are
# summed per calendar year, storage is the last value of the year, and the
# world market price index is the monthly export-volume-weighted mean
# transaction price over non-domestic flows (plot_wm_price_timeseries).
# Trade arrays are stored as [time, consumer, producer] (src/io.jl).

using NCDatasets, Statistics, Dates, Printf

const LOCAL = "/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/data/netcdf/"
const AUTHOR = "/Users/mjp38/GitHub/agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/"
const STEM = "agrimate_baseline=2007-2009_"
const TAIL = "regions=AgrimateEU28_start=2000-01-01.nc"
const SCEN = [
    ("baseline", STEM * "extra_regions=(Egypt=EGY)_" * TAIL),
    ("harvest", STEM * "extra_regions=(Egypt=EGY)_production_anomalies=FAOsince-2005_" * TAIL),
    ("harvest+restr", STEM * "export_restrictions=2007-2011_extra_regions=(Egypt=EGY)_production_anomalies=FAOsince-2005_" * TAIL),
]
const KEY = ["USA", "EU-28", "Russia", "Ukraine", "Kazakhstan", "Argentina", "Australia",
             "Canada", "India", "China", "Egypt"]

nz(x) = isnan(x) ? 0.0 : x

function load(path)
    ds = NCDataset(path)
    d = Dict{String,Any}()
    for k in keys(ds)
        x = Array(ds[k])
        if eltype(x) >: Missing && nonmissingtype(eltype(x)) <: AbstractFloat
            nmiss = count(ismissing, x)
            nmiss > 0 && (d["_missing_" * k] = nmiss)
            x = Float64.(coalesce.(x, NaN))
        end
        d[k] = x
    end
    d["_attrib"] = Dict(String(k) => string(v) for (k, v) in ds.attrib)
    close(ds)
    d["region"] = String.(d["region"])
    d
end

function wm_price_monthly(d)
    tq = nz.(d["transaction quantity"]); tp = nz.(d["transaction price"])
    T, R, _ = size(tq)
    ym = [(year(t), month(t)) for t in d["time"]]
    keys_ = unique(ym)
    out = Float64[]
    for k in keys_
        v = 0.0; q = 0.0
        for t in findall(==(k), ym), c in 1:R, p in 1:R
            p == c && continue
            v += tq[t, c, p] * tp[t, c, p]; q += tq[t, c, p]
        end
        push!(out, v / q)
    end
    keys_, out
end

function annual(d, var, op, idx)
    yrs = year.(d["time"])
    ys = sort(unique(yrs))
    x = nz.(d[var])
    vals = [op(vec(sum(x[yrs .== y, idx]; dims = 2))) for y in ys]
    ys, vals
end
annual_sum(d, var, idx) = annual(d, var, sum, idx)
annual_last(d, var, idx) = annual(d, var, last, idx)
stocks(d, idx) = begin
    ys, a = annual_last(d, "producer storage", idx)
    _, b = annual_last(d, "consumer storage", idx)
    ys, a .+ b
end

rel(a, b) = 100 * (a / b - 1)

function header(s)
    println("\n## ", s, "\n")
end

# ---------------------------------------------------------------- structure
header("File structure")
D = Dict{Tuple{String,String},Any}()
for (lab, fn) in SCEN
    D[(lab, "local")] = load(LOCAL * fn)
    D[(lab, "author")] = load(AUTHOR * fn)
end
for (lab, _) in SCEN
    L = D[(lab, "local")]; A = D[(lab, "author")]
    vl = filter(k -> !startswith(k, "_"), collect(keys(L))); va = filter(k -> !startswith(k, "_"), collect(keys(A)))
    for (src, X) in (("local", L), ("author", A))
        m = [(k[10:end], X[k]) for k in keys(X) if startswith(k, "_missing_")]
        println("  $src missing/fill cells by variable: ", sort(m))
    end
    println("$lab: vars local-only=", setdiff(vl, va), " author-only=", setdiff(va, vl))
    println("  same region order: ", L["region"] == A["region"], "; same time axis: ", L["time"] == A["time"])
    bad = [k for k in intersect(vl, va) if size(L[k]) != size(A[k])]
    println("  shape mismatches: ", bad)
    al = L["_attrib"]; aa = A["_attrib"]
    for k in sort(collect(union(keys(al), keys(aa))))
        get(al, k, "—") == get(aa, k, "—") && continue
        println("  attrib $k: local=", get(al, k, "—"), " | author=", get(aa, k, "—"))
    end
end

for (lab, _) in SCEN, src in ("local", "author")
    h = D[(lab, src)]["harvest"]
    np = [D[(lab, src)]["region"][i] for i in 1:size(h, 2) if all(isnan, h[:, i])]
    println("$lab $src: regions with no producer output (harvest all missing): ", np)
end

L0 = D[("baseline", "local")]; R = L0["region"]; NR = length(R)
allr = 1:NR
ri(n) = findfirst(==(n), R)

# orientation check: summed over dim 2 (consumer) should give producer exports
tq = nz.(L0["transaction quantity"])
usa = ri("USA"); egy = ri("Egypt")
println("\norientation check (local baseline, step 1, off-diagonal): USA as producer ",
        @sprintf("%.0f", sum(tq[1, [c for c in allr if c != usa], usa])),
        ", USA as consumer ", @sprintf("%.0f", sum(tq[1, usa, [p for p in allr if p != usa]])),
        "; Egypt as producer ", @sprintf("%.0f", sum(tq[1, [c for c in allr if c != egy], egy])),
        ", Egypt as consumer ", @sprintf("%.0f", sum(tq[1, egy, [p for p in allr if p != egy]])))

# ---------------------------------------------------------------- static inputs
header("Calibrated per-region inputs (baseline file; same in all three)")
A0 = D[("baseline", "author")]
println("| region | baseline harvest/yr L | A | L/A-1 % | baseline consumption/yr L | A | L/A-1 % | ψ L | ψ A | A_d* L | A_d* A | A_c* L | A_c* A |")
println("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for n in vcat(KEY, ["World"])
    idx = n == "World" ? allr : [ri(n)]
    hl = sum(nz.(L0["baseline harvest"][:, idx])); ha = sum(nz.(A0["baseline harvest"][:, idx]))
    cl = sum(nz.(L0["baseline consumption"][:, idx])); ca = sum(nz.(A0["baseline consumption"][:, idx]))
    if n == "World"
        @printf("| %s | %.0f | %.0f | %+.1f | %.0f | %.0f | %+.1f | | | | | | |\n", n, hl, ha, rel(hl, ha), cl, ca, rel(cl, ca))
    else
        i = idx[1]
        @printf("| %s | %.0f | %.0f | %+.1f | %.0f | %.0f | %+.1f | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f |\n",
                n, hl, ha, rel(hl, ha), cl, ca, rel(cl, ca), L0["ψ"][i], A0["ψ"][i],
                L0["A_d_star"][i], A0["A_d_star"][i], L0["A_c_star"][i], A0["A_c_star"][i])
    end
end
btl = nz.(L0["baseline transaction quantity"]); bta = nz.(A0["baseline transaction quantity"])
offd(x) = sum(x[n, c, p] for n in 1:size(x, 1), c in allr, p in allr if c != p)
@printf("\nbaseline international trade/yr: local %.0f, author %.0f (%+.1f %%)\n", offd(btl), offd(bta), rel(offd(btl), offd(bta)))
@printf("baseline price (mean of 24): local %.4f, author %.4f\n", mean(L0["baseline price"]), mean(A0["baseline price"]))
println("all-region max |ψ L-A| = ", @sprintf("%.3f", maximum(abs.(L0["ψ"] .- A0["ψ"]))),
        ", corr(baseline harvest share L,A) = ",
        @sprintf("%.3f", cor(vec(sum(nz.(L0["baseline harvest"]); dims = 1)), vec(sum(nz.(A0["baseline harvest"]); dims = 1)))))
STU(d) = begin
    _, s = stocks(d, allr); _, c = annual_sum(d, "consumption", allr); s[end] / c[end]
end
@printf("world end-2012 stocks ÷ annual consumption, baseline run: local %.3f, author %.3f\n", STU(L0), STU(A0))

# ---------------------------------------------------------------- prices
header("World market price index (monthly, export-weighted transaction price)")
P = Dict{Tuple{String,String},Vector{Float64}}()
mkeys = wm_price_monthly(D[("baseline", "local")])[1]
for (lab, _) in SCEN, src in ("local", "author")
    k, P[(lab, src)] = wm_price_monthly(D[(lab, src)])
    @assert k == mkeys
end
myr = first.(mkeys)
inyrs(ys) = [y in ys for y in myr]
pre = inyrs(2000:2005)
w0708 = [(y == 2007 && m >= 7) || (y == 2008 && m <= 6) for (y, m) in mkeys]
w1011 = [(y == 2010 && m >= 7) || (y == 2011 && m <= 6) for (y, m) in mkeys]
println("Windows: pre = 2000-2005 mean; 07/08 = Jul 2007-Jun 2008; 10/11 = Jul 2010-Jun 2011.")
println("Raw transaction prices for every run. The paper's plot replaces the baseline run's")
println("transaction price with `baseline price` (mean local ",
        @sprintf("%.4f", mean(D[("baseline", "local")]["baseline price"])), ", author ",
        @sprintf("%.4f", mean(D[("baseline", "author")]["baseline price"])), ").\n")
println("| run | src | pre mean | 07/08 mean | 07/08 ÷ pre | 10/11 mean | 10/11 ÷ pre | peak | peak month |")
println("|---|---|---|---|---|---|---|---|---|")
for (lab, _) in SCEN, src in ("local", "author")
    p = P[(lab, src)]; b = mean(p[pre]); k = argmax(p)
    @printf("| %s | %s | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f | %d-%02d |\n", lab, src, b, mean(p[w0708]),
            mean(p[w0708]) / b, mean(p[w1011]), mean(p[w1011]) / b, p[k], mkeys[k]...)
end
println("\n| run | corr L,A (monthly, all) | corr 2005-2012 | mean |L/A-1| % | max |L/A-1| % |")
println("|---|---|---|---|---|")
late = inyrs(2005:2012)
for (lab, _) in SCEN
    l = P[(lab, "local")]; a = P[(lab, "author")]
    @printf("| %s | %.3f | %.3f | %.1f | %.1f |\n", lab, cor(l, a), cor(l[late], a[late]),
            mean(abs.(l ./ a .- 1)) * 100, maximum(abs.(l ./ a .- 1)) * 100)
end
println("\nShock effect on price, ratio of runs (07/08 and 10/11 window means):")
println("| effect | src | 07/08 | 10/11 | corr L,A of monthly ratio 2005-2012 |")
println("|---|---|---|---|---|")
for (nm, x, y) in (("harvest ÷ baseline", "harvest", "baseline"), ("restr ÷ harvest", "harvest+restr", "harvest"))
    rl = P[(x, "local")] ./ P[(y, "local")]; ra = P[(x, "author")] ./ P[(y, "author")]
    for (src, r) in (("local", rl), ("author", ra))
        @printf("| %s | %s | %.3f | %.3f | %s |\n", nm, src, mean(r[w0708]), mean(r[w1011]),
                src == "local" ? @sprintf("%.3f", cor(rl[late], ra[late])) : "")
    end
end
println("\nAnnual mean WM price index:")
yrs = sort(unique(myr))
println("| year | " * join(["$lab L | $lab A" for (lab, _) in SCEN], " | ") * " |")
println("|---" ^ (1 + 2 * length(SCEN)) * "|")
for y in yrs
    print("| $y |")
    for (lab, _) in SCEN
        @printf(" %.3f | %.3f |", mean(P[(lab, "local")][myr .== y]), mean(P[(lab, "author")][myr .== y]))
    end
    println()
end

# ---------------------------------------------------------------- quantities
header("World quantities (1000 t): harvest and consumption are annual sums, stocks end-of-year")
for (lab, _) in SCEN
    L = D[(lab, "local")]; A = D[(lab, "author")]
    ys, hl = annual_sum(L, "harvest", allr); _, ha = annual_sum(A, "harvest", allr)
    _, cl = annual_sum(L, "consumption", allr); _, ca = annual_sum(A, "consumption", allr)
    _, sl = stocks(L, allr); _, sa = stocks(A, allr)
    println("\n### $lab\n")
    println("| year | harvest L | A | % | consumption L | A | % | stocks L | A | % |")
    println("|---|---|---|---|---|---|---|---|---|---|")
    for (i, y) in enumerate(ys)
        @printf("| %d | %.0f | %.0f | %+.1f | %.0f | %.0f | %+.1f | %.0f | %.0f | %+.1f |\n", y, hl[i], ha[i],
                rel(hl[i], ha[i]), cl[i], ca[i], rel(cl[i], ca[i]), sl[i], sa[i], rel(sl[i], sa[i]))
    end
end

header("Per-region, 2007-2009 means (baseline run)")
L = D[("baseline", "local")]; A = D[("baseline", "author")]
sel(ys, v) = mean(v[[y in 2007:2009 for y in ys]])
println("| region | harvest L | A | % | consumption L | A | % | stocks L | A | % | consumer price L | A |")
println("|---|---|---|---|---|---|---|---|---|---|---|---|")
for n in vcat(KEY, ["World"])
    idx = n == "World" ? allr : [ri(n)]
    ys, hl = annual_sum(L, "harvest", idx); _, ha = annual_sum(A, "harvest", idx)
    _, cl = annual_sum(L, "consumption", idx); _, ca = annual_sum(A, "consumption", idx)
    _, sl = stocks(L, idx); _, sa = stocks(A, idx)
    yr = year.(L["time"]); m = [y in 2007:2009 for y in yr]
    cpl = n == "World" ? NaN : mean(L["consumer price"][m, idx[1]])
    cpa = n == "World" ? NaN : mean(A["consumer price"][m, idx[1]])
    a, b, c, d_, e, f = sel(ys, hl), sel(ys, ha), sel(ys, cl), sel(ys, ca), sel(ys, sl), sel(ys, sa)
    @printf("| %s | %.0f | %.0f | %+.1f | %.0f | %.0f | %+.1f | %.0f | %.0f | %+.1f | %.3f | %.3f |\n",
            n, a, b, rel(a, b), c, d_, rel(c, d_), e, f, rel(e, f), cpl, cpa)
end

header("Shock effects by region (percent change vs the reference run, crop years summed by calendar year)")
function effect(lab_x, lab_y, src, var, idx, ys_sel; op = :sum)
    X = D[(lab_x, src)]; Y = D[(lab_y, src)]
    if var == "stocks"
        ys, x = stocks(X, idx); _, y = stocks(Y, idx)
    else
        ys, x = annual_sum(X, var, idx); _, y = annual_sum(Y, var, idx)
    end
    m = [yy in ys_sel for yy in ys]
    rel(sum(x[m]), sum(y[m]))
end
for (nm, x, y) in (("harvest vs baseline", "harvest", "baseline"), ("restr vs harvest", "harvest+restr", "harvest"))
    for (wl, ws) in (("2007-2008", 2007:2008), ("2010-2011", 2010:2011))
        println("\n### $nm, $wl\n")
        println("| region | harvest L | A | consumption L | A | end stocks L | A |")
        println("|---|---|---|---|---|---|---|")
        for n in vcat(KEY, ["World"])
            idx = n == "World" ? allr : [ri(n)]
            v = [effect(x, y, s, var, idx, ws) for var in ("harvest", "consumption", "stocks") for s in ("local", "author")]
            @printf("| %s | %+.1f | %+.1f | %+.1f | %+.1f | %+.1f | %+.1f |\n", n, v...)
        end
    end
end

header("Export restrictions (harvest+restr run)")
L = D[("harvest+restr", "local")]; A = D[("harvest+restr", "author")]
println("| region | steps>0 L | A | max L | A | first step>0 L | A | last L | A |")
println("|---|---|---|---|---|---|---|---|---|")
tt = L["time"]
for i in allr
    el = nz.(L["export restriction"][:, i]); ea = nz.(A["export restriction"][:, i])
    (any(el .> 0) || any(ea .> 0)) || continue
    fl = findfirst(>(0), el); fa = findfirst(>(0), ea); ll = findlast(>(0), el); la = findlast(>(0), ea)
    f(x) = isnothing(x) ? "—" : Dates.format(tt[x], "yyyy-mm-dd")
    @printf("| %s | %d | %d | %.2f | %.2f | %s | %s | %s | %s |\n", R[i], count(>(0), el), count(>(0), ea),
            maximum(el), maximum(ea), f(fl), f(fa), f(ll), f(la))
end
