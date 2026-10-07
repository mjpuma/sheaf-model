# getrow(df::AbstractDataFrame, index) = df[findfirst(==(index), df[:, begin]), :]

using DataFrames


function multiunstack(df; index, columns = nothing, values = nothing, variable_name = :variable)
    @assert !(isnothing(columns) && isnothing(values))
    if isnothing(columns) 
        columns = names(df, Not(String.(vcat(index, values))))
    end
    if isnothing(values) 
        values = names(df, Not(String.(vcat(index, columns))))
    end
    @assert !(isnothing(variable_name) && length(values) > 1)
    df = transform(df, AsTable(columns) => ByRow(identity) => :_columns_)
    dfs = [
        unstack(
            df, 
            index, 
            :_columns_, 
            value;
            renamecols = col -> begin
                pairs = keys(col) .=> Base.values(col)
                isnothing(variable_name) ? pairs : (variable_name => value, pairs...)
            end
        )
        for value in values
    ]
    if length(dfs) == 1
        return dfs[begin]
    else
        return outerjoin(dfs...; on = index)
    end
end


function multistack(df; index, value_name = :value)
    df = stack(df, Not(index); value_name, variable_name = :_columns_)
    var(pair) = begin 
        v = pair.args[2]
        v isa QuoteNode ? v.value : Symbol(v.args[2])
    end
    val(pair) = begin
        v = pair.args[3]
        (v == :missing) && return missing
        (v == :nothing) && return nothing
        v
    end
    get_values(cell) = val.(Meta.parse(cell).args)
    get_names(cell) = var.(Meta.parse(cell).args)
    names = get_names(df[begin, :_columns_])
    df = transform(df, :_columns_ => ByRow(get_values) => names)
    df = select(df, index, names, value_name)
end


# Example

if false

    df = DataFrame(
        :Year => repeat([2000, 2001]; inner = 8),
        :Region => repeat(["USA", "CHN"]; inner = 4, outer = 2), 
        :Crop => repeat(["wheat", "rice"]; inner = 2, outer = 4),
        :Source => repeat(["FAO", "USDA"]; outer = 8),
        :Production => 1:16, 
        :Consumption => 17:32,
        :StockVariation => 33:48,
    )

    df = df[1:15, :]
    @show df;

    df_wide = multiunstack(df, index = :Region, columns = [:Year, :Crop, :Source], variable_name = :Variable)
    @show df_wide;

    df_index = DataFrame(:Region => [unique(df_wide.Region)..., "DEU"])
    df_wide = leftjoin(df_index, df_wide; on = :Region)

    df_long = multistack(df_wide; index = :Region, value_name = :Value)
    @show df_long;

end