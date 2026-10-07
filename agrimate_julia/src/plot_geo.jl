using DrWatson
@quickactivate "Agrimate"

using DataFrames
using ArchGDAL;
const AG = ArchGDAL;
using GeoDataFrames: GeoDataFrames;
const GDF = GeoDataFrames;
using GeoFormatTypes: GeoFormatTypes;
const GFT = GeoFormatTypes;
using GeoMakie;
const GM = GeoMakie;
using CairoMakie
using ColorSchemes
using AlgebraOfGraphics
using Random

include(srcdir("regions.jl"))
include(srcdir("preprocess.jl"))
include(srcdir("auxiliary.jl"))

function load_gdf(path)
    dataset = AG.read(path)
    layer = AG.getlayer(dataset, 0)
    df = DataFrame(layer)
    return df = rename(df, 1 => :geom)
end

function write_gdf(
    path,
    gdf;
    crs = GFT.ProjString("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"),
)
    isfile(path) && rm(path)
    return GDF.write(
        path,
        gdf;
        layer_name = first(splitext(basename(path))),
        geom_column = :geom,
        crs,
    )
end

function union(geoms::AbstractVector)
    geom = first(geoms)
    for i in 2:length(geoms)
        geom = AG.union(geom, geoms[i])
    end
    return geom
end

function clean_countries_geodata(file)
    gdf_brk = load_gdf(
        datadir("raw", "natural_earth", "ne_50m_admin_0_breakaway_disputed_areas.shp"),
    )
    gdf_brk = select(
        gdf_brk,
        :geom,
        :BRK_NAME => :Area,
        :ISO_A3_EH => :ISO3,
        :ADM0_A3,
        :ADM0_A3_US,
        :ADM0_A3_DE,
        :featurecla => :Class,
        :NOTE_BRK => :Note,
    )

    # List those areas whose default NE attribution differs from German POV
    gdf_brk = gdf_brk[gdf_brk.ADM0_A3 .!= gdf_brk.ADM0_A3_DE, :]
    # Keep original attribution if German POV does not state any specific attribution
    hasdigits(s::AbstractString) = any(isdigit(c) for c in s)
    gdf_brk = gdf_brk[.!hasdigits.(gdf_brk.ADM0_A3_DE), :]
    println("Areas to modify")
    show(gdf_brk[:, Not(:geom)]; allrows = true)
    println()
    gdf_brk =
        select(gdf_brk, :geom, :Area, :ADM0_A3 => :ADM0_A3_old, :ADM0_A3_DE => :ADM0_A3_new)

    gdf = load_gdf(datadir("raw", "natural_earth", "ne_50m_admin_0_countries.shp"))
    gdf = select(
        gdf,
        :geom,
        :NAME => :Area,
        :ISO_A3_EH => :ISO3,
        :ADM0_A3,
        :NOTE_ADM0 => :Note,
    )
    for row in eachrow(gdf_brk)
        id_brk = findfirst(==(row.Area), gdf.Area)
        # Exception for W. Sahara
        if row.Area == "W. Sahara"
            id_brk = nothing
        end
        geom_brk = isnothing(id_brk) ? row.geom : gdf[id_brk, :geom]
        id_old = findfirst(==(row.ADM0_A3_old), gdf.ADM0_A3)
        id_new = findfirst(==(row.ADM0_A3_new), gdf.ADM0_A3)
        if !isnothing(id_old)
            @assert !isnothing(id_new)
            gdf[id_old, :geom] = AG.difference(gdf[id_old, :geom], geom_brk)
            gdf[id_new, :geom] = AG.union(gdf[id_new, :geom], geom_brk)
        end
    end
    gdf = gdf[.!AG.isempty.(gdf.geom), :]

    # Add Kosovo code XKX
    gdf[findfirst(==("KOS"), gdf.ADM0_A3), :ISO3] = "XKX"
    gdf = sort(gdf, :ISO3)

    println("All areas")
    show(gdf; allrows = true)
    println()

    return write_gdf(file, gdf)
end

