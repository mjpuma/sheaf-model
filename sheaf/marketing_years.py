"""USDA PSD marketing-year end months, by crop and SHEAF node.

PSD ending stocks are **local marketing-year** carry, not calendar December.
Scoring country stocks at one global month (May wheat, August maize, December
rice) therefore compares post-harvest peaks in some countries to lean-season
carry in others. This table is the USDA FAS convention used in *Grain: World
Markets and Trade*, not a 28-region grouping.

Unlisted nodes fall back to the crop default (the month that matches *world*
summed PSD ending stocks).
"""
from __future__ import annotations

# Crop default = month whose world model stocks best match summed PSD ending
# (wheat USDA US MY is June–May; maize US MY September–August; rice world
# summed PSD is an August-scale mix, not calendar December).
CROP_MY_END_MONTH = {"wheat": 5, "maize": 8, "rice": 8}

# Country overrides where FAS uses a different local MY than the crop default.
# Values are calendar month of MY-end (1–12).
COUNTRY_MY_END_MONTH = {
    "wheat": {
        "USA": 5,
        "EU": 6,
        "Russia": 6,
        "Ukraine": 6,
        "Kazakhstan": 6,
        "Canada": 7,
        "China": 6,
        "India": 3,       # April–March
        "Australia": 9,   # October–September
        "Argentina": 11,  # December–November
        "Brazil": 9,
        "Egypt": 5,
    },
    "maize": {
        "USA": 8,
        "China": 9,
        "EU": 9,
        "Mexico": 9,
        "Canada": 8,
        "Brazil": 2,      # March–February
        "Argentina": 2,
        "SouthAfrica": 4,
        "Ukraine": 9,
        "India": 9,
    },
    "rice": {
        "USA": 7,         # August–July
        "India": 9,       # October–September
        "Thailand": 12,   # calendar
        "Vietnam": 12,
        "China": 12,
        "Indonesia": 12,
        "Brazil": 2,
        "Egypt": 9,
    },
}


def my_end_month(crop: str, country: str | None = None) -> int:
    crop = crop.lower().strip()
    if crop not in CROP_MY_END_MONTH:
        raise ValueError(f"unsupported crop {crop!r}")
    if country is None:
        return CROP_MY_END_MONTH[crop]
    table = COUNTRY_MY_END_MONTH.get(crop, {})
    return int(table.get(country, CROP_MY_END_MONTH[crop]))
