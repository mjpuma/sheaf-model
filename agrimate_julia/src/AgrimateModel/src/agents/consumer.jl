module ConsumerModule

export delivery_step!, consumption_step!, accounting_step!, procurement_step!, price_index_step!

using Parameters
using Statistics: mean

using ..AgentsModule

function delivery_step!(consumer)
    @unpack δ = consumer.local_params
    delivery = popfirst!(consumer.delivery_queue)
    consumer.delivery = delivery.quantity
    consumer.delivery_price = delivery.price
    return consumer.storage *= 1 - δ
end

function consumption_step!(consumer)
    @unpack pipeline_stock = consumer.global_params
    @unpack ε_c, C_star, A_c_star = consumer.local_params

    consumer_price = determine_consumer_price(
        consumer.storage,
        consumer.price_stored,
        consumer.delivery,
        consumer.delivery_price;
    )
    consumption = determine_consumption(
        consumer_price,
        consumer.storage + consumer.delivery,
        # (1. - pipeline_stock) * consumer.storage + consumer.delivery,
        consumer.household_budget;
        ε_c,
        A_c_star = A_c_star * consumer.substitution_factor_prev,
    )

    consumer.consumption = consumption
    consumer.storage += consumer.delivery - consumer.consumption
    if consumer.storage < 0 
        consumer.storage = 0
    end
    return consumer.price_stored = consumer_price
end

function accounting_step!(consumer)
    total_purchase =
        reduce(+, transaction.quantity for transaction in consumer.transactions; init = 0.0)
    price_purchased = (
        total_purchase > 0 ?
        sum(
            transaction.quantity * transaction.price for
            transaction in consumer.transactions
        ) / total_purchase : 0
    )
    push!(consumer.delivery_queue, Delivery(total_purchase, price_purchased))
    # Update expectation on storage in N_del timesteps
    return consumer.expected_storage = determine_expected_storage(consumer)
end

function price_index_step!(consumer, t, producers::Dict{String,Producer};)
    @unpack σ = consumer.local_params
    @unpack two_markets = consumer.global_params

    empty!(consumer.demand_requests)

    update_offer_prices!(consumer, producers)
    update_demand_shares!(consumer, t, producers)

    consumer.crop_price_index = determine_crop_price_index(;
            suppliers = consumer.suppliers,
            demand_shares = consumer.demand_shares,
            offer_prices = consumer.offer_prices,
            σ,
        )
    if two_markets
        consumer.crop_price_index_domestic, consumer.crop_price_index_foreign = determine_crop_price_index_two_markets(;
            consumer_id = consumer.id,
            suppliers = consumer.suppliers,
            demand_shares = consumer.demand_shares,
            offer_prices = consumer.offer_prices,
            σ,
        )
    end
    return consumer
end

function procurement_step!(consumer, t, producers::Dict{String,Producer};)
    @unpack C_star, σ, ε_d, ε_d_domestic, ε_d_foreign = consumer.local_params
    @unpack ι, two_markets, ε_d_adjust = consumer.global_params

    consumer.extra_demand = determine_extra_demand(consumer, t)
    consumer.crop_budget_share =
    determine_crop_budget_share(consumer, t; ΔD = consumer.extra_demand)
    if two_markets && ε_d_adjust
        consumer.crop_price_index_domestic = consumer.crop_price_index
        consumer.crop_price_index_foreign = consumer.crop_price_index
        demands = determine_demands_two_markets(;
            consumer_id = consumer.id,
            suppliers = consumer.suppliers,
            demand_shares = consumer.demand_shares,
            offer_prices = consumer.offer_prices,
            price_index = consumer.crop_price_index,
            price_index_domestic = consumer.crop_price_index_domestic,
            price_index_foreign = consumer.crop_price_index_foreign,
            budget_share = consumer.crop_budget_share,
            budget = consumer.budget,
            σ,
            ε_d_domestic,
            ε_d_foreign,
        )
    else
        demands = determine_demands(;
            suppliers = consumer.suppliers,
            demand_shares = consumer.demand_shares,
            offer_prices = consumer.offer_prices,
            price_index = consumer.crop_price_index,
            budget_share = consumer.crop_budget_share,
            budget = consumer.budget,
            σ,
            ε_d,
        )
    end
    consumer.total_demand = sum(values(demands))
    
    for (producer_id, demand) in demands

        producer = producers[producer_id]
        reservation_price = consumer.offer_prices[producer_id]

        demand_request = Transaction(producer.id, consumer.id, demand, reservation_price)
        push!(consumer.demand_requests, demand_request)
        push!(producer.demand_requests, demand_request)
    end

    # Prepare for incoming transactions
    return empty!(consumer.transactions)
end

# Auxiliary functions

function determine_consumer_price(storage, price_stored, delivery, delivery_price)
    availability = storage + delivery
    consumer_price = (
        availability > 0 ?
        (storage * price_stored + delivery * delivery_price) / availability : 0
    )
    return consumer_price
