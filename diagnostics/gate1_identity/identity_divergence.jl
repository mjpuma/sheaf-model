# First divergence between a maize single-crop run and maize inside the
# ξ = 0 coupled setup. Stops at the first mismatched field.
#
# Does not retune, does not edit economics, and does not step past t = 2.
# Nash initialization is loaded from the identity cache (use_cache = true),
# the same files the 2026-10-10 singles wrote and the 2026-10-11 coupled
# run loaded. This script does not rewrite those files.
#
#   arch -x86_64 /Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia \
#     --project=agrimate_julia \
#     diagnostics/gate1_identity/identity_divergence.jl
#
#   # same, but only the cold maize single (no coupled run in the process):
#   ... identity_divergence.jl single
#
using DrWatson
@quickactivate "Agrimate"

using Dates
using LinearAlgebra
using Printf
using NCDatasets

include(srcdir("simulation.jl"))

const ROOT = dirname(dirname(dirname(@__FILE__)))
const INPUTROOT = joinpath(ROOT, "inputs", "generated", "agrimate_input_g1")
const OUTPUTROOT = joinpath(ROOT, "agrimate_julia", "data_g1prep_identity")
const CROPS = ("wheat", "rice", "maize")
const FOCUS = ("Argentina", "USA", "Southern Africa")

struct Hit
    step::Int
    field::String
    region::String
    single::String
    coupled::String
end

const HIT = Ref{Union{Nothing,Hit}}(nothing)

function note_hit(step, field, region, single, coupled)
    HIT[] === nothing || return
    HIT[] = Hit(step, field, region, string(single), string(coupled))
    println()
    println("FIRST MISMATCH")
    println("  step   = ", step < 0 ? "t=0 (after init, before any step)" : "t=$step (after that step)")
    println("  crop   = maize")
    println("  field  = $field")
    println("  region = $region")
    println("  single = $single")
    println("  coupled= $coupled")
    println()
    flush(stdout)
end

function sha12(path)
    isfile(path) || return "MISSING"
    split(read(`shasum -a 256 $path`, String))[1][1:12]
end

function nc_filename(crop)
    stem = crop == "wheat" ? "" : "_crops=$(crop)"
    "agrimate_baseline=2007-2009$(stem)_extra_regions=(Egypt=EGY)_regions=AgrimateEU28_start=2000-01-01.nc"
end

function cache_path(params)
    d = joinpath(OUTPUTROOT, "agrimate_cache")
    n1 = savename(params, "jld2"; savename_kwargs...)
    n2 = savename("agrimate", params, "jld2"; savename_kwargs...)
    for n in (n1, n2, "agrimate_" * n1)
        p = joinpath(d, n)
        isfile(p) && return p
    end
    return joinpath(d, n1)
end

function base_params(; crop = "wheat")
    Params(
        crops = crop,
        baseline = "2007-2009",
        regions = "AgrimateEU28",
        extra_regions = Dict{String,Any}("Egypt" => "EGY"),
        start = Date(2000, 1, 1),
        ξ = 0.0,
    )
end

function input_files(crop)
    b = "2007-2009"
    [
        "food-balance_baseline=$(b)_crop=$(crop).csv",
        "trade-flows_baseline=$(b)_crop=$(crop).csv",
        "harvest-distributions_crop=$(crop).csv",
        "parameters_baseline=$(b)_crop=$(crop)_source=empirical.csv",
        # Present on disk. The identity runs left production_anomalies and
        # export_restrictions as nothing, so these three are not read.
        "harvest-anomalies_crop=$(crop)_source=FAOsince-2005.csv",
        "harvest-trends_crop=$(crop)_source=FAOsince-2005.csv",
        "export-restrictions_crop=$(crop)_source=2007-2011.csv",
    ]
end

