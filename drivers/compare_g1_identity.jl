# Gate 1 ξ=0 identity: coupled vs single-crop monthly world prices.
# Bar: max |P_coupled / P_single - 1| ≤ 0.5% (GATE1_DESIGN.md §7 / §8).
#
#   arch -x86_64 .../julia --project=agrimate_julia \
#     drivers/compare_g1_identity.jl agrimate_julia/data_g1prep_identity
#
using NCDatasets, Dates, Printf, Statistics

const BAR = 0.005
const ROOT = length(ARGS) >= 1 ? ARGS[1] : error("usage: compare_g1_identity.jl <outputroot>")

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

function written_steps(d)
    haskey(d, "transaction quantity") || return 0
    tq = nz.(d["transaction quantity"])
    last_t = 0
    for t in 1:size(tq, 1)
        s = 0.0
        for c in 1:size(tq, 2), p in 1:size(tq, 3)
            p == c && continue
            s += tq[t, c, p]
        end
        s > 0 && (last_t = t)
    end
    last_t
end

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
        push!(out, q > 0 ? v / q : NaN)
    end
    ks, out
end

function crop_of(name)
    occursin("crops=rice", name) && return "rice"
    occursin("crops=maize", name) && return "maize"
    return "wheat"
end

single_dir = joinpath(ROOT, "netcdf")
coupled_dir = joinpath(ROOT, "netcdf", "coupled")
isdir(single_dir) || error("missing $single_dir")
isdir(coupled_dir) || error("missing $coupled_dir (coupled run not written yet)")

singles = filter(f -> endswith(f, ".nc"), readdir(single_dir))
pass = true
println("Gate 1 ξ=0 identity  (bar 0.5% monthly world price)")
println("single:  $single_dir")
println("coupled: $coupled_dir")
println()

for fname in sort(singles)
    cpath = joinpath(coupled_dir, fname)
    if !isfile(cpath)
        @printf("FAIL  %s: no coupled file\n", crop_of(fname))
        global pass = false
        continue
    end
    S = load(joinpath(single_dir, fname))
    C = load(cpath)
    Ts, Tc = written_steps(S), written_steps(C)
    T = min(Ts, Tc)
    if T == 0
        @printf("FAIL  %s: no written steps (single %d, coupled %d)\n", crop_of(fname), Ts, Tc)
        global pass = false
        continue
    end
    ks, ps = wm_price_monthly(S, T)
    _, pc = wm_price_monthly(C, T)
    n = min(length(ps), length(pc))
    rel = [isfinite(ps[i]) && isfinite(pc[i]) && ps[i] > 0 ? abs(pc[i] / ps[i] - 1) : NaN for i in 1:n]
    finite = filter(isfinite, rel)
    mx = isempty(finite) ? NaN : maximum(finite)
    ok = isfinite(mx) && mx <= BAR
    ok || (global pass = false)
    @printf(
        "%s  %s  steps=%d months=%d  max |P_c/P_s-1|=%.4f%%  (bar 0.50%%)\n",
        ok ? "PASS" : "FAIL",
        crop_of(fname),
        T,
        n,
        100 * mx,
    )
end

exit(pass ? 0 : 1)
