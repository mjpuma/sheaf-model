module RunModule

export Run, run_model!, initialize_model_run

using DataFrames: DataFrame, allowmissing!
using ..ModelModule
using ProgressMeter


mutable struct Run
    model::Model
    # Current timestep
    timestep::Int
    # Input data
    input_data::InputData
    # Maximum timestep
    t_max::Int
    # Output data
    output_data::DataFrame
    # Constructor
    function Run(model, input_data)
        run = new()
        run.model = model
        run.timestep = 1
        run.input_data = input_data
        run.output_data = DataFrame(
            t = Int[],
            n = Int[],
            producer = String[],
            consumer = String[],
            variable = String[],
            value = Float64[],
        )
        allowmissing!(run.output_data)
        return run
    end
end

include("run/observation.jl")
include("run/expected_harvests.jl")

using .ObservationModule


function observe!(run)
    for observe_function! in [
        observe_producers!,
        observe_consumers!,
        # observe_extra_data!
    ]
        observe_function!(run.output_data, run.model, run.timestep)
    end
end

function run_model!(run, timesteps; verbose::Bool = true, progressbar_name = "RUN")
    # for i in 1:timesteps
    progressshower = Progress(timesteps; desc=progressbar_name, barglyphs=BarGlyphs("[=> ]"), color=:white, showspeed=true)
    for i in 1:timesteps
    # @showprogress 1 "RUN" for i in 1:timesteps
        step!(run.model, run.timestep, run.input_data; verbose)
        observe!(run)
        run.timestep += 1
        next!(progressshower)
    end
end

function initialize_model_run(model, input_data, initialization_data)
    
    if isempty(input_data.expected_harvests)
        harvests = input_data.harvests
        baseline_harvests = initialization_data.baseline_harvests
        t_max = length(first(harvests).second) - model.global_params[:N_hor]
        expected_harvests = generate_expected_harvests(model, harvests, baseline_harvests; t_max)
        input_data = InputData(harvests, expected_harvests, input_data.export_restriction_intervals, input_data.export_restriction_dict)
    end

    run = Run(model, input_data)
    return run
end

end
