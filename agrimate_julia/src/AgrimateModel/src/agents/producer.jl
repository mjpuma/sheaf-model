module ProducerModule

export harvest_step!, sales_step!, communication_step!, export_restriction_step!, policy_implementation_step!, get_storage_timeseries

using Parameters
using LinearAlgebra: LowerTriangular
using Statistics: mean

using ..AgentsModule

# Producers' actions

function harvest_step!(producer, harvest::Float64, expected_harvests::Vector{Float64})
    @unpack δ = producer.local_params
    producer.harvest = harvest
    producer.expected_harvests[:] .= expected_harvests
    # producer.expected_harvests[1:N_for] .= producer.harvest[t:t+N_for]
    producer.storage *= 1 - δ
end


function export_restriction_step!(producer,t,export_restriction_dict)
    @unpack N_hor, pol_hor = producer.global_params
    if pol_hor
        for n in 1:N_hor+1
            if (t+n-1,producer.id) in keys(export_restriction_dict)
                # producer.export_restrictions[n] =  export_restriction_dict[(t+n-1,producer.id)]
                if n > 1
                    if producer.export_restrictions[n-1] ==  export_restriction_dict[(t+n-1,producer.id)]
                        producer.export_restrictions[n] =  export_restriction_dict[(t+n-1,producer.id)]
                    else
                        producer.export_restrictions[n:N_hor] .= 0.     
                        break
                    end
                else
                    producer.export_restrictions[n] =  export_restriction_dict[(t+n-1,producer.id)]
                end
            else
                producer.export_restrictions[n:N_hor] .= 0.     
                break
            end
        end
    else
        if (t,producer.id) in keys(export_restriction_dict)
            producer.export_restrictions[1] = export_restriction_dict[(t,producer.id)]
            producer.export_restrictions[2:N_hor] .= 0.
        else
            producer.export_restrictions[1:N_hor] .= 0.
        end

        
    end
end


