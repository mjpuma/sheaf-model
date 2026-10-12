# Bitwise t_max=2 dumps for the Gate 1 reproducibility check.
# Refuses to write if git is dirty. Stamps the commit in every output file.
# Does not retune, does not start ξ>0, and does not rewrite the Nash cache.
#
#   arch -x86_64 .../julia-1.6.5/bin/julia --project=agrimate_julia \
#     diagnostics/gate1_identity/determinism_t2.jl cold maize cold1
#   ... after maize after1
#   ... coupled coupled1
#   ... cold rice rice_cold
#
using DrWatson
@quickactivate "Agrimate"

using Dates
using LinearAlgebra
using Printf

include(srcdir("simulation.jl"))

const ROOT = dirname(dirname(dirname(@__FILE__)))
const INPUTROOT = joinpath(ROOT, "inputs", "generated", "agrimate_input_g1")
const OUTPUTROOT = joinpath(ROOT, "agrimate_julia", "data_g1prep_identity")
const OUTDIR = joinpath(OUTPUTROOT, "determinism")

function git_commit_or_refuse()
    por = read(`git -C $ROOT status --porcelain`, String)
    if !isempty(strip(por))
        error("refusing to write outputs: git status is dirty:\n$por")
    end
    return readchomp(`git -C $ROOT rev-parse HEAD`)
end

function base_params(; crop)
    Params(
        crops = crop,
        baseline = "2007-2009",
        regions = "AgrimateEU28",
        extra_regions = Dict{String,Any}("Egypt" => "EGY"),
        start = Date(2000, 1, 1),
        ξ = 0.0,
    )
end

function cache_path(params)
    d = joinpath(OUTPUTROOT, "agrimate_cache")
    n1 = savename(params, "jld2"; savename_kwargs...)
    for n in (n1, "agrimate_" * n1)
        p = joinpath(d, n)
        isfile(p) && return p
    end
    return joinpath(d, n1)
end

function hexfloat(x::Float64)
    string(reinterpret(UInt64, x), base = 16, pad = 16)
end

function hexvec(x)
    join((hexfloat(float(v)) for v in x), ",")
end

const CROP_OF = Dict{UInt,String}()

function register_run!(crop, run)
    for prod in values(run.model.producers)
        CROP_OF[objectid(prod)] = crop
    end
end

function open_outputs(label, commit)
    mkpath(OUTDIR)
    dump_path = joinpath(OUTDIR, "dump_$(label).txt")
    mon_path = joinpath(OUTDIR, "monitor_$(label).csv")
    dump = open(dump_path, "w")
    mon = open(mon_path, "w")
    println(dump, "# commit $(commit)")
    println(mon, "# commit $(commit)")
    println(mon, "commit,run,crop,region,step,event,value,threshold")
    flush(dump)
    flush(mon)
    return dump, mon, dump_path, mon_path
end

function install_monitor!(mon, label, commit)
    pm = AgrimateModel.AgentsModule.ProducerModule
    pm.diag_log[] = function (kind, producer, t, value, threshold)
        crop = get(CROP_OF, objectid(producer), "unknown")
        println(mon, join((
            commit, label, crop, producer.id, t, string(kind),
            @sprintf("%.16g", value), @sprintf("%.16g", threshold),
        ), ","))
        flush(mon)
        return nothing
    end
    return pm
end

function write_header(io, commit, label, mode, crop)
    println(io, "# commit $(commit)")
    println(io, "label $(label)")
    println(io, "mode $(mode)")
    println(io, "focus $(crop)")
    println(io, "blas_threads $(BLAS.get_num_threads())")
    println(io, "nthreads $(Threads.nthreads())")
    println(io, "JULIA_HASH_SEED $(get(ENV, "JULIA_HASH_SEED", "unset"))")
    println(io, "OPENBLAS_NUM_THREADS $(get(ENV, "OPENBLAS_NUM_THREADS", "unset"))")
    flush(io)
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
        if isdefined(c, :crop_price_index)
            println(io, "val $t price_index $id $(hexfloat(float(c.crop_price_index)))")
        end
    end
    for (id, p) in m.producers
        for (name, fld) in (
            ("expected_sales", :expected_sales),
            ("expected_sales_domestic", :expected_sales_domestic),
            ("expected_sales_foreign", :expected_sales_foreign),
            ("expected_price", :expected_price),
            ("expected_price_domestic", :expected_price_domestic),
            ("expected_price_foreign", :expected_price_foreign),
        )
            isdefined(p, fld) || continue
            println(io, "val $t $name $id $(hexfloat(float(getfield(p, fld))))")
        end
        for (name, fld) in (
            ("optimal_sales", :optimal_sales),
            ("optimal_sales_domestic", :optimal_sales_domestic),
            ("optimal_sales_foreign", :optimal_sales_foreign),
        )
            isdefined(p, fld) || continue
            v = getfield(p, fld)
            println(io, "vec $t $name $id $(hexvec(v))")
        end
    end
    flush(io)
