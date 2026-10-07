using CodecZlib
using CSV: CSV
using DataFrames: DataFrame
using FileIO: FileIO
using JSON: JSON
using NCDatasets
# using IterTools


macro source()
    return QuoteNode(__source__)
end

function meaningful_data(x)
    y = filter(!isnothing,x)
    y = filter(!ismissing,y)
    return y
end


function get_wanted_pairs(x...)
    if length(x) == 1
        return x
    elseif length(x) == 2
        return unique([(i, j) for i in x[1], j in x[2]])
    elseif length(x) == 3
        return unique([(i, j, k) for i in x[1], j in x[2], k in x[3]])
    elseif length(x) == 4
        return unique([(i, j, k, l) for i in x[1], j in x[2], k in x[3], l in x[4]])
    end
end

function netcdf_save(file, df::DataFrame, meta = nothing)
    if !isdir(dirname(file))
        mkdir(dirname(file))
    end

    nc = NCDataset(file,"c")
    if !isnothing(meta)
        dict_flat = merge(meta[:params],Dict(:gitcommit => meta[:gitcommit]),Dict(:script => meta[:script]),Dict(:simulation_begin => meta[:simulation_begin]),Dict(:simulation_end => meta[:simulation_end]))
        dict_flat = Dict( (k => string(v) for (k, v) in dict_flat) )
        for key in keys(dict_flat)
            nc.attrib[key] = dict_flat[key]
        end
    end
    
    variables = meaningful_data(unique(df[!,:variable]))
    regions = meaningful_data(unique(df[!,:consumer]))
    timesteps = meaningful_data(unique(df[!,:t]))
    inner_annual_timesteps = meaningful_data(unique(df[!,:n]))
    dates = meaningful_data(unique(df[!,:datetime]))[1:lastindex(timesteps)]


    # create all dimensions needed and corresponding variables
    # create time dimensions and variable
    start_time = Date(dict_flat[:start])  # to be exchanged by real start_time 
    defDim(nc,"time",size(dates)[1])
    defVar(nc,"time",dates,("time",),attrib = Dict("calendar" => "gregorian","standard_name" => "time","units" => "days since $start_time 00:00:00",))
    nc["time"][:] = dates[:]

    # create inner-annual timestep dimensions and variable
    basis_step_name = "inner_annual_timestep" 
    defDim(nc,basis_step_name,size(inner_annual_timesteps)[1])
    defVar(nc,basis_step_name,Int64,(basis_step_name,))
    nc[basis_step_name][:] = inner_annual_timesteps[:]

    # create region dimensions and variable
    defDim(nc,"region",size(regions)[1])
    defVar(nc,"region",String,("region",),
        attrib = Dict("units" => "unitless"))
    nc["region"][:] = regions[:]

    # create all other variables
    defVar(nc,"timestep",Int64,("time",),
        attrib = OrderedDict("units" => "unitless"))
    nc["timestep"][:] = timesteps[:]

    dimension_dict = Dict("baseline transaction quantity" => (basis_step_name,"region","region",), 
                            "export tax factor" => ("time","region",), 
                            "restricted export" => ("time","region",), 
                            "export restriction" => ("time","region",), 
                            "consumer price" => ("time","region",), 
                            "baseline consumer storage" => (basis_step_name,"region",), 
                            "transaction price" => ("time","region","region",), 
                            "baseline price" => (basis_step_name,), 
                            "transaction quantity" => ("time","region","region",), 
                            "producer storage" => ("time","region",), 
                            "demanded quantity" => ("time","region","region",), 
                            "baseline producer storage" => (basis_step_name,"region",), 
                            "harvest" => ("time","region",), 
                            "expected profit" => ("time","region",), 
                            "expected price" => ("time","region",), 
                            "expected price domestic" => ("time","region",), 
                            "expected price foreign" => ("time","region",), 
                            "extra demand" => ("time","region",), 
                            "A_d_star" => ("region",), 
                            "baseline share foreign sales" => ("region",), 
                            "reservation price" => ("time","region","region",), 
                            "demand" => ("time","region",), 
                            "delivery" => ("time","region",), 
                            "baseline sales" => (basis_step_name,"region",), 
                            "ψ" => ("region",), 
                            "α domestic" => ("region",), 
                            "baseline consumer price" => (basis_step_name,"region",), 
                            "price adjustment factor" => ("time","region",), 
                            "price adjustment factor domestic" => ("time","region",), 
                            "price adjustment factor foreign" => ("time","region",), 
                            "baseline harvest" => (basis_step_name,"region",), 
                            "expected sales" => ("time","region",), 
                            "expected sales domestic" => ("time","region",), 
                            "expected sales foreign" => ("time","region",), 
                            "consumer storage" => ("time","region",), 
                            "A_c_star" => ("region",), 
                            "baseline demand" => (basis_step_name,"region",), 
                            "sales" => ("time","region",), 
                            "sales domestic" => ("time","region",), 
                            "sales foreign" => ("time","region",), 
                            "consumption" => ("time","region",), 
                            "baseline consumption" => (basis_step_name,"region",))



    production_variable_list = ["baseline harvest","baseline sales","baseline producer storage","producer storage","expected profit","expected price","expected price domestic","expected price foreign","expected sales","expected sales domestic","expected sales foreign","harvest","restricted export","export tax factor","export restriction","sales","sales domestic","sales foreign","price adjustment factor","price adjustment factor domestic","price adjustment factor foreign","baseline share foreign sales", "α domestic"]
    consumption_variable_list = ["baseline demand","baseline consumption","baseline consumer storage","baseline consumer price","delivery","consumer price","consumption","consumer storage","extra demand","demand"]

    unitless_string = "unitless"
    price_string = "index per tonne"
    ton_string = "1000 tonne"
    unit_dict = Dict("baseline transaction quantity" => ton_string, 
                            "restricted export" => ton_string, 
                            "export tax factor" => unitless_string, 
                            "export restriction" => unitless_string, 
                            "consumer price" => price_string, 
                            "baseline consumer storage" => ton_string, 
                            "transaction price" => price_string, 
                            "baseline price" => price_string, 
                            "transaction quantity" => ton_string, 
                            "producer storage" => ton_string, 
                            "demanded quantity" => ton_string, 
                            "baseline producer storage" => ton_string, 
                            "harvest" => ton_string, 
                            "expected profit" => unitless_string, 
                            "expected price" => price_string, 
                            "expected price domestic" => price_string, 
                            "expected price foreign" => price_string, 
                            "extra demand" => ton_string, 
                            "A_d_star" => unitless_string, 
                            "reservation price" => price_string, 
                            "demand" => ton_string, 
                            "delivery" => ton_string, 
                            "baseline sales" => ton_string, 
                            "ψ" => unitless_string, 
                            "α domestic" => unitless_string, 
                            "baseline consumer price" => price_string, 
                            "price adjustment factor" => unitless_string, 
                            "price adjustment factor domestic" => unitless_string, 
                            "price adjustment factor foreign" => unitless_string, 
                            "baseline harvest" => ton_string, 
                            "expected sales" => ton_string, 
                            "expected sales domestic" => ton_string, 
                            "expected sales foreign" => ton_string, 
                            "consumer storage" => ton_string, 
                            "A_c_star" => unitless_string, 
                            "baseline share foreign sales" => unitless_string, 
                            "baseline demand" => ton_string, 
                            "sales" => ton_string, 
                            "sales domestic" => ton_string, 
                            "sales foreign" => ton_string, 
                            "consumption" => ton_string, 
                            "baseline consumption" => ton_string)
    region_dict = Dict( (k => i for (i, k) in enumerate(regions)) )

    for var in variables

        defVar(nc,var,Float64,dimension_dict[var],fillvalue = NaN, attrib = OrderedDict("units" => unit_dict[var]), deflatelevel =  9)
        # defVar(nc,var,Float64,dimension_dict[var],fillvalue = NaN, attrib = OrderedDict("units" => unit_dict[var]))
        if dimension_dict[var] == ("time","region","region",)
            # get sub-DataFrame only with the corresponding variable
            sub_df = select(filter(row  -> row[:variable] == var,df),[:t,:producer,:consumer,:value])
            # check if any pair of coordinates does not exist and make it to a NaN entry in the sub-DataFrame
            pairs = unique([(x,y,z) for (x,y,z) in zip(sub_df.t,sub_df.producer,sub_df.consumer)])
            left_overs_pairs = setdiff(get_wanted_pairs(timesteps,regions,regions), pairs)
            if size(left_overs_pairs)[1] != 0
                add_frame = DataFrame(t = [i[1] for i in left_overs_pairs], producer = [i[2] for i in left_overs_pairs],consumer = [i[3] for i in left_overs_pairs], value = [NaN for i in size(left_overs_pairs)[1]])
                sub_df = vcat(sub_df,add_frame)
            end
            # create new frame with indices of region in order to sort the DataFrame
            additional_frame_producer = map(a -> region_dict[a], sub_df.producer)
            additional_frame_consumer = map(a -> region_dict[a], sub_df.consumer)
            # add the index column to the Dataframe for each region string
            sub_df[!,:producer_index] = additional_frame_producer
            sub_df[!,:consumer_index] = additional_frame_consumer

            # Sort the dataframe
            sort!(sub_df,[:t,:producer_index,:consumer_index])
            df_reshape = reshape(sub_df[:,:value], size(regions)[1],size(regions)[1],size(timesteps)[1])
            df_reshape = permutedims(df_reshape,[3,1,2])
            # save in nc output
            # nc[var][:,:] = df_reshape
            nc[var][:,:,:] = df_reshape
            
        elseif dimension_dict[var] == (basis_step_name,"region","region",)
            # get sub-DataFrame only with the corresponding variable
            sub_df = select(filter(row  -> row[:variable] == var,df),[:n,:producer,:consumer,:value])
            # check if any pair of coordinates does not exist and make it to a NaN entry in the sub-DataFrame
            pairs = unique([(x,y,z) for (x,y,z) in zip(sub_df.n,sub_df.producer,sub_df.consumer)])
            left_overs_pairs = setdiff(get_wanted_pairs(inner_annual_timesteps,regions,regions), pairs)
            if size(left_overs_pairs)[1] != 0
                add_frame = DataFrame(n = [i[1] for i in left_overs_pairs], producer = [i[2] for i in left_overs_pairs],consumer = [i[3] for i in left_overs_pairs], value = [NaN for i in size(left_overs_pairs)[1]])
                sub_df = vcat(sub_df,add_frame)
            end
            # create new frame with indices of region in order to sort the DataFrame
            additional_frame_producer = map(a -> region_dict[a], sub_df.producer)
            additional_frame_consumer = map(a -> region_dict[a], sub_df.consumer)
            # add the index column to the Dataframe for each region string
            sub_df[!,:producer_index] = additional_frame_producer
            sub_df[!,:consumer_index] = additional_frame_consumer

            # Sort the dataframe
            sort!(sub_df,[:n,:producer_index,:consumer_index])
            df_reshape = reshape(sub_df[:,:value], size(regions)[1],size(regions)[1],size(inner_annual_timesteps)[1])
            df_reshape = permutedims(df_reshape,[3,1,2])
            # save in nc output
            # nc[var][:,:] = df_reshape
            nc[var][:,:,:] = df_reshape
            
        elseif dimension_dict[var] == ("time","region") && String(var) in consumption_variable_list
            # get sub-DataFrame only with the corresponding variable
            sub_df = select(filter(row  -> row[:variable] == var,df),[:t,:consumer,:value])

            # check if any pair of coordinates does not exist and make it to a NaN entry in the sub-DataFrame
            pairs = unique([(x,y) for (x,y) in zip(sub_df.t,sub_df.consumer)])
            left_overs_pairs = setdiff(get_wanted_pairs(timesteps,regions), pairs)
            if size(left_overs_pairs)[1] != 0
                add_frame = DataFrame(t = [i[1] for i in left_overs_pairs], consumer = [i[2] for i in left_overs_pairs], value = [NaN for i in size(left_overs_pairs)[1]])
                sub_df = vcat(sub_df,add_frame)
            end
            # create new frame with indices of region in order to sort the DataFrame
            additional_frame_consumer = map(a -> region_dict[a], sub_df.consumer)
            # add the index column to the Dataframe for each region string
            sub_df[!,:consumer_index] = additional_frame_consumer

            # Sort the dataframe
            sort!(sub_df,[:t,:consumer_index])
            df_reshape = reshape(sub_df[:,:value], size(regions)[1],size(timesteps)[1])
            df_reshape = transpose(df_reshape)
            # save in nc output
            nc[var][:,:] = df_reshape
        elseif dimension_dict[var] == ("time","region") && String(var) in production_variable_list
            # get sub-DataFrame only with the corresponding variable
            sub_df = select(filter(row  -> row[:variable] == var,df),[:t,:producer,:value])

            # check if any pair of coordinates does not exist and make it to a NaN entry in the sub-DataFrame
            pairs = unique([(x,y) for (x,y) in zip(sub_df.t,sub_df.producer)])
            left_overs_pairs = setdiff(get_wanted_pairs(timesteps,regions), pairs)
            if size(left_overs_pairs)[1] != 0
                add_frame = DataFrame(t = [i[1] for i in left_overs_pairs], producer = [i[2] for i in left_overs_pairs], value = [NaN for i in size(left_overs_pairs)[1]])
                sub_df = vcat(sub_df,add_frame)
            end
            # create new frame with indices of region in order to sort the DataFrame
            additional_frame_producer = map(a -> region_dict[a], sub_df.producer)
            # add the index column to the Dataframe for each region string
            sub_df[!,:producer_index] = additional_frame_producer

            # Sort the dataframe
            sort!(sub_df,[:t,:producer_index])
            df_reshape = reshape(sub_df[:,:value], size(regions)[1],size(timesteps)[1])
            df_reshape = transpose(df_reshape)
            # save in nc output
            nc[var][:,:] = df_reshape
        elseif dimension_dict[var] == (basis_step_name,"region") && String(var) in consumption_variable_list
            # get sub-DataFrame only with the corresponding variable
            sub_df = select(filter(row  -> row[:variable] == var,df),[:n,:consumer,:value])

            # check if any pair of coordinates does not exist and make it to a NaN entry in the sub-DataFrame
            pairs = unique([(x,y) for (x,y) in zip(sub_df.n,sub_df.consumer)])
            left_overs_pairs = setdiff(get_wanted_pairs(inner_annual_timesteps,regions), pairs)
            if size(left_overs_pairs)[1] != 0
                add_frame = DataFrame(n = [i[1] for i in left_overs_pairs], consumer = [i[2] for i in left_overs_pairs], value = [NaN for i in size(left_overs_pairs)[1]])
                sub_df = vcat(sub_df,add_frame)
            end
            # create new frame with indices of region in order to sort the DataFrame
            additional_frame_consumer = map(a -> region_dict[a], sub_df.consumer)
            # add the index column to the Dataframe for each region string
            sub_df[!,:consumer_index] = additional_frame_consumer

            # Sort the dataframe
            sort!(sub_df,[:n,:consumer_index])
            df_reshape = reshape(sub_df[:,:value], size(regions)[1],size(inner_annual_timesteps)[1])
            df_reshape = transpose(df_reshape)
            # save in nc output
            nc[var][:,:] = df_reshape
        elseif dimension_dict[var] == (basis_step_name,"region") && String(var) in production_variable_list
            # get sub-DataFrame only with the corresponding variable
            sub_df = select(filter(row  -> row[:variable] == var,df),[:n,:producer,:value])

            # check if any pair of coordinates does not exist and make it to a NaN entry in the sub-DataFrame
            pairs = unique([(x,y) for (x,y) in zip(sub_df.n,sub_df.producer)])
            left_overs_pairs = setdiff(get_wanted_pairs(inner_annual_timesteps,regions), pairs)

            if size(left_overs_pairs)[1] != 0
                add_frame = DataFrame(n = [i[1] for i in left_overs_pairs], producer = [i[2] for i in left_overs_pairs], value = [NaN for i in size(left_overs_pairs)[1]])
                sub_df = vcat(sub_df,add_frame)
            end
            # create new frame with indices of region in order to sort the DataFrame
            additional_frame_producer = map(a -> region_dict[a], sub_df.producer)
            # add the index column to the Dataframe for each region string
            sub_df[!,:producer_index] = additional_frame_producer

            # Sort the dataframe
            sort!(sub_df,[:n,:producer_index])
            df_reshape = reshape(sub_df[:,:value], size(regions)[1],size(inner_annual_timesteps)[1])
            df_reshape = transpose(df_reshape)
            # save in nc output
            nc[var][:,:] = df_reshape
        elseif dimension_dict[var] == (basis_step_name,)
            sub_df = select(filter(row  -> row[:variable] == var,df),[:n,:value])
            pairs = unique(sub_df.n)
            left_overs_pairs = setdiff(inner_annual_timesteps, pairs)
            if size(left_overs_pairs)[1] != 0
                add_frame = DataFrame(n = [i for i in left_overs_pairs], value = [NaN for i in size(left_overs_pairs)[1]])
                sub_df = vcat(sub_df,add_frame)
            end 
            # sort according to baseline time step
            sort!(sub_df,[:n])
            # save in nc output
            nc[var][:] = sub_df[:,:value]

        elseif dimension_dict[var] == ("region",) && !(String(var) in production_variable_list)
            sub_df = select(filter(row  -> row[:variable] == var,df),[:consumer,:value])
            pairs = unique(sub_df.consumer)
            left_overs_pairs = setdiff(regions, pairs)
            if size(left_overs_pairs)[1] != 0
                add_frame = DataFrame( consumer = [i for i in left_overs_pairs], value = [NaN for i in size(left_overs_pairs)[1]])
                sub_df = vcat(sub_df,add_frame)
            end 
            # create new frame with indices of region in order to sort the DataFrame
            additional_frame_consumer = map(a -> region_dict[a], sub_df.consumer)
            # add the index column to the Dataframe for each region string
            sub_df[!,:consumer_index] = additional_frame_consumer

            # Sort the dataframe
            sort!(sub_df,[:consumer_index])
            # save in nc output
            nc[var][:] = sub_df[:,:value]
        elseif dimension_dict[var] == ("region",) && String(var) in production_variable_list
            # get sub-DataFrame only with the corresponding variable
            sub_df = select(filter(row  -> row[:variable] == var,df),[:producer,:value])

            # check if any pair of coordinates does not exist and make it to a NaN entry in the sub-DataFrame
            pairs = unique(sub_df.producer)
            left_overs_pairs = setdiff(regions, pairs)
            if size(left_overs_pairs)[1] != 0
                add_frame = DataFrame(producer = [i for i in left_overs_pairs], value = [NaN for i in size(left_overs_pairs)[1]])
                sub_df = vcat(sub_df,add_frame)
            end
            # create new frame with indices of region in order to sort the DataFrame
            additional_frame_producer = map(a -> region_dict[a], sub_df.producer)
            # add the index column to the Dataframe for each region string
            sub_df[!,:producer_index] = additional_frame_producer

            # Sort the dataframe
            sort!(sub_df,[:producer_index])
            # save in nc output
            nc[var][:] = sub_df[:,:value]
        end
    end
    close(nc)