function sales_step!(producer, t, consumers::Dict{String,Consumer}; verbose::Bool = true)

    @unpack N_year, N_hor, ι, optimization_tol,pol_sales,foreign_market, two_markets, ζ, x_minimum, pipeline_stock = producer.global_params
    @unpack X_star,X_only_foreign, pl_opt, pol_opt = producer.global_params
    @unpack α, α_domestic, α_foreign, β, λ, δ, ρ, p_sto, τ_P, σ, storage_hold_back,equal_constraint = producer.local_params
    @unpack X_avg, X_avg_foreign, X_avg_domestic, domestic_profit_factor,  X_star_foreign,annual_self_supply, equal_domestic_sales, X_foreign, X_star_domestic, sales_share_foreign_baseline, share_imports_foreign_sales_other_producers = producer.local_params
    @unpack market_constraint, unique_market_constraint, rationing = producer.local_params
    
     # Sort demand requests
    sort!(producer.demand_requests, lt = (d1, d2) -> d1.price > d2.price)
    
    
    # Update local price adjustment factor
    D_tot = reduce(+, d.quantity for d in producer.demand_requests; init = 0.)
    D_tot_foreign = sum(d.quantity for d in producer.demand_requests if d.buyer_id != producer.id; init = 0.)
    D_tot_domestic = sum(d.quantity for d in producer.demand_requests if d.buyer_id == producer.id; init = 0.)
    if D_tot_foreign <  ι * X_avg
        D_tot_foreign = 0.
    end
    if D_tot_domestic <  ι * X_avg
        D_tot_domestic = 0.
    end
    X̂ = producer.expected_sales
    P_loc = producer.price_adjustment_factor
    P_loc_foreign = producer.price_adjustment_factor_foreign
    P_loc_domestic = producer.price_adjustment_factor_domestic
    P_loc_tgt = determine_target_price_adjustment_factor(P_loc, D_tot, X̂, β, ι * X_avg)
    # P_loc_tgt_foreign = determine_target_price_adjustment_factor(P_loc_foreign, D_tot_foreign, producer.expected_sales_foreign, β, ι * X_avg)
    # P_loc_tgt_domestic = determine_target_price_adjustment_factor(P_loc_domestic, D_tot_domestic, producer.expected_sales_domestic, β, ι * X_avg)
    P_loc_tgt_foreign = 1.
    P_loc_tgt_domestic = 1.
    # P_loc_tgt_foreign = P_loc_tgt
    # P_loc_tgt_domestic = P_loc_tgt
    # P_loc_tgt = 1.
    if producer.baseline_sales[mod(t, 1:N_year)] ≤ ι * X_avg
        P_loc_tgt = 1.
    end
    
    if τ_P == 0.
        producer.price_adjustment_factor = P_loc_tgt
        producer.price_adjustment_factor_foreign = P_loc_tgt_foreign
        producer.price_adjustment_factor_domestic = P_loc_tgt_domestic
    else
        producer.price_adjustment_factor = 1 / τ_P * P_loc_tgt + (1 - 1 / τ_P) * P_loc
        producer.price_adjustment_factor_foreign = 1 / τ_P * P_loc_tgt_foreign + (1 - 1 / τ_P) * P_loc_foreign
        producer.price_adjustment_factor_domestic = 1 / τ_P * P_loc_tgt_domestic + (1 - 1 / τ_P) * P_loc_domestic
    end
    #
    # Form current revenue expectation
    if two_markets 
        (revenue_curve, thresholds) = determine_revenue_curve_two_markets(producer.demand_requests,producer.id)
    else
        (revenue_curve, thresholds) = determine_revenue_curve(producer.demand_requests; rationing)
    end
    # All the demand requests are satisfied if the availability permits
    X1 = min(D_tot, producer.harvest + producer.storage) 

    # Needed for TWO MARKETS: Domestic and Foreign demand requests are satisfied if the availability permits ASSUMPTION: if not, domestic market are priotized 
    # X1_domestic = min(min(1.1 * producer.expected_sales_domestic, D_tot_domestic), producer.harvest + producer.storage)
    # X1_foreign = min(min(1.1 * producer.expected_sales_foreign,D_tot_foreign), producer.harvest + producer.storage - X1_domestic)
    X1_domestic = min( D_tot_domestic, producer.harvest + producer.storage)
    X1_foreign = min(D_tot_foreign, producer.harvest + producer.storage - X1_domestic)
    
    # Optimize sales
    H = vcat(producer.harvest, producer.expected_harvests)
    S_beg = producer.storage
    S_end = producer.baseline_storage[mod(t + N_hor, 1:N_year)]
    X_oth = producer.expected_others_sales
    
    X_init = vcat(
        producer.optimal_sales[2:end],
        producer.baseline_sales[mod(t + N_hor, 1:N_year)]
    )
    # Needed for TWO MARKETS
    X_oth_foreign = producer.expected_others_sales_foreign
    X_init_domestic = vcat(
        producer.optimal_sales_domestic[2:end],
        producer.baseline_sales_domestic[mod(t + N_hor, 1:N_year)]
    )
    
    X_init_foreign = vcat(
        producer.optimal_sales_foreign[2:end],
        producer.baseline_sales_foreign[mod(t + N_hor, 1:N_year)]
    )
    verbose && println("  Optimizing sales of $(producer.id)...")
    
    if two_markets
        X_avg_2 = X_avg / 2.
        X_norm_domestic = X_avg
        # X_norm_domestic = X_star_domestic
        X_norm_foreign = X_avg
        # X_norm_foreign = X_only_foreign
        # X_norm_domestic = 1.
        # X_norm_foreign = 1.

        producer.optimal_sales_domestic[:], producer.optimal_sales_foreign[:], producer.expected_profit = 
            optimize_sales_NLopt_two_markets(;
                revenue_curve = (x_dom,x_for) -> revenue_curve(x_dom * X_norm_domestic,x_for * X_norm_foreign ) ./ (X_norm_domestic,X_norm_foreign,1,1),
                x1_domestic = X1_domestic / X_norm_domestic,
                x1_foreign = X1_foreign / X_norm_foreign,
                h = H ./ X_norm_domestic,
                s_beg = S_beg / X_norm_domestic,
                # s_beg = (1. - pipeline_stock) * S_beg / X_norm_domestic,
                # s_end = S_end / X_norm_domestic,
                x_oth_domestic = share_imports_foreign_sales_other_producers .* producer.expected_others_sales_foreign ./ X_norm_domestic, 
                x_oth_foreign =  producer.expected_others_sales_foreign ./ X_norm_foreign,
                # x_oth_foreign = (1 - share_imports_foreign_sales_other_producers) .* producer.expected_others_sales_foreign ./ X_norm_foreign,
                # x_oth_domestic = zeros(length(producer.expected_others_sales_foreign)) ./ X_avg_2, 
                x_init_domestic = X_init_domestic ./ X_norm_domestic,
                x_init_foreign = X_init_foreign ./ X_norm_foreign,
                α_domestic,
                α_foreign,
                λ,
                δ,
                ρ,
                p_sto,
                x_star_domestic = X_star_domestic / X_norm_domestic,
                x_star_foreign = X_only_foreign / X_norm_foreign,
                # x_star_foreign = X_foreign / X_norm_foreign,
                N_hor,
                sales_share_foreign_baseline,
                x_market = (false ? producer.market_size / X_avg_foreign : nothing),
                # x_market = (market_constraint ? producer.market_size / X_norm_domestic : nothing),

                x_market_unique = (false ? producer.market_size_unique / X_avg_foreign : nothing),
                # x_market_unique = (unique_market_constraint ? producer.market_size_unique / X_norm_domestic : nothing),
                equal_constraint = equal_constraint,
                tol = (!isnothing(optimization_tol) ? optimization_tol : 1e-8 / X_avg_2),
                # tol = 1e-8 / X_avg,
                P_loc_domestic = 1.,
                P_loc_foreign = 1.,
                # P_loc_domestic = producer.price_adjustment_factor_domestic,
                # P_loc_foreign = producer.price_adjustment_factor_foreign,
                verbose = false,
                ζ = ζ,
                x_minimum = x_minimum,
                equal_domestic_sales = equal_domestic_sales ? (annual_self_supply / N_year) / X_norm_domestic : nothing,
                # storage_hold_back,
                domestic_profit_factor = 1.,
                # domestic_profit_factor = domestic_profit_factor,
                producer_id = producer.id,
                )


        producer.optimal_sales_domestic[:] = X_norm_domestic .* producer.optimal_sales_domestic[:]
        producer.optimal_sales_foreign[:] = X_norm_foreign .* producer.optimal_sales_foreign[:]
        producer.expected_profit = X_norm_domestic * producer.expected_profit # This is a quantities which does not make any sense more since there is normalized to different things


    elseif foreign_market && sales_share_foreign_baseline != 0
        opt_factor = sales_share_foreign_baseline

        producer.optimal_sales[:] =
            X_avg_foreign .* optimize_sales(;
                revenue_curve = (x1) -> revenue_curve(x1 * X_avg_foreign) ./ (X_avg_foreign, 1),
                x1_max = opt_factor * X1 / X_avg_foreign,
                x1_min = opt_factor * X1 / X_avg_foreign,
                x1_thresholds = thresholds ./ X_avg_foreign,
                h = opt_factor * H ./ X_avg_foreign,
                s_beg = opt_factor * S_beg / X_avg_foreign,
                s_end = opt_factor * S_end / X_avg_foreign,
                x_oth = producer.expected_others_sales_foreign ./ X_avg_foreign,
                x_init = opt_factor * X_init ./ X_avg_foreign,
                P_loc = (pl_opt ? producer.price_adjustment_factor : 1),
                α,
                λ,
                δ,
                ρ,
                p_sto,
                x_star = X_star_foreign / X_avg_foreign,
                N_hor,
                x_market = (market_constraint ? producer.market_size / X_avg_foreign : nothing),
                x_market_unique = (unique_market_constraint ? producer.market_size_unique / X_avg_foreign : nothing),
                equal_constraint = equal_constraint,
                tol = (!isnothing(optimization_tol) ? optimization_tol : 1e-8 / X_avg_foreign),
                # tol = 1e-8 / X_avg,
                verbose = false,
                storage_hold_back,
            )
        producer.optimal_sales[:] = producer.optimal_sales[:] / opt_factor
    else
        opt_factor = 1.
        producer.optimal_sales[:], producer.expected_profit =
             optimize_sales(;
                revenue_curve = (x1) -> revenue_curve(x1 * X_avg) ./ (X_avg, 1),
                x1_max = X1 / X_avg,
                x1_min = X1 / X_avg,
                x1_thresholds = thresholds ./ X_avg,
                h = H ./ X_avg,
                s_beg = S_beg / X_avg,
                s_end = S_end / X_avg,
                x_oth = X_oth ./ X_avg,
                x_init = X_init ./ X_avg,
                P_loc = (pl_opt ? producer.price_adjustment_factor : 1),
                α,
                λ,
                δ,
                ρ,
                p_sto,
                x_star = X_star / X_avg,
                N_hor,
                x_market = (market_constraint ? producer.market_size / X_avg : nothing),
                x_market_unique = (unique_market_constraint ? producer.market_size_unique / X_avg : nothing),
                equal_constraint = equal_constraint,
                tol = (!isnothing(optimization_tol) ? optimization_tol : 1e-8 / X_avg),
                # tol = 1e-8 / X_avg,
                verbose = false,
                storage_hold_back,
            )
        producer.optimal_sales[:] = X_avg .* producer.optimal_sales[:]
        producer.expected_profit = X_avg * producer.expected_profit
    end

    

    if two_markets
        # Update transactions
        producer.sales_domestic = producer.optimal_sales_domestic[1]
        producer.sales_foreign = producer.optimal_sales_foreign[1]
        producer.total_sales = producer.sales_domestic + producer.sales_foreign
        foreign_sales_ratio = producer.total_sales > 0 ? producer.sales_foreign / producer.total_sales : 0
        producer.export_restriction = producer.export_restrictions[1]
        empty!(producer.transactions)
        if pol_opt && pol_sales
            producer.transactions, producer.total_sales =
                determine_transactions_two_markets(producer.sales_domestic, producer.sales_foreign, producer.demand_requests, producer.export_restriction)
            # producer.total_sales = producer.total_sales * (1 - producer.export_restriction * foreign_sales_ratio)
        else
            producer.transactions =
                determine_transactions_two_markets(producer.sales_domestic, producer.sales_foreign, producer.demand_requests, 0.)
        end
    else
    
        # Update transactions
        producer.total_sales = get_current_sales(producer.optimal_sales)
    
        producer.export_restriction = producer.export_restrictions[1]
        empty!(producer.transactions)
        if pol_opt && pol_sales
            producer.transactions =
                determine_transactions(producer.total_sales, producer.demand_requests, producer.export_restriction; rationing)
            producer.total_sales = producer.total_sales * (1 - producer.export_restriction * sales_share_foreign_baseline)
        else
            producer.transactions =
                determine_transactions(producer.total_sales, producer.demand_requests, 0.; rationing)
        end     
    end
    # Send transactions
    for transaction in producer.transactions
        customer = consumers[transaction.buyer_id]
        push!(customer.transactions, transaction)
    end

    # Update storage
    producer.storage += producer.harvest - producer.total_sales
    # @assert producer.storage > -1e-4
    producer.storage = max(0, producer.storage)