end

function determine_consumption(
    consumer_price,
    availability,
    household_budget;
    ε_c,
    A_c_star,
)
    if availability == 0
        return 0
    end
    desired_consumption =
        A_c_star * consumer_price^(-ε_c) / (1 + A_c_star * (consumer_price^(1 - ε_c) - 1)) *
        household_budget
    return min(desired_consumption, availability)
end

function determine_expected_storage(consumer)
    @unpack pipeline_stock = consumer.global_params
    @unpack δ, ε_c, A_c_star = consumer.local_params
    expected_storage = consumer.storage
    expected_price_stored = consumer.price_stored
    if expected_storage < 0
        expected_storage = 0
    end
    for delivery in consumer.delivery_queue
        expected_storage *= 1 - δ
        expected_price_stored = determine_consumer_price(
            expected_storage,
            expected_price_stored,
            delivery.quantity,
            delivery.price,
        )
        expected_consumption = determine_consumption(
            expected_price_stored,
            expected_storage + delivery.quantity,
            # (1. - pipeline_stock) * expected_storage + delivery.quantity,
            consumer.household_budget;
            ε_c,
            A_c_star,
        )
        expected_storage += delivery.quantity - expected_consumption
        if expected_storage < 0
            expected_storage = 0
        end
    end
    return expected_storage
end

function update_offer_prices!(consumer, producers::Dict{String,Producer})

    for producer_id in consumer.suppliers
        producer = producers[producer_id]
        @unpack pol_opt, pol_exp_p, two_markets = producer.global_params
        if two_markets
            if producer_id != consumer.id
                consumer.offer_prices[producer_id] = producer.expected_price_foreign
            else
                consumer.offer_prices[producer_id] = producer.expected_price_domestic
            end
        elseif pol_exp_p && pol_opt
            consumer.offer_prices[producer_id] = producer.expected_price
        else
            consumer.offer_prices[producer_id] = producer.expected_price
            if pol_opt == false
                if producer_id != consumer.id
                    consumer.offer_prices[producer_id] *= producer.export_tax_factor
                end
            end
        end
       
    end
end

function update_demand_shares!(consumer, t, producers::Dict{String,Producer}) #switch should be removed after the decision which variant is taken
    @unpack N_year, ι = consumer.global_params
    @unpack σ, τ_a, C_star, switch_preference = consumer.local_params
    
    old_demand_shares = consumer.demand_shares
    for producer_id in consumer.suppliers
        producer = producers[producer_id]
        @unpack two_markets, X_star = producer.global_params

        a_star = consumer.baseline_demand_shares[producer_id][mod(t, 1:N_year)]
        
        if two_markets
            @unpack X_avg, X_avg_foreign, X_avg_domestic = producer.local_params
                            
            a_star_prev = consumer.demand_shares[producer_id]                
            mean_a_star = consumer.annual_demand_shares[producer_id]
            if consumer.id == producer_id
                ratio = producer.expected_sales_domestic  / X_avg_domestic
            else       
                ratio = producer.expected_sales_foreign / X_avg_foreign
            end
            a_star = mean_a_star * ratio
            consumer.demand_shares[producer_id] = mean_a_star * ratio

        elseif switch_preference == "restriction"
            if producer_id == consumer.id
                consumer.demand_shares[producer_id] = a_star
            else
                a_star_prev = consumer.baseline_demand_shares[producer_id][mod(t - 1, 1:N_year)]
                a_prev = consumer.demand_shares[producer_id]
                prev_ratio = (a_star_prev > 0 ? a_prev / a_star_prev : 1)
                export_restriction = 1 - producer.export_tax_factor^(-σ)
                consumer.demand_shares[producer_id] =
                    a_star * ((1 - 1 / τ_a) * prev_ratio + 1 / τ_a * (1 - export_restriction))
            end
        elseif switch_preference == "expectation"
                @unpack X_avg, two_markets = producer.local_params
                                
                mean_a_star = consumer.annual_demand_shares[producer_id]
                
                if consumer.id == producer_id
                    a_star = mean_a_star * ( producer.expected_sales  + producer.restricted_export ) / X_avg
                else       
                    a_star = mean_a_star * producer.expected_sales  / X_avg
                end
                consumer.demand_shares[producer_id] = a_star
        elseif switch_preference == "foreign"
                @unpack X_foreign_avg,X_domestic_avg = producer.local_params
                                
                mean_a_star = consumer.annual_demand_shares[producer_id]
                if consumer.id == producer_id
                    a_star = X_domestic_avg != 0. ? mean_a_star *  producer.expected_domestic_sales / X_domestic_avg : 0.
                else       
                    a_star = X_foreign_avg != 0. ? mean_a_star * producer.expected_foreign_sales / X_foreign_avg : 0.
                end

                consumer.demand_shares[producer_id] = a_star
        elseif switch_preference == "expectation_decay"
                @unpack X_avg = producer.local_params
                
                a_star_prev = consumer.demand_shares[producer_id]                
                mean_a_star = consumer.annual_demand_shares[producer_id]
                
                a_star = mean_a_star * producer.expected_sales / X_avg
                prev_ratio = (a_star_prev > 0 ? a_star / a_star_prev : 1)
                consumer.demand_shares[producer_id] = a_star * (1 - 1 / τ_a) * prev_ratio

        elseif switch_preference == "baseline"
            consumer.demand_shares[producer_id] = a_star
        elseif switch_preference == "former"
            if producer_id == consumer.id
                consumer.demand_shares[producer_id] = a_star
            else
                a_star_prev = consumer.baseline_demand_shares[producer_id][mod(t - 1, 1:N_year)]
                a_prev = consumer.demand_shares[producer_id]
                prev_ratio = (a_star_prev > 0 ? a_prev / a_star_prev : 1)
                consumer.demand_shares[producer_id] = a_star * (1 - 1 / τ_a) * prev_ratio 
            end

        end

    end
    # Ensure normalization
    
    a_sum = sum(values(consumer.demand_shares))
    for producer_id in consumer.suppliers
        if a_sum != 0
            consumer.demand_shares[producer_id] /= a_sum
        else
            consumer.demand_shares[producer_id] = 1/length(consumer.suppliers)
        end
    end

