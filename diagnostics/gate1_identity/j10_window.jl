# J10 wheat under the published SLSQP clock, through the 2007/08 window.
# Steps 181–204 are the timesteps whose midpoints fall in July 2007–June 2008
# (N_year = 24, start 2000-01-01). Reaching them requires stepping from t = 1.
# Does not change the objective, xtol, ι, the price cap, or Params.
#
#   AGRIMATE_NLOPT_LOG=1 arch -x86_64 .../julia --project=agrimate_julia \
#     diagnostics/gate1_identity/j10_window.jl
using DrWatson
@quickactivate "Agrimate"

using Dates

include(srcdir("simulation.jl"))

const ROOT = dirname(dirname(dirname(@__FILE__)))
const INPUTROOT = "/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/data/agrimate_input_authorbase"
const OUTPUTROOT = joinpath(ROOT, "agrimate_julia", "data_g1prep_identity", "j10_window")
const T_MAX = 204

function git_commit_or_refuse()
    por = read(`git -C $ROOT status --porcelain`, String)
    if !isempty(strip(por))
        error("refusing to write outputs: git status is dirty:\n$por")
    end
    return readchomp(`git -C $ROOT rev-parse HEAD`)
end

function main()
    commit = git_commit_or_refuse()
    mkpath(OUTPUTROOT)
    log_path = joinpath(OUTPUTROOT, "nlopt_j10_wheat.csv")
    ENV["AGRIMATE_NLOPT_LOG_PATH"] = log_path
    open(log_path, "w") do io
        println(io, "# commit $(commit)")
        println(io, "# J10 wheat production_anomalies=FAOsince-2005 export_restrictions=2007-2011 t_max=$(T_MAX)")
        println(io, "crop,region,step,call,code,evals,seconds,xhex")
    end
    println("commit $commit")
    println("nlopt log $log_path")
    flush(stdout)
    params = Params(
        crops = "wheat",
        baseline = "2007-2009",
        regions = "AgrimateEU28",
        extra_regions = Dict{String,Any}("Egypt" => "EGY"),
        start = Date(2000, 1, 1),
        production_anomalies = "FAOsince-2005",
        export_restrictions = "2007-2011",
    )
    init = initialize_crop(params, "wheat"; inputroot = INPUTROOT, outputroot = OUTPUTROOT, verbose = false, use_cache = false)
    run = prepare_crop_run(init; t_max = T_MAX, inputroot = INPUTROOT)
    AgrimateModel.AgentsModule.ProducerModule.nlopt_log_crop[] = "wheat"
    open(joinpath(OUTPUTROOT, "steptime_j10_wheat.txt"), "w") do io
        println(io, "# commit $(commit)")
        for step in 1:T_MAX
            println("step wheat t=$step")
            flush(stdout)
            t0 = time()
            run_model!(run, 1; verbose = false, progressbar_name = "j10wheat")
            dt = time() - t0
            println("steptime wheat $step $dt")
            println(io, "steptime $step $dt")
            flush(stdout)
            flush(io)
        end
    end
    println("done j10_window")
end

main()