end


    

    

function policy_implementation_step!(producer,t,consumers)
    @unpack pol_opt,ι, two_markets = producer.global_params
    @unpack sales_share_foreign_baseline,X_avg, σ = producer.local_params
    
    if two_markets
        pre_expected_sales_foreign = producer.optimal_sales_foreign[2] > 0 ? producer.optimal_sales_foreign[2] : 0. 
        # If expected sale is beneath threshold set it to zero
        if pre_expected_sales_foreign < ι * X_avg
            pre_expected_sales_foreign = 0.
        end
        producer.restricted_export = pre_expected_sales_foreign * producer.export_restrictions[2]
        producer.domestic_demand_compensation = consumers[producer.id].total_demand > producer.restricted_export ? producer.restricted_export : consumers[producer.id].total_demand
        producer.expected_sales_foreign = producer.optimal_sales_foreign[2] - producer.restricted_export
        producer.expected_sales_domestic = producer.optimal_sales_domestic[2] + producer.restricted_export

        producer.optimal_sales_domestic[2:end]  = producer.optimal_sales_domestic[2:end] .+ producer.optimal_sales_foreign[2:end] .* producer.export_restrictions[2:end]

        producer.optimal_sales_foreign[2:end]  = producer.optimal_sales_foreign[2:end] .* (1 .- producer.export_restrictions[2:end])
        producer.expected_sales = producer.expected_sales_foreign + producer.expected_sales_domestic
        
    elseif pol_opt
        pre_expected_sales = producer.optimal_sales[2] > 0 ? producer.optimal_sales[2] : 0. 
        # If expected sale is beneath threshold set it to zero
        if pre_expected_sales < ι * X_avg
            pre_expected_sales = 0.
        end
        producer.restricted_export = pre_expected_sales * producer.export_restrictions[1] * sales_share_foreign_baseline
        producer.domestic_demand_compensation = consumers[producer.id].total_demand > producer.restricted_export ? producer.restricted_export : consumers[producer.id].total_demand
        # producer.expected_sales_foreign = pre_expected_sales * sales_share_foreign_baseline * (1 - producer.export_restrictions[1])
        # producer.expected_sales_domestic = pre_expected_sales * (1 -  sales_share_foreign_baseline) + producer.restricted_export
    
        producer.optimal_sales[2:end] = producer.optimal_sales[2:end] .* (1 .- producer.export_restrictions[2:end] * sales_share_foreign_baseline)
        
    else
        producer.restricted_export = 0
        # producer.expected_sales_foreign = producer.optimal_sales[2] * sales_share_foreign_baseline 
        # producer.expected_sales_domestic = producer.optimal_sales[2] * (1 -  sales_share_foreign_baseline)
        producer.export_restriction = producer.export_restrictions[1]
        producer.export_tax_factor = (1 - producer.export_restriction)^(-1/σ) 

    end
 
