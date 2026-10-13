# J10 wheat at a chosen SLSQP evaluation budget.
# Author baseline, FAOsince-2005, restrictions 2007-2011, t_max = 312.
# maxeval is a Params field. The objective, xtol_abs, ι, and the price cap
# are unchanged.
#
#   AGRIMATE_NLOPT_LOG=1 arch -x86_64 .../julia --project=agrimate_julia \
#     diagnostics/gate1_identity/j10_budget.jl MAXEVAL LABEL
using DrWatson
@quickactivate "Agrimate"

using Dates
using Printf

include(srcdir("simulation.jl"))

const ROOT = dirname(dirname(dirname(@__FILE__)))
const INPUTROOT = "/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/data/agrimate_input_authorbase"
const T_MAX = 312

function git_commit_or_refuse()
    por = read(`git -C $ROOT status --porcelain`, String)
    if !isempty(strip(por))
        error("refusing to write outputs: git status is dirty:\n$por")
    end
    return readchomp(`git -C $ROOT rev-parse HEAD`)
end

function main()
    length(ARGS) == 2 || error("usage: j10_budget.jl MAXEVAL LABEL")
    budget = parse(Int, ARGS[1])
    label = ARGS[2]
    commit = git_commit_or_refuse()
    outputroot = joinpath(ROOT, "agrimate_julia", "data_g1prep_identity", "j10_$(label)")
    mkpath(outputroot)
    log_path = joinpath(outputroot, "nlopt.csv")
    mon_path = joinpath(outputroot, "monitor.csv")
    ENV["AGRIMATE_NLOPT_LOG_PATH"] = log_path
    open(log_path, "w") do io
        println(io, "# commit $(commit)")
        println(io, "# maxeval=$(budget) t_max=$(T_MAX) label=$(label)")
        println(io, "crop,region,step,call,code,evals,seconds,xhex")
    end
    mon = open(mon_path, "w")
    println(mon, "# commit $(commit)")
    println(mon, "commit,run,crop,region,step,event,value,threshold")
    flush(mon)
    pm = AgrimateModel.AgentsModule.ProducerModule
    pm.nlopt_log_crop[] = "wheat"
    pm.diag_log[] = function (kind, producer, t, value, threshold)
        println(mon, join((
            commit, label, "wheat", producer.id, t, string(kind),
            @sprintf("%.16g", value), @sprintf("%.16g", threshold),
        ), ","))
        flush(mon)
        return nothing
    end
    params = Params(
        crops = "wheat",
        baseline = "2007-2009",
        regions = "AgrimateEU28",
        extra_regions = Dict{String,Any}("Egypt" => "EGY"),
        start = Date(2000, 1, 1),
        production_anomalies = "FAOsince-2005",
        export_restrictions = "2007-2011",
        maxeval = budget,
    )
    println("commit $commit")
    println("maxeval $budget")
    println("output $outputroot")
    flush(stdout)
    t0 = time()
    simulate(params; t_max = T_MAX, inputroot = INPUTROOT, outputroot = outputroot, verbose = false, use_cache = false)
    dt = time() - t0
    open(joinpath(outputroot, "walltime.txt"), "w") do io
        println(io, "# commit $(commit)")
        println(io, "label $(label)")
        println(io, "maxeval $(budget)")
        println(io, "seconds $(dt)")
    end
    println("walltime $(label) $(dt)")
    println("done $(label)")
    close(mon)
end

main()
