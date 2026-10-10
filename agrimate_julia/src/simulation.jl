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
    
    @unpack start, N_year, initialization_tol, generalname = params
    @info "$timestamp_begin | AGRIMATE SIMULATION" source t_max params
        
    if isnothing(inputroot)
        inputroot = joinpath(get(ENV, "AGRIMATE_INPUT_ROOT", datadir()), "agrimate_input")
    end
    inputdir(path...) = joinpath(inputroot, path...)
    
    if isnothing(outputroot)
        outputroot = get(ENV, "AGRIMATE_OUTPUT_ROOT", datadir())
    end
    outputdir_csv(path...) = joinpath(outputroot, "csv", path...)
    outputdir_nc(path...) = joinpath(outputroot, "netcdf", path...)
    cachedir(path...) = joinpath(outputroot,"agrimate_cache",(!isnothing(processid) ? ("$processid",) : ())..., path...)

    @info "$(now()) | INITIALIZATION"
    flush(stderr)

    @unpack crops, baseline = params
    @unpack regions, extra_regions, flow_cutoff, production_cutoff = params

    crop = split(crops, ",")[1] |> string

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
    # harvest_distributions = Dict(
    #     String(row[:Area]) => [val for val in row[Between("1", "365")]] 
    #     for row in eachrow(df_harvest_distributions)
    # )
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

    
    baseline_transactions, baseline_production = apply_filter_if_producer_not_exist(baseline_transactions,baseline_production,baseline_harvests)

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
        # Update empirical params if a special value for a selected area is found in the suffix
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

    add_datetime_col!(output_baseline_data; start, N_year, timestep_field = :n)
    
    output_baseline_data[!, :value] = round.(output_baseline_data[!, :value]; digits=4)
    if isnothing(generalname)
        output_filename_csv = outputdir_csv(savename(params, !compress_output ? "csv" : "csv.gz"; savename_kwargs...))
        output_filename_nc = outputdir_nc(savename(params, "nc"; savename_kwargs...))
    else
        output_filename_csv = outputdir_csv(generalname*".csv")
        output_filename_nc = outputdir_nc(generalname*".nc")
    end
    
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

    @unpack N_hor = model.global_params

    @unpack production_anomalies = params

    if isa(production_anomalies, String)
        filename = savename(anomaly_name, (;source=production_anomalies, crop), "csv"; savename_kwargs...)
        df_harvest_anomalies = wload(inputdir(filename))
        df_harvest_anomalies = aggregate_areas(df_harvest_anomalies, df_region)


        filename = savename(compare_name, (;source=production_anomalies, crop), "csv"; savename_kwargs...)
        df_harvest_trends = wload(inputdir(filename)) 
        df_harvest_trends = aggregate_areas(df_harvest_trends, df_region)
        
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
        baseline_production, 
        baseline_harvests, 
        harvest_distributions,
        harvest_forcings,
        y_timeseries;
        start,
        t_max, 
        N_year, 
        N_hor,
    )

    @unpack export_restrictions = params

    if isa(export_restrictions, String)
        filename = savename("export-restrictions", (;source=export_restrictions, crop), "csv"; savename_kwargs...)
        df_export_restrictions = wload(inputdir(filename))
        df_export_restrictions = aggregate_export_restrictions(
            df_export_restrictions,
            df_region, 
            df_baseline_trade_flows_non_agg, 
            df_baseline_trade_flows
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

    run = initialize_model_run(model, input_data, init_data)

    N_chunk = ceil(Int, t_max / N_save)
    for chunk = 1:N_chunk
        t_start = (chunk - 1) * N_save + 1
        t_end = min(chunk * N_save, t_max)
        timesteps = t_end - t_start + 1
        # @info "$(now()) | Timesteps t ∈ [$t_start, $t_end] (t_max=$t_max)"
        # flush(stderr)

        run_model!(run, timesteps; verbose, progressbar_name = progressbar_name)

        output_data = copy(run.output_data)
        add_datetime_col!(output_data; start, N_year)
        output_data[!, :value] = round.(output_data[!, :value]; digits=4)
        combined_output_data = vcat(output_baseline_data, output_data)
        meta[:simulation_end] = now()
        if save_in_csv
            wsave(output_filename_csv, (;df=combined_output_data, meta))
            # @info "$(now()) | Saved baseline output: $output_filename_csv"
        end
        if save_in_netcf
            netcdf_save(output_filename_nc,combined_output_data,meta)
            # @info "$(now()) | Saved baseline output: $output_filename_nc"
        end
        
        
        # @info "$(now()) | Saved output: $output_filename_nc"
        # flush(stderr)
    end
end


"""Three-crop run (`GATE1_DESIGN.md`).

At `ξ = 0` (or `t_max = 0`) this is three independent `simulate` calls —
the identity. Coupled stepping (`step_coupled!` / `run_model_coupled!`)
is used only when `ξ ≠ 0` and `t_max > 0`, and then `reference_index`
must hold each purchaser's undisturbed price index: keys
`(crop, region, t)`.
"""
function simulate_coupled(
    params::Params = Params();
    crops = ("wheat", "rice", "maize"),
    ξ = nothing,
    t_max = 0,
    reference_index = Dict(),
    kwargs...,
)
    ξ_use = ξ === nothing ? params.ξ : Float64(ξ)
    @info "$(now()) | AGRIMATE-SHEAF COUPLED" crops ξ = ξ_use t_max
    if ξ_use != 0 && t_max > 0
        isempty(reference_index) && error(
            "simulate_coupled with ξ≠0 needs reference_index from undisturbed " *
            "single-crop runs (GATE1_DESIGN.md §3). Keys: (crop, region, t).",
        )
        error(
            "Coupled stepping is in step_coupled! / run_model_coupled!; " *
            "wiring three Runs into this wrapper is the next Gate 1 edit.",
        )
    end
    for crop in crops
        p = deepcopy(params)
        p.crops = String(crop)
        p.ξ = ξ_use
        simulate(p; t_max = t_max, kwargs...)
    end
end