function plot_regions(
    file = nothing;
    countries_file = datadir("clean", "geodata", "countries.gpkg"),
    df_region,
    df = nothing,
    variable = "Region",
    categorical = true,
    cat_colors = nothing,
    combine_regions = true,
    drop_regionless_areas = true,
    title = "",
)

    # Read, combine, and save data to *.geojson
    gdf = make_gdf(;
        df_region,
        df,
        countries_file,
        join_on = :Region,
        combine_regions,
        drop_regionless_areas,
    )
    gdf = select(gdf, :geom, variable)

    tmpfile = isnothing(file) ? datadir("tmp.geojson") : first(splitext(file)) * ".geojson"
    write_gdf(tmpfile, gdf)
    geodata = GM.GeoJSON.read(read(tmpfile))
    isnothing(file) && rm(tmpfile)

    # Create color codes for features
    features = GM.GeoInterface.properties.(GM.GeoInterface.features(geodata))
    features = getindex.(features, string(variable))
    (v_min, v_max) = extrema(features)
    if categorical
        # Categorical feature
        if isnothing(cat_colors)
            categories = unique(features)
            n_colors = length(categories)
            colormap = :Spectral
            colormap = cgrad(colormap, n_colors; categorical = true)
            cat_colors = categories .=> colors
        end
        feature_to_color = Dict("None" => :white, cat_colors...)
        color = [feature_to_color[f] for f in features]
    else
        # Numerical feature
        (v_min, v_max) = (-0.15, 0.15)
        normalize(v) = (v .- v_min) ./ (v_max - v_min)
        colormap = :vik
        n_colors = 14
        n_ticks = (n_colors - 2) ÷ 2 + 1
        colormap = cgrad(colormap, n_colors; rev = true, categorical = true)
        (lowclip, highclip) = (first(colormap), last(colormap))
        colormap = cgrad(colormap[(begin + 1):(end - 1)]; categorical = true)
        function get_color(x)
            return (0.0 ≤ x ≤ 1.0) ? (x == 0.5 ? :white : colormap[x]) :
                   (x < 0.0 ? lowclip : highclip)
        end
        color = [get_color(x) for x in normalize(features)]
    end

    # Set theme

    theme = set_my_theme!(fontsize=11)
    titlefont = theme.Axis.titlefont
    # titlesize = theme.fontsize[] + 1
    # linepatchsize = theme.linepatchsize[]

    # Create geoaxis
    fig = Figure(; resolution = categorical ? (800, 300) : (800, 400))
    ax = GeoAxis(fig[1, 1]; lonticks = [-180, 180], latticks = [-90, 90])
    # for i = 1:length(ax.scene.plots)
    #     ax.scene[i].visible = false
    # end
    empty!(ax)
    hidedecorations!(ax)

    # Add background
    bg_color = :white
    bg_edgewidth = 0
    ((x_min, x_max), (y_min, y_max)) = ax.limits.val
    n_side_bg = 100
    bg =
        GM.GeometryBasics.Point2f.(
            vcat(
                [(x_min, y) for y in range(y_min, y_max; length = n_side_bg)][begin:(end - 1)],
                [(x, y_max) for x in range(x_min, x_max; length = n_side_bg)][begin:(end - 1)],
                [(x_max, y) for y in range(y_max, y_min; length = n_side_bg)][begin:(end - 1)],
                [(x, y_min) for x in range(x_max, x_min; length = n_side_bg)][begin:(end - 1)],
            ),
        )
    bg = poly!(ax, bg; color = bg_color, strokecolor = :black, strokewidth = bg_edgewidth)

    # Plot regions
    plt =
        poly!(ax, geodata; color, strokecolor = :black, strokewidth = 0.25, overdraw = true)

    # Add colorbar / legend
    if categorical
        legend = Legend(
            fig[1, 2],
            [
                PolyElement(; color, strokecolor = :transparent) for
                color in last.(cat_colors)
            ],
            first.(cat_colors),
            "$variable";
            nbanks = length(cat_colors) ≤ 15 ? 1 : 2,
            # valign = :top,
        )
    else
        cb = Colorbar(
            fig[1, 2];
            colormap,
            highclip,
            lowclip,
            limits = (v_min, v_max),
            ticks = range(v_min, v_max; length = n_ticks),
            label = "$variable",
            height = Relative(0.8),
        )
    end

    fig[0, :] = Label(fig, title; font = titlefont)

    if !isnothing(file)
        save(file, fig; px_per_unit = 4)
    end
    return fig
end

