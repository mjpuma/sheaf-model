"""
Gate 0 J9: write `data/agrimate_input_authorrestr/`, the J8 input set with
the author's per-region export-restriction series in place of ours.

    cd /Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty
    arch -x86_64 /Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia \\
        --project=. /Users/mjp38/GitHub/sheaf-model/inputs/from_paper_restrictions.jl

Every file of `data/agrimate_input_authorparams/` is byte-copied except
`export-restrictions_crop=wheat_source=2007-2011.csv`. That file gets one
country per restricted region: the area with the largest export fraction
(as computed by `aggregate_export_restrictions` on the J8 trade inputs), and
one row per constant run of the author's `export restriction` with
Value = v_author / fraction. From is the first day of the run's first step
and To the day before the last day of its last step, so consecutive rows are
never day-adjacent (day-adjacent rows make the paper's overlap resolver emit
an extra From > To period). Check the result with
`check_agrimate_restriction_mapping.jl`.
"""

using DrWatson
@quickactivate "Agrimate"
include(srcdir("simulation.jl"))

const AUTHOR_NC = "/Users/mjp38/GitHub/agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/" *
    "agrimate_baseline=2007-2009_export_restrictions=2007-2011_extra_regions=(Egypt=EGY)_production_anomalies=FAOsince-2005_regions=AgrimateEU28_start=2000-01-01.nc"
const SRC = datadir("agrimate_input_authorparams")
const DST = datadir("agrimate_input_authorrestr")
const ER_FILE = "export-restrictions_crop=wheat_source=2007-2011.csv"
const START = Date(2000, 1, 1)
const N_YEAR = 24

ds = NCDataset(AUTHOR_NC)
regions = String.(Array(ds["region"]))
@assert dimnames(ds["export restriction"]) == ("time", "region")
A = coalesce.(Array(ds["export restriction"]), 0.0)
@assert Array(ds["timestep"]) == 1:size(A, 1)
close(ds)

df_region = make_regions_dataframe(get_regions("AgrimateEU28"), Dict{String,Any}("Egypt" => "EGY"))
tf_non_agg = wload(joinpath(SRC, "trade-flows_baseline=2007-2009_crop=wheat.csv"))
fb = aggregate_areas(wload(joinpath(SRC, "food-balance_baseline=2007-2009_crop=wheat.csv")), df_region)
tf = infer_trade_flows(aggregate_areas(tf_non_agg, df_region), fb)

# the paper function fails on an empty frame (vcat of nothing), which is what a zero fraction leaves
fraction(area) = try
    d = DataFrame(Exporter = [area], From = [START], To = [START], Value = [1.0])
    aggregate_export_restrictions(d, df_region, tf_non_agg, tf).Value[1]
catch err
    err isa MethodError || rethrow()
    0.0
end

# first / last calendar day of each step under the paper's date_to_timestep (Feb 29 cannot be parsed)
first_day = Dict{Int,Date}(); last_day = Dict{Int,Date}()
for d in START:Day(1):Date(2013, 12, 31)
    (month(d) == 2 && day(d) == 29) && continue
    t = date_to_timestep(d; start = START, N_year = N_YEAR)
    haskey(first_day, t) || (first_day[t] = d)
    last_day[t] = d
end

rows = String[]
summary = []
for (j, reg) in enumerate(regions)
    v = A[:, j]
    any(>(0), v) || continue
    areas = df_region.Area[df_region.Region .== reg]
    fr = [(a, fraction(a)) for a in areas]
    sort!(fr; by = x -> -x[2])
    (area, f) = fr[1]
    if f == 0
        println("UNMATCHED: no area in $reg has a positive export fraction; author max $(maximum(v)), ",
                "$(count(>(0), v)) steps; areas: ", join(areas, " "))
        push!(summary, (reg, "-", 0.0, maximum(v), 0, count(>(0), v), length(areas)))
        continue
    end
    runs = Tuple{Int,Int,Float64}[]
    for t in eachindex(v)
        v[t] > 0 || continue
        if !isempty(runs) && runs[end][2] == t - 1 && runs[end][3] == v[t]
            runs[end] = (runs[end][1], t, v[t])
        else
            push!(runs, (t, t, v[t]))
        end
    end
    for (s, e, val) in runs
        from = first_day[s]
        to = last_day[e] - Day(1)
        (month(to) == 2 && day(to) == 29) && (to -= Day(1))
        @assert date_to_timestep(from; start = START, N_year = N_YEAR) == s
        @assert date_to_timestep(to; start = START, N_year = N_YEAR) == e
        x = val / f
        @assert round(x * f; digits = 4) == round(val; digits = 4)
        push!(rows, "$area,$from,$to,$(repr(x))")
    end
    push!(summary, (reg, area, f, maximum(v), length(runs), count(>(0), v), length(areas)))
end

mkpath(DST)
for f in readdir(SRC)
    f == ER_FILE && continue
    cp(joinpath(SRC, f), joinpath(DST, f); force = true)
end
open(joinpath(DST, ER_FILE), "w") do io
    println(io, "Exporter,From,To,Value")
    foreach(r -> println(io, r), rows)
end

println("region | area | export fraction | author max | runs | steps > 0 | areas in region")
for s in summary
    println(join(string.(s), " | "))
end
println("wrote ", length(rows), " rows to ", joinpath(DST, ER_FILE))