function provenance()
    println("=== 1. Provenance ===")
    println("current HEAD: ", readchomp(`git -C $ROOT rev-parse HEAD`))
    println("current branch: ", readchomp(`git -C $ROOT rev-parse --abbrev-ref HEAD`))
    println("input root:  $INPUTROOT")
    println("output root: $OUTPUTROOT")
    println("BLAS threads: ", BLAS.get_num_threads())
    println()
    println("Stored NetCDF attributes (identity run). Differences other than")
    println("script / simulation_begin / simulation_end are flagged.")
    skip = Set(["script", "simulation_begin", "simulation_end"])
    println()
    @printf("%-8s %-8s %-16s %-28s %-22s %-22s %-8s %-14s %-12s %s\n",
        "crop", "side", "gitcommit", "script", "begin", "end", "ξ", "anomalies", "restrictions", "crops attr")
    attr_by = Dict{String,Dict{String,String}}()
    for crop in CROPS
        fname = nc_filename(crop)
        for (side, sub) in (("single", ""), ("coupled", "coupled"))
            path = joinpath(OUTPUTROOT, "netcdf", sub, fname)
            ds = NCDataset(path)
            a = Dict(string(k) => string(ds.attrib[k]) for k in keys(ds.attrib))
            close(ds)
            attr_by["$crop/$side"] = a
            @printf("%-8s %-8s %-16s %-28s %-22s %-22s %-8s %-14s %-12s %s\n",
                crop, side,
                get(a, "gitcommit", "?")[1:min(end, 16)],
                get(a, "script", "?"),
                get(a, "simulation_begin", "?"),
                get(a, "simulation_end", "?"),
                get(a, "ξ", "?"),
                get(a, "production_anomalies", "?"),
                get(a, "export_restrictions", "?"),
                get(a, "crops", "?"),
            )
        end
    end
    println()
    println("Attribute diffs, single vs coupled (excluding script and clock):")
    any_diff = false
    for crop in CROPS
        s = attr_by["$crop/single"]
        c = attr_by["$crop/coupled"]
        keys_all = sort(collect(union(keys(s), keys(c))))
        for k in keys_all
            k in skip && continue
            sv = get(s, k, "<absent>")
            cv = get(c, k, "<absent>")
            if sv != cv
                any_diff = true
                println("  $crop  $k")
                println("    single  $sv")
                println("    coupled $cv")
            end
        end
    end
    any_diff || println("  none. Every Params field stored in the file matches.")
    println()
    println("Git commits differ from HEAD or between sides:")
    head = readchomp(`git -C $ROOT rev-parse --short=12 HEAD`)
    for crop in CROPS
        for side in ("single", "coupled")
            g = attr_by["$crop/$side"]["gitcommit"]
            println("  $crop $side  $g")
        end
    end
    println("  HEAD short $head  (stored tag is e9d5a14-dirty; this branch commits that tree)")
    println()
    println("Input files (sha256/12). Anomaly and restriction files were not")
    println("loaded: both sides have production_anomalies=nothing and export_restrictions=nothing.")
    for crop in CROPS
        println("  $crop")
        for name in input_files(crop)
            path = joinpath(INPUTROOT, name)
            println("    ", sha12(path), "  ", name)
        end
    end
    println()
    println("Nash cache that initialize_crop will load (use_cache=true):")
    for crop in CROPS
        p = base_params(crop = crop)
        path = cache_path(p)
        if isfile(path)
            m = unix2datetime(mtime(path))
            println("  $crop  $path")
            println("       mtime=$m  bytes=$(filesize(path))")
        else
            println("  $crop  NOT FOUND at $path")
        end
    end
    println()
    println("Scorer pairing (drivers/compare_g1_identity.jl matches by filename;")
    println("crop_of defaults to wheat only when the name lacks crops=rice/maize):")
    for crop in CROPS
        fname = nc_filename(crop)
        label = occursin("crops=rice", fname) ? "rice" : occursin("crops=maize", fname) ? "maize" : "wheat"
        stored = attr_by["$crop/single"]["crops"]
        println("  file crops=$(stored)  scorer label=$label  name=$(fname)")
        label == stored || println("    FLAG scorer label does not match the crops attribute")
    end
    println()
    flush(stdout)
end

function fget(obj, name)
    isdefined(obj, name) ? getfield(obj, name) : nothing
end

function pget(d, key)
    d[key]
end

function show_val(x)
    if x isa AbstractFloat
        return @sprintf("%.10g", x)
    elseif x isa AbstractVector{<:AbstractFloat}
        if length(x) > 8
            head = join([@sprintf("%.6g", v) for v in x[1:4]], ",")
            return "len=$(length(x)) [$(head),...]"
        end
        return "[" * join([@sprintf("%.6g", v) for v in x], ",") * "]"
    elseif x isa AbstractDict
        ks = sort(collect(keys(x)))
        parts = String[]
        for k in ks
            v = x[k]
            push!(parts, string(k) * "=" * (v isa AbstractFloat ? @sprintf("%.6g", v) : string(v)))
        end
        return "{" * join(parts, ",") * "}"
    elseif x isa AbstractVector
        return "[" * join(string.(x), ",") * "]"
    else
        return string(x)
    end
