using DataFrames
using Dates: Date, Year, year
using CairoMakie
using AlgebraOfGraphics
using Statistics: mean

function set_my_theme!(;
    fontsize = 7,
    ticksize = 4,
    minorticksize = 2,
    markersize = 6,
    patchsize = (8, 8),
    linewidth = 1.5,
    linepatchsize = (9 * linewidth, patchsize[2]),
    figure_padding = 8,
    rowgap = 12,
    colgap = 12,
)
    set_aog_theme!(; fonts = ["Lato Regular", "Lato Light"])
    update_theme!(;
        fontsize,
        markersize,
        linewidth,
        figure_padding,
        rowgap,
        colgap,
        Axis = (;
            xticksize = ticksize,
            yticksize = ticksize,
            xminorticksize = minorticksize,
            yminorticksize = minorticksize,
        ),
        Colorbar = (;
            ticksize,
            minorticksize,
            size = 8,
            tickcolor = :darkgrey,
            labelpadding = 3,
        ),
        Legend = (; patchsize, rowgap = 2, titlegap = 4, groupgap = 8),
        linepatchsize,
        palette = (;
            linestyle = [
                :solid, # solid
                [0, 2.25, 3.375], # dash
                [0, 1, 2], # dot
                [0, 2, 3, 4, 5], # dash dot
                [0, 2, 3, 4, 5, 6, 7], # dash dot dot
            ]
        ),
    )
    return Makie.current_default_theme()
end

function updatezorder!(grid, zorderdict; feature = :color)
    categoricalscales = first(grid).categoricalscales
    categories, palette = getproperty.(Ref(categoricalscales[feature]), (:data, :palette))
    hasproperty(categories[1], :value) && (categories = getproperty.(categories, :value))
    catdict = Dict(palette .=> categories)
    for cell in grid
        isempty(cell.entries) && continue
        features = getindex.(getproperty.(cell.entries, :named), feature)
        zorder = [zorderdict[catdict[f]] for f in features]
        plots = cell.axis.scene.plots[(end - length(zorder) + 1):end]
        translate!.(plots, 0, 0, zorder)
    end
end

function setticksvisible!(grid)
    for cell in grid
        cell.axis.xticksvisible[] = true
        cell.axis.yticksvisible[] = true
    end
end

# Necessary to allow for saving figures
Base.copy(fig::Makie.Figure) = fig

# Fix PPI after saving 
function DrWatson._wsave(file, fig::Makie.Figure; kwargs...)
    pt_per_unit = 1
    pt_per_inch = 72
    res_unit = size(fig.scene)
    res_mm = (round.(Int64, res_unit .* pt_per_unit ./ pt_per_inch .* 25.4)...,)
    if endswith(file, ".png") && :px_per_inch in keys(kwargs)
        px_per_inch = kwargs[:px_per_inch]
        px_per_unit = pt_per_unit * px_per_inch / pt_per_inch
        kwargs = (;
            (key => val for (key, val) in kwargs if key ∉ [:px_per_inch, :px_per_unit])...,
            px_per_unit,
        )
        save(file, fig; kwargs...)
        try
            run(`convert -units PixelsPerInch $file -density $px_per_inch $file`)
        catch e
            @warn "PPI of output PNG file was not adjusted. Maybe ImageMagick is not installed."
        end
        res_px = (round.(Int64, res_unit .* px_per_unit)...,)
        res_mm = (round.(Int64, res_unit .* pt_per_unit ./ pt_per_inch .* 25.4)...,)
        @info "Resolution: $res_unit units = $res_mm mm = $res_px px"
    elseif any(endswith.(file, [".svg", ".pdf"])) && get(kwargs, :pt_per_unit, 0.75) == 1
        save(file, fig; kwargs...)
        @info "Resolution: $res_unit units = $res_mm mm"
    else
        save(file, fig; kwargs...)
    end
end

# Elsevier guidelines
# Figure fontsize: 7 pt

# TARGET SIZE       Image width 	    Pixels at 300 dpi 	Pixels at 500 dpi 	Pixels at 1000 dpi
# Minimal size 	    30 mm (85 pt) 	    354 	            591 	            1181
# Single column     90 mm (255 pt) 	    1063 	            1772 	            3543
# 1.5 column 	    140 mm (397 pt)     1654 	            2756 	            5512
# Double column 	190 mm (539 pt)     2244 	            3740 	            7480

