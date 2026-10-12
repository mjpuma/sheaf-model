module CouplingModule

export substitution_factor, RHO_SUBST, COUPLED_CROPS
export reference_index_path, save_reference_index, load_reference_index
export assert_coupled_clocks, assert_reference_coverage

using CSV
using DataFrames: DataFrame, nrow

# Frozen substitutability (August Gate 1 plan / GATE1_DESIGN.md).
# Not Agrimate's interest-rate ρ.
const COUPLED_CROPS = ("wheat", "rice", "maize")
const RHO_SUBST = Dict(
    ("wheat", "rice") => 0.30,
    ("wheat", "maize") => 0.40,
    ("rice", "wheat") => 0.30,
    ("rice", "maize") => 0.20,
    ("maize", "wheat") => 0.40,
    ("maize", "rice") => 0.20,
)

"""Sidecar from an undisturbed single-crop run: `root/reference/crop_price_index_<crop>.csv`."""
function reference_index_path(root::AbstractString, crop::AbstractString)
    joinpath(root, "reference", "crop_price_index_$(crop).csv")
end

function save_reference_index(path::AbstractString, crop::AbstractString, df::DataFrame)
    mkpath(dirname(path))
    out = DataFrame(
        crop = fill(String(crop), nrow(df)),
        t = df.t,
        consumer = df.consumer,
        value = df.value,
    )
    CSV.write(path, out)
    return path
end

function load_reference_index(root::AbstractString, crops)
    ref = Dict{Tuple{String,String,Int},Float64}()
    missing_crops = String[]
    for crop in crops
        path = reference_index_path(root, crop)
        if !isfile(path)
            push!(missing_crops, String(crop))
            continue
        end
        df = CSV.read(path, DataFrame)
        for row in eachrow(df)
            ref[(String(row.crop), String(row.consumer), Int(row.t))] = Float64(row.value)
        end
    end
    if !isempty(missing_crops)
        example = reference_index_path(root, missing_crops[1])
        error(
            "missing undisturbed reference index for $(join(missing_crops, ", ")). " *
            "Run each crop with no anomalies and no restrictions, then pass that output root. " *
            "Expected e.g. $example",
        )
    end
    return ref
end

function assert_coupled_clocks(starts, n_years)
    start_list = collect(starts)
    year_list = collect(n_years)
    length(unique(start_list)) == 1 || error("coupled crops must share start; got $start_list")
    length(unique(year_list)) == 1 || error("coupled crops must share N_year; got $year_list")
    return nothing
end

function assert_reference_coverage(reference_index, crops, t_max::Integer)
    for crop in crops
        g = String(crop)
        ts = Set{Int}()
        for (c, _, t) in keys(reference_index)
            c == g && push!(ts, t)
        end
        isempty(ts) && error("reference_index has no entries for $g")
        for t in 1:Int(t_max)
            t in ts || error("reference_index for $g missing timestep $t (need 1:$t_max)")
        end
    end
    return nothing
end

"""M^g_s(t) = Π_{h≠g} (P^h_s(t) / P̄^h_s(t))^{ξ ρ_gh ε_d^g}.

`current_index` keys are `(crop, region)`. `reference_index` keys are
`(crop, region, t)`. A crop with no purchaser in `region` contributes 1.
At ξ = 0 the product is identically 1.
"""
function substitution_factor(
    crop::AbstractString,
    region::AbstractString,
    t::Integer,
    ξ::Float64,
    ε_d::Float64,
    current_index,
    reference_index,
)
    ξ == 0 && return 1.0
    M = 1.0
    g = String(crop)
    s = String(region)
    for h in COUPLED_CROPS
        h == g && continue
        P = get(current_index, (h, s), nothing)
        Pbar = get(reference_index, (h, s, Int(t)), nothing)
        (P === nothing || Pbar === nothing) && continue
        (!isfinite(P) || !isfinite(Pbar) || Pbar <= 0) && continue
        η = ξ * get(RHO_SUBST, (g, h), 0.0) * ε_d
        M *= (P / Pbar)^η
    end
    return M
end

end