end

function communication_step!(producer, t, producers::Dict{String,Producer})
    @unpack N_year, N_hor,ι, pol_opt,pol_exp_p, two_markets = producer.global_params
    @unpack X_star,X_only_foreign  = producer.global_params
    @unpack α, α_domestic, α_foreign,  λ, τ_exp, σ , X_avg,X_avg_foreign, X_avg_domestic,X_star_foreign,X_foreign, X_star_domestic, sales_share_foreign_baseline, purchaser_foreign_share,  = producer.local_params
    @unpack purchaser_foreign_share,share_imports_foreign_sales_other_producers = producer.local_params


    expected_other_sales_foreign_next = sum(other_producer.optimal_sales_foreign[2]
    for other_producer in values(producers) if other_producer.id != producer.id
   )
   
    if τ_exp != 0.
        expected_other_sales_foreign_next =
            1 / τ_exp * expected_other_sales_foreign_next +
            (1 - 1 / τ_exp) * producer.expected_others_sales_foreign[1]
    end 
    if two_markets
        # If expected sale is beneath threshold set it to zero
        if producer.expected_sales_domestic < ι * X_avg
            producer.expected_sales_domestic = 0.
        end
        if producer.expected_sales_foreign < ι * X_avg
            producer.expected_sales_foreign = 0.
        end

    else
        producer.expected_sales = get_expected_sales(producer.optimal_sales)
        # If expected sale is beneath threshold set it to zero
        if producer.expected_sales < ι * X_avg
            producer.expected_sales = 0.
        end
    end
    
    
    if two_markets

        producer.expected_price_domestic = 
        P(
            (producer.expected_sales_domestic + share_imports_foreign_sales_other_producers * expected_other_sales_foreign_next) /
            (X_star_domestic),
            α_domestic,
            λ,
        )

        if producer.expected_price_domestic > 1000 || isinf(producer.expected_price_domestic) 
            producer.expected_price_domestic = 1000
        end          
        producer.expected_price_foreign = 
        P(
            (producer.expected_sales_foreign +  expected_other_sales_foreign_next) /
            (X_only_foreign),
            α_foreign,
            λ,
        ) 

        if producer.expected_price_foreign > 1000 || isinf(producer.expected_price_foreign) 
            producer.expected_price_foreign = 1000
        end        

        producer.expected_price_foreign = producer.expected_price_foreign * producer.price_adjustment_factor_foreign
        producer.expected_price_domestic = producer.expected_price_domestic * producer.price_adjustment_factor_domestic
    ### Attention! The following part is still experimental/to be build up!
    elseif pol_opt && pol_exp_p 

        producer.expected_price =
        P(
            (producer.expected_sales + first(producer.expected_others_sales) ) /
            (X_star),
            α,
            λ,
        )

        producer.expected_price = producer.expected_price * producer.price_adjustment_factor
    else
        producer.expected_price =
        P(
            (producer.expected_sales + first(producer.expected_others_sales)) /
            X_star,
            α,
            λ,
        ) * producer.price_adjustment_factor
       
    end
   
    

    
    # Form expectation on other producers' sales
    if two_markets
        # Form expectation on other producers' on FOREIGN sales as vector
        expected_others_sales_foreign = sum(
                other_producer.optimal_sales_foreign[3:end] for other_producer in values(producers) if other_producer.id != producer.id
        )
        if τ_exp == 0.
            producer.expected_others_sales_foreign[1:N_hor-1] = expected_others_sales_foreign
            producer.expected_others_sales_foreign[end] = mean(expected_others_sales_foreign)
        else
            producer.expected_others_sales_foreign[1:N_hor-1] =
                1 / τ_exp .* expected_others_sales_foreign +
                (1 - 1 / τ_exp) .* producer.expected_others_sales_foreign[2:N_hor]
            producer.expected_others_sales_foreign[end] = mean(producer.expected_others_sales_foreign[1:N_hor-1])
        end      

    else
        expected_others_sales = sum(
            get_expected_future_sales(
                other_producer.optimal_sales,
                other_producer.baseline_sales,
                t,
                N_hor,
                N_year,
            ) for other_producer in values(producers) if other_producer.id != producer.id
        )
        if τ_exp == 0.
            producer.expected_others_sales[1:end] = expected_others_sales[1:end]
        else
            producer.expected_others_sales[1:N_hor-1] =
                1 / τ_exp .* expected_others_sales[1:N_hor-1] +
                (1 - 1 / τ_exp) .* producer.expected_others_sales[2:N_hor]
            producer.expected_others_sales[end] = expected_others_sales[end]
        end
    end
    # Prepare for new demand requests
    empty!(producer.demand_requests)