function plot_agent(
    df;
    param = nothing,
    param_values = nothing,
    runs = nothing,
    zorderdict = nothing,
    colordict = nothing,
    linestyledict = nothing,
    producer = nothing,
    consumer = nothing,
    rowlabelsposition = :right,
    skip_years = (0, 0),
    axwidth = 133,
    axheight = 100,
    title = nothing,
    sel_variables = nothing,
    layout = false,
    returngrid = false,
    σ = missing,
)
    theme = set_my_theme!()
    titlefont = theme.Axis.titlefont
    titlesize = theme.fontsize[] + 1
    linepatchsize = theme.linepatchsize[]

    (datetime_min, datetime_max) = extrema(df.datetime)
    datetime_min += Year(skip_years[1])
    datetime_max -= Year(skip_years[2])
    years = year(datetime_min):(year(datetime_max) + 1)

    if isnothing(runs)
        runs = ["simulation", "baseline"]
    end

    if !isnothing(producer)
        df_plt = df[.!ismissing.(df.producer) .& in(vcat(producer)).(df.producer), :]
        for pair in ["average transaction price" => "price", "price" => "selling price"]
            df_plt[!, :variable] .= replace(df_plt.variable, pair)
        end
        variables = [
            "harvest",
            "export restriction",
            "export tax factor",
            "incoming demand",
            "sales",
            "producer storage",
            "price adjustment factor",
            "selling price",
        ]
        isnothing(title) && (title = "Producer: $producer")
        for var in ["export tax factor", "price adjustment factor"]
            unique_runs = unique(df_plt.run)
            non_b_run = unique_runs[unique_runs .!= "baseline"][1]
            df_b = df_plt[(df_plt.variable .== var) .& (df_plt.run .== non_b_run), :]
            df_b[!, :run] .= "baseline"
            df_b[!, :value] .= 1.0
            df_plt = vcat(df_plt, df_b)
        end
        df_er = df_plt[df_plt.variable .== "export tax factor", :]
        df_er[!, :value] .= 1 .- (df_er.value) .^ (-σ)
        df_er[!, :variable] .= "export restriction"
        df_plt = vcat(df_plt, df_er)
        df_b = df_plt[(df_plt.variable .== "sales") .& (df_plt.run .== "baseline"), :]
        df_b[!, :variable] .= "incoming demand"
        df_plt = vcat(df_plt, df_b)
    elseif !isnothing(consumer)
        df_plt = df[.!ismissing.(df.consumer) .& in(vcat(consumer)).(df.consumer), :]
        variables = [
            "demand",
            "extra demand",
            "purchase",
            "consumption",
            "consumer storage",
            "consumer price",
        ]
        isnothing(title) && (title = "Consumer: $consumer")
        for var in ["extra demand"]
            df_b = df_plt[df_plt.variable .== var, :]
            df_b[!, :run] .= "baseline"
            df_b[!, :value] .= 0.0
            df_plt = vcat(df_plt, df_b)
        end
    end

    df_plt = df_plt[in(variables).(df_plt.variable), :]
    if !isnothing(sel_variables)
        df_plt = df_plt[in(first.(sel_variables)).(df_plt.variable), :]
        df_plt[!, :variable] = replace(df_plt.variable, sel_variables...)
        variables = [var for var in last.(sel_variables) if var in unique(df_plt.variable)]
    end
    df_plt = df_plt[
        .!ismissing(df_plt.t) .& (datetime_min .≤ df_plt.datetime .≤ datetime_max),
        :,
    ]

    df_plt = df_plt[in(runs).(df_plt.run), :]
    run_sorted = :run => sorter(runs) => ""

    plt = (
        data(df_plt) *
        visual(Lines) *
        mapping(:datetime => "", :value => "") *
        mapping(; linestyle = run_sorted, color = run_sorted)
    )
    if !layout
        plt *= mapping(; row = :variable => sorter(variables))
    else
        plt *= mapping(; layout = :variable => sorter(variables))
    end
    if !isnothing(param)
        isnothing(param_values) && (param_values = unique(df[!, param]))
        param_renamed = param => renamer([v => "$param = $v" for v in param_values])
        plt *= mapping(; col = param_renamed)
    end
    if (!isnothing(param) && string(param) in ["producer", "consumer"]) || layout == true
        facet = (; linkyaxes = :none)
    else
        facet = (; linkyaxes = :minimal)
    end
    xticks = datetimeticks([Date("$y-01-01") for y in years], ["$y" for y in years])
    axis = (; xticks, width = axwidth, height = axheight)
    legend = (; patchsize = linepatchsize, titlegap = 0)
    palettes = (;)
    if !isnothing(colordict)
        color = [colordict[p] for p in runs]
        palettes = merge(palettes, (; color))
    end
    if !isnothing(linestyledict)
        linestyle = [linestyledict[p] for p in runs]
        palettes = merge(palettes, (; linestyle))
    end
    fig, grid = draw(plt; facet, axis, legend, palettes)
    setticksvisible!(grid)

    if !isnothing(zorderdict)
        updatezorder!(grid, zorderdict)
    end

    if rowlabelsposition == :left
        delete!.(contents(fig[:, end, Right()]))
        delete!.(contents(fig[:, 1, Left()]))
        for (i, row_val) in enumerate(variables)
            Label(
                fig[i, 1, Left()],
                "$row_val";
                rotation = π / 2,
                font = titlefont,
                padding = (0, 40, 0, 0),
                tellheight = false,
            )
        end
    end

    if !isempty(title)
        fig[0, :] = Label(fig, title; font = titlefont, textsize = titlesize)
    end

    resize_to_layout!(fig)

    if !returngrid
        return fig
    else
        return (fig, grid)
    end
