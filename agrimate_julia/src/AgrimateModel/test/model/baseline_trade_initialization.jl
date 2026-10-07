module TestBaselineTradeInitializationModule

#using Test

include("../../src/model/baseline_trade_initialization.jl")

N_year = 4
N_prod = 4
N_cons = 4

supply = Dict("P$r" => fill(N_cons / N_prod / N_year, N_year) for r = 1:N_prod)
demand = Dict("C$s" => fill(1. / N_year, N_year) for s = 1:N_cons)
annual_trade = Dict(("P$r", "C$s") => 1. / N_prod for r = 1:N_prod for s = 1:N_cons)

N_trade = N_prod * N_cons
println("Number of constraints: $((N_prod+N_cons)*N_year+N_trade)")
println("Number of variables: $(N_trade*N_year)")

trade = determine_baseline_trade(supply, demand, annual_trade, tol = 1e-8, verbose = true)

println(trade)

end
