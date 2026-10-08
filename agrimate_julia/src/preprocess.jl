using Interpolations
using QuadGK
using Dates
using DataFrames


function make_regions_dataframe(regions::AbstractDict, extra_regions = nothing)
    df_region = DataFrame(Area=String[], Region=String[])
    for (region, areas) in regions
        for area in areas
            push!(df_region, [area, region])
        end
    end
    all_areas = [area for area in df_region[:, :Area]]
    if !isnothing(extra_regions)
        for (region, areas) in extra_regions
            areas = split(areas, ",")
            for area in areas
                if area in all_areas
                    df_region[findfirst(==(area), df_region[:, :Area]), :Region] = region
                else
                    push!(df_region, [area, region])
                end
            end
        end
    end
    return df_region
end


function aggregate_areas(df, df_region)
    if :Area in propertynames(df)
        df = leftjoin(df, df_region, on=:Area)
        df = filter(row -> !ismissing(row[:Region]), df)
        @assert nrow(df[ismissing.(df[:, :Region]), :]) == 0
        df = rename(df[:, Not(:Area)], :Region => :Area)
        gdf = groupby(df, :Area)
        columns = valuecols(gdf)
        df = combine(gdf, columns .=> sum .=> columns)
        df = select(df, vcat(:Area, columns))
        df = sort(df, :Area)
        return df
    end
    if (:Origin in propertynames(df)) && (:Destination in propertynames(df))
        df = leftjoin(
            df, 
            df_region, 
            on=(:Origin => :Area), 
            renamecols=(identity => col -> :OriginRegion), 
        )
        df = leftjoin(
            df, 
            df_region, 
            on=(:Destination => :Area), 
            renamecols=(identity => col -> :DestinationRegion), 
        )
        @assert nrow(df[ismissing.(df[:, :OriginRegion]), :]) == 0
        @assert nrow(df[ismissing.(df[:, :DestinationRegion]), :]) == 0
        df = rename(
            df[:, Not([:Origin, :Destination])], 
            :OriginRegion => :Origin, 
            :DestinationRegion => :Destination
        )
        gdf = groupby(df, [:Origin, :Destination])
        columns = valuecols(gdf)
        df = combine(gdf, columns .=> sum .=> columns)
        df = select(df, vcat(:Origin, :Destination, columns))
        df = sort(df, [:Origin, :Destination])
        return df
    end
end


function generate_empirical_params(params, df_empirical_params, df_consumption, df_region)
    empirical_params = Dict()

    @unpack ψ, A_d_star, A_c_star = params
    col_name = Dict(:ψ => "STU", :A_d_star => "A_d", :A_c_star => "A_c")        
    for (param, value) in Dict(pairs((;ψ, A_d_star, A_c_star)))
        !(value isa Symbol) && continue
        df_param = select(df_empirical_params, :Area, col_name[param] => param)
        
        df_param = leftjoin(df_param, df_consumption, on = :Area)
        df_param = leftjoin(df_param, df_region, on = :Area)
        
        # Impute missing values by medians
        global_median = median(skipmissing(df_param[!, param]))
        df_param = transform(
            groupby(df_param, :Region),
            param => (
                x -> coalesce.(x, isempty(skipmissing(x)) ? missing : median(skipmissing(x)))
            ) => param,
        )

        df_param[!, param] = coalesce.(df_param[!, param], global_median)

        # Average weighted by consumption
        df_param[!, param] .*= df_param[!, :Consumption]
        df_param = combine(
            groupby(df_param, :Region),
            param => sum => param,
            :Consumption => sum => :Consumption,
        )
        df_param[!, param] ./= df_param[!, :Consumption]
        df_param = rename(df_param, :Region => :Area)
        
        empirical_params[param] = Dict(row[:Area] => round(row[param]; digits=4) for row in eachrow(df_param))
    end 
    return empirical_params
end


