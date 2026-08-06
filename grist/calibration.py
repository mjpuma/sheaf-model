"""
grist.calibration
=================
A prototype calibration for GRIST: three grains (wheat, rice, maize) across a
country set that trades meaningfully in all three, plus a Rest-of-World node that
closes the global balance. Numbers are order-of-magnitude realistic (MMT, $/t)
but are illustrative placeholders -- swap in FAOSTAT/USDA PSD production and
consumption and BACI/COMTRADE flows for a production run.
"""

from __future__ import annotations
import numpy as np
from .core import build_demand_system, Country

GRAINS = ("wheat", "rice", "maize")
P0 = np.array([250.0, 400.0, 200.0])            # reference prices $/t
OWN_ELAST = np.array([-0.25, -0.20, -0.30])     # own-price elasticities
FREIGHT_MULT = np.array([1.00, 1.10, 0.95])     # per-grain freight scaling

# substitutability indices rho[g,h] in [0,1); symmetric, zero diagonal.
#            wheat  rice  maize
RHO = np.array([[0.00, 0.30, 0.40],   # wheat
                [0.30, 0.00, 0.20],   # rice
                [0.40, 0.20, 0.00]])  # maize  (wheat<->maize strongest via feed)

# name, region, lat, lon,
#   prod (W,R,M), cons (W,R,M), export_grains,
#   fs (per-grain weight,p_target as (w,r,m) tuples), gov (stock,ratio,trigger),
#   mkt (gamma per grain)
_OPEN = 0.3
_RESTR = 5.0
INF = np.inf

DATA = [
    # ---- wheat-centric exporters ----
    dict(name="USA", region="N.America", lat=39, lon=-98,
         prod=(45, 7, 350), cons=(30, 4, 300), export=("wheat", "maize"),
         fs_w=(0.3, 0.3, 0.3), pt=(340, 560, 300),
         mkt=(0.15, 0.0, 0.15)),
    dict(name="Russia", region="FSU", lat=61, lon=99,
         prod=(90, 1, 15), cons=(45, 1.5, 13), export=("wheat",),
         fs_w=(6.0, 0.0, 0.5), pt=(265, INF, 250),
         mkt=(0.10, 0.0, 0.0)),
    dict(name="EU", region="Europe", lat=50, lon=10,
         prod=(130, 2, 65), cons=(120, 4, 85), export=("wheat",),
         fs_w=(0.3, 0.0, 0.3), pt=(340, INF, 300),
         mkt=(0.15, 0.0, 0.10)),
    dict(name="Ukraine", region="FSU", lat=49, lon=32,
         prod=(25, 0, 30), cons=(9, 0.3, 6), export=("wheat", "maize"),
         fs_w=(3.6, 0.0, 2.5), pt=(278, INF, 235),
         mkt=(0.05, 0.0, 0.05)),
    dict(name="Canada", region="N.America", lat=56, lon=-106,
         prod=(34, 0, 14), cons=(10, 0.4, 15), export=("wheat",),
         fs_w=(0.3, 0.0, 0.3), pt=(340, INF, 300),
         mkt=(0.10, 0.0, 0.0)),
    dict(name="Australia", region="Oceania", lat=-25, lon=133,
         prod=(30, 0.5, 0.5), cons=(8, 0.5, 1), export=("wheat",),
         fs_w=(0.3, 0.0, 0.0), pt=(340, INF, INF),
         mkt=(0.10, 0.0, 0.0)),
    dict(name="Argentina", region="S.America", lat=-38, lon=-63,
         prod=(20, 1.5, 55), cons=(6, 1, 12), export=("wheat", "maize"),
         fs_w=(5.0, 0.0, 3.0), pt=(268, INF, 232),
         mkt=(0.05, 0.0, 0.08)),
    # ---- maize-centric ----
    dict(name="Brazil", region="S.America", lat=-14, lon=-51,
         prod=(8, 11, 120), cons=(13, 11, 75), export=("maize",),
         fs_w=(0.0, 0.4, 2.0), pt=(INF, 520, 240),
         mkt=(0.0, 0.05, 0.10)),
    # ---- rice-centric exporters ----
    dict(name="India", region="S.Asia", lat=22, lon=79,
         prod=(110, 130, 32), cons=(105, 110, 30), export=("rice",),
         fs_w=(2.0, 5.0, 0.0), pt=(300, 430, INF),
         gov=dict(stock=(20, 25, 0), ratio=(0.2, 0.22, 0), trig=(330, 520, INF)),
         mkt=(0.0, 0.05, 0.0)),
    dict(name="Thailand", region="SE.Asia", lat=15, lon=101,
         prod=(0, 33, 5), cons=(2, 20, 6), export=("rice",),
         fs_w=(0.0, 0.5, 0.0), pt=(INF, 560, INF),
         mkt=(0.0, 0.05, 0.0)),
    dict(name="Vietnam", region="SE.Asia", lat=14, lon=108,
         prod=(0, 43, 4), cons=(2.5, 30, 8), export=("rice",),
         fs_w=(0.0, 4.0, 0.0), pt=(INF, 445, INF),
         mkt=(0.0, 0.04, 0.0)),
    # ---- strategic-reserve importers ----
    dict(name="China", region="E.Asia", lat=35, lon=104,
         prod=(138, 210, 275), cons=(145, 212, 295), export=(),
         gov=dict(stock=(100, 100, 100), ratio=(0.5, 0.5, 0.4),
                  trig=(400, 600, 320))),
    dict(name="Egypt", region="MENA", lat=27, lon=30,
         prod=(9, 4, 7), cons=(20, 4, 16), export=(),
         gov=dict(stock=(4.5, 0, 0), ratio=(0.3, 0, 0), trig=(300, INF, INF))),
    # ---- pure importers ----
    dict(name="Indonesia", region="SE.Asia", lat=-2, lon=118,
         prod=(0, 54, 23), cons=(11, 56, 24), export=()),
    dict(name="Mexico", region="N.America", lat=23, lon=-102,
         prod=(3, 0.2, 27), cons=(8, 1, 44), export=()),
    dict(name="Nigeria", region="Africa", lat=9, lon=8,
         prod=(0.1, 8, 12), cons=(6, 8.5, 13), export=()),
]

