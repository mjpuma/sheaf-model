# Cap and ι-threshold rows for a run, and a side-by-side file when a
# ξ > 0 run is compared with the ξ = 0 run. The callback does not
# mutate agents. The threshold test and the price cap are unchanged.

const _EVENT_IO = Ref{Any}(nothing)
const _EVENT_PATH = Ref{String}("")

const _CAP_EVENTS = ("cap_domestic", "cap_foreign")
const _PAIRED_EVENTS = ("cap_domestic", "cap_foreign", "zeroed_domestic", "zeroed_foreign")

function _event_commit()
    try
        return readchomp(`git rev-parse --short HEAD`)
    catch
        return "unknown"
    end
end

"""Open `outputroot/monitor/events_<tag>.csv` unless a driver already set `diag_log`."""
function start_event_monitor!(outputroot, tag, xi; crop::AbstractString = "")
    pm = AgrimateModel.AgentsModule.ProducerModule
    pm.diag_log[] === nothing || return nothing
    dir = joinpath(outputroot, "monitor")
    mkpath(dir)
    path = joinpath(dir, "events_$(tag).csv")
    io = open(path, "w")
    commit = _event_commit()
    xi_s = string(xi)
    println(io, "# commit $(commit)")
    println(io, "commit,run,xi,crop,region,step,event,value,threshold")
    flush(io)
    _EVENT_IO[] = io
    _EVENT_PATH[] = path
    pm.diag_log[] = function (kind, producer, t, value, threshold)
        c = get(pm.diag_crop, objectid(producer), String(crop))
        if isempty(c)
            c = pm.nlopt_log_crop[]
        end
        println(io, join((
            commit, tag, xi_s, c, producer.id, t, string(kind),
            string(value), string(threshold),
        ), ","))
        flush(io)
        return nothing
    end
    return path
end

function close_event_monitor!()
    io = _EVENT_IO[]
    io === nothing && return nothing
    close(io)
    _EVENT_IO[] = nothing
    return _EVENT_PATH[]
end

function _read_event_rows(path)
    rows = NamedTuple{(:crop, :region, :step, :event, :value),Tuple{String,String,Int,String,Float64}}[]
    isfile(path) || return rows
    for line in eachline(path)
        (isempty(line) || startswith(line, "#") || startswith(line, "commit,")) && continue
        p = split(line, ",")
        if length(p) >= 9
            crop, region, step, event, value = p[4], p[5], p[6], p[7], p[8]
        elseif length(p) >= 8
            crop, region, step, event, value = p[3], p[4], p[5], p[6], p[7]
        else
            continue
        end
        push!(rows, (crop = String(crop), region = String(region), step = parse(Int, step),
                     event = String(event), value = parse(Float64, value)))
    end
    return rows
end

"""
Write cap and threshold events from the ξ = 0 file and the ξ > 0 file on
one row. `spillover` is 1 when the ξ > 0 run has an event the ξ = 0 run
does not, and some other crop has a cap event at that region and step
in the ξ > 0 run.
"""
function write_cap_spillover(xi0_path, xi_path, out_path)
    z = _read_event_rows(xi0_path)
    x = _read_event_rows(xi_path)
    keep(rows) = [r for r in rows if r.event in _PAIRED_EVENTS]
    z = keep(z)
    x = keep(x)
    zkeys = Set((r.crop, r.region, r.step, r.event) for r in z)
    xkeys = Set((r.crop, r.region, r.step, r.event) for r in x)
    caps = Set((r.region, r.step, r.crop) for r in x if r.event in _CAP_EVENTS)
    mkpath(dirname(out_path))
    open(out_path, "w") do io
        println(io, "crop,region,step,event,in_xi0,in_xi,cap_other_crop,spillover")
        for key in sort!(collect(union(zkeys, xkeys)))
            crop, region, step, event = key
            in0 = key in zkeys
            inx = key in xkeys
            others = String[]
            for (reg, st, other) in caps
                reg == region && st == step && other != crop && push!(others, other)
            end
            cap_other = join(sort!(unique(others)), "|")
            spill = inx && !in0 && !isempty(cap_other) ? 1 : 0
            println(io, join((crop, region, step, event, Int(in0), Int(inx), cap_other, spill), ","))
        end
    end
    return out_path
end

function test_write_cap_spillover()
    root = mktempdir()
    z = joinpath(root, "xi0.csv")
    x = joinpath(root, "xi.csv")
    out = joinpath(root, "side.csv")
    header = "commit,run,xi,crop,region,step,event,value,threshold"
    open(z, "w") do io
        println(io, header)
        println(io, "c,xi0,0,wheat,USA,1,cap_domestic,1200,1000")
        println(io, "c,xi0,0,rice,USA,1,zeroed_domestic,0.1,0.2")
    end
    open(x, "w") do io
        println(io, header)
        println(io, "c,xi,0.3,wheat,USA,1,cap_domestic,1300,1000")
        println(io, "c,xi,0.3,rice,USA,1,zeroed_domestic,0.1,0.2")
        println(io, "c,xi,0.3,maize,USA,1,zeroed_foreign,0.05,0.2")
        println(io, "c,xi,0.3,rice,CHN,2,zeroed_domestic,0.01,0.2")
    end
    write_cap_spillover(z, x, out)
    lines = readlines(out)
    maize = [ln for ln in lines if startswith(ln, "maize,")]
    length(maize) == 1 || error("expected one maize row, got $(maize)")
    occursin(",1", maize[1]) || error("maize spillover not flagged: $(maize[1])")
    split(maize[1], ",")[end] == "1" || error("spillover flag: $(maize[1])")
    chn = [ln for ln in lines if occursin("CHN", ln)]
    split(chn[1], ",")[end] == "0" || error("cap-free new event must not be spillover: $(chn[1])")
    rice = [ln for ln in lines if startswith(ln, "rice,USA")]
    split(rice[1], ",")[end] == "0" || error("shared rice event must not be spillover: $(rice[1])")
    println("event monitor spillover test passed")
    return true
end
