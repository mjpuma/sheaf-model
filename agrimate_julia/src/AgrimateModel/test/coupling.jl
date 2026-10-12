using Test
using DataFrames: DataFrame
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

@testset "reference_index io" begin
    @test endswith(reference_index_path("/tmp/out", "wheat"), "reference/crop_price_index_wheat.csv")
    @test assert_coupled_clocks(["2000-01-01", "2000-01-01"], [24, 24]) === nothing
    @test_throws ErrorException assert_coupled_clocks(["2000-01-01", "2001-01-01"], [24, 24])
    @test_throws ErrorException assert_coupled_clocks(["2000-01-01", "2000-01-01"], [24, 12])

    root = mktempdir()
    df = DataFrame(t = [1, 1, 2], consumer = ["USA", "CHN", "USA"], value = [1.0, 1.1, 1.05])
    path = reference_index_path(root, "wheat")
    save_reference_index(path, "wheat", df)
    @test isfile(path)
    ref = load_reference_index(root, ("wheat",))
    @test ref[("wheat", "USA", 1)] == 1.0
    @test ref[("wheat", "CHN", 1)] == 1.1
    @test assert_reference_coverage(ref, ("wheat",), 2) === nothing
    @test_throws ErrorException assert_reference_coverage(ref, ("wheat",), 3)
    @test_throws ErrorException load_reference_index(root, ("wheat", "rice"))
end
