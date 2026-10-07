module InitializationModule

export create_agents!, initialize_agents!

using Parameters
using Statistics: mean

using ..ModelModule, ..AgentsModule
using ..AgentsModule.ProducerModule: P, optimize_periodic_sales
using ..AgentsModule.ConsumerModule:
    P_inv, determine_crop_budget_share, determine_crop_price_index

include("producer_initialization.jl")
include("consumer_initialization.jl")
include("baseline_trade_initialization.jl")
include("baseline_observation.jl")

function create_hetereogenous_agents!(
    model::Model;
    producer_params::AbstractDict,
    consumer_params::AbstractDict,
)
    empty!(model.producers)
    empty!(model.consumers)
    for (id, params) in producer_params
        model.producers[id] =
            Producer(id; local_params = params, global_params = model.global_params)
    end
    for (id, params) in consumer_params
        model.consumers[id] =
            Consumer(id; local_params = params, global_params = model.global_params)
    end
end

function create_agents!(
    model::Model;
    producer_ids::Vector{String},
    consumer_ids::Vector{String},
    producer_params,
    consumer_params,
)
    producer_params = Dict(id => producer_params for id in producer_ids)
    consumer_params = Dict(id => consumer_params for id in consumer_ids)

    return create_hetereogenous_agents!(model; producer_params, consumer_params)
end

