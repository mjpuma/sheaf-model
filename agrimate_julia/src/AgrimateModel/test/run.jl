module TestRunModule

using Test
using DataFrames: nrow

include("../src/agents.jl")
include("../src/model.jl")
include("../src/run.jl")

using .ModelModule, .RunModule
using .RunModule: observe!

model = Model(;global_params=(;N_year=52, N_hor=52, N_del=52, ι=0.001))

producer_params = Dict(pairs((;
    α = 2.5,
    λ = 1.0,
    β = 0.05,
    δ = 0.0,
    ρ = 0.0,
    σ = 2.,
    p_sto = 0.2 / 52,
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
    τ = 4.,
    ψ = 12.,
    ε_c = 0.2,
    A_d_star = 0.2,
    A_c_star = 0.2,
    τ_a = 8,
)))


create_agents!(model; producer_ids=["USA", "DEU"], consumer_ids=["CHN", "DEU"], producer_params, consumer_params)

baseline_harvests = Dict(region => ones(52) for region in ["USA", "DEU"])
baseline_consumption = Dict(region => 1. for region in ["CHN", "DEU"])
baseline_transactions = Dict(("USA", "CHN") => 1., ("DEU", "DEU") => 1.)

init_data =
    InitializationData(baseline_harvests, baseline_consumption, baseline_transactions)

initialize_agents!(model, init_data)

T = 10
harvests = Dict(region => ones(T) for region in ["USA", "DEU"])
expected_harvests = Dict(region => ones(T, 52) for region in ["USA", "DEU"])

input_data = InputData(harvests, expected_harvests)

@test_nowarn run = Run(model, input_data)

run = Run(model, input_data)

nrows = nrow(run.output_data)

@test begin
    run.timestep = 0
    observe!(run)
    run.timestep = 1
    nrow(run.output_data) > nrows
end

nrows = nrow(run.output_data)

@test begin
    run_model!(run, 4)
    nrow(run.output_data) > nrows
end




end