end

function plot_partners(
    df;
    producer = nothing,
    consumer = nothing,
    param = nothing,
    runs = nothing,
    zorderdict = nothing,
    colordict = nothing,
    linestyledict = nothing,
    skip_years = (0, 0),
    axwidth = 133,
    axheight = 100,
    unit = "mln t / month",
    fig = Figure(),
    returngrid = false,
)
    theme = set_my_theme!()
    titlefont = theme.Axis.titlefont
    titlesize = theme.fontsize[] + 1
    linepatchsize = theme.linepatchsize[]

    areaplot = isequal(param, :run)

    (datetime_min, datetime_max) = extrema(df.datetime)
    datetime_min += Year(skip_years[1])
    datetime_max -= Year(skip_years[2])
    years = year(datetime_min):(year(datetime_max) + 1)

    if !isnothing(producer)
        (df_plt, partners) = process_trade_flow_data(df; producer)
        partner = :customer
        rename!(df_plt, :consumer => partner)
        ylabel = "sales ($unit)"
        title = "Producer: $producer"
    elseif !isnothing(consumer)
        (df_plt, partners) = process_trade_flow_data(df; consumer)
        partner = :supplier
        rename!(df_plt, :producer => partner)
        ylabel = "purchase ($unit)"
        title = "Consumer: $consumer"
    end

    df_plt = df_plt[(datetime_min .≤ df_plt.datetime .≤ datetime_max), :]

    if isnothing(runs)
        runs = ["simulation", "baseline"]
    end
    df_plt = df_plt[in(runs).(df_plt.run), :]
    run_sorted = :run => sorter(runs) => ""

    if areaplot
        # Calculate ymin and ymax for each partner
        partner_to_id = Dict(p => id for (id, p) in enumerate(partners))
        for subdf in groupby(df_plt, [:datetime, :run])
            sort!(subdf, partner; by = p -> partner_to_id[p])
            subdf[!, :ymax] = cumsum(subdf[!, "transaction quantity"])
            subdf[!, :ymin] = subdf[!, :ymax] - subdf[!, "transaction quantity"]
        end
        plt =
            data(df_plt) *
            visual(Band) *
            mapping(:datetime => "", :ymin => ylabel, :ymax => "") *
            mapping(; color = partner => sorter(reverse(partners))) *
            mapping(; col = run_sorted)
    else
        plt =
            data(df_plt) *
            visual(Lines) *
            mapping(:datetime => "", "transaction quantity" => ylabel) *
            mapping(; linestyle = run_sorted, color = run_sorted)
        partner_renamed = partner => renamer([p => "$partner =\n$p" for p in partners])
        if !isnothing(param)
            param_renamed =
                param => renamer([v => "$param = $v" for v in unique(df[!, param])])
            plt *= mapping(; row = partner_renamed) * mapping(; col = param_renamed)
        else
            plt *= mapping(; layout = partner_renamed)
        end
    end

    facet = (; linkyaxes = :minimal)
    xticks = datetimeticks([Date("$y-01-01") for y in years], ["$y" for y in years])
    axis = (; xticks, width = axwidth, height = axheight)
    legend = (;)
    !areaplot && (legend = merge(legend, (; patchsize = linepatchsize, titlegap = 0)))
    palettes = (;)
    if areaplot
        if !isnothing(colordict)
            color = [colordict[p] for p in reverse(partners)]
            palettes = merge(palettes, (; color))
        end
    else
        if !isnothing(colordict)
            color = [colordict[r] for r in runs]
            palettes = merge(palettes, (; color))
        end
        if !isnothing(linestyledict)
            linestyle = [linestyledict[r] for r in runs]
            palettes = merge(palettes, (; linestyle))
        end
    end
    grid = draw!(fig, plt; facet, axis, palettes)
    setticksvisible!(grid)

    if !areaplot && !isnothing(zorderdict)
        updatezorder!(grid, zorderdict)
    end

    if !areaplot
        legend!(fig[:, end + 1], grid; legend...)
    end

    fig[0, :] = Label(fig, title; font = titlefont, textsize = titlesize)

    fig isa Makie.Figure && resize_to_layout!(fig)

    if !returngrid
        return fig
    else
        return (fig, grid)
    end
end

