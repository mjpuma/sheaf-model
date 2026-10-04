# Gate 0 J9 diagnosis: which regions carry the residual world-price and
# world-stock gaps between the local harvest + restrictions run and the
# author's, once the author's ψ, A_d*, A_c* (J8) and the author's export
# restrictions (J9) are already in the inputs.
#
# Run read-only from the paper project (uses its NCDatasets):
#   cd /Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty
#   arch -x86_64 /Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia \
#       --project=. /Users/mjp38/GitHub/sheaf-model/scripts/diagnose_agrimate_j9_gaps.jl
#
# Price decomposition. The world market price of compare_agrimate_julia_runs.jl
# is P = Σ_{t,c,p≠c} q·p / Σ_{t,c,p≠c} q over a window. Writing w_p for the
# producer's share of window export volume and p̄_p for its export-weighted
# mean price, P = Σ_p w_p p̄_p. The local-minus-author gap then splits into a
# volume-share term Σ_p (w_p^L − w_p^A) p̄_p^A and a price term
# Σ_p w_p^L (p̄_p^L − p̄_p^A).
#
# Stock decomposition is the plain end-of-year producer + consumer storage
# difference per region, as a share of the world difference.

using NCDatasets, Statistics, Dates, Printf

const FILE = "agrimate_baseline=2007-2009_export_restrictions=2007-2011_" *
             "extra_regions=(Egypt=EGY)_production_anomalies=FAOsince-2005_" *
             "regions=AgrimateEU28_start=2000-01-01.nc"
const LOCAL = get(ENV, "J9_LOCAL",
    "/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/data_authorrestr/netcdf/" * FILE)
const AUTHOR = get(ENV, "J9_AUTHOR",
    "/Users/mjp38/GitHub/agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/" * FILE)

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

L = load(LOCAL); A = load(AUTHOR)
R = L["region"]; NR = length(R); T = L["time"]
@assert R == A["region"] && T == A["time"]

# ------------------------------------------------------------------ price
"Export volume and volume-weighted price per producer over the steps in `m`."
function by_producer(d, m)
    q = nz.(d["transaction quantity"]); p = nz.(d["transaction price"])
    vol = zeros(NR); val = zeros(NR)
    for t in findall(m), c in 1:NR, pr in 1:NR
        pr == c && continue
        vol[pr] += q[t, c, pr]
        val[pr] += q[t, c, pr] * p[t, c, pr]
    end
    vol, val
end

function price_table(label, m)
    vl, al = by_producer(L, m); va, aa = by_producer(A, m)
    Ql = sum(vl); Qa = sum(va)
    Pl = sum(al) / Ql; Pa = sum(aa) / Qa
    wl = vl ./ Ql; wa = va ./ Qa
    pl = [vl[i] > 0 ? al[i] / vl[i] : NaN for i in 1:NR]
    pa = [va[i] > 0 ? aa[i] / va[i] : NaN for i in 1:NR]
    contr = [nz(wl[i] * pl[i]) - nz(wa[i] * pa[i]) for i in 1:NR]
    volterm = [(wl[i] - wa[i]) * nz(pa[i]) for i in 1:NR]
    prterm = [wl[i] * (nz(pl[i]) - nz(pa[i])) for i in 1:NR]
    ord = sortperm(abs.(contr); rev = true)
    println("\n### $label world price: local $(@sprintf("%.3f", Pl)) vs author $(@sprintf("%.3f", Pa)), gap $(@sprintf("%+.3f", Pl - Pa))\n")
    println("Export volume over the window: local $(@sprintf("%.0f", Ql)) kt, author $(@sprintf("%.0f", Qa)) kt ($(@sprintf("%+.1f", 100*(Ql/Qa-1))) %).\n")
    println("| producer region | vol share L | A | mean export price L | A | contribution to price gap | of which volume-share | of which price |")
    println("|---|---|---|---|---|---|---|---|")
    for i in ord[1:min(10, end)]
        (vl[i] == 0 && va[i] == 0) && continue
        @printf("| %s | %.3f | %.3f | %.3f | %.3f | %+.4f | %+.4f | %+.4f |\n",
                R[i], wl[i], wa[i], pl[i], pa[i], contr[i], volterm[i], prterm[i])
    end
    @printf("| **all 28** | 1.000 | 1.000 | %.3f | %.3f | %+.4f | %+.4f | %+.4f |\n",
            Pl, Pa, sum(contr), sum(volterm), sum(prterm))
end

println("# J9 residual-gap diagnosis (harvest + restrictions)\n")
println("local:  ", LOCAL)
println("author: ", AUTHOR)

ym = [(year(t), month(t)) for t in T]
price_table("Jul 2007 - Jun 2008", [(y == 2007 && m >= 7) || (y == 2008 && m <= 6) for (y, m) in ym])
price_table("May 2008 (author peak month)", [y == 2008 && m == 5 for (y, m) in ym])
price_table("Jun 2008 (local peak month)", [y == 2008 && m == 6 for (y, m) in ym])
price_table("2000 - 2005 baseline window", [y in 2000:2005 for (y, _) in ym])

# ----------------------------------------------------------------- stocks
function stock_table(label, yr)
    m = findall(y -> y == yr, year.(T))
    t = last(m)
    sl = nz.(L["producer storage"][t, :]) .+ nz.(L["consumer storage"][t, :])
    sa = nz.(A["producer storage"][t, :]) .+ nz.(A["consumer storage"][t, :])
    g = sl .- sa
    tot = sum(g)
    ord = sortperm(abs.(g); rev = true)
    println("\n### $label world stocks: local $(@sprintf("%.0f", sum(sl))) kt vs author $(@sprintf("%.0f", sum(sa))) kt, gap $(@sprintf("%+.0f", tot)) kt ($(@sprintf("%+.1f", 100*(sum(sl)/sum(sa)-1))) %)\n")
    println("| region | stocks L | A | gap kt | gap % | share of world gap |")
    println("|---|---|---|---|---|---|")
    cum = 0.0
    for i in ord[1:min(10, end)]
        cum += g[i]
        @printf("| %s | %.0f | %.0f | %+.0f | %+.1f | %.0f %% |\n", R[i], sl[i], sa[i], g[i],
                sa[i] > 0 ? 100 * (sl[i] / sa[i] - 1) : NaN, 100 * g[i] / tot)
    end
    @printf("| **top 10 together** | | | %+.0f | | %.0f %% |\n", cum, 100 * cum / tot)
end

stock_table("End 2008", 2008)
stock_table("End 2012", 2012)