function aggregate_export_restrictions(
    df_export_restrictions,
    df_region, 
    df_baseline_trade_flows_non_agg, 
    df_baseline_trade_flows_agg
)
    df = leftjoin(df_export_restrictions, df_region, on = :Exporter => :Area)
    for row in eachrow(df)
        # Sum exports from the area going outside of the region's area
        df_e_non_agg = df_baseline_trade_flows_non_agg[df_baseline_trade_flows_non_agg.Origin .== row[:Exporter], :]
        df_e_non_agg = leftjoin(df_e_non_agg, df_region, on = :Destination => :Area)

        export_area = sum(df_e_non_agg[df_e_non_agg.Region .!= row[:Region], "Trade Flow"])
        # Sum total exports of the region
        df_e_agg = df_baseline_trade_flows_agg[df_baseline_trade_flows_agg.Origin .== row[:Region], :]
        export_region = sum(df_e_agg[df_e_agg.Destination .!= row[:Region], "Trade Flow"])

        export_fraction = (export_region > 0 ? export_area / export_region : 0)
        row[:Value] *= export_fraction
    end
    df = select(df, :Region => :Exporter, :From, :To, :Value)
    df = df[df.Value .> 0, :]
    df = sort(df, [:Exporter, :From, :To])

    # Resolve overlapping policies
    dfs = []
    contains(start1, end1, start2, end2) = (start1 <= start2) && (end2 <= end1)
    for (key, df) in pairs(groupby(df, :Exporter))
        # Define periods
        middates = sort(vcat(df.From, df.To))
        periods = [(first(middates), first(middates))]
        for i in 2:length(middates)
            push!(periods, (middates[i - 1] + Dates.Day(1), middates[i] - Dates.Day(1)))
            push!(periods, (middates[i], middates[i]))
        end
        # Attribute policy magnitude to each period
        values = zeros(length(periods))
        for row in eachrow(df)
            for i in 1:length(periods)
                if contains(row.From, row.To, periods[i]...)
                    values[i] += row.Value
                end
            end
        end

        # Merge / remove periods
        final_periods = [first(periods)]
        final_values = [first(values)]
        not_hit_zero = true
        for (period, value) in zip(periods[2:end], values[2:end])
            if final_values[end] == value
                if not_hit_zero
                    final_periods[end] = (final_periods[end][1], period[2])
                else
                    push!(final_periods, (period[1], period[2]))
                    push!(final_values, value)
                    not_hit_zero = true
                end
            elseif value == 0
                not_hit_zero = false
            elseif value > 0
                push!(final_periods, (period[1], period[2]))
                push!(final_values, value)
            end
        end

        # Create a final data frame
        df = DataFrame(
            :Exporter => fill(key.Exporter, length(final_periods)),
            :From => first.(final_periods), 
            :To => last.(final_periods),
            :Value => min.(final_values, 1.),
        )
        push!(dfs, df)
    end

    df = vcat(dfs...)

    # Assure there are no overlaps
    overlap(start1, end1, start2, end2) = (start1 <= end2) && (start2 <= end1)
    for (key, subdf) in pairs(groupby(df, :Exporter))
        for i = 1:nrow(subdf)-1
            @assert !overlap(subdf[i, :From], subdf[i, :To], subdf[i + 1, :From], subdf[i + 1, :To]) "Policy overlap $(key.Exporter)"
        end
    end


    return df
end



function aggregate_harvest_distributions(df_harvest_distributions, df_region; df_baseline_production)
    df_harvest_distributions = leftjoin(df_harvest_distributions, df_baseline_production, on=:Area)
    df_harvest_distributions[!, :Production] = coalesce.(df_harvest_distributions[:, :Production], 0)
    df_harvest_distributions[!, Between("1", "365")] .*= df_harvest_distributions[:, :Production]
    df_harvest_distributions = aggregate_areas(df_harvest_distributions, df_region)
    df_harvest_distributions[!, Between("1", "365")] ./= df_harvest_distributions[:, :Production]
    return df_harvest_distributions
end


