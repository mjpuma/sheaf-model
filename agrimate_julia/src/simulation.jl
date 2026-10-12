using DrWatson
@quickactivate "Agrimate"

using Dates
using Parameters
using Statistics: median

using AgrimateModel


include(srcdir("params.jl"))
include(srcdir("regions.jl"))
include(srcdir("io.jl"))
include(srcdir("preprocess.jl"))


function resolve_io_roots(inputroot, outputroot)
    if isnothing(inputroot)
        inputroot = joinpath(get(ENV, "AGRIMATE_INPUT_ROOT", datadir()), "agrimate_input")
    end
    if isnothing(outputroot)
        outputroot = get(ENV, "AGRIMATE_OUTPUT_ROOT", datadir())
    end
    return inputroot, outputroot
end

function is_undisturbed(params::Params)
    return isnothing(params.production_anomalies) && isnothing(params.export_restrictions)
end

"""Per-crop setup through `initialize_model` (`GATE1_DESIGN.md` §5 #8)."""
function initialize_crop(
    params::Params,
    crop::AbstractString;
    inputroot,
    outputroot,
    verbose::Bool = true,
    use_cache = false,
    processid = nothing,
)
    crop = String(crop)
    @unpack start, N_year, initialization_tol, baseline = params
    @unpack regions, extra_regions, flow_cutoff, production_cutoff = params

    inputdir(path...) = joinpath(inputroot, path...)
    cachedir(path...) = joinpath(outputroot, "agrimate_cache", (!isnothing(processid) ? ("$processid",) : ())..., path...)

    df_region = make_regions_dataframe(get_regions(regions), extra_regions)
    filename = savename("food-balance", (;baseline, crop), "csv"; savename_kwargs...)
    df_baseline_food_balance_non_agg = wload(inputdir(filename))

    filename = savename("trade-flows", (;baseline, crop), "csv"; savename_kwargs...)
    df_baseline_trade_flows_non_agg = wload(inputdir(filename))

    filename = savename("harvest-distributions", (;crop), "csv"; savename_kwargs...)
    df_harvest_distributions = wload(inputdir(filename))
    df_harvest_distributions = aggregate_harvest_distributions(
        df_harvest_distributions,
        df_region;
        df_baseline_production=df_baseline_food_balance_non_agg[:, [:Area, :Production]],
    )
    harvest_distributions = Dict(
        String(row[:Area]) => [isnan(val) ? 0.0 : val for val in row[Between("1", "365")]]
        for row in eachrow(df_harvest_distributions)
    )
    df_baseline_food_balance = aggregate_areas(df_baseline_food_balance_non_agg, df_region)
    df_baseline_trade_flows = aggregate_areas(df_baseline_trade_flows_non_agg, df_region)
    df_baseline_trade_flows = infer_trade_flows(df_baseline_trade_flows, df_baseline_food_balance)

    baseline_trade_flows = Dict(
        (String(row[:Origin]), String(row[:Destination])) => row["Trade Flow"] / N_year
        for row in eachrow(df_baseline_trade_flows)
    )

    baseline_transactions = apply_cutoffs_to_trade_network(baseline_trade_flows; flow_cutoff, production_cutoff)
    (baseline_production, baseline_consumption) = get_baseline_production_and_consumption(baseline_transactions)
    baseline_harvests = generate_baseline_harvests(baseline_production, harvest_distributions; N_year)

    baseline_transactions, baseline_production = apply_filter_if_producer_not_exist(baseline_transactions, baseline_production, baseline_harvests)

    init_data = InitializationData(
        baseline_harvests,
        baseline_consumption,
        baseline_transactions,
    )

    @unpack ψ, A_d_star, A_c_star = params
    param_sources = unique(split(string(v), "_")[begin] for v in [ψ, A_d_star, A_c_star] if v isa Symbol)
    @assert length(param_sources) < 2
    if length(param_sources) == 1
        source = string(param_sources[1])
        filename = savename("parameters", (;baseline, crop, source), "csv"; savename_kwargs...)
        df_empirical_params = wload(inputdir(filename))
        for (col_name, value) in [
            "STU" => ψ,
            "A_d" => A_d_star,
            "A_c" => A_c_star,
        ]
            value = split(string(value), "_")
            length(value) == 1 && continue
            (area, value) = split(value[end], "=")
            df_empirical_params[findfirst(==(area), df_empirical_params.Area), col_name] = parse(Float64, value)
        end
        df_consumption = df_baseline_food_balance_non_agg[!, [:Area, :Consumption]]
        empirical_params = generate_empirical_params(params, df_empirical_params, df_consumption, df_region)
    elseif length(param_sources) == 0
        empirical_params = Dict()
    end

    init_dict, path = produce_or_load(
        cachedir(),
        params;
        force =! use_cache,
        savename_kwargs...
    ) do params
        flush(stderr)

        agrimate_params = AgrimateParams(;(field => getfield(params, field) for field in fieldnames(AgrimateParams))...)

        n_start = calculate_year_and_n(start; N_year)[2]

        (model, output_baseline_data) = initialize_model(
            init_data,
            agrimate_params;
            n_start,
            κ = 0.2,
            tol = (!isnothing(initialization_tol) ? initialization_tol : 1e-4),
            verbose,
            empirical_params,
        )

        return Dict("model" => model, "output_baseline_data" => output_baseline_data)

    end

    @unpack model, output_baseline_data = init_dict

    return (;
        crop,
        params,
        model,
        output_baseline_data,
        init_data,
        df_region,
        df_baseline_food_balance_non_agg,
        df_baseline_trade_flows,
        df_baseline_trade_flows_non_agg,
        harvest_distributions,
        baseline_production,
        baseline_harvests,
    )
