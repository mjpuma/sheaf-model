
function equilibrate_producers!(model; κ = 0.25, tol = 1e-9, max_iter = 500, verbose::Bool = true)
    """
    Find Nash equilibrium for an oligopoly of producers
    P(x_all) = (1 - α * (x_all - 1)^λ)^(1 / λ)
    """
    @unpack N_year = model.global_params

    prev_X_mat = Matrix{Float64}(undef, length(model.producers), N_year)
    X_mat = Matrix{Float64}(undef, length(model.producers), N_year)
    prev_S_beg_vec = Vector{Float64}(undef, length(model.producers))
    S_beg_vec = Vector{Float64}(undef, length(model.producers))

    κ_eff_vec = Vector{Float64}()
    let i = 1
        while length(κ_eff_vec) < max_iter
            κ_eff_vec = vcat(κ_eff_vec, fill(κ / sqrt(i), i))
            i += 1
        end
    end
    κ_eff_vec = κ_eff_vec[1:max_iter]

    for n_iter = 1:max_iter
        for (i, producer) in enumerate(values(model.producers))
            prev_X_mat[i, :] = producer.optimal_sales
            prev_S_beg_vec[i] = producer.storage
        end
        all_sales = sum(prev_X_mat, dims = 1)'
        for producer in values(model.producers)
            producer.expected_others_sales[:] = all_sales - producer.optimal_sales
        end
        # @sync Threads.@threads
        
        for producer in collect(values(model.producers))
            @unpack α, β, λ, δ, ρ, p_sto, storage_hold_back = producer.local_params
            @unpack X_avg = producer.local_params
            @unpack X_star = producer.global_params
            @unpack market_constraint, unique_market_constraint = producer.local_params
            # println(producer.id)
            (x_opt, s_beg_opt) = optimize_periodic_sales(;
                h = producer.expected_harvests ./ X_avg,
                x_oth = producer.expected_others_sales ./ X_avg,
                x_init = producer.optimal_sales ./ X_avg,
                s_beg_init = producer.storage / X_avg,
                α,
                λ,
                δ,
                ρ,
                p_sto,
                N_year,
                x_star = X_star / X_avg,
                x_market = (market_constraint ? producer.market_size / X_avg : nothing),
                x_market_unique = (unique_market_constraint ? producer.market_size_unique / X_avg : nothing),
                tol = 0.001 * tol / X_avg,
                verbose = false,
                storage_hold_back,
            )
            producer.optimal_sales[:] = x_opt .* X_avg
            producer.storage = s_beg_opt * X_avg
            # println(producer.id,X_avg,producer.optimal_sales[:])
            # println(producer.id,X_avg,producer.storage)
        end
        for (i, producer) in enumerate(values(model.producers))
            X_mat[i, :] = producer.optimal_sales
            S_beg_vec[i] = producer.storage
        end
        # exit()
        # println("------")
        # println(prev_S_beg_vec)
        # println(prev_X_mat)
        # println(S_beg_vec)
        # println(X_mat)
        max_S_diff = maximum(abs.(prev_S_beg_vec - S_beg_vec))
        max_X_diff = maximum(abs.(prev_X_mat - X_mat))
        verbose && println("Iteration $n_iter")
        @unpack X_star = first(values(model.producers)).global_params
        verbose && println(" Max S_beg difference / X_star: ", max_S_diff / X_star)
        verbose && println(" Max X difference / X_star: ", max_X_diff / X_star)
        verbose && println(" Tolerance / X_star: ", tol / X_star)

        if max_S_diff ≤ tol && max_X_diff ≤ tol
            verbose && println("Nash equilibrium found in iteration $n_iter.")
            return true
        else
            κ_eff = κ_eff_vec[n_iter]
            verbose && println("κ_eff: ", κ_eff)
            for (producer, prev_X, prev_S_beg) in
                zip(values(model.producers), eachrow(prev_X_mat), prev_S_beg_vec)
                producer.optimal_sales[:] = κ_eff .* producer.optimal_sales + (1 - κ_eff) .* prev_X
                producer.storage = κ_eff * producer.storage + (1 - κ_eff) * prev_S_beg
            end
        end
    end
    verbose && println("No convergence after $max_iter iterations.")
    return false
end