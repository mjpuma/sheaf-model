module TestProducerOptimizationModule

using Test

include("../../src/agents.jl")
using .AgentsModule
using .AgentsModule.ProducerModule:
    P,
    grad_P,
    determine_revenue_curve,
    optimize_sales_NLopt,
    optimize_sales_NLopt_LineSearch,
    optimize_periodic_sales_NLopt


# Periodic optimization

h = 0.1 .* ones(12)
x_oth = 0.9 .* ones(12)

x_init = 0.1 .* (ones(12) + 0.01 .* randn(12))

(x, s_beg) = optimize_periodic_sales_NLopt(;
    h = h,
    x_oth = x_oth,
    x_init = x_init,
    s_beg_init = 0,
    α = 2.5,
    λ = 1.,
    δ = 0.,
    ρ = 0.,
    p_sto = 0.2 / 12,
    x_star = 1.,
    N_year = 12,
    tol = 1e-6,
    verbose = true,
)

@test x ≈ h
@test s_beg < 1e-6


h = zeros(12)
h[7] = 0.1

x_oth = 0.9 .* ones(12)

(x, s_beg) = optimize_periodic_sales_NLopt(;
    h = h,
    x_oth = x_oth,
    x_init = x_init,
    s_beg_init = 0,
    α = 2.5,
    λ = 1.,
    δ = 0.,
    ρ = 0.,
    p_sto = 0.2 / 12,
    x_star = 1.,
    N_year = 12,
    tol = 1e-8,
    verbose = true,
)

@test sum(x) ≈ sum(h)
@test x[7] == maximum(x)
@test s_beg ≥ 1e-6

s = get_storage_timeseries(h, x, s_beg)

@test s[end] ≈ s_beg

x_init = x + 0.05 .* randn(12)
x_init[x_init .< 0] .= 0

# Test if the optimized sales (with boundary condition) equal the periodic sales

function expected_revenue_curve(x1)
    value = P(x1 + x_oth[1], 2.5, 1) * x1
    grad = P(x1 + x_oth[1], 2.5, 1) + grad_P(x1 + x_oth[1], 2.5, 1)[1] * x1
    return (value, grad)
end

x_opt, f_opt = optimize_sales_NLopt(;
    revenue_curve = expected_revenue_curve,
    x1_max = 12.,
    h = h,
    s_beg = s_beg,
    s_end = s_beg,
    x_oth = x_oth[2:end],
    Δp = 0,
    x_init = x_init,
    α = 2.5,
    λ = 1.,
    δ = 0.,
    ρ = 0.,
    p_sto = 0.2 / 12,
    N_hor = 11,
    x_star = 1.,
    tol = 1e-6,
    verbose = true,
)

@test isapprox(x_opt, x; atol = 1e-5)

# Test if demand request with low reservation price is rejected

sorted_demand_requests = [
    Transaction("id", "id", quantity, price)
    for
    (quantity, price) in
    zip([0.05, 0.05], [1., 0.2])
]

(revenue_curve, x1_thresholds) = determine_revenue_curve(sorted_demand_requests)

x_opt, f_opt = optimize_sales_NLopt(;
    revenue_curve = x -> revenue_curve(x; max_slope = 1e6),
    x1_max = 0.1,
    h = ones(12) .* 0.1, #vcat(1, zeros(11)),
    s_beg = 0.,
    s_end = 0.,
    x_oth = 0.9 .* ones(11),
    Δp = 0,
    x_init = 0.1 .* ones(12),
    α = 2.5,
    λ = 1.,
    δ = 0.,
    ρ = 0.,
    p_sto = 0.2 / 12,
    N_hor = 11,
    x_star = 1.,
    tol = 1e-8,
    verbose = true,
)

@test isapprox(x_opt[1], 0.05, atol = 1e-4)

# Test if the line search optimization method leads to the same result

(revenue_curve, x1_thresholds) = determine_revenue_curve(sorted_demand_requests)