end

# Auxiliary functions

function P(x, α, λ)
    p = max.(0, x)
    if λ == 0
        return p .^ (-α)
    elseif λ == 1
        return 1 .- α .* (p .- 1)
    else
        return (1 .- α .* (p .^ λ .- 1)) .^ (1 / λ)
    end
end

function P_inv(p, α, λ)
    if λ == 0
        return p.^(-1 / α)
    elseif λ == 1
        return 1 .- (p .- 1) ./ α
    else
        return (1 .- (p.^λ .- 1) ./ α).^(1 / λ)
    end
end

function grad_P(x, α, λ)
    if λ == 0
        return -α .* x .^ (-α - 1)
    elseif λ == 1
        return -α .* ones(length(x))
    else
        return -α .* (P(x, α, λ) ./ x) .^ (1 - λ)
    end
end

function determine_J(total_sales, sorted_demand_requests)
    if total_sales == 0
        return Int[1]
    end
    @assert total_sales ≤ sum(d.quantity for d in sorted_demand_requests)
    # Find one possible J
    J = Int[]
    let X = total_sales
        for j = 1:lastindex(sorted_demand_requests)
            X -= sorted_demand_requests[j].quantity
            if X ≤ 0 || j == lastindex(sorted_demand_requests)
                push!(J, j)
                break
            end
        end
    end
    # Find all other possible J's
    while first(J) > firstindex(sorted_demand_requests)
        if sorted_demand_requests[first(J)-1].price ==
           sorted_demand_requests[first(J)].price
            pushfirst!(J, first(J) - 1)
        else
            break
        end
    end
    while last(J) < lastindex(sorted_demand_requests)
        if sorted_demand_requests[last(J)+1].price == sorted_demand_requests[last(J)].price
            push!(J, last(J) + 1)
        else
            break
        end
    end
    return J
end


# Needed for two markets
function determine_transactions_two_markets(sales_domestic,sales_foreign, sorted_demand_requests,export_restriction)
    if !isempty(sorted_demand_requests)
        total_demand = sum(d.quantity for d in sorted_demand_requests; init = 0.)
        demand_foreign = sum(d.quantity for d in sorted_demand_requests if d.seller_id != d.buyer_id; init = 0.)
        demand_domestic = total_demand - demand_foreign
    else
        return Transaction[]
    end

    # @assert (sales_domestic + sales_foreign) ≤ total_demand
    transactions = Transaction[]
    ratio_foreign = demand_foreign > 0 ? sales_foreign / demand_foreign : 0
    ratio_domestic = demand_domestic > 0 ? sales_domestic / demand_domestic : 0
    ratio_foreign = ratio_foreign > 1 ? 1 : ratio_foreign
    ratio_domestic = ratio_domestic > 1 ? 1 : ratio_domestic
    total_sales = 0
    for d in sorted_demand_requests

        if d.seller_id != d.buyer_id
            transfer = d.quantity * ratio_foreign * ( 1. - export_restriction)
        else
            transfer = d.quantity * ratio_domestic
        end

        transaction = Transaction(d.seller_id, d.buyer_id, transfer , d.price)
        total_sales = total_sales + transfer                    
        push!(transactions, transaction)
    end
    return transactions, total_sales
end

