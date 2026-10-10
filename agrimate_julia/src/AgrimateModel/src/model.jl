module ModelModule

export InitializationData, InputData, Model
export create_agents!, initialize_agents!, step!, step_coupled!
export substitution_factor, RHO_SUBST, COUPLED_CROPS

using DataStructures: DefaultDict
using Parameters

using ..AgentsModule

struct InitializationData
    baseline_harvests::Dict{String,Vector{Float64}}
    baseline_consumption::Dict{String,Float64}
    baseline_transactions::Dict{Tuple{String,String},Float64}
end

struct InputData
    harvests::Dict{String,Vector{Float64}}
    expected_harvests::Dict{String,Matrix{Float64}}
    export_restriction_intervals::Vector{Pair{Tuple{Int,Int},Tuple{String,Float64}}}
    export_restriction_dict::Dict{Tuple{Int,String},Float64}
end

InputData(harvests::Dict{String,Vector{Float64}}, expected_harvests::Dict{String,Matrix{Float64}}) =
    InputData(harvests, expected_harvests, Vector{Pair{Tuple{Int,Int},Tuple{String,Float64}}}())

InputData(harvests::Dict{String,Vector{Float64}}) = InputData(harvests, Dict{String,Matrix{Float64}}())

InputData(harvests::Dict{String,Vector{Float64}}, export_restriction_intervals::Vector{Pair{Tuple{Int,Int},Tuple{String,Float64}}}) =
    InputData(harvests, Dict{String,Matrix{Float64}}(), export_restriction_intervals)

InputData(harvests::Dict{String,Vector{Float64}}, export_restriction_intervals::Vector{Pair{Tuple{Int,Int},Tuple{String,Float64}}},export_restriction_dict::Dict{Tuple{Int,String},Float64}) =
    InputData(harvests, Dict{String,Matrix{Float64}}(), export_restriction_intervals,export_restriction_dict)

InputData(harvests::Dict{String,Vector{Float64}},export_restriction_dict::Dict{Tuple{Int,String},Float64}) =
    InputData(harvests, Dict{String,Matrix{Float64}}(), export_restriction_dict)

mutable struct Model
    producers::Dict{String,Producer}
    consumers::Dict{String,Consumer}

    # Global parameters
    global_params::DefaultDict{Symbol,Any,Nothing}

    # Constructor
    function Model(;global_params)
        model = new()
        model.global_params = DefaultDict(nothing, Dict{Symbol,Any}(pairs(global_params)))
        model.producers = Dict{String,Producer}()
        model.consumers = Dict{String,Consumer}()
        return model
    end
end

function step!(model, t, input_data::InputData; verbose::Bool = true)
    @unpack N_hor = model.global_params
    verbose && println("Timestep $t...")

    # @sync Threads.@threads
    for producer in collect(values(model.producers))
        harvest = input_data.harvests[producer.id][t]
        expected_harvests = input_data.expected_harvests[producer.id][t, :]
        harvest_step!(producer, harvest, expected_harvests)
        export_restriction_step!(producer,t,input_data.export_restriction_dict)
        sales_step!(producer, t, model.consumers; verbose)
        
    end


    for producer in values(model.producers)
        policy_implementation_step!(producer, t,model.consumers)
    end
    for producer in values(model.producers)
        communication_step!(producer, t, model.producers)
    end

    for consumer in values(model.consumers)
        delivery_step!(consumer)
        consumption_step!(consumer)
        accounting_step!(consumer)
        price_index_step!(consumer, t, model.producers)
        procurement_step!(consumer, t, model.producers)
    end
end

include("coupling.jl")
using .CouplingModule

function step_coupled!(
    models::Dict{String,Model},
    t::Int,
    input_data::Dict{String,InputData},
    ξ::Float64,
    reference_index;
    verbose::Bool = true,
)
    verbose && println("Timestep $t (coupled)...")
    for (crop, model) in models
        inp = input_data[crop]
        for producer in collect(values(model.producers))
            harvest = inp.harvests[producer.id][t]
            expected_harvests = inp.expected_harvests[producer.id][t, :]
            harvest_step!(producer, harvest, expected_harvests)
            export_restriction_step!(producer, t, inp.export_restriction_dict)
            sales_step!(producer, t, model.consumers; verbose)
        end
        for producer in values(model.producers)
            policy_implementation_step!(producer, t, model.consumers)
        end
        for producer in values(model.producers)
            communication_step!(producer, t, model.producers)
        end
        for consumer in values(model.consumers)
            delivery_step!(consumer)
            consumption_step!(consumer)
            accounting_step!(consumer)
            price_index_step!(consumer, t, model.producers)
        end
    end
    current_index = Dict{Tuple{String,String},Float64}()
    for (crop, model) in models
        for consumer in values(model.consumers)
            current_index[(crop, consumer.id)] = consumer.crop_price_index
        end
    end
    for (crop, model) in models
        for consumer in values(model.consumers)
            ε_d = consumer.local_params[:ε_d]
            consumer.substitution_factor = substitution_factor(
                crop, consumer.id, t, ξ, ε_d, current_index, reference_index,
            )
        end
    end
    for (crop, model) in models
        for consumer in values(model.consumers)
            procurement_step!(consumer, t, model.producers)
            consumer.substitution_factor_prev = consumer.substitution_factor
        end
    end
end

include("model/initialization.jl")

using .InitializationModule

end