function make_gdf(;
    df = nothing,
    df_region = nothing,
    countries_file = datadir("clean", "geodata", "countries.gpkg"),
    join_on = :Region,
    combine_regions = true,
    drop_regionless_areas = true,
)
    gdf = load_gdf(countries_file)

    if !isnothing(df_region)
        gdf = leftjoin(gdf, df_region; on = :ISO3 => :Area)
        if drop_regionless_areas
            dropmissing!(gdf)
        else
            gdf.Region = coalesce.(gdf.Region, "None")
        end
        if combine_regions
            gdf = combine(groupby(gdf, :Region), :geom => union => :geom)
            gdf = select(gdf, :geom, :Region)
        else
            gdf = select(gdf, :geom, :Region, :ISO3)
        end
    else
        gdf = select(gdf, :geom, :ISO3)
    end

    if !isnothing(df)
        df = multiunstack(df; index = join_on, values = [:value], variable_name = nothing)
        gdf = leftjoin(gdf, df; on = join_on)
        gdf = multistack(gdf; index = [:geom, join_on])
        gdf[!, :value] = coalesce.(gdf[!, :value], 0.0)
        gdf[isnan.(gdf.value) .| isinf.(gdf.value), :value] .= 0.0
    end

    disallowmissing!(gdf)
    return gdf
end

function plot_geolayout(
    gdf;
    fig = Figure(),
    i0 = 0,
    j0 = 0,
    value_col = :value,
    row_col = nothing,
    column_col = nothing,
    axwidth = 200,
    axheight = 90,
    unit = "Anomaly",
    title = nothing,
    limits = (-0.15, 0.15),
    colormap = :vik,
    rev = true,
    n_colors = 14,
    drawrowlabels = true,
)

    # TODO: add i_0 parameter and get figure from an argument

    # Set theme

    theme = set_my_theme!()
    titlefont = theme.Axis.titlefont

    # Set colormap limits
    (v_min, v_max) = isnothing(limits) ? extrema(gdf[!, value_col]) : limits
    normalize(v) = (v .- v_min) ./ (v_max - v_min)

    # Set colormap
    n_ticks = (n_colors - 2) ÷ 2 + 1
    colormap = cgrad(colormap, n_colors; rev, categorical = true)
    (lowclip, highclip) = colormap[[begin, end]]
    colormap = cgrad(colormap[(begin + 1):(end - 1)]; categorical = true)
    function get_color(x)
        return (0.0 ≤ x ≤ 1.0) ? (x == 0.5 ? :white : colormap[x]) :
               (x < 0.0 ? lowclip : highclip)
    end

    # Group data
    ggdf = groupby(gdf, [Symbol(col) for col in [row_col, column_col] if !isnothing(col)])
    row_vals = isnothing(row_col) ? [nothing] : unique(getindex.(keys(ggdf), row_col))
    column_vals =
        isnothing(column_col) ? [nothing] : unique(getindex.(keys(ggdf), column_col))

    # Create cells for plot elements
    empty_cell = fig[i0 + 1, j0 + 1]
    row_label_cells =
        [fig[(isnothing(column_col) ? i0 : i0 + 1) + i, j0 + 1] for i in 1:length(row_vals)]
    column_label_cells =
        [fig[i0 + 1, (isnothing(row_col) ? j0 : j0 + 1) + j] for j in 1:length(column_vals)]
    map_cells = [
        fig[
            (isnothing(column_col) ? i0 : i0 + 1) + i,
            (isnothing(row_col) ? j0 : j0 + 1) + j,
        ] for i in 1:length(row_vals), j in 1:length(column_vals)
    ]

    for (i, row_val) in enumerate(row_vals)
        for (j, column_val) in enumerate(column_vals)
            gdf = ggdf[((val for val in [row_val, column_val] if !isnothing(val))...,)]
            gdf = select(gdf, :geom, value_col)

            tmpfile = datadir("cache", randstring(16) * ".geojson")
            write_gdf(tmpfile, gdf)
            geodata = GM.GeoJSON.read(read(tmpfile))
            rm(tmpfile)

            # Create color codes for features
            features = GM.GeoInterface.properties.(GM.GeoInterface.features(geodata))
            features = getindex.(features, string(value_col))
            color = [get_color(x) for x in normalize(features)]

            # Create geoaxis
            ax = GeoAxis(
                map_cells[i, j];
                lonticks = [-180, 180],
                latticks = [-70, 90],
                width = axwidth,
                height = axheight,
                tellwidth = true,
                tellheight = true,
            )
            empty!(ax)
            hidedecorations!(ax)

            # Add background
            bg_color = :white
            bg_edgewidth = 0
            ((x_min, x_max), (y_min, y_max)) = ax.limits.val
            n_side_bg = 100
            bg =
                GM.GeometryBasics.Point2f.(
                    vcat(
                        [(x_min, y) for y in range(y_min, y_max; length = n_side_bg)][begin:(end - 1)],
                        [(x, y_max) for x in range(x_min, x_max; length = n_side_bg)][begin:(end - 1)],
                        [(x_max, y) for y in range(y_max, y_min; length = n_side_bg)][begin:(end - 1)],
                        [(x, y_min) for x in range(x_max, x_min; length = n_side_bg)][begin:(end - 1)],
                    ),
                )
            bg = poly!(
                ax,
                bg;
                color = bg_color,
                strokecolor = :black,
                strokewidth = bg_edgewidth,
            )

            # Plot regions
            plt = poly!(
                ax,
                geodata;
                color,
                strokecolor = :black,
                strokewidth = 0.25,
                overdraw = true,
            )
        end
    end

    # Add row / column labels
    if !isnothing(row_col) && drawrowlabels
        for (i, row_val) in enumerate(row_vals)
            Label(
                row_label_cells[i], # fig[i, i == 1 ? 0 : 1] 
                "$row_val";
                rotation = π / 2,
                font = titlefont,
                tellheight = false,
            )
        end
    end
    if !isnothing(column_col)
        for (j, col_val) in enumerate(column_vals)
            Label(
                column_label_cells[j], # fig[j == 1 ? 0 : 1, isnothing(row_col) ? j : j + 1]
                "$col_val";
                font = titlefont,
                tellwidth = false,
            )
        end
    end

    trim!(fig.layout)
    # Add colorbar
    cb = Colorbar(
        fig[(isnothing(column_col) ? i0 : i0 + 1) + length(row_vals) + 1, (j0 + 1):end];
        colormap,
        highclip,
        lowclip,
        limits = (v_min, v_max),
        ticks = range(v_min, v_max; length = n_ticks),
        label = unit,
        width = Relative(0.5),
        vertical = false,
        flipaxis = false,
    )
    trim!(fig.layout)

    if !isnothing(title)
        fig[i0, (j0 + 1):end] = Label(fig, title; font = titlefont)
    end

    resize_to_layout!(fig)

    return fig
