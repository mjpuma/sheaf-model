module CouplingModule

export substitution_factor, RHO_SUBST, COUPLED_CROPS

# Frozen substitutability (August Gate 1 plan / GATE1_DESIGN.md).
# Not Agrimate's interest-rate ρ.
const COUPLED_CROPS = ("wheat", "rice", "maize")
const RHO_SUBST = Dict(
    ("wheat", "rice") => 0.30,
    ("wheat", "maize") => 0.40,
    ("rice", "wheat") => 0.30,
    ("rice", "maize") => 0.20,
    ("maize", "wheat") => 0.40,
    ("maize", "rice") => 0.20,
)

"""M^g_s(t) = Π_{h≠g} (P^h_s(t) / P̄^h_s(t))^{ξ ρ_gh ε_d^g}.

`current_index` keys are `(crop, region)`. `reference_index` keys are
`(crop, region, t)`. A crop with no purchaser in `region` contributes 1.
At ξ = 0 the product is identically 1.
"""
function substitution_factor(
    crop::AbstractString,
    region::AbstractString,
    t::Integer,
    ξ::Float64,
    ε_d::Float64,
    current_index,
    reference_index,
)
    ξ == 0 && return 1.0
    M = 1.0
    g = String(crop)
    s = String(region)
    for h in COUPLED_CROPS
        h == g && continue
        P = get(current_index, (h, s), nothing)
        Pbar = get(reference_index, (h, s, Int(t)), nothing)
        (P === nothing || Pbar === nothing) && continue
        (!isfinite(P) || !isfinite(Pbar) || Pbar <= 0) && continue
        η = ξ * get(RHO_SUBST, (g, h), 0.0) * ε_d
        M *= (P / Pbar)^η
    end
    return M
end

end