end
    

function DrWatson._wsave(file, df::DataFrame; meta = nothing)
    args = !endswith(file, ".gz") ? (file, "w") : (GzipCompressorStream, file, "w")
    open(args...) do stream
        if !isnothing(meta)
            write(stream, "#meta " * JSON.json(meta) * "\n")
            CSV.write(stream, df; append = true, writeheader = true)
        else
            CSV.write(stream, df)
        end
    end
end

function DrWatson._wsave(file, data::NamedTuple{(:df, :meta),Tuple{DataFrame,T}}) where {T}
    return DrWatson._wsave(file, data.df; meta = data.meta)
end

function DrWatson.wload(file; metaonly = false)
    if endswith(file, ".csv") || endswith(file, ".csv.gz")
        args = !endswith(file, ".gz") ? (file, "r") : (GzipDecompressorStream, file, "r")
        open(args...) do stream
            firstline = first(eachline(stream))
            if !metaonly
                seekstart(stream)
                df = CSV.read(stream, DataFrame; comment = "#")
            end
            if startswith(firstline, "#meta ")
                meta = JSON.parse(firstline[7:end])
                return metaonly ? meta : (; df, meta)
            elseif !startswith(firstline, "#meta ") && metaonly
                return nothing
            else
                return df
            end
        end
    else
        return FileIO.load(file)
    end
end



