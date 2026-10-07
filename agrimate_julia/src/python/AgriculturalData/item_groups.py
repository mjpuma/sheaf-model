 
# Based on FAOSTAT_Item.csv 

item_group_codes_fao = {
    "wheat": [2511],
    "maize": [2514],
    "rice": [2805, 2807],
}

item_groups_fao = {
    "wheat": { # Item Code: 2511
        15: 1, # wheat
        16: 1, # flour
        17: 1, # bran
        18: 1, # macaroni
        20: 1.15, # bread
        22: 1.15, # pastry
        41: 0.9, # cereals
        110: 1, # wafers
        114: 0.9, # mixes
        115: 0.9, # preparations
        21: 0.95, # bulgur
        19: 1, # germ (no FAO trade data)
        23: 1, # starch (no FAO trade data)
        24: 1, # gluten (no FAO trade data)
    },
    "maize": { # Item Code: 2514
        56: 1, # maize
        57: 1, # germ 
        58: 1, # flour
        59: 1, # bran 
        63: 0.85, # gluten
        64: 0.85, # starch
        846: 1, # meal
    },
    "rice": { # Item Code: 2807
        27: 1, # paddy
        28: 0.77, # husked
        29: 0.77, # milled-husked
        31: 0.75, # milled
        32: 0.75, # broken
        33: 0.75, # gluten
        34: 0.75, # starch
        35: 0.75, # bran
        38: 0.71, # flour
    }
}



