# Gate 0 on PIK develop-substitution-claude (snapshot of develop-consumers f492df9),
# one consumer per region, published maxtime = 60 SLSQP stop.
#
#   arch -x86_64 .../julia-1.6.5/bin/julia --project=/Users/mjp38/GitHub/agrimate \
#     diagnostics/gate0_v2/gate0_4crop.jl CROP T_MAX [INPUTS]
#
# CROP in wheat, rice, maize, soybean. T_MAX = 0 is the startup check; 312 is J10 length.
# INPUTS: kilian (default; his 2026 package) or published (wheat only; the J10 input set
# that reproduced the 2025 published hindcast on the old host).
using DrWatson
@quickactivate "Agrimate"

using Dates

include(srcdir("simulation.jl"))

const AGRIMATE = "/Users/mjp38/GitHub/agrimate"
const SHEAF = dirname(dirname(dirname(@__FILE__)))
const INPUTROOTS = Dict(
    "kilian" => joinpath(AGRIMATE, "data", "agrimate_input"),
    "published" => "/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/data/agrimate_input_authorbase",
)
const OUTPARENT = joinpath(AGRIMATE, "data", "gate0_v2")

function head_or_refuse(repo; untracked = "all")
    por = strip(read(`git -C $repo status --porcelain --untracked-files=$untracked`, String))
    isempty(por) || error("refusing to write outputs: $repo is dirty:\n$por")
    return readchomp(`git -C $repo rev-parse HEAD`)
end

function main()
    length(ARGS) in (2, 3) || error("usage: gate0_4crop.jl CROP T_MAX [kilian|published]")
    crop = ARGS[1]
    t_max = parse(Int, ARGS[2])
    inputs = length(ARGS) == 3 ? ARGS[3] : "kilian"
    crop in ("wheat", "rice", "maize", "soybean") || error("unknown crop $crop")
    haskey(INPUTROOTS, inputs) || error("unknown input set $inputs")
    inputs == "published" && crop != "wheat" && error("published inputs exist for wheat only")
    inputroot = INPUTROOTS[inputs]
    agrimate_commit = head_or_refuse(AGRIMATE)
    sheaf_commit = head_or_refuse(SHEAF; untracked = "no")
    outputroot = joinpath(OUTPARENT, inputs == "kilian" ? "$(crop)_t$(t_max)" : "$(crop)_t$(t_max)_$(inputs)")
    mkpath(outputroot)
    inputs_sha = read(pipeline(`find $inputroot -name "*crop=$(crop)*" -type f`, `sort`, `xargs shasum -a 256`), String)
    open(joinpath(outputroot, "provenance.txt"), "w") do io
        println(io, "agrimate_commit $agrimate_commit")
        println(io, "agrimate_note develop-substitution-claude snapshot of PIK develop-consumers f492df9")
        println(io, "sheaf_commit $sheaf_commit")
        println(io, "crop $crop")
        println(io, "t_max $t_max")
        println(io, "inputs $inputs")
        println(io, "stop_rule SLSQP maxtime = 60 (published)")
        println(io, "consumers one per region (no consumer_share / consumer_A_c input)")
        println(io, "inputroot $inputroot")
        print(io, inputs_sha)
    end
    params = Params(
        crops = crop,
        baseline = "2007-2009",
        regions = "AgrimateEU28",
        extra_regions = Dict{String,Any}("Egypt" => "EGY"),
        start = Date(2000, 1, 1),
        production_anomalies = "FAOsince-2005",
        export_restrictions = "2007-2011",
        consumer_A_c_source = nothing,
        consumer_share_source = nothing,
        A_c_star = :empirical,
    )
    println("agrimate_commit $agrimate_commit")
    println("sheaf_commit $sheaf_commit")
    println("crop $crop t_max $t_max inputs $inputs output $outputroot")
    flush(stdout)
    t0 = time()
    simulate(params; t_max = t_max, inputroot = inputroot, outputroot = outputroot,
             verbose = true, use_cache = false, use_netcdf_input = false,
             progressbar_name = crop)
    dt = time() - t0
    open(joinpath(outputroot, "walltime.txt"), "w") do io
        println(io, "agrimate_commit $agrimate_commit")
        println(io, "sheaf_commit $sheaf_commit")
        println(io, "seconds $dt")
    end
    println("done $crop t_max=$t_max inputs=$inputs $dt")
end

main()
