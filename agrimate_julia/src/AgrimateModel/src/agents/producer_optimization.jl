using NLopt: Opt, equality_constraint!, inequality_constraint!, optimize



optimizer = :NLopt_LineSearch
# optimizer = :NLopt
@assert optimizer ∈ [:NLopt, :NLopt_LineSearch]

periodic_optimizer = :NLopt
@assert periodic_optimizer ∈ [:NLopt]

function optimize_sales(;kwargs...)
    if optimizer == :NLopt
        return optimize_sales_NLopt(;kwargs...)
        # return optimize_sales_NLopt(;kwargs...)[begin]
    elseif optimizer == :NLopt_LineSearch
        return optimize_sales_NLopt_LineSearch(;kwargs...)
    end
end

function optimize_periodic_sales(;kwargs...)
    if periodic_optimizer == :NLopt
        return optimize_periodic_sales_NLopt(;kwargs...)
    end
end


# Needed for TWO MARKETS
function optimize_sales_NLopt_two_markets(;
    revenue_curve::Function,
    x1_domestic,
    x1_foreign,
    h::Vector{Float64},
    s_beg,
    # s_end,
    x_oth_domestic::Vector{Float64},
    x_oth_foreign::Vector{Float64},
    x_init_domestic::Vector{Float64},
    x_init_foreign::Vector{Float64},
    α_domestic,
    α_foreign, 
    λ,
    δ,
    ρ,
    p_sto,
    x_star_domestic = 1.,
    x_star_foreign = 1.,
    N_hor,
    sales_share_foreign_baseline,
    equal_constraint = false,
    x_market = nothing,
    x_market_unique = nothing,
    tol = 1e-8,
    P_loc_domestic = 1.,
    P_loc_foreign = 1.,
    ζ = 1.,
    equal_domestic_sales = nothing,
    verbose = true,
    domestic_profit_factor = 1.,
    producer_id = nothing,
    x_minimum = 0.
)
    
    # only single L_matrix because same shape is used for domestic and foreign sales.
    L = get_L_matrix(N_hor + 1; δ)
    unit_costs = get_unit_storage_costs(N_hor + 1, p_sto; δ, ρ)

    # x1 is fixed
    x1_total = (x1_domestic + x1_foreign)
    stock_begin = s_beg + h[1] - x1_total
    N = N_hor
    n = 2:N_hor+1
    
    total_possible_sales = stock_begin + sum(h[n])
    x_minimum_two_markets = x_minimum * total_possible_sales /(N * 2)  # If you have N_hor time steps you can distribute 100% on 2 markets for N_hor timesteps --> 1/(2* N_hor) for equal complete distribution of minimum sales. x_minimum says how much you want to use from that. 
    x_minimum_one_market = x_minimum * total_possible_sales /(N)  # If you have N_hor time steps you can distribute 100% on 1 markets for N_hor timesteps --> 1/( N_hor) for equal complete distribution. x_minimum says how much you want to use from that equal distribution for minimum sales. 
    

    # Current profit based on demand requests
    (current_revenue, grad_current_revenue_total,grad_current_revenue_domestic, grad_current_revenue_foreign) = 
        revenue_curve(x1_domestic,x1_foreign)
    current_profit = current_revenue - unit_costs[1] * (x1_domestic + x1_foreign - h[1])
    grad_current_profit = grad_current_revenue_total - unit_costs[1]
    grad_current_profit_domestic = grad_current_revenue_domestic - unit_costs[1]
    grad_current_profit_foreign = grad_current_revenue_foreign - unit_costs[1]

    #Attention! Here has our x the dimension 2 * N!
    function write_matrix(L)
        x_dim = size(L)[1]
        y_dim = size(L)[2]
        for i in 1:x_dim
            for j in 1:y_dim
                print(L[i, j], " ")
            end
        end
    end
    function availability_constraints_both_markets!(result,x, grad)
        
        c = L[n, n] * h[n] + L[n, begin] .* stock_begin 
        
        if length(grad) > 0
            grad[1:N_hor,:] = L[n, n]'
            grad[N_hor+1:end,:] = L[n, n]'
        end


        result[:] = L[n, n] * x[1:N_hor] + L[n, n] * x[N_hor+1:end] - c

    end
    function availability_constraints_single_market!(result,x, grad)
        c = L[n, n] * h[n] + L[n, begin] .* stock_begin 

        if length(grad) > 0
            grad[1:N_hor,:] = L[n, n]'
        end
        result[:] = L[n, n] * x[1:N_hor] - c
    end
    function availability_constraints_fixed_sales!(result,x, grad;fixed_sales=fill(0.,N))
        c = L[n, n] * h[n] + L[n, begin] .* stock_begin 

        if length(grad) > 0
            grad[1:N_hor,:] = L[n, n]'
        end
        result[:] = L[n, n] * x[1:N_hor] + fixed_sales[:] - c
    end
   
    function boundary_condition_both_markets!(x, grad)
        c = L[end, n]' * h[n] + L[end, begin] * stock_begin - s_beg
        if length(grad) > 0
            grad[1:N_hor] = L[end, n]
            grad[N_hor+1:end] = L[end, n]
        end
        return L[end, n]' * (x[1:N_hor] + x[N_hor+1:end]) - c
    end
    function boundary_condition_single_market!(x, grad)
        c = L[end, n]' * h[n] + L[end, begin] * stock_begin - s_beg
        if length(grad) > 0
            grad[:] = L[end,n]
        end
        return L[end, n]' * x - c
    end
    
    

    function objective_function_both_markets!(x, grad)
        # Expected future profit based on profit function
        expected_profit =
            profit_function_two_markets(
                x[1:N_hor],
                x[N_hor+1:end],
                x_oth_domestic,
                x_oth_foreign,
                x_star_domestic,
                x_star_foreign,
                α_domestic, 
                α_foreign, 
                λ,
                unit_costs[2:end],
                h[2:end];
                P_loc_domestic = P_loc_domestic,
                P_loc_foreign = P_loc_foreign,
                ρ = ρ,
                domestic_profit_factor = domestic_profit_factor,
            ) / (1 + ρ)
        # Quadratic penalty favoring constant sales | First (Second) penalty part from domestic (foreign) sales
        # penalty = pre_factor * quadratic_penalty_former_sells(x[1:N_hor],x_oth_domestic,x_star_domestic,α_domestic, λ,x_init_domestic[2:end]; ρ) + 
        # quadratic_penalty_former_sells(x[N_hor+1:end],x_oth_foreign,x_star_foreign,α_foreign, λ,x_init_foreign[2:end]; ρ) 
        penalty = quadratic_minimum_sale_penalty_two_markets(x[1:N_hor], x[N_hor+1:end], x_oth_domestic, x_oth_foreign,
                                                             x_star_domestic, x_star_foreign, α_domestic, α_foreign, λ, x_minimum_two_markets)

        if length(grad) > 0
            grad[1:N_hor] = 
                grad_profit_function(
                    x[1:N_hor], 
                    x_oth_domestic, 
                    x_star_domestic, 
                    α_domestic, 
                    λ,
                    unit_costs[2:end]; 
                    P_loc = P_loc_domestic, 
                    ρ = ρ
                ) ./ (1 + ρ)
            grad[N_hor+1:end] = 
                grad_profit_function(
                    x[N_hor+1:end], 
                    x_oth_foreign, 
                    x_star_foreign, 
                    α_foreign, 
                    λ,
                    unit_costs[2:end]; 
                    P_loc = P_loc_foreign, 
                    ρ = ρ
                ) ./ (1 + ρ)
            # grad[1:N_hor] -= (1 - ζ) .* pre_factor * grad_quadratic_penalty_former_sells(x[1:N_hor],x_oth_domestic,x_star_domestic,α_domestic, λ,x_init_domestic[2:end] ; ρ)
            # grad[N_hor+1:end] -= (1 - ζ) .* grad_quadratic_penalty_former_sells(x[N_hor+1:end],x_oth_foreign,x_star_foreign,α_foreign, λ,x_init_foreign[2:end]; ρ)
            
            grad_penalty_dom, grad_penalty_for = gradient_quadratic_minimum_sale_penalty_two_markets(x[1:N_hor], x[N_hor+1:end], x_oth_domestic, x_oth_foreign, x_star_domestic, x_star_foreign, α_domestic, α_foreign, λ, x_minimum_two_markets)
            grad[1:N_hor] -= (1 - ζ) .* grad_penalty_dom 
            grad[N_hor+1:end] -= (1 - ζ) .* grad_penalty_for
        end
        return   (expected_profit) - (1 - ζ) * penalty 
    end


    function objective_function_single_market!(x, grad, x_star, α, other_sales,P_loc,x_former)
        # Expected future profit based on profit function
        expected_profit =
            profit_function(
                x[1:N_hor],
                other_sales,
                x_star,
                α, 
                λ,
                unit_costs[2:end],
                h[2:end];
                P_loc,
                ρ,
            ) / (1 + ρ)
        # penalty = pre_factor * quadratic_penalty_former_sells(x[1:N_hor],other_sales, x_star, α ,λ, x_former; ρ) 
        
        penalty = quadratic_minimum_sale_penalty(x[1:N_hor],other_sales, x_star, α ,λ, x_minimum_one_market) 
        if length(grad) > 0
            grad[1:N_hor] = 
                grad_profit_function(
                    x[1:N_hor], 
                    other_sales, 
                    x_star, 
                    α, 
                    λ,
                    unit_costs[2:end]; 
                    P_loc, 
                    ρ
                ) ./ (1 + ρ)
            # grad[1:N_hor] -= (1 - ζ) * pre_factor .* grad_quadratic_penalty_former_sells(x[1:N_hor],other_sales, x_star, α ,λ, x_former; ρ)
            grad[1:N_hor] -= (1 - ζ) .* gradient_quadratic_minimum_sale_penalty(x[1:N_hor],other_sales, x_star, α ,λ, x_minimum_one_market)
        end
        return (expected_profit) - (1 - ζ) * penalty
    end

    
    x_max_domestic = x_star_domestic * (1 / α_domestic + 1) ^ (1 / λ) .- x_oth_domestic
    x_max_foreign = x_star_foreign * (1 / α_foreign + 1) ^ (1 / λ) .- x_oth_foreign


    
    if !isnothing(x_market_unique)
        x_min = zeros(N_hor)
        # 2) Supply > exclusive market demand (optional)
        x_min_avail = s_beg + h[1]
        
        for n = 1:N_hor
            x_min_avail += h[n+1] - (n == 1 ? x1_total : x_min[n-1])
            x_min[n] = min(
                (x_market_unique / (x_star_domestic + x_star_foreign)) / (1 - x_market_unique / (x_star_domestic + x_star_foreign)) * x_oth_foreign[n],
                x_min_avail,
            )
        end
        x_min_domestic = (1. - sales_share_foreign_baseline) .* x_min
        x_min_foreign = sales_share_foreign_baseline .* x_min
    else
        x_min_domestic = zeros(N_hor)
        x_min_foreign = zeros(N_hor)
    end
    
    # Upper bounds for x
    # 1) Price > 0
    if !isnothing(x_market)
        # 2) Supply < maximum market demand (optional)
        if x_market / (x_star_domestic + x_star_foreign) < 1
            x_max_supply = (x_market / ((x_star_domestic + x_star_foreign))) / (1 - x_market / (x_star_domestic + x_star_foreign)) .* x_oth_foreign
        else
            x_max_supply = fill(Inf, N_hor)
        end
        x_max_domestic = min.(x_max_domestic, (1. - sales_share_foreign_baseline) .* x_max_supply)
        x_max_foreign = min.(x_max_foreign, sales_share_foreign_baseline .* x_max_supply)
    end

    
    #Set optimizer algorithm --> Needs to be a optimizer which takes inequality constraint. (but grad-based algorithm is not strictly required)
    optimizer_algorithm = :LD_SLSQP
    # optimizer_algorithm = :LN_COBYLA
    # optimizer_algorithm = :LN_AUGLAG
    
    inequality_constraint_number = 0.
    if sales_share_foreign_baseline == 0.
        #only domestic market --> sinlge market objective function with x array of 1*N with domestic parameters! --> zeros(N) for foreign sales are added at the end.
        if !isnothing(equal_domestic_sales)
            expected_profit = 100.
            println("equal domestic sales")
            x_opt_domestic = vcat(x1_domestic,fill(equal_domestic_sales,N_hor))
            x_opt_foreign = vcat(x1_foreign,zeros(N_hor))
            return (x_opt_domestic,x_opt_foreign,expected_profit)
        end

        opt = Opt(optimizer_algorithm, N)
        opt.max_objective = (x,grad) -> objective_function_single_market!(x,grad,x_star_domestic,α_domestic,x_oth_domestic,P_loc_domestic,x_init_domestic[2:end])    
        inequality_constraint!(opt, availability_constraints_single_market!, fill(inequality_constraint_number, N_hor))
        if equal_constraint
            equality_constraint!(opt, boundary_condition_single_market!, tol)
        end
        # Lower bounds for x
        x_min = x_min_domestic
        opt.lower_bounds = x_min
        # Upper bounds for x
        x_max = x_max_domestic
        opt.upper_bounds = x_max 
        # Set x_init 
        x_init = x_init_domestic[2:end]
    
    elseif sales_share_foreign_baseline == 1. || !isnothing(equal_domestic_sales)
        #only world/foreign market --> single market objective function with x array of 1*N with foreign parameters! --> zeros(N) for domestic sales are added at the end.
        opt = Opt(optimizer_algorithm, N)
        opt.max_objective = (x,grad) -> objective_function_single_market!(x,grad,x_star_foreign,α_foreign,x_oth_foreign,P_loc_foreign,x_init_foreign[2:end])    
        
        if isnothing(equal_domestic_sales)
            inequality_constraint!(opt, availability_constraints_single_market!, fill(inequality_constraint_number, N_hor))
            if equal_constraint
                equality_constraint!(opt, boundary_condition_single_market!, tol)
            end
        else
            inequality_constraint!(opt, (result, x, grad) -> availability_constraints_fixed_sales!(result, x, grad; fixed_sales = fill(equal_domestic_sales, N_hor)), fill(inequality_constraint_number, N_hor))
            
        end
        #Lower bounds for x
        x_min = x_min_foreign
        opt.lower_bounds = x_min
        # Upper bounds for x
        x_max = x_max_foreign
        opt.upper_bounds = x_max 
        # Set x_init
        x_init = x_init_foreign[2:end]
    else
        #both markets (domestic and foreign) are used! --> both market objective function!
        opt = Opt(optimizer_algorithm, 2*N)
        opt.max_objective = objective_function_both_markets!    
        inequality_constraint!(opt, (result, x, grad) -> availability_constraints_both_markets!(result, x, grad), fill(inequality_constraint_number, 1*N_hor))
        if equal_constraint
            equality_constraint!(opt, boundary_condition_both_markets!, tol)
        end
        # Lower bounds for x
        x_min = vcat(x_min_domestic,x_min_foreign)
        opt.lower_bounds = x_min
        # Upper bounds for x
        
        x_max = vcat(x_max_domestic, x_max_foreign)
        opt.upper_bounds = x_max 
        x_init = vcat(x_init_domestic[2:end],x_init_foreign[2:end])
    end
    x_init_new = x_init
    x_init_new = fill((stock_begin + sum(h[n])) / length(x_init), length(x_init))
    
    x_init = max.(opt.lower_bounds, min.(x_init_new, opt.upper_bounds))
    opt.xtol_abs = tol
    
    opt.maxtime = 60
    f_opt = nothing
    v_opt = nothing
    return_code = nothing
    try
        (f_opt, x_opt, return_code) = optimize(opt, x_init)
    catch
        x_init_new_new = opt.upper_bounds
        (f_opt, x_opt, return_code) = optimize(opt, x_init_new_new)
    end
    # (f_opt, x_opt, return_code) = optimize(opt, x_init)

    if return_code ≠ :XTOL_REACHED
        verbose && println("Repeated optimization (1/3) [return string: $return_code] ", producer_id)
        x_init_new = max.(x_init .- 0.01, opt.lower_bounds)
        (f_opt, x_opt, return_code) = optimize(opt, x_init_new)
    end
    if return_code ≠ :XTOL_REACHED
        verbose && println("Repeated optimization (2/3) [return string: $return_code] ", producer_id)
        x_init_new = min.(x_init .+ 0.01, opt.upper_bounds)
        (f_opt, x_opt, return_code) = optimize(opt, x_init_new)
    end
    if return_code ≠ :XTOL_REACHED
        verbose && println("Repeated optimization (3/3) [return string: $return_code] ", producer_id)
        x_init_new = fill((stock_begin + sum(h[n])) / length(x_init), length(x_init))
        x_init_new = max.(opt.lower_bounds, min.(x_init, opt.upper_bounds))
        (f_opt, x_opt, return_code) = optimize(opt, x_init_new)
    end
    if return_code ≠ :XTOL_REACHED
        verbose && println("Repeated optimization (4/3) [return string: $return_code] ", producer_id)
        (f_opt, x_opt, return_code) = optimize(opt, x_init)
    end
    
    if !isnothing(equal_domestic_sales)
        x_opt_domestic = vcat(x1_domestic, fill(equal_domestic_sales,N_hor))
        x_opt_foreign = vcat(x1_foreign,x_opt[1:N_hor])
    elseif sales_share_foreign_baseline == 0.
        #zeros(N) for foreign sales are added.
        x_opt_domestic = vcat(x1_domestic,x_opt[1:N_hor])
        x_opt_foreign = vcat(x1_foreign,zeros(N_hor))
    elseif sales_share_foreign_baseline == 1. 
        x_opt_domestic = vcat(x1_domestic, zeros(N_hor))
        x_opt_foreign = vcat(x1_foreign,x_opt[1:N_hor])
        #only world/foreign market --> single market objective function with x array of 1*N with foreign parameters! --> zeros(N) for domestic sales are added at the end.
    else
        x_opt_domestic = vcat(x1_domestic,x_opt[1:N_hor])
        x_opt_foreign = vcat(x1_foreign,x_opt[N_hor+1:end])
        
        rev_dom = x_opt[1:N_hor] .* P((x_opt[1:N_hor] + x_oth_domestic) ./ x_star_domestic, α_domestic, λ)
        rev_dom_minus = (x_opt[1:N_hor] .- 1.) .* P(((x_opt[1:N_hor] .- 1.) + x_oth_domestic) ./ x_star_domestic, α_domestic, λ)
        rev_dom_plus = (x_opt[1:N_hor] .+ 1.) .* P(((x_opt[1:N_hor] .+ 1.) + x_oth_domestic) ./ x_star_domestic, α_domestic, λ)
        rev_for = x_opt[N_hor+1:end] .* P((x_opt[N_hor+1:end] + x_oth_foreign) ./ x_star_foreign, α_foreign, λ)
        rev_for_minus = (x_opt[N_hor+1:end] .- 1.) .* P(((x_opt[N_hor+1:end] .- 1.) + x_oth_foreign) ./ x_star_foreign, α_foreign, λ)
        rev_for_plus = (x_opt[N_hor+1:end] .+ 1.) .* P(((x_opt[N_hor+1:end] .+ 1.) + x_oth_foreign) ./ x_star_foreign, α_foreign, λ)


    end
    x_opt = vcat(x_opt_domestic,x_opt_foreign) # Actually I do not need this one. I leave it in just in case for later usage 

    if verbose
        fixed_x1 = (N == N_hor ? "yes" : "no")
        println("OPTIMIZATION RESULTS (fixed x1: $fixed_x1, return string: $return_code)")
        println("x_opt: ", round.(x_opt, digits = 4))
        println("f(x_opt): ", round(f_opt, digits = 4))
        println("evaluations: ", opt.numevals)
    end


    return (x_opt_domestic,x_opt_foreign, f_opt)
