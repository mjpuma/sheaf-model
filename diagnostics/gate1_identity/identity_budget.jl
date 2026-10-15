# Gate 1 identity at maxeval = 116534 (the provisional Gate 1 budget).
# ξ = 0 only. Refuses a dirty tree and stamps the commit.
#
#   arch -x86_64 .../julia --project=agrimate_julia \
#     diagnostics/gate1_identity/identity_budget.jl single wheat undisturbed 24
#     diagnostics/gate1_identity/identity_budget.jl coupled undisturbed 24
#     diagnostics/gate1_identity/identity_budget.jl single wheat crisis 312
#     diagnostics/gate1_identity/identity_budget.jl coupled crisis 312
using DrWatson
@quickactivate "Agrimate"

using Dates
using LinearAlgebra
using Printf

include(srcdir("simulation.jl"))

const ROOT = dirname(dirname(dirname(@__FILE__)))
const INPUTROOT = joinpath(ROOT, "inputs", "generated", "agrimate_input_g1")
const CACHE_ROOT = joinpath(ROOT, "agrimate_julia", "data_g1prep_identity")
const OUTDIR = joinpath(CACHE_ROOT, "g1_bsmall")

function git_commit_or_refuse()
    por = read(`git -C $ROOT status --porcelain`, String)
    if !isempty(strip(por))
        error("refusing to write outputs: git status is dirty:\n$por")
    end
    return readchomp(`git -C $ROOT rev-parse HEAD`)
end

function base_params(; crop, crisis::Bool)
    kwargs = (
        crops = crop,
        baseline = "2007-2009",
        regions = "AgrimateEU28",
        extra_regions = Dict{String,Any}("Egypt" => "EGY"),
        start = Date(2000, 1, 1),
        ξ = 0.0,
    )
    if crisis
        return Params(; kwargs..., production_anomalies = "FAOsince-2005", export_restrictions = "2007-2011")
    end
    return Params(; kwargs...)
end

function hexfloat(x::Float64)
    string(reinterpret(UInt64, x), base = 16, pad = 16)
end

function hexvec(x)
    join((hexfloat(float(v)) for v in x), ",")
end

function order_line(run)
    prod = join(collect(keys(run.model.producers)), ",")
    cons = join(collect(keys(run.model.consumers)), ",")
    return prod, cons
end

function dump_state(io, run, t)
    m = run.model
    prod_order, cons_order = order_line(run)
    println(io, "order $t producer $prod_order")
    println(io, "order $t consumer $cons_order")
    for (id, c) in m.consumers
        isdefined(c, :crop_price_index) || continue
        println(io, "val $t price_index $id $(hexfloat(float(c.crop_price_index)))")
    end
    for (id, p) in m.producers
        for (name, fld) in (
            ("expected_sales_domestic", :expected_sales_domestic),
            ("expected_sales_foreign", :expected_sales_foreign),
            ("expected_price_domestic", :expected_price_domestic),
            ("expected_price_foreign", :expected_price_foreign),
        )
            isdefined(p, fld) || continue
            println(io, "val $t $name $id $(hexfloat(float(getfield(p, fld))))")
        end
        for (name, fld) in (
            ("optimal_sales_domestic", :optimal_sales_domestic),
            ("optimal_sales_foreign", :optimal_sales_foreign),
        )
            isdefined(p, fld) || continue
            println(io, "vec $t $name $id $(hexvec(getfield(p, fld)))")
        end
    end
    flush(io)
end

function step_run!(run, crop, t_max, dump; tag)
    AgrimateModel.AgentsModule.ProducerModule.nlopt_log_crop[] = crop
    for step in 1:t_max
        println("step $tag $crop t=$step")
        flush(stdout)
        t0 = time()
        run_model!(run, 1; verbose = false, progressbar_name = crop)
        println("steptime $tag $crop $step $(time() - t0)")
        println(dump, "steptime $step $(time() - t0)")
        dump_state(dump, run, step)
        flush(stdout)
    end
end

function load_run(crop, crisis, t_max)
    p = base_params(crop = crop, crisis = crisis)
    # Undisturbed caches already live under CACHE_ROOT. Crisis caches are
    # per run directory so parallel crops do not share a file.
    outputroot = crisis ? joinpath(OUTDIR, "crisis_cache") : CACHE_ROOT
    init = initialize_crop(p, crop; inputroot = INPUTROOT, outputroot = outputroot, verbose = false, use_cache = true)
    run = prepare_crop_run(init; t_max = t_max, inputroot = INPUTROOT)
    return run
end

function main()
    length(ARGS) == 4 || error("usage: identity_budget.jl {single|coupled} {wheat|rice|maize|all} {undisturbed|crisis} T_MAX")
    mode = ARGS[1]
    crop = ARGS[2]
    kind = ARGS[3]
    t_max = parse(Int, ARGS[4])
    mode in ("single", "coupled") || error("mode must be single or coupled")
    kind in ("undisturbed", "crisis") || error("kind must be undisturbed or crisis")
    1 <= t_max || error("t_max must be positive")
    crisis = kind == "crisis"
    commit = git_commit_or_refuse()
    mkpath(OUTDIR)
    label = mode == "single" ? "$(kind)_$(crop)" : "$(kind)_coupled"
    dump_path = joinpath(OUTDIR, "dump_$(label).txt")
    dump = open(dump_path, "w")
    println(dump, "# commit $(commit)")
    println(dump, "label $(label)")
    println(dump, "t_max $(t_max)")
    println(dump, "kind $(kind)")
    flush(dump)
    println("commit $commit")
    println("writing $dump_path")
    flush(stdout)
    t0 = time()
    if mode == "single"
        run = load_run(crop, crisis, t_max)
        step_run!(run, crop, t_max, dump; tag = label)
        if !crisis
            ref_path = reference_index_path(joinpath(OUTDIR, "reference_root"), crop)
            save_reference_index(ref_path, crop, run.price_index_data)
            println("reference $ref_path")
        end
    else
        runs = Dict{String,Run}()
        for g in ("wheat", "rice", "maize")
            println("load $g")
            flush(stdout)
            runs[g] = load_run(g, crisis, t_max)
            prod, cons = order_line(runs[g])
            println(dump, "order 0 $g producer $prod")
            println(dump, "order 0 $g consumer $cons")
        end
        for step in 1:t_max
            println("step $label t=$step")
            flush(stdout)
            t1 = time()
            run_model_coupled!(runs, 1; ξ = 0.0, reference_index = Dict{Tuple{String,String,Int},Float64}(), verbose = false, progressbar_name = label)
            println("steptime $label $step $(time() - t1)")
            for g in ("wheat", "rice", "maize")
                println(dump, "crop $g")
                dump_state(dump, runs[g], step)
            end
        end
    end
    dt = time() - t0
    println(dump, "walltime $dt")
    close(dump)
    open(joinpath(OUTDIR, "wall_$(label).txt"), "w") do io
        println(io, "# commit $(commit)")
        println(io, "label $(label)")
        println(io, "seconds $(dt)")
    end
    println("done $label $dt")
end

main()
