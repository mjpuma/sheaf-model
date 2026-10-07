module TestAgrimateModel

using Test
using CSV, DataFrames

include("../src/AgrimateModel.jl")

using .AgrimateModel

baseline_harvests =
   Dict("RUS" => vcat(2.0 .* ones(6), zeros(6)), "ARG" => vcat(zeros(6), 2.0 .* ones(6)))
baseline_consumption = Dict(region => 1.0 for region in ["EGY", "IDN"])
baseline_transactions = Dict(
   ("RUS", "EGY") => 0.5,
   ("RUS", "IDN") => 0.5,
   ("ARG", "EGY") => 0.5,
   ("ARG", "IDN") => 0.5,
)

T = 12
harvests = Dict(
   "RUS" => vcat(2.0 .* ones(6), zeros(6), 2.0 .* ones(6), zeros(6)),
   "ARG" => vcat(zeros(6), 2.0 .* ones(6), zeros(6), 2.0 .* ones(6)),
)
expected_harvests = Dict(
   "RUS" => permutedims(hcat([circshift(harvests["RUS"][1:12], -t) for t=1:T]...)),
   "ARG" => permutedims(hcat([circshift(harvests["ARG"][1:12], -t) for t=1:T]...)),
)

init_data = InitializationData(
   baseline_harvests,
   baseline_consumption,
   baseline_transactions,
)

input_data = InputData(
   harvests,
   expected_harvests,
)

agrimate_params = AgrimateParams(
   N_year = 12,
   N_hor = 12,
   τ_exp = 0.2,
   α = 2.0,
   β = 0.1,
   σ = 2.,
   λ = 1.0,
   p_sto = 0.2,
   τ = 0.25,
   τ_P = 0.5,
   ψ = 0.3,
   ε_c = 0.2,
   market_constraint = true,
   unique_market_constraint = true,
   N_for = 3,
   N_del = 1,
)

(model, output_baseline_data) = initialize_model(init_data, agrimate_params)
run = initialize_model_run(model, input_data, init_data)

run_model!(run, T)

output_data = run.output_data

output_data = vcat(output_baseline_data, output_data)
output_data[:, :value] = round.(output_data[:, :value], digits = 5)

producers = keys(model.producers)
consumers = keys(model.consumers)

for t in 1:T
   for producer in producers
      df = output_data[isequal.(output_data.t, t) .& isequal.(output_data.producer, producer), :]
      total_sales = df[df.variable .== "sales", :value][1, 1]
      total_transaction = sum(df[df.variable .== "transaction quantity", :value])
      #println("Testing sales & transactions: $producer at t=$t")
      @test isapprox(total_sales, total_transaction, atol=2e-5)
   end
   for consumer in consumers
      df = output_data[isequal.(output_data.t, t) .& isequal.(output_data.consumer, consumer), :]
      total_demand = df[df.variable .== "demand", :value][1, 1]
      total_requests = sum(df[df.variable .== "demanded quantity", :value])
      #println("Testing demand & demand requests: $consumer at t=$t")
      @test isapprox(total_demand, total_requests, atol=2e-5)
   end
end

for t in 2:T
   for producer in producers
      df = output_data[isequal.(output_data.producer, producer), :]
      beg_storage = df[(df.t .== t - 1) .& (df.variable .== "producer storage"), :value][1, 1]
      beg_storage *= (1 - model.producers[producer].local_params[:δ])
      df = df[isequal.(df.t, t), :]
      harvest = df[df.variable .== "harvest", :value][1, 1]
      sales = df[df.variable .== "sales", :value][1, 1]
      end_storage = df[df.variable .== "producer storage", :value][1, 1]
      # println("Testing balance: $producer at t=$t")
      @test isapprox(beg_storage + harvest, sales + end_storage, atol=2e-5)
   end
   for consumer in consumers
      df = output_data[isequal.(output_data.consumer, consumer), :]
      beg_storage = df[isequal.(df.t, t - 1) .& (df.variable .== "consumer storage"), :value][1, 1]
      beg_storage *= (1 - model.consumers[consumer].local_params[:δ])
      df = df[isequal.(df.t, t), :]
      delivery = df[df.variable .== "delivery", :value][1, 1]
      consumption = df[df.variable .== "consumption", :value][1, 1]
      end_storage = df[df.variable .== "consumer storage", :value][1, 1]
      #println("Testing balance: $consumer at t=$t")
      @test isapprox(beg_storage + delivery, consumption + end_storage, atol=2e-5)
   end
end

N_del = model.global_params[:N_del]
for t in 1+N_del:T
   for consumer in consumers
      df = output_data[isequal.(output_data.consumer, consumer), :]
      delivery = df[isequal.(df.t, t) .& (df.variable .== "delivery"), :value][1, 1]
      total_transactions = sum(df[isequal.(df.t, t - N_del) .&
                                  (df.variable .== "transaction quantity"), :value])
      #println("Testing deliveries: $consumer at t=$t")
      @test isapprox(delivery, total_transactions, atol=2e-5)
   end
end


filename = (endswith(pwd(), "/test") ? "test_agrimate_output.csv" :
                                       "test/test_agrimate_output.csv")

# CSV.write(filename, output_data)
reference_data = DataFrame(CSV.File(filename))

@test isequal(output_data, reference_data)

end