end

function differ(a, b)
    if a isa AbstractFloat && b isa AbstractFloat
        return !isequal(a, b)
    elseif a isa AbstractDict && b isa AbstractDict
        sort(string.(collect(keys(a)))) != sort(string.(collect(keys(b)))) && return true
        for k in keys(a)
            haskey(b, k) || return true
            differ(a[k], b[k]) && return true
        end
        return false
    elseif a isa AbstractVector && b isa AbstractVector
        length(a) != length(b) && return true
        for i in eachindex(a)
            differ(a[i], b[i]) && return true
        end
        return false
    else
        return !isequal(a, b)
    end
end

function check(step, field, region, a, b)
    HIT[] === nothing || return
    differ(a, b) || return
    extra = ""
    if a isa AbstractVector && b isa AbstractVector && length(a) == length(b)
        for i in eachindex(a)
            if differ(a[i], b[i])
                extra = " first index $i single=$(a[i]) coupled=$(b[i])"
                break
            end
        end
    elseif a isa AbstractVector && b isa AbstractVector
        extra = " length $(length(a)) vs $(length(b))"
    end
    note_hit(step, field, region, show_val(a) * extra, show_val(b))
end

function snapshot_aliases(runs)
    println("Shared mutable state across the three coupled models:")
    buckets = Dict{UInt,Vector{String}}()
    function note(obj, label)
        push!(get!(buckets, objectid(obj), String[]), label)
    end
    for crop in CROPS
        run = runs[crop]
        m = run.model
        note(m, "$crop model")
        note(m.producers, "$crop producers")
        note(m.consumers, "$crop consumers")
        note(m.global_params, "$crop model.global_params")
        note(run.input_data.harvests, "$crop harvests")
        note(run.input_data.expected_harvests, "$crop expected_harvests")
        note(run.input_data.export_restriction_dict, "$crop export_restriction_dict")
        gp = Set{UInt}()
        lp = Set{UInt}()
        cgp = Set{UInt}()
        clp = Set{UInt}()
        for (id, prod) in m.producers
            note(prod, "$crop producer $id")
            note(prod.global_params, "$crop p:$id global_params")
            note(prod.local_params, "$crop p:$id local_params")
            push!(gp, objectid(prod.global_params))
            push!(lp, objectid(prod.local_params))
        end
        for (id, cons) in m.consumers
            note(cons, "$crop consumer $id")
            note(cons.global_params, "$crop c:$id global_params")
            note(cons.local_params, "$crop c:$id local_params")
            push!(cgp, objectid(cons.global_params))
            push!(clp, objectid(cons.local_params))
            fget(cons, :demand_shares) === nothing || note(cons.demand_shares, "$crop c:$id demand_shares")
            fget(cons, :suppliers) === nothing || note(cons.suppliers, "$crop c:$id suppliers")
        end
        println("  $crop producers=$(length(m.producers)) distinct global_params=$(length(gp)) distinct local_params=$(length(lp))")
        println("  $crop consumers=$(length(m.consumers)) distinct global_params=$(length(cgp)) distinct local_params=$(length(clp))")
        println("  $crop Run.timestep=$(run.timestep)")
    end
    cross = 0
    within = 0
    for labels in values(buckets)
        length(labels) <= 1 && continue
        crops = Set(split(l, " ")[1] for l in labels)
        if length(crops) > 1
            cross += 1
            println("  CROSS-CROP ALIAS: ", join(labels, " == "))
        else
            within += 1
        end
    end
    println(cross == 0 ? "  no object is shared across crops" : "  cross-crop aliases: $cross")
    println("  within-crop aliases (same objectid used more than once inside one crop): $within")
    println("  timesteps: ", [runs[c].timestep for c in CROPS])
    println()
    flush(stdout)
end

