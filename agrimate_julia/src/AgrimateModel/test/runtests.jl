using Test

@time @testset "AgentsModule" begin
    include("agents/producer.jl")
    include("agents/producer_optimization.jl")
    include("agents/consumer.jl")
    include("agents.jl")
end

@time @testset "ModelModule" begin
    include("model.jl")
end

@time @testset "RunModule" begin
    include("run.jl")
end

@time @testset "AgrimateModel" begin
    include("AgrimateModel.jl")
end