function plot_aggregates(
    df_sim,
    df_emp;
    region = "World",
    param = nothing,
    skip_years = (0, 0),
    labels,
    barplot = true,
    axwidth = 133,
    axheight = 100,
    colordict = nothing,
    linkyaxes = :all,
    ylabel = "",
    rowlabelsposition = :right,
    legendposition = :right,
    variables = nothing,
    marksource = true,
    showbaseline = false,
    title = nothing,
)
    # Select the region
    df_sim = df_sim[df_sim.Region .== region, :]
    df_emp = df_emp[df_emp.Region .== region, :]

    if isnothing(variables)
        variables = [
            "Anomaly Production" => "Production",
            "Anomaly Purchase" => "Purchase",
            "Anomaly Consumption" => "Consumption",
            "Anomaly Stock Variation" => "Stock Variation",
            "Anomaly Consumption + Stock Var." => "Consumption + Stock Var.",
        ]
    else
        variables = ["Anomaly $v" => v for v in variables]
    end

    # Join df_sim and df_emp
    index = [:Region, :Year, :Label]
    df_emp = stack(df_emp, first.(variables), index)
    if !isnothing(param)
        df_param = DataFrame(param => unique(df_sim[!, param]))
        df_emp = crossjoin(df_emp, df_param)
        push!(index, Symbol(param))
    end
    df_sim = stack(df_sim, first.(variables), index)
    df = vcat(df_sim, df_emp)

    # Limit years
    years = (minimum(df_sim.Year) + skip_years[1]):(maximum(df_sim.Year) - skip_years[2])
    df = df[in(years).(df.Year), :]

    # Rename variables
    df[!, :variable] = replace(df.variable, variables...)

    if showbaseline
        df_b = df[df.Label .== first(unique(df.Label)), :]
        df_b[!, :Label] .= "baseline"
        df_b[:, :value] .= 0.0
        df = vcat(df, df_b)
    end

    # Plot

    theme = set_my_theme!()
    titlefont = theme.Axis.titlefont
    titlesize = theme.fontsize[] + 1
    linepatchsize = theme.linepatchsize[]

    isnothing(title) && (title = "Region: $region")
    label_sorted = :Label => sorter(labels...) => ""

    df[!, :source] .= ""
    df[startswith.(df.Label, "emp."), :source] .= "empirical"
    df[startswith.(df.Label, "sim."), :source] .= "simulation"

    source_sorted = :source => sorter("simulation", "empirical") => " "

    df = dropmissing(df)

    plt = data(df) * mapping(:Year => "", :value => "") * mapping(; color = label_sorted)

    if barplot
        plt *= visual(BarPlot) * mapping(; dodge = label_sorted)
    else
        plt *= (
            visual(Lines) *
            mapping(; (marksource ? (; linestyle = source_sorted) : (;))...) +
            visual(Scatter) * mapping(; marker = label_sorted)
        )
    end
    plt *= mapping(; row = :variable => sorter(last.(variables)))
    if !isnothing(param)
        param_renamed = param => renamer([v => "$param = $v" for v in unique(df[!, param])])
        plt *= mapping(; col = param_renamed)
    end
    facet = (; linkyaxes)
    axis = (; width = axwidth, height = axheight, xticks = years, xlabel = "Year", ylabel)
    legend = (; (!barplot ? (; patchsize = linepatchsize) : (;))..., titlegap = 0)
    if legendposition == :bottom
        legend = merge(
            legend,
            (;
                position = :bottom,
                orientation = :vertical,
                tellheight = false,
                tellwidth = false,
            ),
        )
    end
    palettes = (;)
    if !isnothing(colordict)
        color = [colordict[l] for l in labels]
        palettes = merge(palettes, (; color))
    end
    fg = draw(plt; facet, axis, legend, palettes)

    if !showbaseline
        for cell in fg.grid
            hline =
                hlines!(cell.axis, 0; color = :darkgray, linestyle = :dash, linewidth = 1)
            translate!(hline, 0, 0, -1)
        end
    end

    if rowlabelsposition == :left
        delete!.(contents(fg.figure[:, 1, Right()]))
        delete!.(contents(fg.figure[:, 1, Left()]))

        # labels = [
        #     scene for scene in fg.figure.scene.plots
        #     if typeof(scene) <: Makie.MakieCore.Text && scene.input_args[1].val ∈ last.(variables)
        # ]
        # delete!.(fg.figure.scene, labels)
        for (i, row_val) in enumerate(last.(variables))
            # axis = fg.grid[i, 1].axis
            # axis.ylabel = row_val
            # axis.ylabelvisible = true
            Label(
                fg.figure[i, 1, Left()],
                "$row_val";
                rotation = π / 2,
                font = titlefont,
                padding = (0, 30, 0, 0),
                tellheight = false,
            )
        end
    end

    setticksvisible!(fg.grid)

    # fg.figure[0, (rowlabelsposition == :left ? 2 : 1):end] =
    #     Label(fg.figure, title; font = titlefont, textsize = titlesize)

    fg.figure[0, :] = Label(fg.figure, title; font = titlefont, textsize = titlesize)

    resize_to_layout!(fg.figure)

    return fg.figure
