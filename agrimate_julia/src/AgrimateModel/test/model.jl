module TestModelModule

using Test

using Statistics: mean

include("../src/agents.jl")
include("../src/model.jl")
using .ModelModule

@test_nowarn model = Model(;global_params=(;N_year=52, N_hor=52, N_del=52, ι=0.001))

model = Model(;global_params=(;N_year=52, N_hor=52, N_del=52, ι=0.001))

producer_params = Dict(pairs((;
    α = 2.5,
    λ = 1.0,
    β = 0.05,
    δ = 0.0,
    ρ = 0.0,
    σ = 2.,
    p_sto = 0.2 / 365,
    τ_exp = 8,
    N_for = 12,
    τ_for = 8,
    τ_P = 8,
    market_constraint = true,
    unique_market_constraint = true,
    rationing = :proportional,
)))

consumer_params = Dict(pairs((;
    ε_d = 1 / 2.5,
    σ = 2.,
    δ = 0.0,
    β = 0.5,
    τ = 30.0,
    ψ = 90.0,
    ε_c = 0.2,
    A_d_star = 0.2,
    A_c_star = 0.2,
    τ_a = 8,
)))


@test_nowarn create_agents!(model; producer_ids=["USA", "DEU"], consumer_ids=["CHN", "DEU"], producer_params, consumer_params)

baseline_harvests = Dict(region => ones(52) for region in ["USA", "DEU"])
baseline_consumption = Dict(region => 1. for region in ["CHN", "DEU"])
baseline_transactions = Dict(("USA", "CHN") => 1., ("DEU", "DEU") => 1.)

init_data =
    InitializationData(baseline_harvests, baseline_consumption, baseline_transactions)

@test_nowarn initialize_agents!(model, init_data)

T = 10
harvests = Dict(region => ones(T) for region in ["USA", "DEU"])
expected_harvests = Dict(region => ones(T, 52) for region in ["USA", "DEU"])

input_data =  InputData(harvests, expected_harvests)

@test_nowarn step!(model, 1, input_data)
@test_nowarn step!(model, 2, input_data)

# Numerical test

model = Model(global_params=(;N_year=12, N_hor=12, N_del=1, ι=0.001))


consumer_params[:ε_d] = 1. / 2.5
producer_params[:α] = 2.5
producer_params[:p_sto] = 0.2 / 12

create_agents!(model; producer_ids = ["1", "2"], consumer_ids = ["3"], consumer_params, producer_params)

baseline_harvests = Dict(region => zeros(12) for region in ["1", "2"])
baseline_harvests["1"][1] = 6.
baseline_harvests["2"][7] = 6.

baseline_consumption = Dict("3" => 1.)
baseline_transactions = Dict(("1", "3") => 0.5, ("2", "3") => 0.5)

init_data = InitializationData(baseline_harvests, baseline_consumption, baseline_transactions)
initialize_agents!(model, init_data; tol = 1e-6)

@test isapprox(model.producers["1"].baseline_sales,
               circshift(model.producers["2"].baseline_sales, 6), atol = 1e-4)

X1_ref = [0.5256, 0.5233, 0.5211, 0.5189, 0.5167, 0.5144, 0.4856, 0.4833, 0.4811, 0.4789, 0.4767, 0.4744]

@test isapprox(round.(model.producers["1"].baseline_sales, digits = 4), X1_ref, atol=1e-4)

ψ = model.consumers["3"].local_params[:ψ]
@test mean(model.consumers["3"].baseline_storage) ≈ ψ * model.consumers["3"].local_params[:C_star]

end
