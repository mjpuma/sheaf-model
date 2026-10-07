using Statistics: mean


function get_p_sto(S; D_star, p_star, N_del)
    N_y = length(S)
    α = circshift(S, 1) ./ (circshift(S, 1) + circshift(D_star, N_del))
    β = 1 .- α
    p_sto = Vector{Float64}(undef, N_y)
    # Calculate end-of-year p_sto
    p_sto[end] = 0
    prod_α = 1
    for m=N_y:-1:1
        p_sto[end] += prod_α * β[m] * p_star[mod(m-N_del, 1:N_y)]
        prod_α *= α[m]
    end
    p_sto[end] /= (1 - prod_α)
    # Calculate remaining p_sto iteratively
    for n=1:N_y-1
        p_sto[n] = α[n] * p_sto[mod(n-1, 1:N_y)] + β[n] * p_star[mod(n-N_del, 1:N_y)]
    end
    return p_sto
end


function get_C(p_sto; C_star, ε, A)
    c = p_sto.^(-ε) ./ (1 .+ A .* (p_sto.^(1-ε) .- 1))
    return c ./ mean(c) .* C_star
end


function get_S(C; D_star, S_star, N_del)
    N_y = length(C)
    S = Vector{Float64}(undef, N_y)
    # Calculate end-of-year S
    S[end] = sum(((m - 1) / N_y - 1) * (D_star[mod(m - N_del, 1:N_y)] - C[m]) for m = 1:N_y) + S_star
    # Calculate remaining S iteratively
    for n = 1:N_y-1
        S[n] = S[mod(n-1, 1:N_y)] + D_star[mod(n - N_del, 1:N_y)] - C[n]
    end
    return S
end


function solve_consumer_baseline(
    D_star::Vector, 
    p_star::Vector, 
    C_star; 
    N_year = 12, 
    N_del = round(Int, N_year / 12), 
    ψ = 0.3 * N_year, 
    ε = 0.1, 
    A = 0.5, 
    κ = 0.5, 
    tol = 1e-6, 
    max_iter = 100, 
    verbose = false,
)
    S_star = ψ * C_star
    S = fill(S_star, N_year)
    C = fill(C_star, N_year)
    p_sto = fill(1.0, N_year)
    p_sto_prev = Vector{Float64}(undef, N_year)
    verbose && println("Solving consumer baseline...")
    for n_iter = 1:max_iter
        p_sto_prev[:] = p_sto
        C[:] = get_C(p_sto; C_star, ε, A)
        S[:] = get_S(C; D_star, S_star, N_del)
        p_sto[:] = get_p_sto(S; D_star, p_star, N_del)
        if maximum(abs.(p_sto - p_sto_prev)) < tol
            verbose && println("Solution found in iteration $n_iter.")
            return (;C, S, p_sto)
        else
            p_sto[:] = κ .* p_sto .+ (1 - κ) .* p_sto_prev 
        end        
    end
    verbose && println("Solution did not converge.")
    return (;C, S, p_sto)
end
