# Gate 0 J8: check the t_max=0 output of the author-parameter input build.
# Compares every time-free variable (region parameters and the 24-step
# baseline) with the author baseline NetCDF, and with the J2 local baseline
# run on reconstructed parameters. Read-only.
#
#   cd /Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty
#   arch -x86_64 /Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia \
#       --project=. /Users/mjp38/GitHub/sheaf-model/drivers/check_agrimate_authorparams_t0.jl

using NCDatasets, Printf

const FILE = "agrimate_baseline=2007-2009_extra_regions=(Egypt=EGY)_regions=AgrimateEU28_start=2000-01-01.nc"
const NEW = "/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/data_authorparams/netcdf/" * FILE
const J2 = "/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/data/netcdf/" * FILE
const AUTHOR = "/Users/mjp38/GitHub/agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/" * FILE
const KEY = ["USA", "EU-28", "Russia", "Ukraine", "Kazakhstan", "Argentina", "Australia",
             "Canada", "India", "China", "Egypt"]

function load(path)
    ds = NCDataset(path)
    d = Dict{String,Any}()
    d["region"] = String.(Array(ds["region"]))
    for k in keys(ds)
        dn = dimnames(ds[k])
        ("time" in dn || k == "region" || isempty(dn)) && continue
        x = Array(ds[k])
        eltype(x) >: Missing && (x = coalesce.(x, NaN))
        eltype(x) <: Real && (d[k] = Float64.(x))
    end
    close(ds)
    d
end

# reorder region axes of b to a's region order
function align(a, b, k)
    ra, rb = a["region"], b["region"]
    @assert sort(ra) == sort(rb)
    idx = [findfirst(==(r), rb) for r in ra]
    x = b[k]
    nd = ndims(x)
    if k in ("ψ", "A_d_star", "A_c_star", "baseline share foreign sales", "α domestic")
        return x[idx]
    elseif nd == 2
        return x[:, idx]
    elseif nd == 3
        return x[:, idx, idx]
    end
    x
end

nanmax(v) = (w = filter(!isnan, vec(v)); isempty(w) ? NaN : maximum(w))
annual(x) = ndims(x) == 2 ? vec(sum(replace(x, NaN => 0.0); dims = 1)) : x

new, j2, au = load(NEW), load(J2), load(AUTHOR)
regions = new["region"]

println("== region parameters: new (author-param inputs) vs author")
for k in ("ψ", "A_d_star", "A_c_star")
    a = align(new, au, k)
    @printf("%-10s max|new-author| = %.3g   (J2 vs author: %.3g)\n", k,
            nanmax(abs.(new[k] .- a)), nanmax(abs.(align(new, j2, k) .- a)))
end

println("\n== all other time-free variables: max |new - author| (and J2 - author)")
for k in sort(collect(keys(new)))
    k in ("region", "ψ", "A_d_star", "A_c_star", "inner_annual_timestep") && continue
    haskey(au, k) || (println(rpad(k, 36), " not in author file"); continue)
    a = align(new, au, k)
    if size(a) != size(new[k])
        println(rpad(k, 36), " shape ", size(new[k]), " vs author ", size(a)); continue
    end
    @printf("%-36s new %.4g   J2 %.4g\n", k, nanmax(abs.(new[k] .- a)), nanmax(abs.(align(new, j2, k) .- a)))
end

println("\n== key regions, annual sums of the 24-step baseline (1000 t); storages are annual mean")
for k in ("baseline harvest", "baseline sales", "baseline demand", "baseline consumption",
          "baseline producer storage", "baseline consumer storage")
    println("-- ", k, "   (new / author / J2)")
    isstock = occursin("storage", k)
    f(d) = isstock ? annual(align(new, d, k)) ./ size(d[k], 1) : annual(align(new, d, k))
    vn, va, vj = f(new), f(au), f(j2)
    for r in vcat(KEY, ["World"])
        if r == "World"
            @printf("   %-12s %10.0f %10.0f %10.0f  (new/author %+.1f%%)\n", r, sum(vn), sum(va), sum(vj), 100 * (sum(vn) / sum(va) - 1))
        else
            i = findfirst(==(r), regions)
            @printf("   %-12s %10.0f %10.0f %10.0f  (new/author %+.1f%%)\n", r, vn[i], va[i], vj[i],
                    va[i] == 0 ? NaN : 100 * (vn[i] / va[i] - 1))
        end
    end
end

println("\n== baseline price (24 steps): new / author / J2 mean")
@printf("   %.4f %.4f %.4f\n", sum(new["baseline price"]) / 24, sum(au["baseline price"]) / 24, sum(j2["baseline price"]) / 24)

println("\n== region parameter table (new = author? / J2)")
for r in KEY
    i = findfirst(==(r), regions)
    ia = findfirst(==(r), au["region"]); ij = findfirst(==(r), j2["region"])
    @printf("   %-12s ψ %.4f/%.4f (J2 %.4f)  A_d %.4f/%.4f (J2 %.4f)  A_c %.4f/%.4f (J2 %.4f)\n", r,
            new["ψ"][i], au["ψ"][ia], j2["ψ"][ij], new["A_d_star"][i], au["A_d_star"][ia], j2["A_d_star"][ij],
            new["A_c_star"][i], au["A_c_star"][ia], j2["A_c_star"][ij])
end
