module AgrimateModel

export AgrimateParams, InitializationData, InputData
export @AgrimateParamsMix
export initialize_model, initialize_model_run, run_model!

using DataFrames: DataFrame, allowmissing!
using Mixers
using Parameters




include("agents.jl")
include("model.jl")
include("run.jl")

using .AgentsModule, .ModelModule, .RunModule


@mix @with_kw struct AgrimateParamsMix
    N_year::Int = 24                                # timesteps per year
    N_hor::Int = 1 * N_year                         # timesteps of producer optimization horizon
    N_del::Int = 1 * (N_year ÷ 12)                  # timesteps per delivery
    α_domestic::Float64 = 1.0                       # - inverse elasticity of demand assumed by producers for DOMESTIC sells
    α_foreign::Float64 = 3.2                       # - inverse elasticity of demand assumed by producers for FOREIGN sells
    α::Float64 = 3.0                                # - inverse elasticity of demand assumed by producers
    λ::Float64 = 0.0                                # λ=1 => linear / λ=0 => power law inverse demand function assumed by producer
    storage_hold_back::Float64 = 0.00               # storage that is not allowed to be saled
    δ::Float64 = 0.0                                # storage deterioration (per year)
    ρ::Float64 = 0.0                                # interest rate (per year)
    β::Float64 = 0.05                               # strength of producers' local price adjustment
    p_sto::Float64 = 0.1                            # unit storage cost (per year)
    τ_exp::Float64 = 0.5                            # timescale (in yearly unit) of updating expectations on other producers' sales
    τ_P::Float64 = 0.2                              # timescale (in yearly unit) of local price adjustment
    σ::Float64 = 2.                                 # supplier substitution elasticity
    τ::Float64 = 0.1                                # timescale (in yearly unit) of balancing consumer inventory
    ψ::Union{Float64,Symbol} = :empirical                  # target stock-to-use ratio (annual)
    # ψ::Union{Float64,Symbol} = 0.3                  # target stock-to-use ratio (annual)
    ε_d::Float64 = 1 / α                           # - price elasticity of demand
    ε_d_domestic::Float64 = 1 / α_domestic                            # - price elasticity of demand for DOMESTIC sells
    ε_d_foreign::Float64 = 1 / α_foreign                            # - price elasticity of demand for FOREIGN sells
    ε_c::Float64 = 0.1                              # - price elasticity of consumption
    τ_a::Float64 = 0.2                              # timescale (in yearly unit) of supplier change due to export restrictions
    A_d_star::Union{Float64,Symbol} = :empirical           # baseline share of purchaser budget spent on commodity
    A_c_star::Union{Float64,Symbol} = :empirical           # baseline share of household budget spent on commodity
    # A_d_star::Union{Float64,Symbol} = 0.2           # baseline share of purchaser budget spent on commodity
    # A_c_star::Union{Float64,Symbol} = 0.2           # baseline share of household budget spent on commodity
    market_constraint::Bool = true                  # apply max constraint in producer optimization?
    unique_market_constraint::Bool = true           # apply min constraint in producer optimization?
    equal_constraint::Bool = false           # apply equality constraint to simulation optimization 
    rationing::Symbol = :proportional               # rationing scheme (all reservation prices are equal so this paramater doesn't matter) 
    N_for::Int = 3 * (N_year ÷ 12)                  # timesteps for which accurate harvest forecast is possbile
    τ_for::Float64 = 0.2                            # timescale (in yearly units) of transition between accurate and baseline forecast
    ι::Float64 = 0.001                              # relative cutoff under which no demand requests and price adjustment are made (for stability reasons)
    ζ::Float64 = 0.                                 # Penalty parameter for profit optimization. If set to 1., there is no penalty  in the profit optimization 
    # x_minimum::Float64 = 0.02                                 # Penalty parameter for profit optimization. If set to 1., there is no penalty  in the profit optimization 
    x_minimum::Float64 = 0.2                                 # total sales / (time_steps of horizon) = to_distribute, than x_minimum says how much of to_distribute shall be used for the minimum sales penalty
    optimization_tol::Union{Nothing,Float64} = 1e-4                # tolerance for optimization problem. If nothing: tolerances implemented in Dec' 22
    initialization_tol::Union{Nothing,Float64} = 1e-2                # tolerance for initialization of model. If nothing: tolerances implemented in Dec' 22
    baseline_tol::Union{Nothing,Float64} = 1e-4                # tolerance for baseline initialization of model. If nothing: tolerances implemented in Dec' 22
    pipeline_stock::Float64 = 0.02                              # share of stock, supplier and consumer, that is regarded for optimization to have some backup
    
    switch_preference::String = "expectation"                                # switch for purchaser preferences of supplier "restriction": export restriction are included "baseline": preferences are same as baseline "former": preferences arise from former preference with time decay
    pl_opt::Bool = false                                # switch if p_loc is in optimization or it is set to 1
    pol_opt::Bool = true                                # switch so new implemented export restriction is recognized in optimal and communicated sales:true || former version: false
    pol_exp_p::Bool = true                                # Gives you the correct way to form price expectation in the communication step only works with pol_opt==True| CAN PROBABLY BE DELETED
    pol_sales::Bool = true                                # switch so new implemented export restriction is recognized in optimal and communicated sales:true || former version: false
    pol_hor::Bool = true                                # 
    foreign_market::Bool = false                                # To have the optimization only for the foreign traded grain --> domestic sales and prices depend on that optimization
    two_markets::Bool = true                                # In the optimization, the foreign and domestic traded grains are seperated, have different prices.
    equal_domestic_sales::Bool = false                                # Turn on for two-market approach, where in everytime step there are the same domestic sales depending on baseline sales.
    α_adj::Bool = true                                # In the two-market approach: α_domestic is adjusted to fit similar marginal revenue change for domestic and foreign market
    ε_d_adjust::Bool = false                            # In two-market approach: ε_d is adjusted to ε_d_foreign and ε_d_domestic also in the demand decision of the consumer
    generalname::Union{String, Nothing} = nothing