# global production/consumption targets so Rest-of-World closes the balance
GLOBAL_PROD = np.array([780.0, 520.0, 1150.0])
GLOBAL_CONS = np.array([780.0, 520.0, 1150.0])


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def build_countries(substitution: bool = True):
    """Return (countries, transport, GRAINS, FREIGHT_MULT).

    substitution=False zeros the cross-price terms -> independent single-commodity
    markets (the TWIST/Agrimate-style limit).
    """
    subst_scale = 0.6 if substitution else 0.0

    rows = [dict(d) for d in DATA]
    # Rest-of-World closes the global balance
    prod_named = np.sum([r["prod"] for r in rows], axis=0)
    cons_named = np.sum([r["cons"] for r in rows], axis=0)
    row_prod = GLOBAL_PROD - prod_named
    row_cons = GLOBAL_CONS - cons_named
    rows.append(dict(name="RestOfWorld", region="RoW", lat=20, lon=20,
                     prod=tuple(row_prod), cons=tuple(row_cons), export=()))

    lat = np.array([r["lat"] for r in rows], float)
    lon = np.array([r["lon"] for r in rows], float)
    n = len(rows)
    transport = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                transport[i, j] = _haversine(lat[i], lon[i], lat[j], lon[j]) * 0.0025 + 8.0

    countries = []
    for r in rows:
        D0 = np.array(r["cons"], float)
        sysd = build_demand_system(GRAINS, D0, P0, OWN_ELAST, RHO, subst_scale)
        gov = r.get("gov")
        mkt = r.get("mkt")
        c = Country(
            name=r["name"], region=r["region"],
            production=np.array(r["prod"], float), demand=sysd,
            export_grains=tuple(r.get("export", ())),
            fs_weight=np.array(r.get("fs_w", (0, 0, 0)), float),
            p_target=np.array(r.get("pt", (INF, INF, INF)), float),
            mkt_gamma=(np.array(mkt, float) if mkt else None),
            mkt_capacity=(np.array(r["prod"], float) * 0.5 if mkt else None),
            mkt_stock=(np.array(r["prod"], float) * 0.15 if mkt else None),
            gov_stock=(np.array(gov["stock"], float) if gov else None),
            gov_target_ratio=(np.array(gov["ratio"], float) if gov else None),
            gov_price_trigger=(np.array(gov["trig"], float) if gov else None),
        )
        countries.append(c)
    return countries, transport, GRAINS, FREIGHT_MULT
