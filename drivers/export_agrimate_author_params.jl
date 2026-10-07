# Gate 0 J8: export the author's region parameters (ψ, A_d_star, A_c_star)
# from the three Zenodo data v3 wheat NetCDF files, and the area -> region
# map simulate() builds for AgrimateEU28 + Egypt. Read-only on all inputs.
#
#   cd /Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty
#   arch -x86_64 /Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia \
#       --project=. /Users/mjp38/GitHub/sheaf-model/drivers/export_agrimate_author_params.jl
#
# Writes to /Users/mjp38/GitHub/agrimate-2025/j8_author_params/ (outside both repos):
#   author_region_params.csv  Region,psi,A_d_star,A_c_star (fails if the 3 files disagree)
#   area_region_map.csv       Area,Region
# The CSVs feed inputs/from_paper_params.py.

using DrWatson
@quickactivate "Agrimate"
using NCDatasets, Printf

include(srcdir("regions.jl"))
include(srcdir("preprocess.jl"))

const AUTHOR = "/Users/mjp38/GitHub/agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/"
const OUT = "/Users/mjp38/GitHub/agrimate-2025/j8_author_params/"
const VARS = ["ψ", "A_d_star", "A_c_star"]

files = sort(filter(f -> endswith(f, ".nc"), readdir(AUTHOR)))
@assert length(files) == 3
tables = Dict{String,Any}[]
for f in files
    ds = NCDataset(joinpath(AUTHOR, f))
    regions = String.(Array(ds["region"]))
    t = Dict{String,Any}("region" => regions)
    for v in VARS
        var = ds[v]
        println(f, "  ", v, " dims=", dimnames(var), " attrib=", Dict(var.attrib))
        t[v] = Array(var)
    end
    close(ds)
    push!(tables, t)
end

ref = tables[1]
for (f, t) in zip(files[2:end], tables[2:end])
    @assert t["region"] == ref["region"] "region order differs in $f"
    for v in VARS
        a = ref[v]; b = t[v]
        same = all((ismissing(x) && ismissing(y)) || (!ismissing(x) && !ismissing(y) && x == y) for (x, y) in zip(a, b))
        println("agree with first file: ", f, "  ", v, " => ", same)
        @assert same "$v differs in $f"
    end
end

mkpath(OUT)
open(joinpath(OUT, "author_region_params.csv"), "w") do io
    println(io, "Region,psi,A_d_star,A_c_star")
    for (i, r) in enumerate(ref["region"])
        vals = [ismissing(ref[v][i]) ? "" : repr(Float64(ref[v][i])) for v in VARS]
        println(io, "\"", r, "\",", join(vals, ","))
    end
end

df_region = make_regions_dataframe(get_regions("AgrimateEU28"), Dict{String,Any}("Egypt" => "EGY"))
open(joinpath(OUT, "area_region_map.csv"), "w") do io
    println(io, "Area,Region")
    for row in eachrow(df_region)
        println(io, row.Area, ",\"", row.Region, "\"")
    end
end
println("wrote ", OUT)