end

function plot_anomalies(
    df;
    regions,
    labels,
    variables,
    axwidth = 133,
    axheight = 100,
    colordict = nothing,
    ylabel = "Anomaly",
)
    df_plt = subset(
        df,
        :Region => ByRow(in(regions)),
        :Label => ByRow(in(first.(labels))),
        :variable => ByRow(in(variables)),
    )

    theme = set_my_theme!()

    label_sorted = :Label => renamer(labels) => ""
    plt = (
        data(df_plt) *
        visual(BarPlot) *
        mapping(:Region => sorter(regions) => "", :value => ylabel) *
        mapping(; dodge = label_sorted, color = label_sorted) *
        mapping(; row = :variable => sorter(variables) => "")
    )

    facet = (; linkyaxes = :minimal)
    axis = (; width = axwidth, height = axheight)
    legend = (; position = :bottom, titlegap = 0)
    palettes = (;)
    if !isnothing(colordict)
        color = [colordict[l] for l in first.(labels)]
        palettes = merge(palettes, (; color))
    end
    fg = draw(plt; facet, axis, legend, palettes)

    for cell in fg.grid
        hline = hlines!(cell.axis, 0; color = :darkgray, linestyle = :dash, linewidth = 1)
        translate!(hline, 0, 0, -1)
    end

    resize_to_layout!(fg.figure)

    return fg.figure
end

function process_simulation_data(df; param = nothing)
    variables_sum = ["harvest", "consumption", "purchase"]
    variables_last = ["producer storage", "consumer storage"]
    index = [:year, :region, :variable, :run]
    if !isnothing(param)
        push!(index, Symbol(param))
    end
    dfs = []
    for (operator, vars) in zip([sum, last], [variables_sum, variables_last])
        df_v = df[in(vars).(df.variable), :]
        df_v[!, :region] = coalesce.(df_v.producer, df_v.consumer)
        df_v = combine(
            groupby(transform(df_v, :datetime => ByRow(year) => :year), index),
            :value => operator => :value,
        )
        push!(dfs, df_v)
    end
    df = vcat(dfs...)

    # Create baseline variables
    is_baseline = df.run .== "baseline"
    df[is_baseline, :variable] .= "baseline " .* df[is_baseline, :variable]
    df[is_baseline, :run] .= join([r for r in unique(df.run) if r != "baseline"], ";")
    df[!, :run_tmp] = split.(df.run, ";")
    df = rename(select(df, Not(:run)), :run_tmp => :run)
    df = flatten(df, :run)

    # Create columns
    df = unstack(df, :variable, :value)

    df[!, "Anomaly Production"] = df[!, "harvest"] ./ df[!, "baseline harvest"] .- 1
    df[!, "Anomaly Consumption"] =
        df[!, "consumption"] ./ df[!, "baseline consumption"] .- 1
    df[!, "Anomaly Purchase"] = df[!, "purchase"] ./ df[!, "baseline purchase"] .- 1

    index = [col for col in index if col ∉ [:year, :variable]]
    gdf = groupby(sort(df, vcat(index, :year)), index)
    df = combine(
        gdf,
        (
            "$agent storage" =>
                (c -> vcat(missing, diff(c))) => "$agent stock variation" for
            agent in ["producer", "consumer"]
        )...,
        valuecols(gdf),
    )
    for agent in ["producer", "consumer"]
        df[!, "Anomaly Stock Variation ($agent)"] =
            df[!, "$agent stock variation"] ./ df[!, "baseline consumption"]
    end

    df[!, "Anomaly Stock Variation"] = (
        coalesce.(df[!, "Anomaly Stock Variation (producer)"], 0) .+
        coalesce.(df[!, "Anomaly Stock Variation (consumer)"], 0)
    )
    df[!, "Anomaly Consumption + Stock Var."] =
        df[!, "Anomaly Consumption"] + df[!, "Anomaly Stock Variation"]

    value_columns = [
        "Anomaly Production",
        "Anomaly Consumption",
        "Anomaly Purchase",
        "Anomaly Stock Variation",
        "Anomaly Stock Variation (producer)",
        "Anomaly Stock Variation (consumer)",
        "Anomaly Consumption + Stock Var.",
    ]

    df_sim = select(
        df,
        "region" => "Region",
        "year" => "Year",
        "run" => "Label",
        (!isnothing(param) ? (param,) : ())...,
        value_columns...,
    )
    df_sim[!, "Label"] = "sim. " .* df_sim[!, "Label"]

    return df_sim
end