end

function make_countries_geodata()
    countries_file = datadir("clean", "geodata", "countries.gpkg")
    mkpath(datadir("clean", "geodata"))
    return clean_countries_geodata(countries_file)
end

function region_to_color(; extra_regions = nothing)
    tab20 = cgrad(:tab20, 20; categorical = true)
    tab20b = cgrad(:tab20b, 20; categorical = true)
    cat_colors = [
        "Eastern Africa" => tab20[14],
        "Middle Africa" => tab20b[4],
        "Northern Africa" => tab20[16],
        "Southern Africa" => tab20[12],
        "Western Africa" => tab20b[12],
        "Central America" => tab20[18],
        "Canada" => tab20b[9],
        "USA" => tab20b[5],
        "Argentina" => tab20[9],
        "Rest of South America" => tab20[10],
        "Kazakhstan" => tab20[5],
        "Rest of Central Asia" => tab20[6],
        "China" => tab20[19],
        "Rest of Eastern Asia" => tab20[20],
        "Turkey" => tab20[3],
        "Rest of Western Asia" => tab20[4],
        "India" => tab20b[13],
        "Pakistan" => tab20b[14],
        "Rest of Southern Asia" => tab20b[16],
        "South-Eastern Asia" => tab20b[8],
        "EU-27" => tab20[1],
        "EU-28" => tab20[1],
        "Russia" => tab20b[1],
        "Ukraine" => tab20b[17],
        "Rest of Europe" => tab20[2],
        "Australia" => tab20[7],
        "Rest of Oceania" => tab20[8],
    ]
    if !isnothing(extra_regions)
        cat_colors = vcat(cat_colors, extra_regions)
    end
    return cat_colors
end

function make_regions_plot(
    regions = "Agrimate";
    extra_regions = nothing,
    extra_region_colors = nothing,
)
    countries_file = datadir("clean", "geodata", "countries.gpkg")

    mkpath(plotsdir("geoplots"))
    regions_file = plotsdir("geoplots", "regions.png")
    df_region = make_regions_dataframe(get_regions(regions), extra_regions)
    cat_colors = region_to_color(; extra_regions = extra_region_colors)
    if regions == "Agrimate"
        cat_colors = [c for c in cat_colors if first(c) != "EU-28"]
    end
    if regions == "AgrimateEU28"
        println( [first(c) for c in cat_colors] )
        cat_colors = [c for c in cat_colors if first(c) != "EU-27"]
    end

    return plot_regions(
        regions_file;
        countries_file,
        df_region,
        combine_regions = false,
        drop_regionless_areas = false,
        cat_colors,
    )
end

# make_countries_geodata()
# make_regions_plo