end

@AgrimateParamsMix @with_kw struct AgrimateParams{} end


function initialize_model(
    init_data::InitializationData,
    agrimate_params::AgrimateParams;
    n_start = 1,
    κ = 0.25,
    tol = 1e-8,
    verbose = true,
    empirical_params::Dict = Dict(),
)

    @assert n_start == 1 "Start date must be 1st January"
    # TODO: replace t by a tuple (t, n_t); otherwise results with n_start != 1 will be incorrect

    @unpack δ = agrimate_params
    # @assert δ == 0 "Deterioration must be 0"
    # TODO: initialization should capture deterioration correctly (e.g. total harvest should exceed total consumption)
    # TODO: unique market constraint does not take deterioration correctly into account

    # Global params    
    @unpack N_year, N_hor, N_del, ι, ζ, x_minimum, optimization_tol, initialization_tol, baseline_tol, pl_opt, pol_opt,pol_exp_p,pol_sales, α_adj, ε_d_adjust, pol_hor,foreign_market, two_markets, pipeline_stock  = agrimate_params
    global_params = (; N_year, N_hor, N_del, ι, ζ, x_minimum, optimization_tol, initialization_tol, baseline_tol, pl_opt, pol_opt, α_adj,ε_d_adjust, pol_exp_p,pol_sales, pol_hor,foreign_market,two_markets, pipeline_stock)

    # Producer params
    @unpack α,α_domestic,α_foreign, λ, β, σ, δ, ρ, p_sto, τ_exp, τ_P, N_for, τ_for, storage_hold_back= agrimate_params
    @unpack market_constraint, unique_market_constraint, rationing, equal_constraint, equal_domestic_sales = agrimate_params
    producer_params = (; 
        α,α_domestic,α_foreign, λ, β, δ, ρ, σ, 
        N_for = N_for,
        p_sto = p_sto / N_year, 
        τ_exp = τ_exp * N_year, τ_P = τ_P * N_year, τ_for = τ_for * N_year,
        market_constraint, unique_market_constraint, rationing, storage_hold_back, equal_constraint, equal_domestic_sales
    )
    # @assert producer_params.τ_exp ≥ 1.
    # @assert producer_params.τ_P ≥ 1.

    # Consumer params
    @unpack α,α_domestic,α_foreign, σ, δ, τ, ψ, ε_c, ε_d, ε_d_domestic, ε_d_foreign, τ_a, A_d_star, A_c_star,switch_preference = agrimate_params

    consumer_params = (;
        α,α_domestic,α_foreign, σ, δ, ε_d, ε_d_domestic, ε_d_foreign, ε_c, A_d_star, A_c_star,
        ψ = (ψ isa Symbol ? ψ : ψ * N_year),
        τ = τ * N_year, τ_a = τ_a * N_year,
        switch_preference,
    )
    @assert consumer_params.τ ≥ 1.
    @assert consumer_params.τ_a ≥ 1.

    # Producers and consumer ids
    producer_ids = collect(keys(init_data.baseline_harvests))
    consumer_ids = collect(keys(init_data.baseline_consumption))
    model = Model(;global_params)
    create_agents!(model; producer_ids, consumer_ids, producer_params, consumer_params)

    # Load empirical params if present
    for (param, value) in Dict(pairs((;ψ, A_d_star, A_c_star)))
        !(value isa Symbol) && continue
        for (id, consumer) in model.consumers
            consumer.local_params[param] = empirical_params[param][id]
            if param == :ψ
                consumer.local_params[param] *= N_year
            end
        end
    end
    # exit()

    output_baseline_data = DataFrame(
        t = Int[],
        n = Int[],
        producer = String[],
        consumer = String[],
        variable = String[],
        value = Float64[],
    )
    allowmissing!(output_baseline_data)

    for (param, values) in empirical_params
        for (consumer_id, value) in values
            push!(
                output_baseline_data,
                Dict(
                    :t => missing,
                    :n => missing,
                    :producer => missing,
                    :consumer => consumer_id,
                    :variable => "$param",
                    :value => value,
                ),
            )
        end
    end

    initialize_agents!(model, init_data; n_start, output_baseline_data, κ, tol, verbose)
    return (model, output_baseline_data)
end





end
