using SparseArrays
import JuMP, COSMO


function determine_baseline_trade(
    sales::Dict{String,Vector{Float64}},
    demand::Dict{String,Vector{Float64}},
    annual_trade::Dict{Tuple{String,String},Float64};
    tol = 1e-6,
    verbose = false,
)
    N_pro = length(sales)
    N_con = length(demand)
    N_year = length(first(sales).second)
    N_trade = length(annual_trade)

    id_to_trade_pair = Vector{Tuple{String,String}}()
    id_to_producer = collect(keys(sales))
    id_to_consumer = collect(keys(demand))

    trade_ids_of_exports = Dict(producer => Int[] for producer in keys(sales))
    trade_ids_of_imports = Dict(consumer => Int[] for consumer in keys(demand))
    for (i, pair) in enumerate(keys(annual_trade))
        push!(id_to_trade_pair, pair)
        push!(trade_ids_of_exports[pair[1]], i)
        push!(trade_ids_of_imports[pair[2]], i)
    end

    # Define optimization problem
    opt = JuMP.Model(JuMP.optimizer_with_attributes(
        COSMO.Optimizer, 
        "verbose" => verbose, 
        "eps_abs" => tol, 
        "eps_rel" => tol,
        "rho" => 5e-6,
    ))
    JuMP.@variable(opt, x[1:N_trade*N_year])
    JuMP.@constraint(opt, x .>= 0);

    # Penalty function
    Q = begin
        q = spdiagm(
            0 => fill(2, N_year), 
            1 => fill(-1, N_year - 1), 
            -1 => fill(-1, N_year - 1),
            N_year - 1 => fill(-1, 1),
            -(N_year - 1) => fill(-1, 1)
        )
        blockdiag((q ./ annual_trade[id_to_trade_pair[i]]^2 for i = 1:N_trade)...)
    end
    JuMP.@objective(opt, Min, x' * Q * x)

    # Annual trade constraints
    A_trade = begin
        a = sparse(ones(1, N_year))
        blockdiag((a for i = 1:N_trade)...)
    end
    b_trade = [annual_trade[id_to_trade_pair[i]] for i = 1:N_trade]
    JuMP.@constraint(opt, A_trade * x .== b_trade)

    # Total sales constraints
    A_sales = begin
        A_rows = []
        for r = 1:N_pro
            i_vec = trade_ids_of_exports[id_to_producer[r]]
            a = sparsevec([(i - 1) * N_year + 1 for i in i_vec], 1., N_trade * N_year)
            for n=1:N_year
                push!(A_rows, circshift(a, n - 1)')
            end
        end
        vcat(A_rows...)
    end
    b_sales = vcat((sales[id_to_producer[r]] for r = 1:N_pro)...)
    JuMP.@constraint(opt, A_sales * x .== b_sales)

    # Total demand constraints
    A_demand = begin
        A_rows = []
        for s = 1:N_con
            i_vec = trade_ids_of_imports[id_to_consumer[s]]
            a = sparsevec([(i - 1) * N_year + 1 for i in i_vec], 1., N_trade * N_year)
            for n=1:N_year
                push!(A_rows, circshift(a, n - 1)')
            end
        end
        vcat(A_rows...)
    end
    b_demand = vcat((demand[id_to_consumer[s]] for s = 1:N_con)...)
    JuMP.@constraint(opt, A_demand * x .== b_demand)
    # Optimize 
    JuMP.optimize!(opt)
    status = JuMP.termination_status(opt)
    f_opt = JuMP.objective_value(opt)
    x_opt = JuMP.value.(x)

    if verbose
        println("OPTIMIZATION RESULTS (status: $status)")
        println("f(x_opt): ", round(f_opt, digits = 4))
    end

    @assert status == JuMP.MOI.OPTIMAL

    baseline_trade =
        Dict(id_to_trade_pair[i] => x_opt[(i-1)*N_year+1:i*N_year] for i = 1:N_trade)

    return baseline_trade
end