end

function prepare_crop_run(
    init;
    t_max,
    inputroot,
    anomaly_name = "harvest-anomalies",
    compare_name = "harvest-trends",
)
    params = init.params
    crop = init.crop
    @unpack start, N_year, production_anomalies, export_restrictions = params
    @unpack N_hor = init.model.global_params
    inputdir(path...) = joinpath(inputroot, path...)

    if isa(production_anomalies, String)
        filename = savename(anomaly_name, (;source=production_anomalies, crop), "csv"; savename_kwargs...)
        df_harvest_anomalies = wload(inputdir(filename))
        df_harvest_anomalies = aggregate_areas(df_harvest_anomalies, init.df_region)

        filename = savename(compare_name, (;source=production_anomalies, crop), "csv"; savename_kwargs...)
        df_harvest_trends = wload(inputdir(filename))
        df_harvest_trends = aggregate_areas(df_harvest_trends, init.df_region)

        date_start = timestep_to_datetime(0.5; start, N_year) |> Date
        date_end = timestep_to_datetime(t_max + N_hor + 0.5; start, N_year) |> Date
        (year_start, day_start) = calculate_year_and_n(date_start; N_year=365)
        (year_end, day_end) = calculate_year_and_n(date_end; N_year=365)

        @assert "$year_start-$day_start" in names(df_harvest_trends)
        if "$year_end-$day_end" in names(df_harvest_trends)
            columns = Between("$year_start-$day_start", "$year_end-$day_end")
            missing_days = 0
        else
            (last_year, last_day) = parse.(Int, split(names(df_harvest_trends)[end], "-"))
            columns = Between("$year_start-$day_start", "$last_year-$last_day")
            missing_days = 365 * (year_end - last_year) + (day_end - last_day)
        end

        harvest_anomalies = Dict(
            String(row[:Area]) => [val for val in row[columns]]
            for row in eachrow(df_harvest_anomalies)
        )
        harvest_trends = Dict(
            String(row[:Area]) => [val for val in row[columns]]
            for row in eachrow(df_harvest_trends)
        )

        harvest_forcings = Dict(
            area => vcat(
                replace(1 .+ harvest_anomalies[area] ./ harvest_trends[area], NaN => 1., Inf => 1., -Inf => 1.),
                ones(missing_days),
            )
            for area in keys(harvest_trends)
        )

        y_timeseries = date_to_fractional_year(date_start):(1/365):date_to_fractional_year(date_end) |> collect
    else
        harvest_forcings = nothing
        y_timeseries = nothing
    end

    harvests = generate_harvests(
        production_anomalies,
        init.baseline_production,
        init.baseline_harvests,
        init.harvest_distributions,
        harvest_forcings,
        y_timeseries;
        start,
        t_max,
        N_year,
        N_hor,
    )

    if isa(export_restrictions, String)
        filename = savename("export-restrictions", (;source=export_restrictions, crop), "csv"; savename_kwargs...)
        df_export_restrictions = wload(inputdir(filename))
        df_export_restrictions = aggregate_export_restrictions(
            df_export_restrictions,
            init.df_region,
            init.df_baseline_trade_flows_non_agg,
            init.df_baseline_trade_flows,
        )
        export_restrictions = [
            String(row[:Exporter]) => Dict(
                :from => row[:From],
                :to => row[:To],
                :value => row[:Value],
            )
            for row in eachrow(df_export_restrictions)
        ]
    end
    export_restriction_intervals = generate_export_restriction_intervals(export_restrictions; start, N_year)
    export_restriction_dict = generate_export_restriction_dict(export_restriction_intervals)

    input_data = InputData(
        harvests,
        export_restriction_intervals,
        export_restriction_dict,
    )

    return initialize_model_run(init.model, input_data, init.init_data)
