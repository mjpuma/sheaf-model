using Parameters

function generate_expected_harvests(model, harvests, baseline_harvests; t_max)

    @unpack N_year, N_hor = model.global_params

    weight_factor(n; N_for, τ_for) = 1.0 / (1 + exp((n - N_for) / (0.17 * τ_for)))

    expected_harvests = Dict{String,Matrix{Float64}}()
    for (id, producer) in model.producers
        @unpack N_for, τ_for = producer.local_params
        expected_harvests[id] = Matrix{Float64}(undef, t_max, N_hor)
        for t = 1:t_max
            for n = 1:N_hor
                h_star = baseline_harvests[id][mod(t + n, 1:N_year)]
                h = (
                    t + n ≤ length(harvests[id]) ? harvests[id][t+n] :
                        baseline_harvests[id][mod(t + n, 1:N_year)]
                )
                w = weight_factor(n; N_for, τ_for)
                expected_harvests[id][t, n] = (1 - w) * h_star + w * h
            end
        end
    end

    return expected_harvests
end