function compare_inputs(step, single_run, coupled_run)
    sh = single_run.input_data.harvests
    ch = coupled_run.input_data.harvests
    check(step, "harvest input keys", "(all)", sort(collect(keys(sh))), sort(collect(keys(ch))))
    HIT[] === nothing || return
    for id in sort(collect(keys(sh)))
        check(step, "harvest input", id, sh[id], ch[id])
        HIT[] === nothing || return
    end
    se = single_run.input_data.expected_harvests
    ce = coupled_run.input_data.expected_harvests
    check(step, "expected_harvest keys", "(all)", sort(collect(keys(se))), sort(collect(keys(ce))))
    HIT[] === nothing || return
    for id in sort(collect(keys(se)))
        check(step, "expected_harvest", id, se[id], ce[id])
        HIT[] === nothing || return
    end
    check(step, "export_restriction_dict", "(all)",
        single_run.input_data.export_restriction_dict,
        coupled_run.input_data.export_restriction_dict)
end

function compare_models(step, single_run, coupled_run)
    sm = single_run.model
    cm = coupled_run.model
    check(step, "Run.timestep", "(clock)", single_run.timestep, coupled_run.timestep)
    check(step, "producer id order", "(all)", collect(keys(sm.producers)), collect(keys(cm.producers)))
    check(step, "consumer id order", "(all)", collect(keys(sm.consumers)), collect(keys(cm.consumers)))
    HIT[] === nothing || return
    compare_inputs(step, single_run, coupled_run)
    HIT[] === nothing || return
    for id in collect(keys(sm.consumers))
        s = sm.consumers[id]
        c = cm.consumers[id]
        check(step, "baseline price", id, fget(s, :baseline_price), fget(c, :baseline_price))
        check(step, "purchaser budget", id, fget(s, :budget), fget(c, :budget))
        check(step, "A_d_star", id, s.local_params[:A_d_star], c.local_params[:A_d_star])
        check(step, "A_c_star", id, s.local_params[:A_c_star], c.local_params[:A_c_star])
        check(step, "household budget", id, fget(s, :household_budget), fget(c, :household_budget))
        check(step, "consumer storage", id, fget(s, :storage), fget(c, :storage))
        check(step, "suppliers", id, fget(s, :suppliers), fget(c, :suppliers))
        ss = fget(s, :demand_shares)
        cc = fget(c, :demand_shares)
        if ss isa AbstractDict && cc isa AbstractDict
            check(step, "demand_shares key order", id, collect(keys(ss)), collect(keys(cc)))
        end
        check(step, "demand_shares", id, ss, cc)
        check(step, "annual_demand_shares", id, fget(s, :annual_demand_shares), fget(c, :annual_demand_shares))
        check(step, "consumer crop_price_index", id, fget(s, :crop_price_index), fget(c, :crop_price_index))
        HIT[] === nothing || return
    end
    for id in collect(keys(sm.producers))
        s = sm.producers[id]
        c = cm.producers[id]
        check(step, "producer storage", id, fget(s, :storage), fget(c, :storage))
        check(step, "producer α", id, s.local_params[:α], c.local_params[:α])
        check(step, "producer α_domestic", id, s.local_params[:α_domestic], c.local_params[:α_domestic])
        check(step, "producer α_foreign", id, s.local_params[:α_foreign], c.local_params[:α_foreign])
        check(step, "X_star", id, s.global_params[:X_star], c.global_params[:X_star])
        check(step, "X_star_domestic", id, s.local_params[:X_star_domestic], c.local_params[:X_star_domestic])
        check(step, "X_only_foreign", id, s.global_params[:X_only_foreign], c.global_params[:X_only_foreign])
        check(step, "X_avg", id, s.local_params[:X_avg], c.local_params[:X_avg])
        check(step, "optimal_sales_domestic", id, fget(s, :optimal_sales_domestic), fget(c, :optimal_sales_domestic))
        check(step, "optimal_sales_foreign", id, fget(s, :optimal_sales_foreign), fget(c, :optimal_sales_foreign))
        check(step, "expected_sales_domestic", id, fget(s, :expected_sales_domestic), fget(c, :expected_sales_domestic))
        check(step, "expected_price_domestic", id, fget(s, :expected_price_domestic), fget(c, :expected_price_domestic))
        check(step, "producer export_restrictions", id, fget(s, :export_restrictions), fget(c, :export_restrictions))
        HIT[] === nothing || return
    end
end