function process_empirical_data(crop, df_region)
    dfs_emp = []

    for (prefix, label_init, label_final) in zip(
        ["production", "domestic_supply", "stocks"],
        ["Production", "Domestic supply quantity", "Stock Variation"],
        ["Production", "Consumption", "Stock Variation"],
    )
        dfs = []
        for source in ["FAO", "USDA"]
            file = datadir(
                "clean",
                "timeseries",
                savename(prefix, (; crop, source), "csv"; savename_kwargs...),
            )
            df = wload(file)
            columns = [
                col for col in names(df) if
                col ∈ ["Area", "Year", label_init, "$label_init Trend"]
            ]
            df = df[:, columns]
            df = rename(
                df,
                label_init => label_final,
                "$label_init Trend" => "$label_final Trend",
            )
            df[!, "Label"] .= "emp. $source"
            push!(dfs, df)
        end
        push!(dfs_emp, vcat(dfs...))
    end
    df = outerjoin(dfs_emp...; on = [:Year, :Area, :Label])

    df = leftjoin(df, df_region; on = :Area)
    df[df.Area .== "EU-27", :Region] .= "EU-27"
    missing_regions = unique(df[ismissing.(df.Region), [:Area, :Region]])
    !isempty(missing_regions) && @show missing_regions
    df = select(df, Not(:Area))

    gdf = groupby(df, [:Region, :Year, :Label])
    val_cols = valuecols(gdf)
    df = combine(gdf, val_cols .=> sum ∘ skipmissing; renamecols = false)

    gdf_world = groupby(df, [:Year, :Label])
    df_world = combine(gdf_world, val_cols .=> sum ∘ skipmissing; renamecols = false)
    df_world[!, :Region] .= "World"

    df = vcat(df, df_world)

    df[!, "Anomaly Production"] = df[!, "Production"] ./ df[!, "Production Trend"] .- 1
    df[!, "Anomaly Consumption"] = df[!, "Consumption"] ./ df[!, "Consumption Trend"] .- 1
    df[!, "Anomaly Stock Variation"] =
        df[!, "Stock Variation"] ./ df[!, "Consumption Trend"]
    df[!, "Anomaly Consumption + Stock Var."] =
        df[!, "Anomaly Consumption"] + df[!, "Anomaly Stock Variation"]
    insertcols!(df, "Anomaly Purchase" => missing)

    df_emp = select(
        df,
        "Region",
        "Year",
        "Label",
        "Anomaly Production",
        "Anomaly Consumption",
        "Anomaly Stock Variation",
        "Anomaly Consumption + Stock Var.",
        "Anomaly Purchase",
    )

    df_emp = sort(df_emp, [:Region, :Label, :Year])

    return df_emp
end

function aggregate_anomalies(df, years; param = nothing)
    df = df[in(years).(df.Year), Not(:Year)]
    index = isnothing(param) ? ["Region", "Label"] : ["Region", param, "Label"]
    index = [col for col in index if col in names(df)]
    variables = [v => v[(length("Anomaly ") + 1):end] for v in names(df, Not(index))]
    df = combine(groupby(df, index), first.(variables) .=> mean .=> last.(variables))
    return df
end

function define_runs!(df; runs = ["baseline", "prod. anom.", "prod. anom. + exp. rest."])
    @assert runs[1] == "baseline"
    df[(df.run .== "simulation") .& (df[!, "export restrictions"] .== "no"), "run"] .=
        runs[2]
    df[(df.run .== "simulation") .& (df[!, "export restrictions"] .== "yes"), "run"] .=
        runs[3]
    df = df[.!((df.run .== "baseline") .& (df[!, "export restrictions"] .== "yes")), :]
    df = select(df, Not("export restrictions"))
    return df
end

