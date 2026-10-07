
function store_baseline_variables!(
    output_baseline_data, 
    model,                          
    baseline_prices, 
    baseline_transactions,
    baseline_consumer_prices,
)
    
    @unpack N_year, N_del = model.global_params
    # Baseline prices
    for n in 1:N_year
        push!(
            output_baseline_data,
            Dict(
                :t => missing,
                :n => n,
                :producer => missing,
                :consumer => missing,
                :variable => "baseline price",
                :value => baseline_prices[n],
            ),
        )
    end
    # Producer variables
    for (id, producer) in model.producers
        push!(
            output_baseline_data,
            Dict(
                :t => missing,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "baseline share foreign sales",
                :value => producer.local_params[:sales_share_foreign_baseline],
            ),
        )
        push!(
            output_baseline_data,
            Dict(
                :t => missing,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "α domestic",
                :value => producer.local_params[:α_domestic],
            ),
        )
        for n = 1:N_year
            push!(
                output_baseline_data,
                Dict(
                    :t => missing,
                    :n => n,
                    :producer => id,
                    :consumer => missing,
                    :variable => "baseline harvest",
                    :value => producer.expected_harvests[n],
                ),
            )
        end
        for n = 1:N_year
            push!(
                output_baseline_data,
                Dict(
                    :t => missing,
                    :n => n,
                    :producer => id,
                    :consumer => missing,
                    :variable => "baseline sales",
                    :value => producer.baseline_sales[n],
                ),
            )
        end
        for n = 1:N_year
            push!(
                output_baseline_data,
                Dict(
                    :t => missing,
                    :n => n,
                    :producer => id,
                    :consumer => missing,
                    :variable => "baseline producer storage",
                    :value => producer.baseline_storage[n],
                ),
            )
        end
    end
    # Consumer variables
    for (id, consumer) in model.consumers
        for n = 1:N_year
            push!(
                output_baseline_data,
                Dict(
                    :t => missing,
                    :n => n,
                    :producer => missing,
                    :consumer => id,
                    :variable => "baseline demand",
                    :value => consumer.baseline_demand[n],
                ),
            )
        end
        # Baseline storage
        for n = 1:N_year
            push!(
                output_baseline_data,
                Dict(
                    :t => missing,
                    :n => n,
                    :producer => missing,
                    :consumer => id,
                    :variable => "baseline consumer storage",
                    :value => consumer.baseline_storage[n],
                ),
            )
        end
        # Baseline consumption
        for n = 1:N_year
            push!(
                output_baseline_data,
                Dict(
                    :t => missing,
                    :n => n,
                    :producer => missing,
                    :consumer => id,
                    :variable => "baseline consumption",
                    :value => consumer.baseline_consumption[n],
                ),
            )
        end
        # Baseline consumer price
        for n = 1:N_year
            push!(
                output_baseline_data,
                Dict(
                    :t => missing,
                    :n => n,
                    :producer => missing,
                    :consumer => id,
                    :variable => "baseline consumer price",
                    :value => baseline_consumer_prices[id][n],
                ),
            )
        end
    end
    if !isnothing(baseline_transactions)
        for ((producer_id, consumer_id), quantity) in baseline_transactions
            for n = 1:N_year
                push!(
                    output_baseline_data,
                    Dict(
                        :t => missing,
                        :n => n,
                        :producer => producer_id,
                        :consumer => consumer_id,
                        :variable => "baseline transaction quantity",
                        :value => quantity[n],
                    ),
                )
            end
        end
    end
end