function focus_line(run, region)
    m = run.model
    haskey(m.producers, region) || return
    p = m.producers[region]
    c = m.consumers[region]
    ι = p.global_params[:ι]
    xavg = p.local_params[:X_avg]
    esd = fget(p, :expected_sales_domestic)
    epd = fget(p, :expected_price_domestic)
    dem = fget(c, :total_demand)
    @printf("    %-22s  X_avg=%.6g  ι*X_avg=%.6g  X_star_dom=%.6g  α_d=%.6g  E[sales_d]=%s  E[price_d]=%s  demand=%s\n",
        region, xavg, ι * xavg, p.local_params[:X_star_domestic], p.local_params[:α_domestic],
        esd === nothing ? "undef" : @sprintf("%.6g", esd),
        epd === nothing ? "undef" : @sprintf("%.6g", epd),
        dem === nothing ? "undef" : @sprintf("%.6g", dem),
    )
end

function print_focus(tag, run)
    println("  $tag")
    for region in FOCUS
        focus_line(run, region)
    end
    flush(stdout)
end

function build_runs()
    println("=== 2. Initialize (cache load, no Nash recompute) ===")
    println("single: Params(crops=maize) -> initialize_crop -> prepare_crop_run")
    println("coupled: deepcopy wheat Params, set crops, same two calls, wheat then rice then maize")
    flush(stdout)
    before = Dict(crop => mtime(cache_path(base_params(crop = crop))) for crop in CROPS)
    single_params = base_params(crop = "maize")
    println("maize single cache: ", cache_path(single_params))
    t0 = time()
    single_init = initialize_crop(single_params, "maize"; inputroot = INPUTROOT, outputroot = OUTPUTROOT, verbose = false, use_cache = true)
    single_run = prepare_crop_run(single_init; t_max = 2, inputroot = INPUTROOT)
    println(@sprintf("  maize single ready in %.1fs  producers=%d consumers=%d timestep=%d",
        time() - t0, length(single_run.model.producers), length(single_run.model.consumers), single_run.timestep))
    flush(stdout)

    wheat_params = base_params(crop = "wheat")
    runs = Dict{String,Run}()
    for crop in CROPS
        p = deepcopy(wheat_params)
        p.crops = crop
        p.ξ = 0.0
        println("coupled $crop cache: ", cache_path(p), "  params.crops=", p.crops)
        flush(stdout)
        t1 = time()
        init = initialize_crop(p, crop; inputroot = INPUTROOT, outputroot = OUTPUTROOT, verbose = false, use_cache = true)
        runs[crop] = prepare_crop_run(init; t_max = 2, inputroot = INPUTROOT)
        println(@sprintf("  %s ready in %.1fs  producers=%d timestep=%d",
            crop, time() - t1, length(runs[crop].model.producers), runs[crop].timestep))
        flush(stdout)
    end
    for crop in CROPS
        path = cache_path(base_params(crop = crop))
        mtime(path) == before[crop] || error("cache was rewritten: $path")
    end
    println("cache mtimes unchanged (loaded, not recomputed)")
    println()
    snapshot_aliases(runs)
    println("t = 0 field comparison, maize single vs maize inside the coupled setup")
    compare_models(-1, single_run, runs["maize"])
    if HIT[] === nothing
        println("t = 0 matches (inputs, budgets, shares, suppliers, α, X_star, storage, clocks).")
        print_focus("maize single t=0", single_run)
        print_focus("maize coupled t=0", runs["maize"])
    end
    println()
    flush(stdout)
    return single_run, runs
end

function nc_point(path, var, t, region)
    ds = NCDataset(path)
    regs = String.(collect(ds["region"][:]))
    ri = findfirst(==(region), regs)
    v = ds[var]
    dims = dimnames(v)
    A = Array(v)
    close(ds)
    idx = map(dims) do d
        if d == "time"
            t
        elseif d == "region"
            ri
        elseif d == "inner_annual_timestep"
            error("baseline var $var")
        else
            Colon()
        end
    end
    count(d -> d == "region", dims) == 1 || error("$var has regions dims $dims")
    return A[idx...]
end

function id_is(x, region)
    ismissing(x) && return false
    return x == region
end