function determine_transactions(total_sales, sorted_demand_requests,export_restriction; rationing = :price)
    if !isempty(sorted_demand_requests)
        total_demand = sum(d.quantity for d in sorted_demand_requests)
    else
        return Transaction[]
    end
    if total_sales > total_demand && total_sales - total_demand < 1e-5
        total_sales = total_demand
    end
    @assert total_sales ≤ total_demand
    transactions = Transaction[]
    if rationing == :price
        J = determine_J(total_sales, sorted_demand_requests)
        append!(transactions, sorted_demand_requests[1:first(J)-1])
        remaining_sales = total_sales - reduce(+, t.quantity for t in transactions; init = 0.0)
        remaining_demand = sum(d.quantity for d in sorted_demand_requests[J])
        if remaining_sales > 0
            ratio = remaining_sales / remaining_demand
            for d in sorted_demand_requests[J]
                transaction = Transaction(d.seller_id, d.buyer_id, d.quantity * ratio, d.price)
                push!(transactions, transaction)
            end
        end
    elseif rationing == :proportional
        if total_demand > 0
            ratio = total_sales / total_demand
            for d in sorted_demand_requests
                if d.seller_id != d.buyer_id
                    transaction = Transaction(d.seller_id, d.buyer_id, d.quantity * ratio * ( 1. - export_restriction), d.price)
                else
                    transaction = Transaction(d.seller_id, d.buyer_id, d.quantity * ratio, d.price)
                end                    
                push!(transactions, transaction)

            end
        end
    end
    return transactions
end

function get_current_sales(optimal_sales)
    return optimal_sales[1]
end

function get_expected_sales(optimal_sales)
    return optimal_sales[2]
end

function get_expected_future_sales(optimal_sales, baseline_sales, t, N_hor, N_year)
    return vcat(optimal_sales[3:end], baseline_sales[mod(t + 1 + N_hor, 1:N_year)])
end

function determine_target_price_adjustment_factor(P, D_tot, X̂, β, min_X̂)
    if X̂ < min_X̂
        return 1
    end
    return P * (D_tot / X̂)^β
end


function determine_revenue_curve_two_markets(sorted_demand_requests,producer_id)
    average_price_domestic = sum(d.quantity * d.price for d in sorted_demand_requests if d.buyer_id == producer_id; init = 0.)
    average_price_foreign = sum(d.quantity * d.price for d in sorted_demand_requests if d.buyer_id != producer_id; init = 0.)
    demand_domestic = sum(d.quantity for d in sorted_demand_requests if d.buyer_id == producer_id; init = 0.)
    demand_foreign = sum(d.quantity for d in sorted_demand_requests if d.buyer_id != producer_id; init = 0.)
    
    average_price_total = average_price_domestic + average_price_foreign
    demand_total = demand_domestic + demand_foreign
    average_price_total = demand_total > 0 ? average_price_total / demand_total : 0


    average_price_domestic = demand_domestic > 0 ? average_price_domestic / demand_domestic : 0 
    average_price_foreign = demand_foreign > 0 ? average_price_foreign / demand_foreign : 0 
    
    X_thresholds = [demand_total]
    # Return: 1st entry: Revenue, 2nd entry: grad of total revenue (just price), 3rd entry:   grad of domestic revenue, 4th entry: grad of foreign revenue
    revenue_curve = function(X_dom, X_for; max_slope = Inf)
        if (X_dom + X_for) ≤ demand_total
            return (X_dom * average_price_domestic + X_for * average_price_foreign, average_price_total,average_price_domestic,average_price_foreign) 
        else
            out_dom = min(X_dom, demand_total)
            out_for = min(X_for, demand_total - out_dom)
            return (out_dom * average_price_domestic + out_for * average_price_foreign , 0, 0 ,0)
        end
    end
    return (revenue_curve, X_thresholds)
end


function determine_revenue_curve(sorted_demand_requests; rationing = :price)
    if rationing == :price
        X_thresholds = Float64[]
        constants = Float64[]
        prices = Float64[]
        if !isempty(sorted_demand_requests)
            let X = 0, C = 0
                for demand_request in sorted_demand_requests
                    push!(prices, demand_request.price)
                    push!(constants, C - demand_request.price * X)
                    X += demand_request.quantity
                    C += demand_request.price * demand_request.quantity
                    push!(X_thresholds, X)
                end
            end
        else
            push!(X_thresholds, 0)
            push!(prices, 0)
            push!(constants, 0)
        end
        revenue_curve = function(X; max_slope = Inf)
            if X > last(X_thresholds) && X - last(X_thresholds) ≤ 1e-5
                X = last(X_thresholds)
            end
            # @assert X ≤ last(X_thresholds)
            if X ≤ last(X_thresholds)
                j = searchsortedfirst(X_thresholds, X)
            else
                return (constants[end] + prices[end] * X_thresholds[end], 0.)
            end
            value = constants[j] + prices[j] * X
            # Regularized derivative
            if max_slope == Inf
                der = prices[j]
            else
                # Replace the step by a line with slope max_slope
                ΔX_left = (j > 1 ? (prices[j-1] - prices[j]) / (2 * max_slope) : 0)
                ΔX_right =
                    (j < length(X_thresholds) ? (prices[j] - prices[j+1]) / (2 * max_slope) : 0)

                left_to_X = X - (j > 1 ? X_thresholds[j-1] : 0)
                X_to_right = X_thresholds[j] - X

                @assert ΔX_left + ΔX_right ≤ left_to_X + X_to_right

                if left_to_X < ΔX_left
                    der = prices[j] + max_slope * (ΔX_left - left_to_X)
                elseif X_to_right < ΔX_right
                    der = prices[j] - max_slope * (ΔX_right - X_to_right)
                else
                    der = prices[j]
                end
            end
            return (value, der)
        end
        return (revenue_curve, X_thresholds)
    elseif rationing == :proportional
        average_price = 0
        total_demand = 0
        for demand_request in sorted_demand_requests
            average_price += demand_request.price * demand_request.quantity
            total_demand += demand_request.quantity
        end
        if total_demand > 0
            average_price /= total_demand
        end
        X_thresholds = [total_demand]
        revenue_curve = function(X; max_slope = Inf)
            if X ≤ total_demand
                return (X * average_price, average_price)
            else
                return (total_demand * average_price, 0)
            end
        end
        return (revenue_curve, X_thresholds)
    end
    @assert rationing in [:price, :proportional]