end











#########################
##########################
##########################


# Optimization with boundary condition
function optimize_sales_NLopt(;
    revenue_curve::Function,
    x1_min = 0,
    x1_max,
    x1_thresholds = nothing,
    h::Vector{Float64},
    s_beg,
    s_end,
    x_oth::Vector{Float64},
    P_loc,
    x_init::Vector{Float64},
    α,
    λ,
    δ,
    ρ,
    p_sto,
    ζ = 1.,
    N_hor,
    d = 1.,
    x_star = 1.,
    x_market = nothing,
    x_market_unique = nothing,
    equal_constraint = true,
    tol = 1e-8,
    verbose = true,
    storage_hold_back,
)

    L = get_L_matrix(N_hor + 1; δ)
    unit_costs = get_unit_storage_costs(N_hor + 1, p_sto; δ, ρ)

    # Determine dimensionality of the optimization problem
    if !isapprox(x1_min, x1_max, atol=tol)
        # x1 has to be optimized
        N = N_hor + 1
        n = 1:N_hor+1
    else
        # x1 is fixed
        x1 = x1_min
        s_beg = s_beg + h[1] - x1
        N = N_hor
        n = 2:N_hor+1
    end


    function availability_constraints!(result, x, grad)
        c = L[n, n] * h[n] + L[n, begin] .* s_beg * (1-storage_hold_back) # storage_hold_back is to make that not all storage is going to be offered
        if length(grad) > 0
            grad[:] = L[n, n]'
        end
        result[:] = L[n, n] * x - c
    end

    function boundary_condition!(x, grad)
        c = L[end, n]' * h[n] + L[end, begin] * s_beg - s_end
        if length(grad) > 0
            grad[:] = L[end, n]
        end
        return L[end, n]' * x - c
    end

    # 
    
    

    function objective_function!(x, grad)
        # Current profit based on demand requests
        (current_revenue, grad_current_revenue) = revenue_curve(x[1])
        current_profit = current_revenue - unit_costs[1] * (x[1] - h[1])
        grad_current_profit = grad_current_revenue - unit_costs[1]
        # Expected future profit based on profit function
        expected_profit =
            profit_function(
                x[2:end],
                x_oth,
                d * x_star,
                α,
                λ,
                unit_costs[2:end],
                h[2:end];
                P_loc,
                ρ,
            ) / (1 + ρ)
        # Quadratic penalty favoring constant sales
        penalty = quadratic_penalty(x; ρ)

        if length(grad) > 0
            grad[1] = ζ * grad_current_profit
            grad[2:end] =
                ζ .* grad_profit_function(
                    x[2:end],
                    x_oth,
                    d * x_star,
                    α,
                    λ,
                    unit_costs[2:end];
                    P_loc,
                    ρ,
                ) ./ (1 + ρ)
            grad[:] -= (1 - ζ) .* grad_quadratic_penalty(x; ρ)
        end

        return ζ * (current_profit + expected_profit) - (1 - ζ) * penalty
    end

    function objective_function_fixed_x1!(x, grad)
        grad_full = Vector{Float64}(undef, N_hor + 1)
        res = objective_function!(vcat(x1, x), grad_full)
        if length(grad) > 0
            grad[:] = grad_full[2:end]
        end
        return res
    end

    opt = Opt(:LD_SLSQP, N)
    opt.xtol_abs = tol
    opt.maxtime = 60
    if N == N_hor + 1
        opt.max_objective = objective_function!
    elseif N == N_hor
        opt.max_objective = objective_function_fixed_x1!
    end

    inequality_constraint!(opt, availability_constraints!, fill(tol, N))
    if equal_constraint
        equality_constraint!(opt, boundary_condition!, tol)
    end
    # Lower bounds for x
    # 1) Supply ≥ 0
    x_min = zeros(N_hor)
    if !isnothing(x_market_unique)
        # 2) Supply > exclusive market demand (optional)
        x_min_avail = s_beg + h[1]
        for n = 1:N_hor
            x_min_avail += h[n+1] - (n == 1 ? x1_min : x_min[n-1])
            x_min[n] = min(
                (d * x_market_unique / x_star) / (1 - d * x_market_unique / x_star) * x_oth[n],
                x_min_avail,
            )
        end
    end
    x_min = vcat(x1_min, x_min)
    opt.lower_bounds = x_min[n]
    # Upper bounds for x
    # 1) Price > 0
    x_max = d * x_star * (1 / α + 1) ^ (1 / λ) .- x_oth
    if !isnothing(x_market)
        # 2) Supply < maximum market demand (optional)
        if x_market / x_star < 1
            x_max_supply = (x_market / (d * x_star)) / (1 - x_market / x_star) .* x_oth
        else
            x_max_supply = fill(Inf, length(N_hor))
        end
        x_max = min.(x_max, x_max_supply)
    end
    x_max = vcat(x1_max, x_max)
    opt.upper_bounds = x_max[n]

    # Initial vector has to obey the bounds
    x_init = max.(opt.lower_bounds, min.(x_init[n], opt.upper_bounds))

    (f_opt, x_opt, return_code) = optimize(opt, x_init)

    if return_code ≠ :XTOL_REACHED
        verbose && println("Repeated optimization (1/3) [return string: $return_code]")
        x_init_new = max.(x_init .- 0.01, opt.lower_bounds)
        (f_opt, x_opt, return_code) = optimize(opt, x_init_new)
    end
    if return_code ≠ :XTOL_REACHED
        verbose && println("Repeated optimization (2/3) [return string: $return_code]")
        x_init_new = min.(x_init .+ 0.01, opt.upper_bounds)
        (f_opt, x_opt, return_code) = optimize(opt, x_init_new)
    end
    if return_code ≠ :XTOL_REACHED
        verbose && println("Repeated optimization (3/3) [return string: $return_code]")
        x_init_new = fill((s_beg + sum(h)) / length(x_init), length(x_init))
        x_init_new = max.(opt.lower_bounds, min.(x_init, opt.upper_bounds))
        (f_opt, x_opt, return_code) = optimize(opt, x_init_new)
    end
    if return_code ≠ :XTOL_REACHED
        verbose && println("Repeated optimization (4/3) [return string: $return_code]")
        (f_opt, x_opt, return_code) = optimize(opt, x_init)
    end

    if N == N_hor
        x_opt = vcat(x1, x_opt)
    end


    if verbose
        fixed_x1 = (N == N_hor ? "yes" : "no")
        println("OPTIMIZATION RESULTS (fixed x1: $fixed_x1, return string: $return_code)")
        println("x_opt: ", round.(x_opt, digits = 4))
        println("f(x_opt): ", round(f_opt, digits = 4))
        println("evaluations: ", opt.numevals)
    end

    # @assert return_code == :XTOL_REACHED "Producer optimization return code: $return_code"

    return (x_opt, f_opt)
