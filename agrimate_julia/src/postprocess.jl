
using DataFrames

include(srcdir("params.jl"))
include(srcdir("io.jl"))

is_intensive(var) = any(contains.(var, ["price", "tax", "ratio"]))
is_extensive(var) = .!is_intensive(var)
is_baseline(var) = any(contains.(var, "baseline"))


function get_combined_data(files, labels = nothing)
    dfs = []
    for file in files
        df, meta = wload(file)
        df = postprocess_data(df)
        df = extend_baseline_data(df)
        push!(dfs, df)
    end
    if !isnothing(labels)
        for (df, label) in zip(dfs, labels)
            for (key, value) in label
                df[!, key] .= value
            end 
        end 
    end
    return vcat(dfs...)
end


function postprocess_data(df)

    producers = unique(df[!, :producer])
    consumers = unique(df[!, :consumer])

    timecols = [:datetime, :t, :n]
    columns = vcat(timecols, :producer, :consumer, :variable, :value)
    df = select(df, columns)

    # Attribute baseline price to all the regions
    df_bp = df[df[!, :variable] .== "baseline price", :]
    for producer in vcat(producers, "World")
        df_bp[!, :producer] .= producer
        df_bp[!, :consumer] .= missing
        df = vcat(df, df_bp)
    end
    for consumer in vcat(consumers, "World")
        df_bp[!, :producer] .= missing
        df_bp[!, :consumer] .= consumer
        df = vcat(df, df_bp)
    end

    # Add average transaction and reservation prices
    for (quantity_var, price_var, average_price_var) in [
        ("transaction quantity", "transaction price", "average transaction price"), 
        ("demanded quantity", "reservation price", "average reservation price"),
    ]
        df_qp = df[in([quantity_var, price_var]).(df[!, :variable]), :]
        df_qp = unstack(df_qp, :variable, :value)
        df_qp[!, "monetary value"] .= df_qp[!, quantity_var] .* df_qp[!, price_var]
        df_qp_p = combine(
            groupby(df_qp, vcat(timecols, :producer)),
            ["monetary value", quantity_var] => ((v, q) -> sum(v) / sum(q)) => :value,
            :consumer => (c -> missing) => :consumer,
        )
        df_qp_c = combine(
            groupby(df_qp, vcat(timecols, :consumer)),
            ["monetary value", quantity_var] => ((v, q) -> sum(v) / sum(q)) => :value,
            :producer => (p -> missing) => :producer,
        )
        df_qp_wld = combine(
            groupby(df_qp, vcat(timecols)),
            ["monetary value", quantity_var] => ((v, q) -> sum(v) / sum(q)) => :value,
            :producer => (p -> "World") => :producer,
            :consumer => (c -> "World") => :consumer,
        )
        for df_qp in [df_qp_p, df_qp_c, df_qp_wld]
            df_qp[!, :variable] .= average_price_var
            df = vcat(df, select(df_qp, columns))
        end
    end

    # Incoming demand
    df_id = combine(
        groupby(df[df[!, :variable] .== "demanded quantity", :], vcat(timecols, :producer)),
        :consumer => (c -> missing) => :consumer,
        :variable => (v -> "incoming demand") => :variable,
        :value => sum => :value,
    )
    df_index = crossjoin(unique(df_id[!, timecols]), unique(df_id[!, [:producer, :consumer, :variable]]))
    df_id = leftjoin(df_index, df_id; on = [timecols..., :producer, :consumer, :variable], matchmissing = :equal)
    df_id[!, :value] = coalesce.(df_id[!, :value], 0.)
    df = vcat(df, select(df_id, columns))

    # Purchase
    for prefix in ["", "baseline "]
        df_pu = combine(
            groupby(df[df[!, :variable] .== prefix * "transaction quantity", :], vcat(timecols, :consumer)),
            :producer => (p -> missing) => :producer,
            :variable => (v -> prefix * "purchase") => :variable,
            :value => sum => :value,
        )
        if prefix != "baseline"
            df_index = crossjoin(unique(df_pu[!, timecols]), unique(df_pu[!, [:producer, :consumer, :variable]]))
            df_pu = leftjoin(df_index, df_pu; on = [timecols..., :producer, :consumer, :variable], matchmissing = :equal)
            df_pu[!, :value] = coalesce.(df_pu[!, :value], 0.)
        end
        df = vcat(df, select(df_pu, columns))
    end

    # Add world aggregate of extensive variables
    df_wld = df[is_extensive.(df[!, :variable]), :]
    # Aggregate producers
    df_wld_p = combine(
        groupby(df_wld[.!ismissing.(df_wld[!, :producer]), :], vcat(timecols, :variable, :consumer)),
        :producer => (p -> "World") => :producer,
        :value => sum => :value,
    )
    # Aggregate consumers
    df_wld_c = combine(
        groupby(df_wld[.!ismissing.(df_wld[!, :consumer]), :], vcat(timecols, :variable, :producer)),
        :consumer => (c -> "World") => :consumer,
        :value => sum => :value,
    )
    df = vcat(df, (select(df_x, columns) for df_x in [df_wld_p, df_wld_c])...)


    # # Add stock to use ratio
    # df_stu = df[(df[!, :variable] .∈ ["consumer storage", "consumption"]) & !ismissing(df[!, :consumer]) , :]
    # df_stu = unstack(df_qp, :variable, :value)
    # df_stu[!, "stock-to-use ratio"] .= 
    #     (df_stu[!, "producer storage"] .+ df_stu[!, "consumer storage"]) / df_stu[!, "consumption"]
    # df_stu = transform(df_stu, "stock-to-use ratio" => :value)
    # df_stu[!, :variable] .= "stock-to-use ratio"
    # df = vcat(df, select(df_stu, columns))