end

function get_storage_timeseries(H::AbstractVector, X::AbstractVector, S_beg; δ = 0)
    # S_beg = (1 - δ) * s_init
    @assert length(H) == length(X)
    N = length(H)
    L = LowerTriangular(ones((N, N)))
    for index in CartesianIndices(L)
        L[index] *= (1 - δ)^(index[1] - index[2])
    end
    S = L * (H - X) + L[:, begin] .* S_beg
    @assert minimum(S) > -1e-4
    S[S.<0] .= 0
    return S
end

function get_L_matrix(N; δ = 0,storage_hold_back = 0)
    L = Matrix{Float64}(undef, N, N)
    for index in CartesianIndices(L)
        if index[1] ≥ index[2]
            L[index] = (1 - δ)^(index[1] - index[2])
        end
    end
    return LowerTriangular(L)
end

function get_L_matrix_two_markets(N; δ = 0,storage_hold_back = 0)
    L_matrix = get_L_matrix(N; δ,storage_hold_back)

    L_matrix_2N = zeros(2*N, 2*N)
    L_matrix_2N[1:N, 1:N] = L_matrix
    L_matrix_2N[N+1:end, N+1:end] = L_matrix
    return L_matrix_2N
end

function get_unit_storage_costs(N, p_sto; δ = 0, ρ = 0)
    γ = (1 - δ) / (1 + ρ)
    if γ == 1.0
        unit_costs = -p_sto .* [N - (n - 1.0) for n = 1:N]
    else
        unit_costs = -p_sto .* [1.0 - γ^(N - (n - 1.0)) / (1 - γ) for n = 1:N]
    end
    return unit_costs
end

function get_unit_storage_costs_two_markets(N, p_sto; δ = 0, ρ = 0)
    unit_storage = get_unit_storage_costs(N,p_sto;δ, ρ)
    return [unit_storage; unit_storage]
end

# Needed TWO MARKETS
function profit_function_two_markets(x_dom,x_for, x_oth_dom, x_oth_for, x_star_dom,x_star_for, α_domestic, α_foreign, λ, unit_costs, h; P_loc_domestic = 1, P_loc_foreign = 1, ρ = 0, domestic_profit_factor = 1)
    N = length(x_dom)

    revenues_dom = domestic_profit_factor .* (P((x_dom + x_oth_dom) ./ x_star_dom, α_domestic, λ) .* P_loc_domestic) .* x_dom
    revenues_for = (P((x_for + x_oth_for) ./ x_star_for, α_foreign, λ) .* P_loc_foreign) .* x_for
    
    costs = unit_costs .* ((x_dom + x_for) - h)
    return sum((revenues_dom + revenues_for - costs) ./ (1 + ρ).^(0:N-1))
end


function grad_profit_function_two_markets(x_dom,x_for, x_oth_for, x_star_dom,x_star_for, α_domestic, α_foreign, λ, unit_costs, h; P_loc = 1, ρ = 0)
    grad_dom =
        P(x_dom ./ x_star_dom, α_domestic, λ) .* P_loc  +
        grad_P(x_dom ./ x_star_dom, α_domestic, λ) .* P_loc .* (x_dom ./ x_star_dom) - 
        unit_costs
    grad_for =
        P((x_for + x_oth_for) ./ x_star_for, α_foreign, λ) .* P_loc  +
        grad_P((x_for + x_oth_for) ./ x_star_for, α_foreign, λ) .* P_loc .* (x_for ./ x_star_for) - 
        unit_costs
    N = length(x_dom)
    return (grad_dom ./ (1 + ρ) .^ (0:N-1) , grad_for ./ (1 + ρ) .^ (0:N-1))
end



function profit_function(x, x_oth, x_star, α, λ, unit_costs, h; P_loc = 1, ρ = 0)
    revenues = (P((x + x_oth) ./ x_star, α, λ) .* P_loc) .* x
    costs = unit_costs .* (x - h)
    N = length(x)
    return sum((revenues - costs) ./ (1 + ρ).^(0:N-1))
end

function grad_profit_function(x, x_oth, x_star, α, λ, unit_costs; P_loc = 1, ρ = 0)
    N = length(x)
    grad =
        P((x + x_oth) ./ x_star, α, λ) .* P_loc +
        grad_P((x + x_oth) ./ x_star, α, λ) .* P_loc .* (x ./ x_star) - unit_costs
    
    
    return grad ./ (1 + ρ) .^ (0:N-1)
end




function quadratic_penalty(x, x_avg::Union{Float64,Nothing} = nothing; ρ = 0.)
    if isnothing(x_avg)
        # Treat x_avg as a function of x
        x_avg = mean(x)
    end
    N = length(x)
    return sum((x .- x_avg).^2 ./ (1 + ρ).^(0:N-1)) / x_avg
