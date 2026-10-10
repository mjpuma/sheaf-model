using Test
include("../src/coupling.jl")
using .CouplingModule

@testset "substitution_factor" begin
    empty_cur = Dict{Tuple{String,String},Float64}()
    empty_ref = Dict{Tuple{String,String,Int},Float64}()
    @test substitution_factor("rice", "USA", 1, 0.0, 1 / 3, empty_cur, empty_ref) == 1.0
    @test substitution_factor("maize", "CHN", 10, 0.6, 0.33, empty_cur, empty_ref) == 1.0

    current = Dict(("wheat", "USA") => 1.2)
    refs = Dict(("wheat", "USA", 1) => 1.0)
    M_rice = substitution_factor("rice", "USA", 1, 0.6, 1 / 3, current, refs)
    M_maize = substitution_factor("maize", "USA", 1, 0.6, 1 / 3, current, refs)
    @test M_rice > 1.0
    @test M_maize > 1.0
    # wheat–maize ρ is larger than wheat–rice
    @test M_maize > M_rice
end
