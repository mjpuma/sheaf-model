"""Agrimate wheat region map from Zenodo 14022004 ``AgrimateRegionsWheat``.

Paper Tbl. C.1 was described as 28 regions; the author wheat list is 27
names (Egypt and Mexico are inside Northern / Central America; Pakistan and
Turkey are singles; there is no Rest-of-World residual). Host follows the
executable list. See ``diagnostics/GATE0_DEPARTURES.md``.
"""
from __future__ import annotations

# Author ``AgrimateRegionsWheat`` (src/regions.jl), order preserved.
REGION_ISO3: dict[str, list[str]] = {
    "Argentina": ["ARG"],
    "Australia": ["AUS"],
    "Brazil": ["BRA"],
    "Canada": ["CAN"],
    "China": ["CHN", "HKG", "MAC", "TWN"],
    "EU-27": [
        "AUT", "BEL", "BGR", "CYP", "CZE", "DEU", "DNK", "ESP", "EST", "FIN",
        "FRA", "GRC", "HRV", "HUN", "IRL", "ITA", "LTU", "LUX", "LVA", "MLT",
        "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "SWE",
    ],
    "India": ["IND"],
    "Kazakhstan": ["KAZ"],
    "Pakistan": ["PAK"],
    "Russia": ["RUS"],
    "Turkey": ["TUR"],
    "USA": ["USA"],
    "Ukraine": ["UKR"],
    "Central America": [
        "ABW", "AIA", "ANT", "ATG", "BES", "BHS", "BLM", "BLZ", "BMU", "BRB",
        "CRI", "CUB", "CUW", "CYM", "DMA", "DOM", "GLP", "GRD", "GTM", "HND",
        "HTI", "JAM", "KNA", "LCA", "MAF", "MEX", "MSR", "MTQ", "NIC", "PAN",
        "PRI", "SLV", "SXM", "TCA", "TTO", "VCT", "VGB", "VIR",
    ],
    "Rest of Central Asia": ["KGZ", "TJK", "TKM", "UZB"],
    "Eastern Africa": [
        "ATF", "BDI", "COM", "DJI", "ERI", "ETH", "IOT", "KEN", "MDG", "MOZ",
        "MUS", "MWI", "MYT", "REU", "RWA", "SOM", "SSD", "SYC", "TZA", "UGA",
        "ZMB", "ZWE",
    ],
    "Rest of Eastern Asia": ["JPN", "KOR", "MNG", "PRK"],
    "Rest of Europe": [
        "ALA", "ALB", "AND", "BIH", "BLR", "CHE", "FRO", "GBR", "GGY", "GIB",
        "IMN", "ISL", "JEY", "LIE", "MCO", "MDA", "MKD", "MNE", "NOR", "SCG",
        "SJM", "SMR", "SRB", "VAT", "YUG", "XKX",
    ],
    "Middle Africa": ["AGO", "CAF", "CMR", "COD", "COG", "GAB", "GNQ", "STP", "TCD"],
    "Northern Africa": ["DZA", "EGY", "ESH", "LBY", "MAR", "SDN", "TUN"],
    "Rest of Oceania": [
        "ASM", "CCK", "COK", "CXR", "FJI", "FSM", "GUM", "HMD", "JTN", "KIR",
        "MHL", "MID", "MNP", "NCL", "NFK", "NIU", "NRU", "NZL", "PCN", "PLW",
        "PNG", "PYF", "SLB", "TKL", "TON", "TUV", "UMI", "VUT", "WAK", "WLF",
        "WSM",
    ],
    "Rest of South America": [
        "BOL", "BVT", "CHL", "COL", "ECU", "FLK", "GUF", "GUY", "PER", "PRY",
        "SGS", "SUR", "URY", "VEN",
    ],
    "Rest of Southern Asia": ["AFG", "BGD", "BTN", "IRN", "LKA", "MDV", "NPL"],
    "Southeast Asia": [
        "BRN", "IDN", "KHM", "LAO", "MMR", "MYS", "PHL", "SGP", "THA", "TLS", "VNM",
    ],
    "Southern Africa": ["BWA", "LSO", "NAM", "SWZ", "ZAF"],
    "Western Africa": [
        "BEN", "BFA", "CIV", "CPV", "GHA", "GIN", "GMB", "GNB", "LBR", "MLI",
        "MRT", "NER", "NGA", "SEN", "SHN", "SLE", "TGO",
    ],
    "Rest of Western Asia": [
        "ARE", "ARM", "AZE", "BHR", "GEO", "IRQ", "ISR", "JOR", "KWT", "LBN",
        "OMN", "PSE", "QAT", "SAU", "SYR", "YEM", "YMD",
    ],
}

REGION_NAMES: list[str] = list(REGION_ISO3.keys())
assert len(REGION_NAMES) == 27, len(REGION_NAMES)

# Tbl. D.9 named exporters. Others use Eq. D.10.
D9_ALPHA = {
    "Argentina": 2.8,
    "Australia": 2.5,
    "Canada": 2.4,
    "EU-27": 2.2,
    "Kazakhstan": 2.6,
    "Russia": 3.0,
    "Ukraine": 2.7,
    "USA": 2.0,
}
D9_NU = {k: 1.0 for k in D9_ALPHA}


def iso3_to_region() -> dict[str, str]:
    out: dict[str, str] = {}
    occupied: set[str] = set()
    for region in REGION_NAMES:
        for iso in REGION_ISO3[region]:
            if iso in occupied:
                continue
            out[iso] = region
            occupied.add(iso)
    return out