function fresh_point(df, var, t, region; producer = false)
    rows = filter(df) do r
        r.variable == var && r.t == t && (producer ? id_is(r.producer, region) : id_is(r.consumer, region))
    end
    size(rows, 1) == 0 && return NaN
    return rows.value[1]
end

function compare_stored(single_run, nsteps)
    println("=== 4. Current maize single vs stored maize single (first $nsteps steps) ===")
    path = joinpath(OUTPUTROOT, "netcdf", nc_filename("maize"))
    vars = [
        ("expected price domestic", true),
        ("expected sales domestic", true),
        ("expected sales foreign", true),
        ("sales", true),
        ("producer storage", true),
        ("demand", false),
        ("consumer price", false),
        ("harvest", true),
    ]
    regions = String.(collect(keys(single_run.model.producers)))
    # consumers may include non-producers; use consumer keys for demand
    consumers = String.(collect(keys(single_run.model.consumers)))
    first = nothing
    for t in 1:nsteps
        first !== nothing && break
        for (var, isprod) in vars
            first !== nothing && break
            ids = isprod ? regions : consumers
            for region in ids
                got = fresh_point(single_run.output_data, var, t, region; producer = isprod)
                want = nc_point(path, var, t, region)
                rg = round(got; digits = 4)
                if isnan(rg) && isnan(want)
                    continue
                end
                if !isequal(rg, want) && abs(rg - want) > 5e-5
                    first = (t, var, region, rg, want, got)
                    break
                end
            end
        end
    end
    if first === nothing
        println("  stored maize single matches this commit through t=$nsteps (values rounded to 4 digits, as netcdf_save does).")
        println("  The 2026-10-10 maize single is not stale on these fields.")
    else
        t, var, region, rg, want, got = first
        println("  STORED SINGLE DIFFERS from a fresh 2-step run on this commit.")
        println("  t=$t  $var  $region")
        println("  fresh rounded=$(rg)  raw=$(got)  stored=$(want)")
        println("  The stored maize single is stale relative to this commit, or the step is not reproducible.")
    end
    println()
    flush(stdout)
end

function run_single_only()
    println("=== single-only (fresh process, no coupled stepping before it) ===")
    println("BLAS threads: ", BLAS.get_num_threads())
    flush(stdout)
    p = base_params(crop = "maize")
    path = cache_path(p)
    before = mtime(path)
    println("cache: $path")
    init = initialize_crop(p, "maize"; inputroot = INPUTROOT, outputroot = OUTPUTROOT, verbose = false, use_cache = true)
    run = prepare_crop_run(init; t_max = 2, inputroot = INPUTROOT)
    mtime(path) == before || error("cache was rewritten: $path")
    println("t=0 timestep=$(run.timestep) producers=$(length(run.model.producers))")
    print_focus("maize single t=0", run)
    for t in 1:2
        println("stepping maize single, step $t ...")
        flush(stdout)
        run_model!(run, 1; verbose = false, progressbar_name = "MAIZE")
        print_focus("maize single after t=$t", run)
        flush(stdout)
    end
    compare_stored(run, 2)
end

function main()
    if length(ARGS) >= 1 && ARGS[1] == "single"
        provenance()
        run_single_only()
        return
    end
    provenance()
    single_run, runs = build_runs()
    if HIT[] !== nothing
        println("Stopped before stepping. t = 0 already differs.")
        return
    end
    println("=== 3. Step maize alone and the coupled trio (ξ = 0, verbose off) ===")
    println("Coupled is stepped first so its NLopt calls are not preceded by the single's.")
    flush(stdout)
    for t in 1:2
        println("stepping coupled trio, step $t ...")
        flush(stdout)
        run_model_coupled!(runs, 1; ξ = 0.0, reference_index = Dict(), verbose = false, progressbar_name = "COUPLED")
        println("stepping maize single, step $t ...")
        flush(stdout)
        run_model!(single_run, 1; verbose = false, progressbar_name = "MAIZE")
        println("diff after step $t")
        compare_models(t, single_run, runs["maize"])
        print_focus("maize single after t=$t", single_run)
        print_focus("maize coupled after t=$t", runs["maize"])
        if HIT[] !== nothing
            println("Stopped. Later steps not run.")
            compare_stored(single_run, t)
            return
        end
        println("step $t matches.")
        println()
        flush(stdout)
    end
    println("No mismatch through t = 2.")
    compare_stored(single_run, 2)
end

main()