end

function extend_baseline_data(df)

    # Drop rows with parameter data
    df = df[.!(ismissing.(df.t) .& ismissing.(df.n)), :]

    df_date = unique(df[!, [:t, :datetime]])

    is_baseline_filter = is_baseline.(df[!, :variable])

    df_b = select(df[is_baseline_filter, :], Not(:datetime))
    df_b[!, :run] .= "baseline"
    df_b[!, :variable] .= replace.(df_b.variable, "baseline " => "")
    N_year = maximum(df_b[!, :n])

    df = select(df[.!is_baseline_filter, :], Not(:datetime))
    df[!, :run] .= "simulation"
    t_max = maximum(df[!, :t])

    for row in eachrow(df_b)
        t = row[:n]
        while t ≤ t_max
            row[:t] = t
            row[:n] = missing
            push!(df, row)
            t += N_year
        end
    end

    df = leftjoin(df, df_date; on = :t, matchmissing = :equal)
    sort!(df, :t)

    return df
end


function process_trade_flow_data(df; producer = nothing, consumer = nothing)

    quantity_var = "transaction quantity"
    price_var = "transaction price"

    if !isnothing(producer)
        df = df[isequal.(df.producer, producer), :]
        partner = :consumer
    elseif !isnothing(consumer)
        df = df[isequal.(df.consumer, consumer), :]
        partner = :producer
    end

    df = df[in([quantity_var, price_var]).(df.variable), :]
    df = df[.!isequal.(df[!, partner], "World"), :]

    index_cols = [col for col in propertynames(df) if col ∉ [:variable, :value, :run]]
    df_index = unique(df[.!ismissing.(df.t) .& (df.run .== "baseline"), index_cols])
    df_index = crossjoin(df_index, DataFrame(:run => unique(df.run)))
    index_cols = vcat(index_cols, :run)

    # Order partners from highest baseline trade volume to lowest
    df_partners = df[(df.run .== "baseline") .& (df.variable .== quantity_var), :]
    df_partners = combine(groupby(df_partners, partner), :value => sum => quantity_var)
    sort!(df_partners, quantity_var; rev = true)
    partners = [p for p in df_partners[!, partner]]

    # Reformat data and fill missing trade values with 0
    df = unstack(df, :variable, :value)
    df = leftjoin(df_index, df, on = index_cols, matchmissing = :equal)
    sort!(df, :t)

    df[!, quantity_var] = coalesce.(df[!, quantity_var], 0.)

    return df, partners
end

# def process_trade_flow_data(data, region, region_role="supplier", variable="transaction quantity",
#                             param_name=None, param=None):
#     # Extract baseline data
#     region_col = "region" if region_role == "supplier" else "destination"
#     partner_col = "destination" if region_role == "supplier" else "region"

#     df_baseline = data[(data["variable"] == "baseline transaction quantity") & (data[region_col] == region)]
#     df_baseline = df_baseline[[partner_col, "value"]].rename(columns={"value": "baseline transaction quantity"})
#     # Order partners by baseline trade flows
#     df_baseline = df_baseline.drop_duplicates()
#     partners = df_baseline.sort_values(by="baseline transaction quantity", ascending=False)[partner_col].tolist()

#     # Generate data
#     quantity_var = variable
#     price_var = "transaction price" if variable == "transaction quantity" else "reservation price"
#     region_col = "region" if ((region_role == "supplier" and variable == "transaction quantity") or
#                               (region_role == "customer" and variable == "demanded quantity")) else "destination"
#     partner_col = "destination" if region_col == "region" else "region"
#     partner = "customer" if region_role == "supplier" else "supplier"

#     df = data[(data["variable"].isin([quantity_var, price_var])) & (data[region_col] == region)].drop(
#         columns=region_col).rename(columns={partner_col: partner})

#     df = df.pivot(index=[col for col in df.columns if col not in ["variable", "value"]],
#                   columns="variable", values="value").reset_index()

#     df_t = pd.DataFrame(np.arange(df["t"].min(), df["t"].max() + 1), columns=["t"])
#     df = pd.merge(df_t, df, on="t", how="left").sort_values(by="t")
#     df[quantity_var] = df[quantity_var].fillna(0)

#     return df, partners