function infer_trade_flows(df_trade_flows, df_food_balance)
    df_trade_flows = df_trade_flows[
        df_trade_flows[:, :Origin] .!= df_trade_flows[:, :Destination], :]

    df_exports = rename(
        combine(
            groupby(df_trade_flows, :Origin), 
            "Trade Flow" => sum => "Exports (harmonized)",
        ),
        :Origin => :Area, 
    )
    df_imports = rename(
        combine(
            groupby(df_trade_flows, :Destination),
            "Trade Flow" => sum => "Imports (harmonized)"
        ),
        :Destination => :Area,
    ) 

    df_food_balance = df_food_balance[:, Not(["Exports (harmonized)", "Imports (harmonized)"])]
    df_food_balance = leftjoin(df_food_balance, df_imports, on=:Area)
    df_food_balance = leftjoin(df_food_balance, df_exports, on=:Area)
    df_food_balance = coalesce.(df_food_balance, 0)
    disallowmissing!(df_food_balance)

    for row in eachrow(df_food_balance)
        area = row[:Area]
        internal_flow = row["Consumption"] - row["Imports (harmonized)"] - row["Imports (non-harmonized)"]
        if internal_flow < 0
            @warn (
                "Inferred internal flow for $area: $(round(internal_flow,digits=2)) "
                *"(% consumption: $(round(internal_flow/row.Consumption*100,digits=2))). Setting it to zero."
            )
            continue
        end
        push!(df_trade_flows, [area, area, internal_flow])
    end
    return df_trade_flows
end


function generate_baseline_harvest_timeseries(
    production, 
    harvest_distribution::Vector{Float64}; 
    N_year = 365,
)
    @assert length(harvest_distribution) == 365
    harvest_density = LinearInterpolation(
        0:366,
        vcat(
            harvest_distribution[end],
            harvest_distribution,
            harvest_distribution[begin],
        ),
    )
    d = 365 / N_year
    harvests = Vector{Float64}(undef, N_year)
    for n = 1:N_year
        integral, err = quadgk(harvest_density, (n - 1) * d + 0.5, n * d + 0.5)
        if !isfinite(integral)
            integral = 0.0
        end
        harvests[n] = integral
    end
    s = sum(harvests)
    # Zero-production regions (rice: Canada, Rest of Oceania) arrive here with
    # an all-zero calendar: aggregate_harvest_distributions does 0/0, then
    # simulation.jl maps NaN → 0. production / 0 makes every harvest NaN,
    # X_star NaN, and Nash never converges. Wheat never hit this.
    if !isfinite(s) || s <= 0 || !isfinite(production)
        return zeros(Float64, N_year)
    end
    harvests .*= production / s
    return harvests
end


function generate_forced_harvest_timeseries(
    production,
    harvest_distribution::Vector{Float64},
    forcing_timeseries::Vector{Float64},
    y_timeseries::Vector{Float64};
    year_start,
    n_start,
    t_max,
    N_hor,
    N_year
)

    @assert length(harvest_distribution) == 365
    harvest_timeseries = Vector{Float64}(undef, length(forcing_timeseries))
    for i = 1:length(forcing_timeseries)
        n = mod(floor(Int, y_timeseries[i] * 365) + 1, 1:365)
        harvest_timeseries[i] = production * harvest_distribution[n] * forcing_timeseries[i]
    end

    harvest_density = LinearInterpolation(
        y_timeseries .* 365,
        harvest_timeseries,
        extrapolation_bc = Line()
    )

    y0 = calculate_y0(year_start, n_start; N_year)
    d = 365 / N_year
    
    harvests = Vector{Float64}(undef, t_max+N_hor)
    for t = 1:t_max+N_hor
        integral, err = quadgk(harvest_density, y0 * 365 + (t - 1) * d, y0 * 365 + t * d)

        harvests[t] = integral
    end
    return harvests
end