end

function determine_crop_budget_share(consumer, t; ΔD = 0)
    @unpack N_year = consumer.global_params
    @unpack ε_d, A_d_star = consumer.local_params
    # Demand in timestep t is determined by price in timestep t + 1
    B = consumer.budget
    p = consumer.crop_price_index
    A_d_star = consumer.baseline_crop_budget_share[mod(t, 1:N_year)]
    A_d = A_d_star * consumer.substitution_factor + p * ΔD / B
    A_d = max(0, min(A_d, 1))
    return A_d
end

function determine_crop_price_index(; suppliers, demand_shares, offer_prices, σ)
    p = sum(demand_shares[id] * offer_prices[id]^(1 - σ) for id in suppliers)^(1 / (1 - σ))
    return p
end

function determine_crop_price_index_two_markets(; consumer_id, suppliers, demand_shares, offer_prices, σ)
    p_domestic = 0.
    p_foreign = 0.
    for id in suppliers
        if id == consumer_id
            p_domestic = demand_shares[id] * offer_prices[id]
        else
            p_foreign += demand_shares[id] * offer_prices[id]^(1 - σ)
        end
    end
    if p_foreign != 0.
        p_foreign = p_foreign^(1 / (1 - σ))
    end
    return p_domestic,p_foreign
end

function determine_extra_demand(consumer, t)
    @unpack N_year, N_del = consumer.global_params
    @unpack τ, δ = consumer.local_params
    target_storage = consumer.baseline_storage[mod(t + N_del, 1:N_year)]
    storage_demand = (target_storage - consumer.expected_storage) / τ
    loss_demand = δ * target_storage
    ΔD = storage_demand + loss_demand
    return ΔD
end

function determine_demands(;
    suppliers,
    demand_shares,
    offer_prices,
    price_index,
    budget_share,
    budget,
    σ,
    ε_d,
)
    global_factor =
        budget_share * price_index^(-ε_d) /
        (1 + budget_share * (price_index^(1 - ε_d) - 1)) * budget
    return Dict(
        id => offer_prices[id] > 1e-4 ? demand_shares[id] * (offer_prices[id] / price_index)^(-σ) * global_factor : 0. for
        id in suppliers
    )
end
function determine_demands_two_markets(;
    consumer_id,
    suppliers,
    demand_shares,
    offer_prices,
    price_index,
    price_index_domestic,
    price_index_foreign,
    budget_share,
    budget,
    σ,
    ε_d_domestic,
    ε_d_foreign,
)
    
    global_factor_domestic =
        budget_share * price_index_domestic^(-ε_d_domestic) /
        (1 + budget_share * (price_index_domestic^(1 - ε_d_domestic) - 1)) * budget
    global_factor_foreign =
        budget_share * price_index_foreign^(-ε_d_foreign) /
        (1 + budget_share * (price_index_foreign^(1 - ε_d_foreign) - 1)) * budget
    return Dict(
        id => id == consumer_id ? demand_shares[id] * (offer_prices[id] / price_index_domestic )^(-σ) * global_factor_domestic : demand_shares[id] * (offer_prices[id] /  price_index_foreign)^(-σ) * global_factor_foreign for
        id in suppliers
    )
    
end

function P_inv(p, α, λ)
    if λ == 0
        return p .^ (-1 / α)
    elseif λ == 1
        return 1 .- (p .- 1) ./ α
    else
        return (1 .- (p .^ λ .- 1) ./ α) .^ (1 / λ)
    end
end

end