end

function load_and_step(crop; t_max, dump, focus)
    p = base_params(crop = crop)
    path = cache_path(p)
    isfile(path) || error("missing Nash cache $path")
    before = mtime(path)
    println("load $crop  $path")
    flush(stdout)
    init = initialize_crop(p, crop; inputroot = INPUTROOT, outputroot = OUTPUTROOT, verbose = false, use_cache = true)
    run = prepare_crop_run(init; t_max = t_max, inputroot = INPUTROOT)
    mtime(path) == before || error("cache was rewritten: $path")
    register_run!(crop, run)
    prod, cons = order_line(run)
    println(dump, "order 0 producer $prod")
    println(dump, "order 0 consumer $cons")
    flush(dump)
    for step in 1:t_max
        println("step $crop t=$step")
        flush(stdout)
        run_model!(run, 1; verbose = false, progressbar_name = crop)
        if focus
            dump_state(dump, run, step)
        end
    end
    return run
end

function run_coupled(dump)
    wheat = base_params(crop = "wheat")
    runs = Dict{String,Run}()
    for crop in ("wheat", "rice", "maize")
        p = deepcopy(wheat)
        p.crops = crop
        p.ξ = 0.0
        path = cache_path(p)
        before = mtime(path)
        println("load $crop  $path")
        flush(stdout)
        init = initialize_crop(p, crop; inputroot = INPUTROOT, outputroot = OUTPUTROOT, verbose = false, use_cache = true)
        runs[crop] = prepare_crop_run(init; t_max = 2, inputroot = INPUTROOT)
        mtime(path) == before || error("cache was rewritten: $path")
        register_run!(crop, runs[crop])
        prod, cons = order_line(runs[crop])
        println(dump, "order 0 $crop producer $prod")
        println(dump, "order 0 $crop consumer $cons")
    end
    for step in 1:2
        println("step coupled t=$step")
        flush(stdout)
        run_model_coupled!(runs, 1; ξ = 0.0, reference_index = Dict{Tuple{String,String,Int},Float64}(), verbose = false, progressbar_name = "COUPLED")
        for crop in ("wheat", "rice", "maize")
            println(dump, "crop $crop")
            dump_state(dump, runs[crop], step)
        end
    end
end

function main()
    length(ARGS) == 3 || error("usage: determinism_t2.jl {cold|after|coupled} CROP LABEL")
    mode = ARGS[1]
    crop = ARGS[2]
    label = ARGS[3]
    mode in ("cold", "after", "coupled") || error("unknown mode $mode")
    commit = git_commit_or_refuse()
    dump, mon, dump_path, mon_path = open_outputs(label, commit)
    write_header(dump, commit, label, mode, crop)
    install_monitor!(mon, label, commit)
    println("commit $commit")
    println("BLAS threads $(BLAS.get_num_threads())  julia threads $(Threads.nthreads())")
    println("writing $dump_path")
    flush(stdout)
    if mode == "cold"
        load_and_step(crop; t_max = 2, dump = dump, focus = true)
    elseif mode == "after"
        for prior in ("wheat", "rice")
            println("prior $prior")
            flush(stdout)
            load_and_step(prior; t_max = 2, dump = dump, focus = false)
        end
        load_and_step(crop; t_max = 2, dump = dump, focus = true)
    else
        run_coupled(dump)
    end
    println(mon, "# events_done")
    flush(mon)
    close(dump)
    close(mon)
    println("done $label")
end

main()
