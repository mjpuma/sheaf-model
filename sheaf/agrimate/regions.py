"""Agrimate 28-region map (paper Fig. 2 / Suppl. Tbl. C.1).

C.1 itself was not in the cloned tree. This is a UN-M49 aggregation with the
named countries from the main text carved out (USA, Australia, China,
Argentina, Russia, Egypt, Kazakhstan, Ukraine, plus other large wheat
nodes). North Africa follows the paper: Algeria, Libya, Morocco, Sudan,
Tunisia, Western Sahara; Egypt is separate. Recorded as a specification
question until C.1 is in hand.
"""
from __future__ import annotations

from sheaf.data_faostat import EU_ISO3

# Named countries in the wheat application (main text §4.1 / Fig. 2).
SINGLES = {
    "Argentina": ["ARG"],
    "Australia": ["AUS"],
    "Brazil": ["BRA"],
    "Canada": ["CAN"],
    "China": ["CHN"],
    "Egypt": ["EGY"],
    "European Union": list(EU_ISO3),
    "India": ["IND"],
    "Kazakhstan": ["KAZ"],
    "Mexico": ["MEX"],
    "Russia": ["RUS"],
    "Ukraine": ["UKR"],
    "USA": ["USA"],
}

AGGREGATES = {
    "Northern Africa": ["DZA", "LBY", "MAR", "SDN", "TUN", "ESH"],
    "Eastern Africa": [
        "BDI", "COM", "DJI", "ERI", "ETH", "KEN", "MDG", "MWI", "MUS", "MOZ",
        "RWA", "SYC", "SOM", "SSD", "UGA", "TZA", "ZMB", "ZWE",
    ],
    "Middle Africa": ["AGO", "CMR", "CAF", "TCD", "COG", "COD", "GNQ", "GAB", "STP"],
    "Southern Africa": ["BWA", "LSO", "NAM", "ZAF", "SWZ"],
    "Western Africa": [
        "BEN", "BFA", "CPV", "CIV", "GMB", "GHA", "GIN", "GNB", "LBR", "MLI",
        "MRT", "NER", "NGA", "SEN", "SLE", "TGO",
    ],
    "Central America": [
        "BLZ", "CRI", "SLV", "GTM", "HND", "NIC", "PAN", "CUB", "DOM", "HTI",
        "JAM", "TTO", "BHS", "BRB", "ATG", "GRD", "LCA", "VCT", "KNA",
    ],
    "South America": ["BOL", "CHL", "COL", "ECU", "GUY", "PRY", "PER", "SUR", "URY", "VEN"],
    "Central Asia": ["KGZ", "TJK", "TKM", "UZB"],
    "Eastern Asia": ["MNG", "PRK", "KOR", "JPN", "HKG", "MAC", "TWN"],
    "South-Eastern Asia": [
        "BRN", "KHM", "IDN", "LAO", "MYS", "MMR", "PHL", "SGP", "THA", "TLS", "VNM",
    ],
    "Southern Asia": ["AFG", "BGD", "BTN", "IRN", "MDV", "NPL", "PAK", "LKA"],
    "Western Asia": [
        "ARM", "AZE", "BHR", "GEO", "IRQ", "ISR", "JOR", "KWT", "LBN", "OMN",
        "QAT", "SAU", "SYR", "TUR", "ARE", "YEM", "PSE",
    ],
    "Rest of Europe": [
        "ALB", "AND", "BLR", "BIH", "GBR", "ISL", "LIE", "MKD", "MDA", "MNE",
        "NOR", "SMR", "SRB", "CHE", "UKR_SKIP",
    ],
    "Oceania": ["NZL", "FJI", "PNG", "WSM", "TON", "VUT", "SLB", "NCL", "PYF"],
    "Rest of World": [],
}

# Rest of Europe must not include Ukraine (already a single). Filter below.
REGION_ISO3: dict[str, list[str]] = {}
REGION_ISO3.update(SINGLES)
for name, isos in AGGREGATES.items():
    REGION_ISO3[name] = [i for i in isos if i not in {"UKR_SKIP"}]

# Ukraine is a single; drop from Rest of Europe if present
REGION_ISO3["Rest of Europe"] = [
    i for i in REGION_ISO3["Rest of Europe"] if i != "UKR"
]

# Stable order: singles then aggregates (28 names).
REGION_NAMES: list[str] = list(SINGLES.keys()) + list(AGGREGATES.keys())
assert len(REGION_NAMES) == 28, len(REGION_NAMES)

# Tbl. D.9 named exporters (main-text wheat oligopolists). Others use Eq. D.10.
D9_ALPHA = {
    "Argentina": 2.8,
    "Australia": 2.5,
    "Canada": 2.4,
    "European Union": 2.2,
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