end


function optimize_sales_NLopt_LineSearch(;
    revenue_curve::Function,
    x1_min = 0,
    x1_max = Inf,
    x1_thresholds::Vector{Float64},
    h::Vector{Float64},
    s_beg,
    s_end,
    x_oth::Vector{Float64},
    P_loc,
    x_init::Vector{Float64},
    α,
    λ,
    δ,
    ρ,
    p_sto,
    ζ = 1.,
    N_hor,
    d = 1.,
    x_star = 1.,
    x_market = nothing,
    x_market_unique = nothing,
    equal_constraint = true,
    tol = 1e-8,
    verbose = true,
    storage_hold_back,

)
    function get_optimized_sales_and_profit(x1_min, x1_max, x_init)
        # Enforce constant gradient over the segment between two thresholds
        grad_revenue_curve = revenue_curve((x1_min + x1_max) / 2)[2]
        (x_opt, f_opt) = optimize_sales_NLopt(;
            revenue_curve = x -> (revenue_curve(x)[1], grad_revenue_curve),
            x1_min,
            x1_max,
            h,
            s_beg,
            s_end,
            x_oth,
            P_loc,
            x_init,
            α,
            λ,
            δ,
            ρ,
            p_sto,
            ζ,
            N_hor,
            d,
            x_star,
            x_market,
            x_market_unique,
            equal_constraint,
            tol,
            verbose,
            storage_hold_back,

        )
        return (x_opt, f_opt)
    end

    # External constraints
    x1_min_ext = x1_min
    x1_max_ext = x1_max

    # Modify thresholds to account for the availability constraint and external constraints
    x1_upper_bound = min(s_beg + h[1], x1_max_ext)
    if x1_upper_bound < x1_thresholds[end]
        first_index_to_remove = searchsortedfirst(x1_thresholds, x1_upper_bound)
        x1_thresholds = x1_thresholds[begin:first_index_to_remove-1]
        push!(x1_thresholds, x1_upper_bound)
    end
    x1_lower_bound = min(s_beg + h[1], x1_min_ext)
    if x1_lower_bound > 0
        last_index_to_remove = searchsortedlast(x1_thresholds, x1_lower_bound)
        x1_thresholds = x1_thresholds[last_index_to_remove+1:end]
    end

    # If x1 is fixed perform a single optimization
    if isapprox(x1_upper_bound, x1_lower_bound, atol = tol)
        return get_optimized_sales_and_profit(x1_lower_bound, x1_upper_bound, x_init)
        # return get_optimized_sales_and_profit(x1_lower_bound, x1_upper_bound, x_init)[1]
    end

    # Otherwise perform a line search moving segment by segment (starting from the right)
    N_thresh = length(x1_thresholds)
    profit_values = fill(-Inf, N_thresh)
    optimal_solutions = Matrix{Float64}(undef, (N_thresh, N_hor + 1))

    for i = N_thresh:-1:1
        
        x1_min = (i > 1 ? x1_thresholds[i - 1] : x1_lower_bound)
        x1_max = x1_thresholds[i]
        if verbose
            println("Subproblem $(N_thresh - i + 1)/$N_thresh: x1 ∈ [$(round(x1_min, digits = 4)), $(round(x1_max, digits = 4))]")
        end
        (optimal_solutions[i, :], profit_values[i]) = get_optimized_sales_and_profit(
            x1_min,
            x1_max,
            (i < N_thresh ? optimal_solutions[i + 1, :] : x_init)
        )
        # Unless x1 is at the left segment boundary, break to avoid unnecessary optimizations
        if optimal_solutions[i, 1] > x1_min + 10 * tol
            break
        end
    end

    i_max = argmax(profit_values)
    return optimal_solutions[i_max, :]