function get_baseline_production_and_consumption(baseline_transactions)
    baseline_production = Dict{String,Float64}()
    baseline_consumption = Dict{String,Float64}()
    for (partners, flow) in baseline_transactions
        (seller, buyer) = partners
        seller in keys(baseline_production) ? (baseline_production[seller] += flow) : (baseline_production[seller] = flow)
        buyer in keys(baseline_consumption) ? (baseline_consumption[buyer] += flow) : (baseline_consumption[buyer] = flow)
    end
    return baseline_production, baseline_consumption
end


function apply_cutoffs_to_trade_network(baseline_transactions; flow_cutoff, production_cutoff)
    (baseline_production, baseline_consumption) = get_baseline_production_and_consumption(baseline_transactions)
    total_production = sum(values(baseline_production))
    pairs_to_remove = Set()
    for (pair, flow) in baseline_transactions
        (seller, buyer) = pair
        # Trade flow cutoff
        if (flow / baseline_production[seller] < flow_cutoff) & (flow / baseline_consumption[buyer] < flow_cutoff)
            push!(pairs_to_remove, pair)
        end
        # Production cutoff
        if baseline_production[seller] / total_production < production_cutoff
            push!(pairs_to_remove, pair)
        end
    end
    baseline_transactions = Dict(pair => flow for (pair, flow) in baseline_transactions if pair ∉ pairs_to_remove)
    return baseline_transactions
end


function generate_baseline_harvests(baseline_production, harvest_distributions; N_year)

    # baseline_harvests = Dict(
    #     String(area) => generate_baseline_harvest_timeseries(
    #         baseline_production[area] * N_year,
    #         harvest_distributions[area],
    #         N_year = N_year,
    #     ) for area in keys(baseline_production)
    # )
#     baseline_harvests = Dict(
#     String(area) => (
#         if haskey(baseline_production, area) && haskey(harvest_distributions, area)
#             generate_baseline_harvest_timeseries(
#                 baseline_production[area] * N_year,
#                 harvest_distributions[area],
#                 N_year = N_year,
#             )
#         else
#             zeros(Float64, N_year)
#         end
#     ) for area in keys(baseline_production)
# )
    baseline_harvests = Dict{String,Vector{Float64}}()
    for area in filter(a -> haskey(baseline_production, a) && haskey(harvest_distributions, a), keys(baseline_production))
        h = generate_baseline_harvest_timeseries(
            baseline_production[area] * N_year,
            harvest_distributions[area],
            N_year = N_year,
        )
        # A producer with X_avg = 0 still NaNs Nash (`./ X_avg`). Drop them;
        # apply_filter_if_producer_not_exist removes their sales. They remain
        # consumers if they import.
        if any(!isfinite, h) || sum(h) <= 0
            continue
        end
        baseline_harvests[String(area)] = h
    end
    return baseline_harvests
end

function apply_filter_if_producer_not_exist(baseline_transactions,baseline_production,baseline_harvests)
    # Filter baseline_transactions based on the keys of baseline_harvests
    filtered_transactions = Dict(
        k => v for (k,v) in baseline_transactions if k[1] in keys(baseline_harvests)
    )
    filtered_production = Dict(
        k => v for (k,v) in baseline_production if k in keys(baseline_harvests)
    )
    return filtered_transactions, filtered_production
end