end

function grad_quadratic_penalty(x, x_avg::Union{Float64,Nothing} = nothing; ρ = 0.)
    extra_gradient_term = false
    if isnothing(x_avg)
        # Treat x_avg as a function of x
        x_avg = mean(x)
        extra_gradient_term = true
    end
    N = length(x)
    grad = 2 .* (x .- x_avg) ./ x_avg ./ (1 + ρ).^(0:N-1)
    if extra_gradient_term
        # Extra term if x_avg is a function of x
        grad[:] .-= sum((x .- x_avg) .* (x .+ x_avg) ./ (1 + ρ).^(0:N-1)) / x_avg^2 / N
    end
    return grad
end



function quadratic_minimum_sale_penalty_two_markets(x_dom,x_for, x_oth_dom, x_oth_for, x_star_dom,x_star_for, α_domestic, α_foreign, λ, x_minimum)
    # Calculate the penalty by multiplying with prices and summing up
    penalty_sum_dom = quadratic_minimum_sale_penalty(x_dom,x_oth_dom, x_star_dom, α_domestic, λ, x_minimum)
    penalty_sum_for = quadratic_minimum_sale_penalty(x_for,x_oth_for, x_star_for, α_foreign, λ, x_minimum)
    
    return penalty_sum_dom + penalty_sum_for
end

function gradient_quadratic_minimum_sale_penalty_two_markets(x_dom, x_for, x_oth_dom, x_oth_for, x_star_dom, x_star_for, α_domestic, α_foreign, λ, x_minimum)
    
    grad_x_dom = gradient_quadratic_minimum_sale_penalty(x_dom, x_oth_dom, x_star_dom, α_domestic, λ, x_minimum)
    grad_x_for = gradient_quadratic_minimum_sale_penalty(x_for, x_oth_for, x_star_for, α_foreign, λ, x_minimum)

    return grad_x_dom, grad_x_for
end


function quadratic_minimum_sale_penalty(x,x_oth, x_star, α, λ, x_minimum)
    # Calculate the price function values
    prices = P((x + x_oth) ./ x_star, α, λ)

    # Calculate the quadratic errors
    quadratic_errors = (x .- x_minimum) .^ 2

    # Set errors to zero where x >= x_minimum
    quadratic_errors[x .>= x_minimum] .= 0.0
    
    # Calculate the penalty by multiplying with prices and summing up
    penalty_sum = sum(quadratic_errors .* prices)
    
    return penalty_sum
end

function gradient_quadratic_minimum_sale_penalty(x, x_oth, x_star, α, λ, x_minimum)
    prices = P((x + x_oth) ./ x_star, α, λ)
    prices[x .>= x_minimum] .= 0.0

    grad_x = 2 * (x .- x_minimum) .* prices
    
    return grad_x
end




# Needed for two markets
function quadratic_penalty_two_markets(x, x_oth,x_star,α, λ, x_avg::Union{Float64,Nothing} = nothing; ρ = 0.)
    if isnothing(x_avg)
        # Treat x_avg as a function of x
        x_avg = mean(x)
    end
    N = length(x)
    return sum(P((x + x_oth) ./ x_star, α, λ) .* (x .- x_avg).^2 ./ (1 + ρ).^(0:N-1)) / x_avg
end

function grad_quadratic_penalty_two_markets(x, x_oth,x_star,α, λ, x_avg::Union{Float64,Nothing} = nothing; ρ = 0.)
    extra_gradient_term = false
    if isnothing(x_avg)
        # Treat x_avg as a function of x
        x_avg = mean(x)
        extra_gradient_term = true
    end
    N = length(x)
    grad = P((x + x_oth) ./ x_star, α, λ) .* 2 .* (x .- x_avg) ./ x_avg ./ (1 + ρ).^(0:N-1) + 
            1/ x_star .* grad_P((x + x_oth) ./ x_star, α, λ) .* (x .- x_avg).^2 ./ (1 + ρ).^(0:N-1) / x_avg
    if extra_gradient_term
        # Extra term if x_avg is a function of x
        grad[:] .-= sum( P((x + x_oth) ./ x_star, α, λ) .* (x .- x_avg) .* (x .+ x_avg) ./ (1 + ρ).^(0:N-1)) / x_avg^2 / N
    end
    return grad
end

function quadratic_penalty_former_sells(x,x_oth,x_star,α, λ, x_init; ρ = 0.)
    N = length(x)
    return sum(P((x + x_oth) ./ x_star, α, λ) .* (x - x_init).^2 ./ (1 + ρ).^(0:N-1)) / sum(x_init)
end

function grad_quadratic_penalty_former_sells(x, x_oth,x_star,α, λ, x_init; ρ = 0.)
    N = length(x)
    grad = P((x + x_oth) ./ x_star, α, λ) .* 2 .* (x - x_init) ./ sum(x_init) ./ (1 + ρ).^(0:N-1) + 
    1/ x_star .* grad_P((x + x_oth) ./ x_star, α, λ) .* (x - x_init).^2 ./ (1 + ρ).^(0:N-1) / sum(x_init)
    # grad = 2 .* (x - x_init) ./ sum(x_init) ./ (1 + ρ).^(0:N-1)
    return grad
end



include("producer_optimization.jl")

end
