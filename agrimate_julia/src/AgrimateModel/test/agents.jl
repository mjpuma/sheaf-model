module TestAgentsModule

using Test
using DataStructures: Deque
using Parameters


include("../src/agents.jl")
using .AgentsModule
using .AgentsModule.ConsumerModule:
    update_offer_prices!,
    update_demand_shares!



@test_nowarn producer = Producer(
    "USA";
    local_params = (;
        α = 2.5,
        λ = 1.0,
        β = 0.5,
        σ = 2.,
        δ = 0.0,
        ρ = 0.0,
        p_sto = 0.2 / 52,
        N_for = 12,
        τ_for = 8,
        τ_exp = 8,
        τ_P = 8,
        X_avg = 1.0,
        market_constraint = false,
        unique_market_constraint = false,
        rationing = :price,
    ),
    global_params = (;
        N_hor = 52,
        N_year = 52,
        X_star = 100.0,
        ι = 0.001,
    )
)

@test_nowarn consumer = Consumer(
    "ARG";
    local_params = (;
        ε_d = 1 / 2.5,
        σ = 2.,
        δ = 0.0,
        τ = 30,
        ψ = 90,
        ε_c = 0.,
        A_d_star = 0.2,
        A_c_star = 0.2,
        τ_a = 8,
        C_star = 1.,
    ),
    global_params = (;
        N_del = 4,
        N_year = 52,
        ι = 0.001,
    )

)

ids = [string(id) for id in 1:5]
producers = Dict{String,Producer}()
consumers = Dict{String,Consumer}()
    for id in ids
        producers[id] = Producer(
            id;
            local_params = (;
                α = 2.5,
                λ = 1.0,
                β = 0.5,
                δ = 0.0,
                ρ = 0.0,
                σ = 2.,
                p_sto = 0.2 / 52,
                τ_exp = 8,
                N_for = 12,
                τ_for = 8,
                τ_P = 8,
                market_constraint = false,
                unique_market_constraint = false,
                rationing = :price,
                X_avg = 1.0,
            ),
            global_params = (;
                N_hor = 52,
                N_year = 52,
                ι = 0.001,
                X_star = 5.0,
            )
        )
    end
    for id in ids
        consumers[id] = Consumer(
            id;
            local_params = (;
                ε_d = 1 / 2.5,
                σ = 2.,
                δ = 0.0,
                τ = 4,
                ψ = 12,
                ε_c = 0.,
                A_d_star = 0.2,
                A_c_star = 0.2,
                τ_a = 8,
                C_star = 1.,
            ),
            global_params = (;
                N_del = 4,
                N_year = 52,
                ι = 0.001,
            )
        )
    end


@test producers["1"].id == "1"


for producer in values(producers)
    @unpack N_hor, N_year = producer.global_params
    @unpack X_star = producer.global_params
    producer.harvest = 1.
    producer.expected_harvests = ones(N_hor)
    producer.storage = 0
    producer.optimal_sales = ones(N_hor + 1)
    producer.baseline_sales = ones(N_year)
    producer.baseline_storage = zeros(N_year)
    producer.expected_sales = 1.
    producer.expected_price = 1.
    producer.expected_others_sales = 4. .* ones(N_hor)
    producer.market_size = X_star
    producer.market_size_unique = 0.
    producer.export_restriction = 0.
    producer.export_tax_factor = 1.
    producer.price_adjustment_factor = 1.
end

for consumer in values(consumers)
    consumer.baseline_consumption = 1. .* ones(52)
    consumer.baseline_storage = 10. .* ones(52)
    consumer.storage = 10.
    consumer.expected_storage = 10.
    consumer.price_stored = 1.
    consumer.suppliers = ["1", "2", "3", "4", "5"]
    consumer.baseline_demand_shares = 
        Dict(id => 0.2 .* ones(52) for id in consumer.suppliers)
    consumer.demand_shares = Dict(id => 0.2 for id in consumer.suppliers)
    consumer.household_budget = 5
    consumer.budget = 5
    consumer.crop_budget_share = 0.2
    consumer.baseline_price = 1. .* ones(52)
    consumer.baseline_demand = 1. .* ones(52)
    consumer.offer_prices = Dict{String,Float64}()
end

@test begin
    update_offer_prices!(consumers["1"], producers)
    consumers["1"].offer_prices == Dict(id => 1. for id in consumers["1"].suppliers)
end

@test begin
    update_demand_shares!(consumers["1"], 1, producers)
    consumers["1"].demand_shares == Dict(id => 0.2 for id in consumers["1"].suppliers)
end


@testset "procurement_step!" begin
    procurement_step!(consumers["1"], 1, producers)
    demand_requests = [Transaction(string(id), "1", 0.2, 1.) for id in 1:5]
    @test consumers["1"].total_demand == 1.
    @test consumers["1"].extra_demand == 0.
    @test Set(consumers["1"].demand_requests) == Set(demand_requests)
    for id in 2:5
        procurement_step!(consumers[string(id)], 1, producers)
    end
end

@testset "harvest_step!" begin
    harvest_step!(producers["1"], 2.0, 1.5 .* ones(52))
    @test producers["1"].harvest == 2.0
    @test producers["1"].expected_harvests == 1.5 .* ones(52)
    @test producers["1"].storage == 0.0
    for id in 2:5
        harvest_step!(producers[string(id)], 1.0, ones(52))
    end
end

@testset "sales_step!" begin
    sales_step!(producers["1"], 1, consumers)
    transactions = [Transaction("1", string(id), 0.2, 1.0) for id in 1:5]
    @test producers["1"].total_sales ≈ 1.0
    @test collect(t.quantity for t in producers["1"].transactions) ≈
          collect(t.quantity for t in transactions)
    @test collect(t.price for t in producers["1"].transactions) ≈
          collect(t.price for t in transactions)
    @test producers["1"].storage ≈ 1.0
    for id = 2:5
        sales_step!(producers[string(id)], 1, consumers)
    end
end

@testset "communication_step!" begin
    # Producer 1
    communication_step!(producers["1"], 1, producers)
    @test producers["1"].expected_sales > 1.
    @test producers["1"].expected_price < 1.
    @test producers["1"].expected_others_sales ≈ 4. .* ones(52)

    # Producer 2
    communication_step!(producers["2"], 1, producers)
    @test producers["2"].expected_sales ≈ 1.
    @test producers["2"].expected_price ≈ 1.
    @test producers["2"].expected_others_sales > 4. .* ones(52)

    for id in 3:5
        communication_step!(producers[string(id)], 1, producers)
    end
end


@testset "accounting_step!" begin
    accounting_step!(consumers["1"])
    @test first(consumers["1"].delivery_queue).quantity ≈ 1.
    @test consumers["1"].expected_storage ≈ 10.
    for id in 2:5
        accounting_step!(consumers[string(id)])
    end
end

@testset "delivery_step!" begin
    delivery_step!(consumers["1"])
    @test length(consumers["1"].delivery_queue) == 0
    @test consumers["1"].delivery ≈ 1.
    for id in 2:5
        delivery_step!(consumers[string(id)])
    end
end

@testset "consumption_step!" begin
    consumption_step!(consumers["1"])
    @test consumers["1"].consumption == 1.
    @test consumers["1"].storage ≈ 10.
    for id in 2:5
        consumption_step!(consumers[string(id)])
    end
end

end