function generate_harvests(
    production_anomalies, 
    baseline_production, 
    baseline_harvests, 
    harvest_distributions, 
    harvest_forcings = nothing,
    y_timeseries = nothing;
    start,
    t_max, 
    N_year, 
    N_hor,
)
    
    (year_start, n_start) = calculate_year_and_n(start; N_year)
    if isnothing(harvest_forcings)
        harvests = Dict{String,Vector{Float64}}()
        for (area, baseline_harvest) in baseline_harvests
            harvests[area] = Vector{Float64}(undef, t_max + N_hor)
            for t = 1:t_max+N_hor
                harvests[area][t] = baseline_harvest[mod(t + n_start - 1, 1:N_year)]
            end
        end
        if !isnothing(production_anomalies)
            # Stylized forcing scenarios
            for (area, forcing) in production_anomalies
                t_start = date_to_timestep(forcing[:from]; start, N_year)
                t_end = date_to_timestep(forcing[:to]; start, N_year)
                harvests[area][t_start:t_end] .*= forcing[:value]
            end
        end
    else
        # harvests = Dict(
        #     area => generate_forced_harvest_timeseries(
        #         baseline_production[area] .* N_year,
        #         harvest_distributions[area],
        #         harvest_forcings[area],
        #         y_timeseries;
        #         year_start,
        #         n_start,
        #         N_year,
        #         t_max,
        #         N_hor
        #     ) for area in keys(baseline_production)
        # )
        harvests = Dict(
            area => haskey(harvest_forcings, area) ? 
                generate_forced_harvest_timeseries(
                    baseline_production[area] .* N_year,
                    harvest_distributions[area],
                    harvest_forcings[area],
                    y_timeseries;
                    year_start,
                    n_start,
                    N_year,
                    t_max,
                    N_hor
            ) : 
            repeat([baseline_production[area] * N_year], t_max + N_hor)
            for area in keys(baseline_production)
        )
    end
    return harvests
end


function generate_export_restriction_intervals(export_restrictions; start, N_year)
    export_restriction_intervals = Vector{Pair{Tuple{Int,Int},Tuple{String,Float64}}}()
        if !isnothing(export_restrictions)
            for (area, forcing) in export_restrictions
                t_start = date_to_timestep(forcing[:from]; start, N_year)
                t_end = date_to_timestep(forcing[:to]; start, N_year)
                push!(export_restriction_intervals, (t_start, t_end) => (area, forcing[:value]))
            end
        end
    return export_restriction_intervals
end

function generate_export_restriction_dict(export_restriction_intervals)
    export_restriction_dict = Dict{Tuple{Int,String},Float64}()
    for ((t_start, t_end), (producer_id, export_restriction)) in export_restriction_intervals  
        for t in t_start:t_end
            export_restriction_dict[(t,producer_id)] = export_restriction
        end
    end
    return export_restriction_dict
end


function date_to_fractional_year(date::Date)
    (year, month, day) = (Dates.year(date), Dates.month(date), Dates.day(date))
    y = year + (Dates.dayofyear(Date(2001, month, day)) - 0.5) / 365
    return y
end


function calculate_year_and_n(date::Date; N_year)
    (Δy, year) = modf(date_to_fractional_year(date))
    n = floor(Int, Δy * N_year) + 1
    return Int(year), n
end


function date_to_timestep(date::Date; start::Date, N_year)
    (year, n) = calculate_year_and_n(date; N_year)
    (year_start, n_start) = calculate_year_and_n(start; N_year)
    t = (year - year_start) * N_year + n - n_start + 1
    return t
end


function calculate_y0(year_start::Int, n_start::Int; N_year)
    y0 = year_start + (n_start - 1) / N_year
    return y0
end


function timestep_to_fractional_year(t; start::Date, N_year)
    (year_start, n_start) = calculate_year_and_n(start; N_year)
    y0 = calculate_y0(year_start, n_start; N_year)
    Δy = (t - 0.5) / N_year
    return y0 + Δy
end


function timestep_to_datetime(t; start::Date, N_year)
    (Δy, year) = modf(timestep_to_fractional_year(t; start, N_year))
    seconds_in_year = daysinyear(year) * 86400
    dt = DateTime(year, 1, 1, 0, 0, 0) + Second(round(Int, Δy * seconds_in_year))
    return dt
end


function add_datetime_col!(df; start::Date, N_year, timestep_field = :t)
    if timestep_field == :n
        start = Date(Dates.year(start), 1, 1)
    end
    t_to_datetime = t -> (ismissing(t) ? missing : timestep_to_datetime.(t; start, N_year))
    df[!, :datetime] .= t_to_datetime.(df[!, timestep_field])
end


