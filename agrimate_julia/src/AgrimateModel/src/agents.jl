module AgentsModule

export Producer, Consumer, Transaction, Delivery
export harvest_step!, sales_step!, communication_step!, export_restriction_step!, policy_implementation_step!, get_storage_timeseries
export delivery_step!, consumption_step!, accounting_step!, procurement_step!, price_index_step!

using DataStructures: Deque, DefaultDict

struct Transaction
    seller_id::String
    buyer_id::String
    quantity::Float64
    price::Float64
end

struct Delivery
    quantity::Float64
    price::Float64
end

abstract type Agent end

mutable struct Producer <: Agent
    id::String
    # State variables
    harvest::Float64
    expected_harvests::Vector{Float64}
    storage::Float64
    expected_price::Float64
    expected_price_domestic::Float64
    expected_price_foreign::Float64
    expected_sales::Float64
    expected_sales_domestic::Float64
    expected_sales_foreign::Float64
    expected_profit::Float64
    domestic_demand_compensation::Float64
    restricted_export::Float64
    expected_others_sales_foreign::Vector{Float64}
    expected_others_sales_to_domestic_market::Float64
    price_adjustment_factor::Float64
    price_adjustment_factor_foreign::Float64
    price_adjustment_factor_domestic::Float64
    expected_others_sales::Vector{Float64}
    export_restrictions::Vector{Float64}
    baseline_sales::Vector{Float64}
    baseline_sales_foreign::Vector{Float64}
    baseline_sales_domestic::Vector{Float64}
    baseline_storage::Vector{Float64}
    transactions::Vector{Transaction}
    # Auxiliary variables
    demand_requests::Vector{Transaction}
    total_sales::Float64
    sales_domestic::Float64
    sales_foreign::Float64
    optimal_sales::Vector{Float64}
    optimal_sales_domestic::Vector{Float64}
    optimal_sales_foreign::Vector{Float64}
    export_restriction::Float64
    export_tax_factor::Float64
    market_size::Float64
    market_size_unique::Float64
    # Global paramaters
    global_params::DefaultDict{Symbol,Any,Nothing}
    # Agent parameters
    local_params::DefaultDict{Symbol,Any,Nothing}
    function Producer(id; local_params, global_params)
        producer = new()
        producer.id = id
        producer.local_params = DefaultDict(nothing, Dict{Symbol,Any}(pairs(local_params)))
        producer.global_params = DefaultDict(nothing, Dict{Symbol,Any}(pairs(global_params)))
        producer.demand_requests = Transaction[]
        producer.transactions = Transaction[]
        return producer
    end
end

mutable struct Consumer <: Agent
    id::String
    # State variables
    delivery::Float64
    delivery_price::Float64
    delivery_queue::Deque{Delivery}
    storage::Float64
    price_stored::Float64
    domestic_profit_factor::Float64
    suppliers::Vector{String}
    baseline_consumption::Vector{Float64}
    baseline_storage::Vector{Float64}
    demand_requests::Vector{Transaction}
    # Auxiliary variables
    consumption::Float64
    expected_storage::Float64
    extra_demand::Float64
    total_demand::Float64
    # sales::Vector{Float64}
    baseline_price::Vector{Float64}
    baseline_demand::Vector{Float64}
    budget::Float64
    household_budget::Float64
    crop_budget_share::Float64
    baseline_crop_budget_share::Vector{Float64}
    annual_demand_shares::Dict{String,Float64}
    demand_shares::Dict{String,Float64}
    baseline_demand_shares::Dict{String,Vector{Float64}}
    # expected_sales::Vector{Float64}
    offer_prices::Dict{String,Float64}
    crop_price_index::Float64
    crop_price_index_domestic::Float64
    crop_price_index_foreign::Float64
    transactions::Vector{Transaction}
    substitution_factor::Float64
    substitution_factor_prev::Float64
    # Global paramaters
    global_params::DefaultDict{Symbol,Any,Nothing}
    # Agent parameters
    local_params::DefaultDict{Symbol,Any,Nothing}
    function Consumer(id; local_params, global_params)
        consumer = new()
        consumer.id = id
        consumer.local_params = DefaultDict(nothing, Dict{Symbol,Any}(pairs(local_params)))
        consumer.global_params = DefaultDict(nothing, Dict{Symbol,Any}(pairs(global_params)))
        consumer.demand_requests = Transaction[]
        consumer.transactions = Transaction[]
        consumer.delivery_queue = Deque{Delivery}()
        consumer.substitution_factor = 1.0
        consumer.substitution_factor_prev = 1.0
        return consumer
    end
end


include("agents/producer.jl")
include("agents/consumer.jl")

using .ProducerModule
using .ConsumerModule

end
