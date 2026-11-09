# Gate 0 on PIK develop-substitution-claude (snapshot of develop-consumers f492df9),
# one consumer per region, published maxtime = 60 SLSQP stop, Kilian's inputs.
#
#   arch -x86_64 .../julia-1.6.5/bin/julia --project=/Users/mjp38/GitHub/agrimate \
#     diagnostics/gate0_v2/gate0_4crop.jl CROP T_MAX
#
# CROP in wheat, rice, maize, soybean. T_MAX = 0 is the startup check; 312 is J10 length.
using DrWatson
@quickactivate "Agrimate"

using Dates

include(srcdir("simulation.jl"))

const AGRIMATE = "/Users/mjp38/GitHub/agrimate"
const SHEAF = dirname(dirname(dirname(@__FILE__)))
const INPUTROOT = joinpath(AGRIMATE, "data", "agrimate_input")
const OUTPARENT = joinpath(AGRIMATE, "data", "gate0_v2")

function head_or_refuse(repo; untracked = "all")
    por = strip(read(`git -C $repo status --porcelain --untracked-files=$untracked`, String))
    isempty(por) || error("refusing to write outputs: $repo is dirty:\n$por")
    return readchomp(`git -C $repo rev-parse HEAD`)
end

function main()
    length(ARGS) == 2 || error("usage: gate0_4crop.jl CROP T_MAX")
    crop = ARGS[1]
    t_max = parse(Int, ARGS[2])
    crop in ("wheat", "rice", "maize", "soybean") || error("unknown crop $crop")
    agrimate_commit = head_or_refuse(AGRIMATE)
    sheaf_commit = head_or_refuse(SHEAF; untracked = "no")
    outputroot = joinpath(OUTPARENT, "$(crop)_t$(t_max)")
    mkpath(outputroot)
    inputs_sha = read(pipeline(`find $INPUTROOT -name "*crop=$(crop)*" -type f`, `sort`, `xargs shasum -a 256`), String)
    open(joinpath(outputroot, "provenance.txt"), "w") do io
        println(io, "agrimate_commit $agrimate_commit")
        println(io, "agrimate_note develop-substitution-claude snapshot of PIK develop-consumers f492df9")
        println(io, "sheaf_commit $sheaf_commit")
        println(io, "crop $crop")
        println(io, "t_max $t_max")
        println(io, "stop_rule SLSQP maxtime = 60 (published)")
        println(io, "consumers one per region (no consumer_share / consumer_A_c input)")
        println(io, "inputroot $INPUTROOT")
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
    )
    println("agrimate_commit $agrimate_commit")
    println("sheaf_commit $sheaf_commit")
    println("crop $crop t_max $t_max output $outputroot")
    flush(stdout)
    t0 = time()
    simulate(params; t_max = t_max, inputroot = INPUTROOT, outputroot = outputroot,
             verbose = true, use_cache = false, progressbar_name = crop)
    dt = time() - t0
    open(joinpath(outputroot, "walltime.txt"), "w") do io
        println(io, "agrimate_commit $agrimate_commit")
        println(io, "sheaf_commit $sheaf_commit")
        println(io, "seconds $dt")
    end
    println("done $crop t_max=$t_max $dt")
end

main()