end

function crop_output_paths(
    params::Params,
    outputroot;
    compress_output = false,
    coupled = false,
)
    @unpack generalname = params
    outputdir_csv(path...) = joinpath(outputroot, "csv", path...)
    outputdir_nc(path...) = joinpath(outputroot, "netcdf", path...)
    sub = coupled ? ("coupled",) : ()
    if isnothing(generalname)
        csv = outputdir_csv(sub..., savename(params, !compress_output ? "csv" : "csv.gz"; savename_kwargs...))
        nc = outputdir_nc(sub..., savename(params, "nc"; savename_kwargs...))
    else
        csv = outputdir_csv(sub..., generalname * ".csv")
        nc = outputdir_nc(sub..., generalname * ".nc")
    end
    mkpath(dirname(csv))
    mkpath(dirname(nc))
    return csv, nc
end

function save_run_outputs!(
    run,
    output_baseline_data,
    meta,
    params::Params;
    output_filename_csv,
    output_filename_nc,
    save_in_csv,
    save_in_netcf,
)
    @unpack start, N_year = params
    output_data = copy(run.output_data)
    add_datetime_col!(output_data; start, N_year)
    output_data[!, :value] = round.(output_data[!, :value]; digits=4)
    combined_output_data = vcat(output_baseline_data, output_data)
    meta[:simulation_end] = now()
    if save_in_csv
        wsave(output_filename_csv, (;df=combined_output_data, meta))
    end
    if save_in_netcf
        netcdf_save(output_filename_nc, combined_output_data, meta)
    end
    return combined_output_data
end

function maybe_save_reference_index(init, run, outputroot)
    is_undisturbed(init.params) || return nothing
    isempty(run.price_index_data) && return nothing
    path = reference_index_path(outputroot, init.crop)
    save_reference_index(path, init.crop, run.price_index_data)
    @info "$(now()) | Saved undisturbed purchaser index: $path"
    return path
end


function simulate(params::Params = Params(); 
    t_max = 0, 
    N_save = 24,
    verbose::Bool = true, 
    inputroot = nothing, 
    outputroot = nothing,
    compress_output = false,
    use_cache = false, 
    source = @source,
    processid = nothing,
    save_in_netcf = true,
    save_in_csv = false,
    progressbar_name = "RUN",
    anomaly_name = "harvest-anomalies",
    compare_name = "harvest-trends",
)
    timestamp_begin = now()
    meta = Dict(:params=>struct2dict(params), :simulation_begin=>timestamp_begin)
    tag!(meta; source)

    @unpack start, N_year, generalname = params
    @info "$timestamp_begin | AGRIMATE SIMULATION" source t_max params

    inputroot, outputroot = resolve_io_roots(inputroot, outputroot)

    @info "$(now()) | INITIALIZATION"
    flush(stderr)

    crop = split(params.crops, ",")[1] |> string
    init = initialize_crop(
        params, crop;
        inputroot, outputroot, verbose, use_cache, processid,
    )
    output_baseline_data = init.output_baseline_data

    add_datetime_col!(output_baseline_data; start, N_year, timestep_field = :n)
    output_baseline_data[!, :value] = round.(output_baseline_data[!, :value]; digits=4)
    output_filename_csv, output_filename_nc = crop_output_paths(
        params, outputroot; compress_output, coupled = false,
    )

    meta[:simulation_end] = now()
    if save_in_csv
        wsave(output_filename_csv, (;df=output_baseline_data, meta))
        @info "$(now()) | Saved baseline output: $output_filename_csv"
    end
    if save_in_netcf
        netcdf_save(output_filename_nc, output_baseline_data, meta)
        @info "$(now()) | Saved baseline output: $output_filename_nc"
    end

    if t_max == 0
        return
    end

    @info "$(now()) | RUN"
    flush(stderr)

    run = prepare_crop_run(
        init;
        t_max, inputroot, anomaly_name, compare_name,
    )

    N_chunk = ceil(Int, t_max / N_save)
    for chunk = 1:N_chunk
        t_start = (chunk - 1) * N_save + 1
        t_end = min(chunk * N_save, t_max)
        timesteps = t_end - t_start + 1
        run_model!(run, timesteps; verbose, progressbar_name = progressbar_name)
        save_run_outputs!(
            run, output_baseline_data, meta, params;
            output_filename_csv, output_filename_nc, save_in_csv, save_in_netcf,
        )
    end
    maybe_save_reference_index(init, run, outputroot)