function plot_wm_price_timeseries(
    df,
    crop;
    param = nothing,
    price_ref_run,
    runs,
    skip_years = (0, 0),
    axwidth = 133,
    axheight = 100,
    rowlabelsposition = :right,
    colordict = nothing,
    zorderdict = nothing,
    linestyledict = nothing,
    σ,
    layout = false,
)

    # HARVEST

    df_h =
        subset(df, :variable => ByRow(==("harvest")), :producer => ByRow(!isequal("World")))
    df_h = transform(
        df_h,
        :datetime => ByRow(month) => "Month",
        :datetime => ByRow(year) => "Year",
    )
    df_h = combine(
        groupby(
            df_h,
            [:Year, :Month, :variable, :run, (isnothing(param) ? () : (Symbol(param),))...],
        ),
        :value => sum => :value,
    )
    years = (minimum(df_h.Year) + skip_years[1]):(maximum(df_h.Year) - skip_years[2])
    df_h = df_h[in(years).(df_h.Year), :]
    df_h = rename(df_h, :run => :Label)
    df_h[!, "Label"] = "sim. " .* df_h.Label
    if :N_year in propertynames(df_h)
        df_h[!, :value] ./= (df_h.N_year .÷ 12)
    else
        df_h[!, :value] ./= 2 # unit: mln t / month and two points per month in dataset for N_year = 24
    end
    df_h[!, :variable] .= "(a) harvest (mln t / month)"

    # HARVEST ANOMALY

    df_a = df_h[:, :]
    df_a_baseline = subset(df_a, "Label" => ByRow(==("sim. baseline")))
    df_a_baseline = select(df_a_baseline, Not("Label"))
    df_a = leftjoin(
        df_a,
        rename(df_a_baseline, :value => :baseline);
        on = [:Year, :Month, :variable, (isnothing(param) ? () : (Symbol(param),))...],
    )
    df_a = transform(df_a, [:value, :baseline] => ((v, b) -> b .* (v ./ b .- 1.)) => :value)
    df_a = select(df_a, Not(:baseline))
    df_a[!, :variable] .= "(b) harvest anomaly (mln t / month)"


    # RESTRICTED SALES

    df_er = subset(
        df,
        :variable => ByRow(in(["export tax factor", "expected sales"])),
        :producer => ByRow(!isequal("World")),
    )
    df_er = select(
        df_er,
        :datetime,
        :producer,
        :run,
        :variable,
        :value,
        (isnothing(param) ? () : (Symbol(param),))...,
    )
    df_er = unstack(df_er)
    df_er = transform(
        df_er,
        "export tax factor" => f -> coalesce.(f, 1.0),
        "expected sales" => x -> coalesce.(x, 0.0);
        renamecols = false,
    )
    df_er = transform(
        df_er,
        "export tax factor" => ByRow(f -> 1 - f^(-σ)) => "export restriction",
    )
    df_er[!, "restricted sales"] .=
        df_er[!, "export restriction"] .* df_er[!, "expected sales"]

    # Aggregate by month
    df_er = transform(
        df_er,
        :datetime => ByRow(month) => "Month",
        :datetime => ByRow(year) => "Year",
    )
    years = (minimum(df_er.Year) + skip_years[1]):(maximum(df_er.Year) - skip_years[2])
    df_er = combine(
        groupby(
            df_er,
            ["Year", "Month", "run", (isnothing(param) ? () : (string(param),))...],
        ),
        ["restricted sales", "expected sales"] =>
            ((rs, es) -> sum(rs) / sum(es)) => "value",
    )
    df_er[!, :variable] .= "(c) restricted sales share"
    df_er = df_er[in(years).(df_er.Year), :]
    df_er = rename(df_er, :run => :Label)
    df_er[!, "Label"] = "sim. " .* df_er.Label
    # df_er[!, :value] ./= 2 # unit: mln t / month and two points per month in dataset

    df_er_b = subset(df_er, :Label => ByRow(==("sim. production anomalies")))
    df_er_b[!, :Label] .= "sim. baseline"
    df_er = vcat(df_er, df_er_b)

    # PRICES

    # Get baseline prices
    df_bp = df[(df.variable .== "price") .& (df.run .== "baseline"), :]
    df_bp = select(df_bp, Not([:variable, :producer, :consumer, :n]))
    df_bp = rename(df_bp, :value => "baseline price")
    df_bp = unique(df_bp)

    # Keep only non-domestic trade flows
    vars = ["transaction quantity", "transaction price"]
    df = df[in(vars).(df.variable), :]
    df = df[
        (df.producer .!= df.consumer) .& (df.producer .!= "World") .& (df.consumer .!= "World"),
        :,
    ]
    df = unstack(df, :variable, :value)

    # Fill baseline transaction prices
    index = [col for col in names(df_bp) if col != "baseline price"]
    df = leftjoin(df, df_bp; on = index)
    is_baseline = df.run .== "baseline"
    df[is_baseline, "transaction price"] = df[is_baseline, "baseline price"]
    df = select(df, Not("baseline price"))

    # Monthly resolution
    df = transform(
        df,
        :datetime => ByRow(month) => "Month",
        :datetime => ByRow(year) => "Year",
    )
    df = select(df, Not([:t, :n, :datetime]))

    # Calculate average export price weighted by export volume
    index = [col for col in names(df) if (col ∉ vars) & (col ∉ ["producer", "consumer"])]
    df[!, "monetary value"] .= df[!, "transaction quantity"] .* df[!, "transaction price"]
    df_sim = combine(
        groupby(df, index),
        ["monetary value", "transaction quantity"] =>
            ((v, q) -> sum(v) / sum(q)) => "WM price index",
    )
    df_sim = rename(df_sim, :run => :Label)
    df_sim[!, "Label"] = "sim. " .* df_sim.Label

    # Skip years
    years = (minimum(df_sim.Year) + skip_years[1]):(maximum(df_sim.Year) - skip_years[2])
    df_sim = df_sim[in(years).(df_sim.Year), :]

    # Load historical data
    file = datadir("clean", "prices", "commodity_prices.csv")
    df_emp = wload(file)
    price_label = Dict(
        "wheat" => "Wheat, US HRW (deflated)",
        "maize" => "Maize, US (deflated)",
        "rice" => "Rice, Thai 5% (deflated)",
    )
    df_emp = select(df_emp, :Year, :Month, price_label[crop] => "WM price")
    if !isnothing(param)
        df_param = DataFrame(param => unique(df_sim[!, param]))
        df_emp = crossjoin(df_emp, df_param)
    end
    df_emp[!, "Label"] .= "emp. " .* price_label[crop]

    # Skip years
    df_emp = df_emp[in(years).(df_emp.Year), :]

    # Convert price to price index
    index = [col for col in names(df_sim) if col ∉ ["Year", "Month", "WM price index"]]
    df_avg = combine(
        groupby(df_sim, index),
        "WM price index" => mean => "average WM price index",
    )
    avg_price_emp = mean(skipmissing(df_emp[!, "WM price"]))
    df_avg[!, "price to index"] = df_avg[!, "average WM price index"] ./ avg_price_emp
    df_avg = select(df_avg, Not("average WM price index"))
    df_avg = df_avg[df_avg.Label .== "sim. " * price_ref_run, Not("Label")]
    index = [col for col in names(df_avg) if col != "price to index"]
    if !isempty(index)
        df_emp = leftjoin(df_emp, df_avg; on = index)
    else
        df_emp[!, "price to index"] .= df_avg[1, 1]
    end
    df_emp[!, "WM price index"] = df_emp[!, "WM price"] .* df_emp[!, "price to index"]
    df_emp = select(df_emp, Not(["WM price", "price to index"]))

    # Join datasets
    df = vcat(df_sim, df_emp)
    df = rename(df, "WM price index" => :value)
    df[!, :variable] .= "(d) world market price index"

    df = vcat(df_h, df_a, df_er, df)

    # Plot

    theme = set_my_theme!()
    linepatchsize = theme.linepatchsize[]

    # title = ""
    labels = vcat("emp. " * price_label[crop], "sim. " .* runs)
    nlabels = length(unique(df.Label))
    df = df[in(labels).(df.Label), :]
    label_sorted = :Label => sorter(labels...) => ""

    df[!, :Date] = Date.(df.Year, df.Month)
    variables =
        ["(a) harvest (mln t / month)", "(b) harvest anomaly (mln t / month)", "(c) restricted sales share", "(d) world market price index"]

    plt = (
        data(df) *
        visual(Lines) *
        mapping(:Date => "", :value => "") *
        mapping(; linestyle = label_sorted, color = label_sorted)
    )
    if !layout
        plt *= mapping(; row = :variable => sorter(variables))
    else
        plt *= mapping(; layout = :variable => sorter(variables))
    end
    if !isnothing(param)
        param_renamed = param => renamer([v => "$param = $v" for v in unique(df[!, param])])
        plt *= mapping(; col = param_renamed)
    end
    facet = (; linkyaxes = layout ? :none : :minimal)
    years = first(years):(last(years) + 1)
    xticks = datetimeticks([Date("$y-01-01") for y in years], ["$y" for y in years])
    axis = (; xticks, width = axwidth, height = axheight)
    legend = (; patchsize = linepatchsize, titlegap = 0)
    palettes = (;)
    if !isnothing(colordict)
        colordict = Dict("sim. " * r => colordict[r] for r in runs)
        # First line is empirical data
        colordict[labels[1]] = theme.palette.color[][nlabels]
        color = [colordict[l] for l in labels]
        palettes = merge(palettes, (; color))
    end
    if !isnothing(linestyledict)
        linestyledict = Dict("sim. " * r => linestyledict[r] for r in runs)
        # Last line is empirical data
        linestyledict[labels[1]] = theme.palette.linestyle[][nlabels]
        linestyle = [linestyledict[l] for l in labels]
        palettes = merge(palettes, (; linestyle))
    end
    fg = draw(plt; facet, axis, legend, palettes)

    setticksvisible!(fg.grid)

    if !isnothing(zorderdict)
        zorderdict = Dict("sim. " * r => zorderdict[r] for r in runs)
        zorderdict[labels[1]] = maximum(values(zorderdict)) + 1
        updatezorder!(fg.grid, zorderdict)
    end

    if rowlabelsposition == :left
        labels = contents(fg.figure[:, 1, Right()])
        for (i, label) in enumerate(labels)
            label.rotation[] = π / 2
            fg.figure[i, i == 1 ? 0 : 1] = label
        end
    end

    # if layout
    #     leg = contents(fg.figure[:, end])[]
    #     fg.figure[end, end - 1] = leg
    #     trim!(fg.figure.layout)
    # end

    resize_to_layout!(fg.figure)

    return fg.figure, fg.grid, df
end