x_opt_2 = optimize_sales_NLopt_LineSearch(;
    revenue_curve = revenue_curve,
    x1_thresholds = x1_thresholds,
    h = ones(12) .* 0.1, #vcat(1, zeros(11)),
    s_beg = 0.,
    s_end = 0.,
    x_oth = 0.9 .* ones(11),
    Δp = 0,
    x_init = 0.1 .* (ones(12) + 0.01 .* randn(12)),
    α = 2.5,
    λ = 1.,
    δ = 0.,
    ρ = 0.,
    p_sto = 0.2 / 12,
    N_hor = 11,
    x_star = 1.,
    tol = 1e-8,
    verbose = true,
)

@test isapprox(x_opt, x_opt_2, atol = 1e-4)

# Test if demand request can be partially fulfilled

sorted_demand_requests = [
    Transaction("id", "id", quantity, price)
    for
    (quantity, price) in
    zip([0.1], [0.63])
]

(revenue_curve, x1_thresholds) = determine_revenue_curve(sorted_demand_requests)

x_opt, f_opt = optimize_sales_NLopt(;
    revenue_curve = x -> revenue_curve(x; max_slope = 1e6),
    x1_max = 0.1,
    h = vcat(1.2, zeros(11)),
    s_beg = 0.,
    s_end = 0.,
    x_oth = 0.9 .* ones(11),
    Δp = 0,
    x_init = 0.1 .* ones(12),
    α = 2.5,
    λ = 1.,
    δ = 0.,
    ρ = 0.,
    p_sto = 0.2 / 12,
    N_hor = 11,
    x_star = 1.,
    tol = 1e-8,
    verbose = true,
)

@test isapprox(x_opt[1], 0.0587, atol = 1e-4)
# TODO: check the numerical value using an external optimizer - it used to equal 0.056

# Test if the line search optimization method leads to the same result

x_opt_2 = optimize_sales_NLopt_LineSearch(;
    revenue_curve = revenue_curve,
    x1_thresholds = x1_thresholds,
    h = vcat(1.2, zeros(11)),
    s_beg = 0.,
    s_end = 0.,
    x_oth = 0.9 .* ones(11),
    Δp = 0,
    x_init = 0.1 .* ones(12),
    α = 2.5,
    λ = 1.,
    δ = 0.,
    ρ = 0.,
    p_sto = 0.2 / 12,
    N_hor = 11,
    x_star = 1.,
    tol = 1e-8,
    verbose = true,
)

@test isapprox(x_opt, x_opt_2, atol = 1e-4)


# Test boundary cases

sorted_demand_requests = [
    Transaction("id", "id", quantity, price)
    for
    (quantity, price) in
    zip([0.1], [0.01])
]

(revenue_curve, x1_thresholds) = determine_revenue_curve(sorted_demand_requests)

x_opt = optimize_sales_NLopt_LineSearch(;
    revenue_curve = revenue_curve,
    x1_thresholds = x1_thresholds,
    h = fill(0.1, 12),
    s_beg = 0.,
    s_end = 0.,
    x_oth = 0.9 .* ones(11),
    Δp = 0,
    x_init = 0.1 .* ones(12),
    α = 2.5,
    λ = 1.,
    δ = 0.,
    ρ = 0.,
    p_sto = 0.2 / 12,
    N_hor = 11,
    x_star = 1.,
    tol = 1e-8,
    verbose = true,
)

@test x_opt[1] == 0

sorted_demand_requests = [
    Transaction("id", "id", quantity, price)
    for
    (quantity, price) in
    zip([0.1], [1.0])
]

(revenue_curve, x1_thresholds) = determine_revenue_curve(sorted_demand_requests)

x_opt = optimize_sales_NLopt_LineSearch(;
    revenue_curve = revenue_curve,
    x1_thresholds = x1_thresholds,
    h = fill(0.1, 12),
    s_beg = 0.,
    s_end = 0.,
    x_oth = 0.9 .* ones(11),
    Δp = 0,
    x_init = 0.1 .* ones(12),
    α = 2.5,
    λ = 1.,
    δ = 0.,
    ρ = 0.,
    p_sto = 0.2 / 12,
    N_hor = 11,
    x_star = 1.,
    tol = 1e-8,
    verbose = true,
)

@test x_opt[1] == 0.1

end