end


"""Three-crop run (`GATE1_DESIGN.md`).

`t_max = 0` is three independent smokes. `t_max > 0` initializes one
`Run` per crop, checks that `start` and `N_year` match, loads
undisturbed purchaser indices (Pbar) when `ξ ≠ 0`, and steps with
`run_model_coupled!`. Coupled NetCDF goes under `netcdf/coupled/` so it
does not overwrite a single-crop file.
"""
function simulate_coupled(
    params::Params = Params();
    crops = ("wheat", "rice", "maize"),
    ξ = nothing,
    t_max = 0,
    reference_index = Dict(),
    reference_root = nothing,
    N_save = 24,
    verbose::Bool = true,
    inputroot = nothing,
    outputroot = nothing,
    compress_output = false,
    use_cache = false,
    source = @source,
    processid = nothing,
    save_in_netcf = true,
    save_in_csv = false,
    progressbar_name = "COUPLED",
    anomaly_name = "harvest-anomalies",
    compare_name = "harvest-trends",
)
    ξ_use = ξ === nothing ? params.ξ : Float64(ξ)
    @info "$(now()) | AGRIMATE-SHEAF COUPLED" crops ξ = ξ_use t_max
    inputroot, outputroot = resolve_io_roots(inputroot, outputroot)
    if isnothing(reference_root)
        reference_root = outputroot
    end

    if t_max == 0
        for crop in crops
            p = deepcopy(params)
            p.crops = String(crop)
            p.ξ = ξ_use
            simulate(
                p;
                t_max = 0,
                N_save, verbose, inputroot, outputroot, compress_output,
                use_cache, source, processid, save_in_netcf, save_in_csv,
                progressbar_name, anomaly_name, compare_name,
            )
        end
        return
    end

    inits = Dict{String,Any}()
    runs = Dict{String,Run}()
    metas = Dict{String,Any}()
    paths = Dict{String,Tuple{String,String}}()
    for crop in crops
        g = String(crop)
        p = deepcopy(params)
        p.crops = g
        p.ξ = ξ_use
        timestamp_begin = now()
        meta = Dict(:params=>struct2dict(p), :simulation_begin=>timestamp_begin)
        tag!(meta; source)
        @info "$(now()) | INITIALIZATION $g"
        flush(stderr)
        init = initialize_crop(
            p, g;
            inputroot, outputroot, verbose, use_cache, processid,
        )
        output_baseline_data = init.output_baseline_data
        add_datetime_col!(output_baseline_data; start = p.start, N_year = p.N_year, timestep_field = :n)
        output_baseline_data[!, :value] = round.(output_baseline_data[!, :value]; digits=4)
        csv_path, nc_path = crop_output_paths(p, outputroot; compress_output, coupled = true)
        meta[:simulation_end] = now()
        if save_in_csv
            wsave(csv_path, (;df=output_baseline_data, meta))
        end
        if save_in_netcf
            netcdf_save(nc_path, output_baseline_data, meta)
        end
        runs[g] = prepare_crop_run(
            init;
            t_max, inputroot, anomaly_name, compare_name,
        )
        inits[g] = init
        metas[g] = meta
        paths[g] = (csv_path, nc_path)
    end

    assert_coupled_clocks(
        (inits[String(c)].params.start for c in crops),
        (inits[String(c)].params.N_year for c in crops),
    )
    n_years = unique(init.model.global_params[:N_year] for init in values(inits))
    length(n_years) == 1 || error("coupled models have different N_year: $n_years")

    ref = reference_index
    if ξ_use != 0
        if isempty(ref)
            ref = load_reference_index(reference_root, crops)
        end
        assert_reference_coverage(ref, crops, t_max)
    end

    @info "$(now()) | RUN COUPLED" ξ = ξ_use
    flush(stderr)
    N_chunk = ceil(Int, t_max / N_save)
    for chunk = 1:N_chunk
        t_start = (chunk - 1) * N_save + 1
        t_end = min(chunk * N_save, t_max)
        timesteps = t_end - t_start + 1
        run_model_coupled!(
            runs, timesteps;
            ξ = ξ_use, reference_index = ref, verbose, progressbar_name,
        )
        for crop in crops
            g = String(crop)
            csv_path, nc_path = paths[g]
            save_run_outputs!(
                runs[g], inits[g].output_baseline_data, metas[g], inits[g].params;
                output_filename_csv = csv_path,
                output_filename_nc = nc_path,
                save_in_csv, save_in_netcf,
            )
        end
    end
end