function initialize_agents!(
    model::Model,
    init_data::InitializationData;
    n_start = 1,
    κ = 0.25,
    tol = 1e-8,
    max_iter = 750,
    output_baseline_data = nothing,
    verbose::Bool = true,
)
    @assert length(model.producers) == length(init_data.baseline_harvests)
    @assert length(model.consumers) == length(init_data.baseline_consumption)

    @unpack N_year = model.global_params

    # PRODUCERS

    mean_baseline_harvest =
        Dict(id => mean(harvests) for (id, harvests) in init_data.baseline_harvests)

    X_star = sum(values(mean_baseline_harvest))
    market_size = Dict{String,Float64}()
    producer_sales_foreign = Dict(producer_id => 0.0 for producer_id in keys(model.producers))
    producer_sales_domestic = Dict(producer_id => 0.0 for producer_id in keys(model.producers))
    purchaser_share_per_producer_baseline = Dict{String,Dict{String,Float64}}()
    producer_sales_total = Dict(producer_id => 0.0 for producer_id in keys(model.producers))
    producer_import = Dict(producer_id => 0.0 for producer_id in keys(model.producers))
    producer_consumption = Dict(producer_id => 0.0 for producer_id in keys(model.producers))
    for (producer_id, consumer_id) in keys(init_data.baseline_transactions)
        if producer_id in keys(market_size)
            market_size[producer_id] += init_data.baseline_consumption[consumer_id]
        else
            market_size[producer_id] = init_data.baseline_consumption[consumer_id]
        end
        if producer_id in keys(purchaser_share_per_producer_baseline)
            purchaser_share_per_producer_baseline[producer_id][consumer_id] = init_data.baseline_transactions[(producer_id,consumer_id)]
        else
            purchaser_share_per_producer_baseline[producer_id] = Dict(consumer_id => init_data.baseline_transactions[(producer_id,consumer_id)])
        end
        if producer_id != consumer_id
            producer_sales_foreign[producer_id] += init_data.baseline_transactions[(producer_id,consumer_id)]
            if consumer_id in keys(producer_import) 
                producer_import[consumer_id] += init_data.baseline_transactions[(producer_id,consumer_id)]
            end
        else
            producer_sales_domestic[producer_id] += init_data.baseline_transactions[(producer_id,consumer_id)]
        end
        if consumer_id in keys(producer_import) 
            producer_consumption[consumer_id] += init_data.baseline_transactions[(producer_id,consumer_id)]
        end
         
        producer_sales_total[producer_id] += init_data.baseline_transactions[(producer_id,consumer_id)]
    end
    foreign_purchaser_share_per_producer_baseline = Dict(consumer_id => Dict(consumer_id => 0.0 for consumer_id in keys(model.consumers)) for consumer_id in keys(model.consumers))
    for (producer_id, consumer_id) in keys(init_data.baseline_transactions)
        if producer_id != consumer_id
            foreign_purchaser_share_per_producer_baseline[consumer_id][producer_id] = producer_sales_foreign[producer_id] != 0 ? init_data.baseline_transactions[(producer_id,consumer_id)] / producer_sales_foreign[producer_id] : 0.
        end

        purchaser_share_per_producer_baseline[producer_id][consumer_id] = purchaser_share_per_producer_baseline[producer_id][consumer_id] / producer_sales_total[producer_id]
    end
    share_imports_foreign_sales_other_producers = Dict(producer_id => 0.0 for producer_id in keys(model.producers))
    for producer in keys(share_imports_foreign_sales_other_producers)
        share_imports_foreign_sales_other_producers[producer] = producer_import[producer] / sum(producer_sales_foreign[other_producer] for other_producer in keys(producer_sales_foreign) if other_producer != producer)
    end


    baseline_transactions_by_consumer = Dict{String,Dict{String,Float64}}()
    for ((producer_id, consumer_id), quantity) in init_data.baseline_transactions
        if consumer_id in keys(baseline_transactions_by_consumer)
            baseline_transactions_by_consumer[consumer_id][producer_id] = quantity
        else
            baseline_transactions_by_consumer[consumer_id] = Dict(producer_id => quantity)
        end
    end

    market_size_unique = Dict(producer_id => 0.0 for producer_id in keys(model.producers))
    for (consumer_id, baseline_transactions) in baseline_transactions_by_consumer
        if length(baseline_transactions) == 1
            producer_id = first(keys(baseline_transactions))
            market_size_unique[producer_id] += init_data.baseline_consumption[consumer_id]
        end
    end
    #attempt to fix the initial calculation problem for rice and corn
    for producer in values(model.producers)
        if market_size_unique[producer.id] == market_size[producer.id]
            market_size_unique[producer.id] = 0.
        end
    end

    for producer in values(model.producers)
        @unpack α_domestic,α_foreign = producer.local_params
        @unpack α_adj = producer.global_params

        # Set X_star
        producer.global_params[:X_star] = X_star
        producer.global_params[:X_only_foreign] = sum(values(producer_sales_foreign))

        producer.global_params[:sales_baseline_foreign] = sum(values(producer_sales_foreign))
         
        # Set X_star_foreign --> Mean annual sells from producer to only foreign purchasers
        producer.local_params[:X_star_foreign] = producer_sales_foreign[producer.id] > 0. ? producer_sales_foreign[producer.id] : 0.
        # Set X_star_domestic --> Mean annual sells from producer to domestic purchaser + imports of producing region
        producer.local_params[:X_star_domestic] = producer_consumption[producer.id] 
        

        producer.local_params[:X_foreign] = (sum(values(producer_sales_foreign)) - producer_import[producer.id] ) 
        # Set X_avg
        producer.local_params[:X_avg] = mean_baseline_harvest[producer.id]

        # Set sales_share_foreign_baseline
        producer.local_params[:sales_share_foreign_baseline] = producer_sales_foreign[producer.id] / producer_sales_total[producer.id] > 0. ? producer_sales_foreign[producer.id] / producer_sales_total[producer.id] : 0.
        # Set X_avg_foreign
        producer.local_params[:X_avg_foreign] = producer.local_params[:X_avg] * producer.local_params[:sales_share_foreign_baseline]
        # Set X_avg_domestic
        producer.local_params[:X_avg_domestic] = producer.local_params[:X_avg] * (1. - producer.local_params[:sales_share_foreign_baseline]) > 0 ? producer.local_params[:X_avg] * (1. - producer.local_params[:sales_share_foreign_baseline]) : 0.
        # Set Producer self supply
        producer.local_params[:annual_self_supply] = producer_sales_domestic[producer.id]
        # Set domestic profit factor

        if α_adj
            producer.local_params[:α_domestic] = producer_sales_domestic[producer.id] > 0 && producer_sales_foreign[producer.id] > 0 ? producer.local_params[:α_foreign] * producer.local_params[:X_star_domestic] * producer_sales_foreign[producer.id] / ( producer.global_params[:X_only_foreign] * producer_sales_domestic[producer.id] ) : producer.local_params[:α_domestic] 
            if producer.local_params[:α_domestic] > 1.
                producer.local_params[:α_domestic] = 1.
            end
            model.consumers[producer.id].local_params[:ε_d_domestic] = 1. /producer.local_params[:α_domestic] 
          
        end
        # println(producer.id, " & ", round(producer.local_params[:α_domestic]; digits=4), " & ", round(share_imports_foreign_sales_other_producers[producer.id]; digits=4))
        
        # Set share of imports of producer to the total foreign sales of other producer
        producer.local_params[:share_imports_foreign_sales_other_producers] = share_imports_foreign_sales_other_producers[producer.id]
        

        # Set share of each purchaser to the total sales of a producer
        producer.local_params[:purchaser_share] = purchaser_share_per_producer_baseline[producer.id]
        # Set share of each foreign purchaser to the total FOREIGN sales of a producer
        producer.local_params[:purchaser_foreign_share] = foreign_purchaser_share_per_producer_baseline[producer.id]
        # Set market size
        producer.market_size = market_size[producer.id]
        
        # Set size of market for which the producer is the unique supplier
        producer.market_size_unique = market_size_unique[producer.id]
        # Set local price adjustment factor to one
        producer.price_adjustment_factor = 1
        producer.price_adjustment_factor_domestic = 1
        producer.price_adjustment_factor_foreign = 1
        # Set export restriction to zero
        producer.export_restriction = 0
        producer.export_tax_factor = 1
    end
    # Pre-initialize producers for the Nash equilibrium procedure
    for producer in values(model.producers)
        producer.expected_harvests = init_data.baseline_harvests[producer.id]
        # Set initial beginning storage and initial optimal sales to mean baseline harvest
        producer.storage = 0
        producer.optimal_sales = mean_baseline_harvest[producer.id] .* ones(N_year)
        producer.optimal_sales_foreign = producer.local_params[:sales_share_foreign_baseline] * producer.optimal_sales
        producer.optimal_sales_domestic = (1 - producer.local_params[:sales_share_foreign_baseline]) * producer.optimal_sales

    end
    for producer in values(model.producers)
        producer.expected_others_sales = sum(
            other_producer.optimal_sales
            for other_producer in values(model.producers) if other_producer.id != producer.id
        ) 
    end
    
    # println("before nash equil")
    # Find Nash equilibrium
    succes = equilibrate_producers!(model; κ, tol, max_iter, verbose)
    @assert succes == true
    # println("after nash equil")

    # Set baseline sales and storage
    for producer in values(model.producers)
        producer.baseline_sales = producer.optimal_sales
        producer.baseline_sales_foreign = producer.optimal_sales_foreign
        producer.baseline_sales_domestic = producer.optimal_sales_domestic

        producer.baseline_storage = get_storage_timeseries(
            producer.expected_harvests,
            producer.baseline_sales,
            producer.storage;
            δ = producer.local_params[:δ],
        )
    end

    # Initialize producers' state variables
    @unpack N_hor, N_year = model.global_params

    for producer in values(model.producers)
        producer.harvest =
            init_data.baseline_harvests[producer.id][mod(n_start - 1, 1:N_year)]
        producer.expected_harvests = Vector{Float64}(undef, N_hor)
        producer.optimal_sales = Vector{Float64}(undef, N_hor + 1)
        producer.optimal_sales_foreign = Vector{Float64}(undef, N_hor + 1)
        producer.optimal_sales_domestic = Vector{Float64}(undef, N_hor + 1)
        producer.optimal_sales[1] = producer.baseline_sales[mod(n_start - 1, 1:N_year)]
        producer.optimal_sales_foreign[1] = producer.local_params[:sales_share_foreign_baseline] * producer.baseline_sales[mod(n_start - 1, 1:N_year)]
        producer.optimal_sales_domestic[1] = (1 - producer.local_params[:sales_share_foreign_baseline]) * producer.baseline_sales[mod(n_start - 1, 1:N_year)]
        for n in 1:N_hor
            producer.expected_harvests[n] =
                init_data.baseline_harvests[producer.id][mod(n_start - 1 + n, 1:N_year)]
            producer.optimal_sales[n + 1] =
                producer.baseline_sales[mod(n_start - 1 + n, 1:N_year)]
            producer.optimal_sales_foreign[n + 1] =
                producer.local_params[:sales_share_foreign_baseline] * producer.baseline_sales[mod(n_start - 1 + n, 1:N_year)]
            producer.optimal_sales_domestic[n + 1] =
                (1 - producer.local_params[:sales_share_foreign_baseline]) * producer.baseline_sales[mod(n_start - 1 + n, 1:N_year)]
        end
        producer.storage = producer.baseline_storage[mod(n_start - 1, 1:N_year)]
    end

    total_baseline_sales =
        sum(producer.baseline_sales for producer in values(model.producers))

    for producer in values(model.producers)
        producer.expected_others_sales = Vector{Float64}(undef, N_hor)
        producer.expected_others_sales_foreign = Vector{Float64}(undef, N_hor)
        # Important: these expectations are to be used in step n_start (not n_start - 1)!
        for n in 1:N_hor
            producer.expected_others_sales[n] =
                total_baseline_sales[mod(n_start + n, 1:N_year)] -
                producer.baseline_sales[mod(n_start + n, 1:N_year)]
            val = 0
            for other_producer in values(model.producers)
                if producer.id != other_producer.id
                    val = val + other_producer.baseline_sales_foreign[mod(n_start + n, 1:N_year)]
                end
            end
            producer.expected_others_sales_foreign[n] = val
        end
        producer.expected_sales = producer.baseline_sales[n_start]
        producer.expected_sales_foreign = producer.baseline_sales[n_start] * producer.local_params[:sales_share_foreign_baseline]
        producer.expected_sales_domestic = producer.baseline_sales[n_start] * ( 1 - producer.local_params[:sales_share_foreign_baseline])
    end




    #Initialize export restriction of producer
    for producer in values(model.producers)
        producer.export_restrictions = Vector{Float64}(undef, N_hor+1)
        # Important: these expectations are to be used in step n_start (not n_start - 1)!
        for n in 1:N_hor+1
            producer.export_restrictions[n] = 0
        end
    end

    @unpack α, λ = first(values(model.producers)).local_params
    # TODO: α and λ should be global parameters
    baseline_price = P(total_baseline_sales ./ X_star, α, λ)

    for producer in values(model.producers)
        producer.expected_price = baseline_price[n_start]
        producer.expected_profit = 0.
    end

    # CONSUMERS

    @unpack N_del, N_year, baseline_tol = model.global_params

    baseline_consumer_prices = Dict{String,Vector{Float64}}()

    for consumer in values(model.consumers)
        @unpack δ, ψ, ε_c, ε_d, A_d_star, A_c_star = consumer.local_params

        C_star = init_data.baseline_consumption[consumer.id]
        consumer.baseline_price = baseline_price
        # Price in timestep t + 1 determines demand in timestep t
        consumer.baseline_demand = P_inv.(circshift(baseline_price, -1), α, λ) .* C_star

        (baseline_consumption, baseline_storage, baseline_p_sto) = solve_consumer_baseline(
            consumer.baseline_demand,
            consumer.baseline_price,
            C_star;
            N_year,
            N_del,
            ψ,
            ε = ε_c,
            A = A_c_star,
            κ = 0.5,
            tol = (!isnothing(baseline_tol) ? baseline_tol : 1e-6),
            max_iter = 100,
            verbose,
        )

        baseline_consumer_prices[consumer.id] = baseline_p_sto

        # Baseline consumption
        consumer.local_params[:C_star] = C_star
        consumer.baseline_consumption = baseline_consumption


        # Suppliers
        consumer.suppliers = collect(keys(baseline_transactions_by_consumer[consumer.id]))

        # Baseline storage
        consumer.baseline_storage = baseline_storage

        # Storage
        consumer.storage = consumer.baseline_storage[mod(n_start - 1, 1:N_year)]

        # Price of stored commodity
        consumer.price_stored = baseline_p_sto[mod(n_start - 1, 1:N_year)]

        # Storage expected
        consumer.expected_storage =
            consumer.baseline_storage[mod(n_start - 1 + N_del, 1:N_year)]

        # Delivery queue
        empty!(consumer.delivery_queue)
        for n in n_start:(n_start + N_del - 1)
            delivery_price = baseline_price[mod(n - N_del, 1:N_year)]
            delivery =
                consumer.baseline_demand[mod(n - N_del, 1:N_year)] +
                δ * consumer.baseline_storage[mod(n - 1, 1:N_year)]
            push!(consumer.delivery_queue, Delivery(delivery, delivery_price))
        end

        # Initialize empty fields
      

        consumer.budget =
            mean(consumer.baseline_price .* consumer.baseline_demand) / A_d_star

        # Initialize baseline crop budget share
        let B = consumer.budget,
            p_star = circshift(baseline_price, -1),
            D_star = consumer.baseline_demand

            consumer.baseline_crop_budget_share =
                (p_star .^ (1 - ε_d) .* (B ./ (p_star .* D_star) .- 1) .+ 1) .^ (-1)
        end
        consumer.crop_budget_share =
            consumer.baseline_crop_budget_share[mod(n_start, 1:N_year)]
        consumer.offer_prices = Dict(
            producer_id => consumer.baseline_price[mod(n_start, 1:N_year)] for
            producer_id in consumer.suppliers
        )

        consumer.household_budget =
            C_star / mean(
                baseline_p_sto .^ (-ε_c) ./
                (1 .+ A_c_star .* (baseline_p_sto .^ (1 - ε_c) .- 1)),
            ) / A_c_star
    end

    # TRADE FLOWS

    # Demand in timestep t - 1 determines purchases in timestep t
    baseline_purchases = Dict(
        id => circshift(consumer.baseline_demand, 1) for (id, consumer) in model.consumers
    )
    baseline_sales =
        Dict(id => producer.baseline_sales for (id, producer) in model.producers)
    annual_baseline_transactions =
        Dict(key => X * N_year for (key, X) in init_data.baseline_transactions)

    function get_baseline_trade(tol = (!isnothing(baseline_tol) ? baseline_tol : 1e-6))
        try
            baseline_trade = determine_baseline_trade(
                baseline_sales,
                baseline_purchases,
                annual_baseline_transactions;
                tol,
                verbose,
            )
            if tol > 1e-6
                @warn "Reduced accuracy of baseline trade solution (tol=$(round(tol; digits=6)))."
            end
            return baseline_trade
        catch e
            if e isa AssertionError
                tol *= 10^(1 / 3)
                if tol > 1.01e-1
                # if tol > 1.01e-3
                    @error "Baseline trade solution cannot be found with a satisfactory accuracy (tol=$(round(tol; digits=6)))."
                    return nothing
                end
                return get_baseline_trade(tol)
            end
        end
    end

    baseline_transactions = get_baseline_trade()
    # Nullify negative trade flows
    # TODO: implement a warning to the user
    baseline_transactions =
        Dict(key => max.(values, 0) for (key, values) in baseline_transactions)

    # Initialize baseline demand shares

    for consumer in values(model.consumers)
        consumer.baseline_demand_shares = Dict{String,Vector{Float64}}()
        consumer.demand_shares = Dict{String,Float64}()
        consumer.annual_demand_shares = Dict{String,Float64}()
    end

    
    for ((producer_id, consumer_id), trade_flow) in baseline_transactions
        consumer = model.consumers[consumer_id]
        # Trade flow in timestep t + 1 determines demand in timestep t
        consumer.baseline_demand_shares[producer_id] =
            circshift(trade_flow, -1) ./ consumer.baseline_demand
        consumer.annual_demand_shares[producer_id] = sum(trade_flow) / sum(consumer.baseline_demand)
    end
    


    # Initialize demand shares and crop price index

    for consumer in values(model.consumers)
        for producer_id in consumer.suppliers
            consumer.demand_shares[producer_id] =
                consumer.baseline_demand_shares[producer_id][mod(n_start, 1:N_year)]
        end
    end

    # Initialize demand requests
    for producer in values(model.producers)
        empty!(producer.demand_requests)
    end
    for consumer in values(model.consumers)
        consumer.total_demand = consumer.baseline_demand[mod(n_start, 1:N_year)]
        # Send demand requests
        empty!(consumer.demand_requests)
        for producer_id in consumer.suppliers
            producer = model.producers[producer_id]
            price = baseline_price[mod(n_start, 1:N_year)]
            quantity =
                consumer.baseline_demand_shares[producer_id][mod(n_start, 1:N_year)] *
                consumer.total_demand
            demand_request = Transaction(producer.id, consumer.id, quantity, price)
            push!(consumer.demand_requests, demand_request)
            push!(producer.demand_requests, demand_request)
        end
    end

    if !isnothing(output_baseline_data)
        store_baseline_variables!(
            output_baseline_data,
            model,
            baseline_price,
            baseline_transactions,
            baseline_consumer_prices,
        )
    end
end

end
