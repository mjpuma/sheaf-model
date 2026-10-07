module ObservationModule

export observe_consumers!, observe_producers!, observe_extra_data!

using Parameters

# Consumer observables

function observe_consumers!(output_data, model, timestep)
    for (id, consumer) in model.consumers
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => missing,
                :consumer => id,
                :variable => "delivery",
                :value => consumer.delivery,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => missing,
                :consumer => id,
                :variable => "consumer price",
                :value => consumer.price_stored,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => missing,
                :consumer => id,
                :variable => "consumption",
                :value => consumer.consumption,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => missing,
                :consumer => id,
                :variable => "consumer storage",
                :value => consumer.storage,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => missing,
                :consumer => id,
                :variable => "extra demand",
                :value => consumer.extra_demand,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => missing,
                :consumer => id,
                :variable => "demand",
                :value => consumer.total_demand,
            ),
        )
    end
    for (id, consumer) in model.consumers
        for demand_request in consumer.demand_requests
            push!(
                output_data,
                Dict(
                    :t => timestep,
                    :n => missing,
                    :producer => demand_request.seller_id,
                    :consumer => id,
                    :variable => "demanded quantity",
                    :value => demand_request.quantity,
                ),
            )
            push!(
                output_data,
                Dict(
                    :t => timestep,
                    :n => missing,
                    :producer => demand_request.seller_id,
                    :consumer => id,
                    :variable => "reservation price",
                    :value => demand_request.price,
                ),
            )
        end
    end
end


# Producer observables

function observe_producers!(output_data, model, timestep)
    for (id, producer) in model.producers
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "harvest",
                :value => producer.harvest,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "price adjustment factor",
                :value => producer.price_adjustment_factor,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "price adjustment factor domestic",
                :value => producer.price_adjustment_factor_domestic,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "price adjustment factor foreign",
                :value => producer.price_adjustment_factor_foreign,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "export tax factor",
                :value => producer.export_tax_factor,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "restricted export",
                :value => producer.restricted_export,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "export restriction",
                :value => producer.export_restriction,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "sales",
                :value => producer.total_sales,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "sales domestic",
                :value => producer.sales_domestic,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "sales foreign",
                :value => producer.sales_foreign,
            ),
        )
    end
    for (id, producer) in model.producers
        for transaction in producer.transactions
            push!(
                output_data,
                Dict(
                    :t => timestep,
                    :n => missing,
                    :producer => id,
                    :consumer => transaction.buyer_id,
                    :variable => "transaction quantity",
                    :value => transaction.quantity,
                ),
            )
            push!(
                output_data,
                Dict(
                    :t => timestep,
                    :n => missing,
                    :producer => id,
                    :consumer => transaction.buyer_id,
                    :variable => "transaction price",
                    :value => transaction.price,
                ),
            )
        end
    end
    for (id, producer) in model.producers
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "producer storage",
                :value => producer.storage,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "expected profit",
                :value => producer.expected_profit,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "expected price",
                :value => producer.expected_price,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "expected price domestic",
                :value => producer.expected_price_domestic,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "expected price foreign",
                :value => producer.expected_price_foreign,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "expected sales",
                :value => producer.expected_sales,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "expected sales domestic",
                :value => producer.expected_sales_domestic,
            ),
        )
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => id,
                :consumer => missing,
                :variable => "expected sales foreign",
                :value => producer.expected_sales_foreign,
            ),
        )
    end
end

function observe_extra_data!(output_data, model, timestep)
    @unpack N_hor = model.global_params
    for (id, consumer) in model.consumers
        push!(
            output_data,
            Dict(
                :t => timestep,
                :n => missing,
                :producer => missing,
                :consumer => id,
                :variable => "expected storage",
                :value => consumer.expected_storage,
            ),
        )
    end
    for (id, producer) in model.producers
        for n in 0:N_hor
            push!(
                output_data,
                Dict(
                    :t => timestep,
                    :n => n,
                    :producer => id,
                    :consumer => missing,
                    :variable => "optimal sales",
                    :value => producer.optimal_sales[n+1],
                ),
            )
        end
    end
    for (id, producer) in model.producers
        for n in 0:N_hor
            push!(
                output_data,
                Dict(
                    :t => timestep,
                    :n => n,
                    :producer => id,
                    :consumer => missing,
                    :variable => "optimal sales domestic",
                    :value => producer.optimal_sales_domestic[n+1],
                ),
            )
        end
    end
    for (id, producer) in model.producers
        for n in 0:N_hor
            push!(
                output_data,
                Dict(
                    :t => timestep,
                    :n => n,
                    :producer => id,
                    :consumer => missing,
                    :variable => "optimal sales foreign",
                    :value => producer.optimal_sales_foreign[n+1],
                ),
            )
        end
    end
    for (id, producer) in model.producers
        for n in 1:N_hor
            push!(
                output_data,
                Dict(
                    :t => timestep,
                    :n => n,
                    :producer => id,
                    :consumer => missing,
                    :variable => "expected others sales",
                    :value => producer.expected_others_sales[n],
                ),
            )
        end
    end
end





end
