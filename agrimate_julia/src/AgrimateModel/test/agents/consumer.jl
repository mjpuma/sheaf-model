module TestConsumerModule

using Test

include("../../src/agents.jl")
using .AgentsModule.ProducerModule: P
using .AgentsModule.ConsumerModule: 
    P_inv, 
    determine_crop_price_index,
    determine_demands


@test P_inv(1., 2., 1.) == 1.
@test P_inv(1.5, 2., 1.) < 1.
@test P_inv(0.5, 2., 1.) > 1.

@test P_inv(P(1.5, 2., 0.), 2., 0.) ≈ 1.5
@test P_inv(P(1.5, 2., 0.5), 2., 0.5) ≈ 1.5
@test P_inv(P(1.5, 2., 1.), 2., 1.) ≈ 1.5

suppliers = ["A", "B", "C"]
demand_shares = Dict("A" => 0.5, "B" => 0.25, "C" => 0.25)
offer_prices = Dict("A" => 1., "B" => 1., "C" => 1.)

price_index = determine_crop_price_index(; 
    suppliers, 
    demand_shares, 
    offer_prices,
    σ = 2.
)

@test price_index == 1.

demands = determine_demands(;
    suppliers,
    demand_shares,
    offer_prices,
    price_index,
    budget_share = 0.5,
    budget = 10.,
    σ = 2.,
    ε_d = 0.2,
)

@test demands == Dict("A" => 2.5, "B" => 1.25, "C" => 1.25)

end
