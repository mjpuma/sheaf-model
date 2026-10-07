module TestProducerModule

using Test
# using Plots; gr()

include("../../src/agents.jl")
using .AgentsModule
using .AgentsModule.ProducerModule:
    P,
    grad_P,
    determine_J,
    optimize_sales,
    optimize_periodic_sales,
    determine_transactions,
    get_current_sales,
    get_expected_sales,
    get_expected_future_sales,
    determine_revenue_curve,
    quadratic_penalty,
    grad_quadratic_penalty

# Testing auxiliary functions

# Price functions

@test P(1., 1., 0.) == 1.
@test P(1., 1., 0.5) == 1.
@test P(1., 1., 1.) == 1.

@test P(ones(10), 1., 0.) == ones(10)
@test P(ones(10), 1., 0.5) == ones(10)
@test P(ones(10), 1., 1.) == ones(10)

@test grad_P(ones(10), 2., 0.) == -2. .* ones(10)
@test grad_P(ones(10), 2., 0.5) == -2. .* ones(10)
@test grad_P(ones(10), 2., 1.) == -2. .* ones(10)

# x = collect(0.5:0.01:1.5)
# p = Dict(λ => grad_P(x, 2., λ) for λ in [0, 0.5, 1])
# plot(x, p[0], label = "λ = 0")
# plot!(x, p[0.5], label = "λ = 0.5")
# plot!(x, p[1], label = "λ = 1")


# Functions on demand requests

sorted_demand_requests = [
    Transaction("id", "id", quantity, price)
    for
    (quantity, price) in
    zip([10.0, 10.0, 10.0, 5.0, 5.0, 8.0], [3., 2., 1., 1., 1., 0.5])
]

@test determine_J(0., sorted_demand_requests) == [1]
@test determine_J(10., sorted_demand_requests) == [1]
@test determine_J(15., sorted_demand_requests) == [2]
@test determine_J(20., sorted_demand_requests) == [2]
@test determine_J(25., sorted_demand_requests) == [3, 4, 5]
@test determine_J(30., sorted_demand_requests) == [3, 4, 5]
@test determine_J(35., sorted_demand_requests) == [3, 4, 5]
@test determine_J(40., sorted_demand_requests) == [3, 4, 5]
@test determine_J(48., sorted_demand_requests) == [6]
@test_throws AssertionError determine_J(49., sorted_demand_requests)

(revenue_curve, thresholds) = determine_revenue_curve(sorted_demand_requests)
@test revenue_curve(0.) == (0, 3.)
@test revenue_curve(10.) == (30., 3.)
@test revenue_curve(15.) == (40., 2.)
@test revenue_curve(20.) == (50., 2.)
@test revenue_curve(25.) == (55., 1.)
@test revenue_curve(30.) == (60., 1.)
@test revenue_curve(35.) == (65., 1.)
@test revenue_curve(40.) == (70., 1.)
@test revenue_curve(48.) == (74., 0.5)
@test revenue_curve(49.) == (74., 0.)

# n_pts = 400
# x = collect(range(0, stop = 48, length = n_pts))
# r = Matrix{Float64}(undef, 2, n_pts)
# for i in 1:n_pts
#     r[:, i] .= revenue_curve(x[i]; max_slope=0.25)
# end
# plot(x, r[1,:])
# plot(x, r[2,:])

@test length(determine_transactions(0., sorted_demand_requests)) == 0
@test length(determine_transactions(10., sorted_demand_requests)) == 1
@test length(determine_transactions(15., sorted_demand_requests)) == 2
@test length(determine_transactions(20., sorted_demand_requests)) == 2
@test length(determine_transactions(25., sorted_demand_requests)) == 5
@test length(determine_transactions(30., sorted_demand_requests)) == 5
@test length(determine_transactions(35., sorted_demand_requests)) == 5
@test length(determine_transactions(40., sorted_demand_requests)) == 5
@test length(determine_transactions(48., sorted_demand_requests)) == 6
@test sum(t.quantity for t in determine_transactions(10., sorted_demand_requests)) == 10.
@test sum(t.quantity for t in determine_transactions(15., sorted_demand_requests)) == 15.
@test sum(t.quantity for t in determine_transactions(20., sorted_demand_requests)) == 20.
@test sum(t.quantity for t in determine_transactions(25., sorted_demand_requests)) == 25.
@test sum(t.quantity for t in determine_transactions(30., sorted_demand_requests)) == 30.
@test sum(t.quantity for t in determine_transactions(35., sorted_demand_requests)) == 35.
@test sum(t.quantity for t in determine_transactions(40., sorted_demand_requests)) == 40.
@test sum(t.quantity for t in determine_transactions(48., sorted_demand_requests)) == 48.
@test_throws AssertionError determine_transactions(49., sorted_demand_requests)

transactions = determine_transactions(32., sorted_demand_requests)
@test (transactions[1].quantity, transactions[1].price) == (10., 3.)
@test (transactions[2].quantity, transactions[2].price) == (10., 2.)
@test (transactions[3].quantity, transactions[3].price) == (6., 1.)
@test (transactions[4].quantity, transactions[4].price) == (3., 1.)
@test (transactions[5].quantity, transactions[5].price) == (3., 1.)

# Functions on sales

N_hor = 2 * 365
N_year = 365
optimal_sales = 0.5 .* ones(N_hor + 1)
baseline_sales = 2. .* ones(N_year)

@test get_current_sales(optimal_sales) == 0.5
@test get_expected_sales(optimal_sales) == 0.5
@test get_expected_future_sales(optimal_sales, baseline_sales, 1, N_hor, N_year) ==
      append!(0.5 .* ones(N_hor - 1), [2.])
@test get_expected_future_sales(optimal_sales, baseline_sales, 1, N_hor, N_year) ==
      append!(0.5 .* ones(N_hor - 1), [2.])


# Quadratic penalty

x = ones(12)
@test quadratic_penalty(x) ≈ 0
@test grad_quadratic_penalty(x) ≈ zeros(12)

x = vcat(fill(0.5, 6), fill(1.5, 6))
@test quadratic_penalty(x) .≈ 12 * 0.25
@test all(grad_quadratic_penalty(x)[1:6] .< 0)


end