end


# Periodic optimization

function optimize_periodic_sales_NLopt(;
    h::Vector{Float64},
    x_oth::Vector{Float64},
    x_init::Vector{Float64},
    s_beg_init,
    α,
    λ,
    δ,
    ρ,
    p_sto,
    ζ = 1.,
    N_year,
    x_star = 1.,
    x_market = nothing,
    x_market_unique = nothing,
    tol = 1e-8,
    verbose = true,
    storage_hold_back,

)

    @assert length(h) == N_year
    @assert length(x_oth) == N_year
    @assert length(x_init) == N_year

    L = get_L_matrix(N_year, δ = δ)
    unit_costs = get_unit_storage_costs(N_year, p_sto; δ, ρ)
    x_avg = sum(h) / N_year

   

    function availability_constraints!(result, v, grad)
        A = hcat(L, -L[:, begin] * (1 - δ))
        c = L * h
        if length(grad) > 0
            grad[:] = A'
        end
        result[:] = A * v - c
    end

    function periodicity_constraint!(v, grad)
        A = hcat(L[end, :]', 1 - L[end, begin] * (1 - δ))
        c = L[end, :]' * h
        if length(grad) > 0
            grad[:] = A'
        end
        return A * v - c
    end

    function objective_function!(v, grad)
        (x, s_beg) = (v[begin:N_year], v[end])
        unit_cost_of_s_beg = -unit_costs[begin] * (1 - δ)
        if length(grad) > 0
            grad[begin:N_year] =
                ζ .* grad_profit_function(x, x_oth, x_star, α, λ, unit_costs; ρ)
            grad[end] = -ζ * unit_cost_of_s_beg
            grad[begin:N_year] -= (1 - ζ) .* grad_quadratic_penalty(x, x_avg; ρ)
        end
        profit = profit_function(x, x_oth, x_star, α, λ, unit_costs, h; ρ)
        profit -= unit_cost_of_s_beg * s_beg
        penalty = quadratic_penalty(x, x_avg; ρ)
        return ζ * profit - (1 - ζ) * penalty
    end

    opt = Opt(:LD_SLSQP, N_year + 1)
    opt.xtol_abs = tol
    opt.maxtime = 60
    opt.max_objective = objective_function!

    inequality_constraint!(opt, availability_constraints!, fill(tol, N_year))
    equality_constraint!(opt, periodicity_constraint!, tol)
    # Lower bounds for x:
    # 1) Supply ≥ 0
    x_min = zeros(N_year)
    if !isnothing(x_market_unique)
    # 2) Supply > exclusive market demand (optional)
        x_min = (x_market_unique / x_star) / (1 - x_market_unique / x_star) .* x_oth
    end
    opt.lower_bounds = vcat(x_min, 0)
    # Upper bounds for x
    # 1) Price > 0
    x_max = x_star * (1 / α + 1) ^ (1 / λ) .- x_oth
    if !isnothing(x_market)
        # 2) Supply < maximum market demand (optional)
        if x_market / x_star < 1
            x_max_supply = (x_market / x_star) / (1 - x_market / x_star) .* x_oth
        else
            x_max_supply = fill(Inf, length(N_year))
        end
        x_max = min.(x_max, x_max_supply)
    end
    opt.upper_bounds = vcat(x_max, sum(h))
    # Initial vector has to obey the bounds
    v_init = vcat(x_init, s_beg_init)
    v_init = max.(opt.lower_bounds, min.(v_init, opt.upper_bounds))

    f_opt = nothing
    v_opt = nothing
    return_code = nothing
    try
        (f_opt, v_opt, return_code) = optimize(opt, v_init)
    catch e
        try
            v_init_new_new = opt.upper_bounds
            (f_opt, v_opt, return_code) = optimize(opt, v_init_new_new)
        catch
            v_init_new_new = opt.lower_bounds
            (f_opt, v_opt, return_code) = optimize(opt, v_init_new_new)
        end
    end

    # (f_opt, v_opt, return_code) = optimize(opt, v_init)
    if verbose
        println("OPTIMIZATION RESULTS (return code: $return_code)")
        println("v_opt: ", round.(v_opt, digits = 4))
        println("f(v_opt): ", round(f_opt, digits = 4))
        println("evaluations: ", opt.numevals)
    end

    # @assert return_code == :XTOL_REACHED "Producer optimization return code: $return_code"

    x_opt = v_opt[begin:N_year]
    s_beg_opt = v_opt[end]
    return (x_opt, s_beg_opt)
end
