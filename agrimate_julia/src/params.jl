using Parameters: @with_kw
using AgrimateModel: @AgrimateParamsMix
using Dates: Date, TimeType

@AgrimateParamsMix @with_kw mutable struct Params
    crops::String = "wheat"
    baseline::String = "2016-2018"
    start::Date = Date("2018-01-01")
    production_anomalies::Union{Nothing,String,Dict{String,Dict{Symbol,Any}}} = nothing
    export_restrictions::Union{Nothing,String,Dict{String,Dict{Symbol,Any}}} = nothing
    regions::String = "Standard"
    extra_regions::Union{Nothing,Dict{String,Any}} = nothing
    flow_cutoff::Float64 = 0.01 # percentage
    production_cutoff::Float64 = 0. #
end

function DrWatson.allaccess(params::Params)
    defaults = Params()

    return [
        field for
        # field in fieldnames(Params) if getfield(params, field) != getfield(defaults, field) 
        field in fieldnames(Params) if getfield(params, field) != getfield(defaults, field) && field != :ε_d && field != :ε_d_domestic && field != :ε_d_foreign 
        # field in fieldnames(Params) if getfield(params, field) != getfield(defaults, field) && field != :ε_d_domestic && field != :ε_d_foreign 
    ]
end

DrWatson.default_prefix(params::Params) = "agrimate"

const savename_kwargs = (; connector = "_", sigdigits = 3)
# const savename_kwargs = (; connector = ";", sigdigits = 3)

# Base.string(vec::Vector{String}) = join(vec, ",") 

DrWatson.default_allowed(::Any) = (Real, String, Symbol, TimeType, Dict, Tuple, NamedTuple, Nothing)
function DrWatson.default_expand(params::Params)
    return [
        field for
        field in ["production_anomalies", "export_restrictions", "extra_regions"] if
        getfield(params, Symbol(field)) isa Dict
    ]
end
DrWatson.default_expand(d::Dict) = [string(key) for (key, value) in d if value isa Dict]

# DrWatson.savename(d, suffix=""; kwargs...) = DrWatson.savename(d, suffix; savename_kwargs..., kwargs...)

# DrWatson.produce_or_load(f, path, d; kwargs...) = DrWatson.produce_or_load(f, path, d; savename_kwargs..., kwargs...)
