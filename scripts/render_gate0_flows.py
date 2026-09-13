#!/usr/bin/env python3
"""Render Gate 0 option-flow diagrams as SVG into figures/gate0_flows/.

These are discussion pictures (current map vs sitting options), not score
figures. Regenerate:

    python scripts/render_gate0_flows.py
"""
from __future__ import annotations

import html
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "gate0_flows"

NW, NH = 168, 48
RANK_GAP, NODE_GAP, PAD = 62, 22, 28

# tone: default | changed | input | dim
GRAPHS: list[dict] = [
    {
        "file": "01_current_fortnight",
        "title": "Current Gate 0 — one fortnight",
        "option": "P0 / S0 / E0 sequential map",
        "note": "Incoming p, q, S, H. Demand uses last p. Twin is a separate run. No inner solve.",
        "nodes": [
            ("state", "p, q, S, H in", "input"),
            ("twin", "twin free, unmet", "input"),
            ("demand", "d from last p", "default"),
            ("hexp", "H^exp φ-blend", "default"),
            ("target", "T = L + s", "default"),
            ("offers", "O surplus × (1−τ)", "default"),
            ("importd", "D gap + λ rebuild", "default"),
            ("trade", "Armington min-clear", "default"),
            ("stocks", "S′ then W clip", "default"),
            ("asks", "q fill / blockage", "default"),
            ("pscar", "p^scar vs twin", "default"),
            ("pstar", "p* blend ω", "default"),
            ("pout", "p out, smoother", "default"),
            ("next", "next fortnight", "default"),
        ],
        "layers": [
            ["state", "twin", "hexp"],
            ["demand", "target", "offers", "importd"],
            ["trade", "stocks", "asks"],
            ["pscar", "pstar", "pout", "next"],
        ],
        "edges": [
            ("state", "demand"), ("state", "hexp"), ("hexp", "target"),
            ("demand", "offers"), ("demand", "importd"),
            ("target", "offers"), ("target", "importd"),
            ("offers", "trade"), ("importd", "trade"),
            ("trade", "stocks"), ("trade", "asks"), ("stocks", "asks"),
            ("twin", "pscar"), ("stocks", "pscar"),
            ("asks", "pstar"), ("pscar", "pstar"), ("pstar", "pout"),
            ("pout", "next"), ("asks", "next"), ("stocks", "next"),
        ],
    },
    {
        "file": "02_baselines_four_objects",
        "title": "Baselines — four objects that feed the map",
        "option": "B0 name them",
        "note": "Scarcity uses the twin. p0 is the numeraire. Spin-up is 2 years. Twin holds p = p0.",
        "nodes": [
            ("psd", "2005 PSD stocks", "input"),
            ("hseas", "Hseas climatology", "input"),
            ("p0", "p0 Pink Sheet", "input"),
            ("spin", "2-year spin-up", "default"),
            ("s0", "opening S", "default"),
            ("twin", "twin run τ≡0", "default"),
            ("ftwin", "free_twin", "default"),
            ("lowess", "H × (1+LOWESS)", "default"),
            ("treat", "treatment map", "default"),
            ("pt", "p path", "default"),
        ],
        "layers": [
            ["psd", "hseas", "p0"],
            ["spin", "s0", "lowess"],
            ["twin", "ftwin", "treat"],
            ["pt"],
        ],
        "edges": [
            ("psd", "spin"), ("hseas", "spin"), ("spin", "s0"),
            ("s0", "twin"), ("hseas", "twin"), ("p0", "twin"),
            ("twin", "ftwin"), ("hseas", "lowess"),
            ("s0", "treat"), ("lowess", "treat"), ("p0", "treat"),
            ("ftwin", "treat"), ("treat", "pt"),
        ],
    },
    {
        "file": "03_baselines_4year_spinup",
        "title": "Baselines — 4-year spin-up",
        "option": "B2 Agrimate length",
        "note": "Same objects; only spin-up lengthens. Named sensitivity. Do not retune η.",
        "nodes": [
            ("psd", "2005 PSD stocks", "input"),
            ("hseas", "Hseas climatology", "input"),
            ("p0", "p0 Pink Sheet", "input"),
            ("spin", "4-year spin-up", "changed"),
            ("s0", "opening S", "default"),
            ("twin", "twin run τ≡0", "default"),
            ("ftwin", "free_twin", "default"),
            ("treat", "treatment map", "default"),
            ("pt", "p path", "default"),
        ],
        "edges": [
            ("psd", "spin"), ("hseas", "spin"), ("spin", "s0"),
            ("s0", "twin"), ("hseas", "twin"), ("p0", "twin"),
            ("twin", "ftwin"), ("s0", "treat"), ("ftwin", "treat"),
            ("p0", "treat"), ("treat", "pt"),
        ],
    },
    {
        "file": "04_baselines_nash_spe_rest",
        "title": "Baselines — Nash / SPE rest",
        "option": "B3 different object",
        "note": "Not a rename of the twin. Resting p,S come from a yearly program, then the 24-step treatment runs.",
        "nodes": [
            ("data", "FAOSTAT / PSD year", "input"),
            ("nash", "annual Nash or SPE", "changed"),
            ("rest", "resting p, S", "changed"),
            ("treat", "24-step treatment", "default"),
            ("pt", "p path", "default"),
        ],
        "edges": [
            ("data", "nash"), ("nash", "rest"), ("rest", "treat"), ("treat", "pt"),
        ],
    },
    {
        "file": "05_price_same_step",
        "title": "Price — same-step p in demand",
        "option": "P2 inner consistency",
        "note": "Dashed edge: this step’s d uses this step’s p. Not Agrimate. Not SPE.",
        "nodes": [
            ("state", "q, S, H in", "input"),
            ("demand", "d from this p", "changed"),
            ("target", "T = L + s", "default"),
            ("offers", "O", "default"),
            ("importd", "D", "default"),
            ("trade", "Armington", "default"),
            ("stocks", "S′, W clip", "default"),
            ("asks", "ask update", "default"),
            ("pscar", "p^scar", "default"),
            ("pstar", "p*", "default"),
            ("pout", "p out", "default"),
        ],
        "edges": [
            ("state", "demand"), ("demand", "offers"), ("demand", "importd"),
            ("target", "offers"), ("target", "importd"),
            ("offers", "trade"), ("importd", "trade"),
            ("trade", "stocks"), ("trade", "asks"),
            ("stocks", "pscar"), ("asks", "pstar"), ("pscar", "pstar"),
            ("pstar", "pout"), ("pstar", "demand"),
        ],
    },
    {
        "file": "06_price_ask_foc",
        "title": "Price — ask markup FOC",
        "option": "P3 exporter FOC only",
        "note": "World p stays inverse-demand flavored and blended. Only the ask box becomes a FOC.",
        "nodes": [
            ("state", "p, q, S, H in", "input"),
            ("twin", "twin free", "input"),
            ("demand", "d from last p", "default"),
            ("target", "T = L + s", "default"),
            ("offers", "O", "default"),
            ("importd", "D", "default"),
            ("trade", "Armington", "default"),
            ("stocks", "S′, W clip", "default"),
            ("asks", "q markup FOC", "changed"),
            ("pscar", "p^scar still map", "default"),
            ("pstar", "p* blend ω", "default"),
            ("pout", "p out", "default"),
        ],
        "edges": [
            ("state", "demand"), ("demand", "offers"), ("demand", "importd"),
            ("target", "offers"), ("target", "importd"),
            ("offers", "trade"), ("importd", "trade"),
            ("trade", "stocks"), ("trade", "asks"),
            ("twin", "pscar"), ("stocks", "pscar"),
            ("asks", "pstar"), ("pscar", "pstar"), ("pstar", "pout"),
        ],
    },
    {
        "file": "07_price_agrimate_nlps",
        "title": "Price — Agrimate three NLPs",
        "option": "P4 / O4 different object",
        "note": "Prices are outputs of programs. No world p as a primitive. Do not clone as Gate 0.",
        "nodes": [
            ("h", "harvest in", "input"),
            ("tau", "policy τ known", "default"),
            ("sup", "supplier NLP", "changed"),
            ("con", "consumer NLP", "changed"),
            ("pur", "purchaser CES", "changed"),
            ("s", "S′", "default"),
            ("pexp", "export price", "default"),
            ("pdom", "domestic price", "default"),
            ("pworld", "paper world p (acct.)", "default"),
        ],
        "edges": [
            ("h", "tau"), ("tau", "sup"), ("sup", "con"), ("con", "pur"),
            ("pur", "s"), ("sup", "pexp"), ("con", "pdom"),
            ("pexp", "pworld"), ("pdom", "pworld"),
        ],
    },
    {
        "file": "08_price_yearly_spe",
        "title": "Price — yearly SPE heartbeat",
        "option": "P5 / O5 parked host",
        "note": "p is a multiplier on balance. Wrong clock for 2007/08. Parked in sheaf.annual.",
        "nodes": [
            ("ep", "E[p] last year", "input"),
            ("stor", "storage rule", "default"),
            ("qp", "spatial QP", "changed"),
            ("p", "p_year, shipments", "default"),
            ("next", "next year", "default"),
        ],
        "edges": [
            ("ep", "stor"), ("stor", "qp"), ("qp", "p"), ("p", "next"),
        ],
    },
    {
        "file": "09_opt_characterize_foc",
        "title": "Optimization — is the map already a FOC?",
        "option": "O1 / P1 characterize, no solver",
        "note": "Same boxes as the current fortnight. Accent: the two places a potential might live.",
        "nodes": [
            ("state", "p, q, S, H in", "input"),
            ("twin", "twin free", "input"),
            ("demand", "d from last p", "default"),
            ("target", "T = L + s", "default"),
            ("offers", "O", "default"),
            ("importd", "D", "default"),
            ("trade", "Armington", "default"),
            ("stocks", "S′, W clip", "default"),
            ("asks", "ask = FOC?", "changed"),
            ("pscar", "p^scar = FOC?", "changed"),
            ("pstar", "blend still extra", "default"),
            ("pout", "p out", "default"),
        ],
        "edges": [
            ("state", "demand"), ("demand", "offers"), ("demand", "importd"),
            ("target", "offers"), ("target", "importd"),
            ("offers", "trade"), ("importd", "trade"),
            ("trade", "stocks"), ("trade", "asks"),
            ("twin", "pscar"), ("stocks", "pscar"),
            ("asks", "pstar"), ("pscar", "pstar"), ("pstar", "pout"),
        ],
    },
    {
        "file": "10_storage_cover_rule",
        "title": "Storage — cover-rule partition",
        "option": "S0 no storage agent",
        "note": "Why not dump: T withholds cover, not an Euler. No carrying cost r.",
        "nodes": [
            ("avail", "avail = S + H", "input"),
            ("eat", "eat d", "default"),
            ("hold", "hold T = L + s", "default"),
            ("offer", "offer leftover × (1−τ)", "default"),
            ("trade", "Armington", "default"),
            ("sp", "S′", "default"),
            ("w", "soft drain S′−W", "default"),
        ],
        "layers": [
            ["avail"],
            ["eat", "hold", "offer"],
            ["trade", "sp", "w"],
        ],
        "edges": [
            ("avail", "eat"), ("avail", "hold"), ("avail", "offer"),
            ("offer", "trade"), ("eat", "sp"), ("trade", "sp"),
            ("hold", "sp"), ("sp", "w"),
        ],
    },
    {
        "file": "11_storage_store_vs_sell",
        "title": "Storage — store vs sell FOC",
        "option": "S2 one-line Euler",
        "note": "Offer extra iff expected price rise beats r. Named sensitivity; must not be 2008-fit.",
        "nodes": [
            ("avail", "avail = S + H", "input"),
            ("foc", "store vs sell FOC", "changed"),
            ("offer", "offer", "default"),
            ("hold", "hold", "default"),
            ("trade", "Armington", "default"),
            ("sp", "S′", "default"),
        ],
        "edges": [
            ("avail", "foc"), ("foc", "offer"), ("foc", "hold"),
            ("offer", "trade"), ("hold", "sp"), ("trade", "sp"),
        ],
    },
    {
        "file": "12_storage_agrimate_supplier",
        "title": "Storage — Agrimate commercial supplier",
        "option": "S4 commercial NLP",
        "note": "One supplier per region, after policy is known. Strategic refill is a different Agrimate agent.",
        "nodes": [
            ("h", "harvest", "input"),
            ("tau", "policy known", "default"),
            ("nlp", "supplier NLP", "changed"),
            ("sell", "sell domestic + export", "default"),
            ("store", "store", "default"),
        ],
        "edges": [
            ("h", "tau"), ("tau", "nlp"), ("nlp", "sell"), ("nlp", "store"),
        ],
    },
    {
        "file": "13_commercial_rules",
        "title": "Commercial — rules, not agents",
        "option": "Current commercial layer",
        "note": "No supplier/consumer/purchaser program. Destination mix is ask-reweighted FAOSTAT shares.",
        "nodes": [
            ("avail", "avail = S + H", "input"),
            ("rules", "eat / T / O rules", "default"),
            ("aeff", "Ã ∝ A (p0/q)^γ", "default"),
            ("trade", "Armington min", "default"),
            ("sp", "S′", "default"),
        ],
        "edges": [
            ("avail", "rules"), ("rules", "aeff"), ("aeff", "trade"), ("trade", "sp"),
        ],
    },
    {
        "file": "14_commercial_three_agents",
        "title": "Commercial — three Agrimate agents",
        "option": "Same object as P4",
        "note": "Purchaser, not the supplier, chooses how much is sold to each market.",
        "nodes": [
            ("h", "harvest", "input"),
            ("tau", "policy τ", "default"),
            ("sup", "supplier", "changed"),
            ("con", "consumer", "changed"),
            ("pur", "purchaser", "changed"),
            ("s", "S′", "default"),
        ],
        "edges": [
            ("h", "tau"), ("tau", "sup"), ("sup", "con"), ("con", "pur"), ("pur", "s"),
        ],
    },
    {
        "file": "15_commercial_two_prices",
        "title": "Commercial — domestic vs export price",
        "option": "T1 two prices when τ>0",
        "note": "Current map: one world p; a ban does not cheapen a local CPI. Gate 2 welfare wants a split; Pink Sheet does not require it.",
        "nodes": [
            ("tau", "τ > 0", "input"),
            ("p", "one world p", "dim"),
            ("pdom", "p domestic", "changed"),
            ("pexp", "p export / ask", "changed"),
            ("d", "demand on p_dom", "default"),
            ("o", "offers at p_exp", "default"),
        ],
        "edges": [
            ("p", "tau"), ("tau", "pdom"), ("tau", "pexp"),
            ("pdom", "d"), ("pexp", "o"),
        ],
    },
    {
        "file": "16_foresight_current",
        "title": "Foresight — thin expectations",
        "option": "E0 current",
        "note": "Harvest: φ-blend into the lean gap. Price: last fortnight. Lean clock is world-wide.",
        "nodes": [
            ("h", "H this step", "input"),
            ("hseas", "Hseas", "input"),
            ("plast", "p last step", "input"),
            ("hexp", "H^exp φ-blend", "default"),
            ("lean", "world lean clock", "default"),
            ("target", "T = L + s", "default"),
            ("demand", "d(p last)", "default"),
        ],
        "edges": [
            ("h", "hexp"), ("hseas", "hexp"), ("hexp", "lean"),
            ("lean", "target"), ("plast", "demand"),
        ],
    },
    {
        "file": "17_foresight_this_step_p",
        "title": "Foresight — this-step p in demand",
        "option": "E1 = P2",
        "note": "Harvest foresight unchanged. Only the price information set in demand changes.",
        "nodes": [
            ("h", "H this step", "input"),
            ("hseas", "Hseas", "input"),
            ("hexp", "H^exp φ-blend", "default"),
            ("lean", "world lean clock", "default"),
            ("target", "T = L + s", "default"),
            ("demand", "d(this p)", "changed"),
            ("pstar", "p*", "changed"),
        ],
        "edges": [
            ("h", "hexp"), ("hseas", "hexp"), ("hexp", "lean"),
            ("lean", "target"), ("pstar", "demand"), ("demand", "pstar"),
        ],
    },
    {
        "file": "18_foresight_country_lean",
        "title": "Foresight — country lean clock",
        "option": "E2 national calendars",
        "note": "T_i uses i’s harvest pulse, not the world 12% clock. Live modeling choice.",
        "nodes": [
            ("h", "H this step", "input"),
            ("hseas", "Hseas", "input"),
            ("plast", "p last step", "input"),
            ("hexp", "H^exp φ-blend", "default"),
            ("lean", "lean on i’s calendar", "changed"),
            ("target", "T_i = L_i + s", "changed"),
            ("demand", "d(p last)", "default"),
        ],
        "edges": [
            ("h", "hexp"), ("hseas", "hexp"), ("hexp", "lean"),
            ("lean", "target"), ("plast", "demand"),
        ],
    },
    {
        "file": "19_foresight_re_off_table",
        "title": "Foresight — 10-year / RE (not this)",
        "option": "E4 off the table",
        "note": "Opposite of the sitting. Drawn only to show what we are not building.",
        "nodes": [
            ("path", "10-year harvest path", "dim"),
            ("re", "RE E[p] path", "dim"),
            ("euler", "storage Euler", "dim"),
            ("s", "S′", "default"),
        ],
        "edges": [
            ("path", "re"), ("re", "euler"), ("euler", "s"),
        ],
    },
]


def _back_edges(ids: list[str], edges: list[tuple[str, str]]) -> set[tuple[str, str]]:
    """DFS back-edges (the ones that make a cycle)."""
    children: dict[str, list[str]] = defaultdict(list)
    for a, b in edges:
        children[a].append(b)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {i: WHITE for i in ids}
    back: set[tuple[str, str]] = set()

    def visit(u: str) -> None:
        color[u] = GRAY
        for v in children[u]:
            if color[v] == GRAY:
                back.add((u, v))
            elif color[v] == WHITE:
                visit(v)
        color[u] = BLACK

    for i in ids:
        if color[i] == WHITE:
            visit(i)
    return back


def layout(ids: list[str], edges: list[tuple[str, str]],
           layers: list[list[str]] | None = None):
    back = _back_edges(ids, edges)
    if layers is not None:
        pos = {}
        max_w = PAD * 2
        max_h = PAD * 2
        for r, group in enumerate(layers):
            n = len(group)
            row_w = n * NW + (n - 1) * NODE_GAP
            y = PAD + r * (NH + RANK_GAP)
            x0 = PAD
            for k, nid in enumerate(group):
                pos[nid] = (x0 + k * (NW + NODE_GAP), y)
            max_w = max(max_w, x0 + row_w + PAD)
            max_h = max(max_h, y + NH + PAD)
        return pos, max_w, max_h, back
    fwd = [(a, b) for a, b in edges if (a, b) not in back]
    children: dict[str, list[str]] = defaultdict(list)
    indeg = {i: 0 for i in ids}
    for a, b in fwd:
        children[a].append(b)
        indeg[b] += 1
    rank = {i: 0 for i in ids}
    q = deque([i for i in ids if indeg[i] == 0])
    seen = list(q)
    while q:
        u = q.popleft()
        for v in children[u]:
            rank[v] = max(rank[v], rank[u] + 1)
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
                seen.append(v)
    for i in ids:
        if i not in seen:
            rank[i] = max(rank.values(), default=0) + 1
    by_rank: dict[int, list[str]] = defaultdict(list)
    for i in ids:
        by_rank[rank[i]].append(i)
    pos = {}
    max_w = PAD * 2
    max_h = PAD * 2
    for r, group in sorted(by_rank.items()):
        n = len(group)
        row_w = n * NW + (n - 1) * NODE_GAP
        y = PAD + r * (NH + RANK_GAP)
        x0 = PAD
        for k, nid in enumerate(group):
            pos[nid] = (x0 + k * (NW + NODE_GAP), y)
        max_w = max(max_w, x0 + row_w + PAD)
        max_h = max(max_h, y + NH + PAD)
    return pos, max_w, max_h, back


FILL = {
    "default": "#ffffff",
    "changed": "#dbeafe",
    "input": "#f4f4f5",
    "dim": "#fafafa",
}
STROKE = {
    "default": "#3f3f46",
    "changed": "#1d4ed8",
    "input": "#71717a",
    "dim": "#a1a1aa",
}
TEXT = {
    "default": "#18181b",
    "changed": "#1e3a8a",
    "input": "#3f3f46",
    "dim": "#a1a1aa",
}


def svg_for(g: dict) -> str:
    nodes = g["nodes"]
    ids = [n[0] for n in nodes]
    spec = {n[0]: n for n in nodes}
    layers = g.get("layers")
    pos, W, H, back = layout(ids, g["edges"], layers=layers)
    title_h = 64
    H_tot = H + title_h
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H_tot:.0f}" '
        f'viewBox="0 0 {W:.0f} {H_tot:.0f}" font-family="ui-sans-serif, Helvetica, Arial, sans-serif">',
        f'<rect width="{W:.0f}" height="{H_tot:.0f}" fill="#ffffff"/>',
        f'<text x="{PAD}" y="28" font-size="16" font-weight="600" fill="#18181b">'
        f'{html.escape(g["title"])}</text>',
        f'<text x="{PAD}" y="48" font-size="12" fill="#52525b">'
        f'{html.escape(g["option"])} — {html.escape(g["note"])}</text>',
        '<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">'
        '<path d="M0,0 L8,4 L0,8 Z" fill="#71717a"/></marker></defs>',
    ]
    dy = title_h

    def anchor(nid: str, incoming: bool):
        x, y = pos[nid]
        y = y + dy
        if incoming:
            return x + NW / 2, y
        return x + NW / 2, y + NH

    for a, b in g["edges"]:
        sx, sy = anchor(a, False)
        tx, ty = anchor(b, True)
        dashed = ' stroke-dasharray="5 4"' if (a, b) in back else ""
        if (a, b) in back:
            side = W - 10
            d = f"M {sx:.1f} {sy:.1f} C {side:.1f} {sy:.1f}, {side:.1f} {ty:.1f}, {tx:.1f} {ty:.1f}"
        else:
            mid = (sy + ty) / 2
            d = f"M {sx:.1f} {sy:.1f} C {sx:.1f} {mid:.1f}, {tx:.1f} {mid:.1f}, {tx:.1f} {ty:.1f}"
        parts.append(
            f'<path d="{d}" fill="none" stroke="#71717a" stroke-width="1.25"{dashed} marker-end="url(#arr)"/>'
        )
    for nid, label, tone in nodes:
        x, y = pos[nid]
        y = y + dy
        sw = 1.75 if tone == "changed" else 1.0
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{NW}" height="{NH}" rx="6" '
            f'fill="{FILL[tone]}" stroke="{STROKE[tone]}" stroke-width="{sw}"/>'
        )
        parts.append(
            f'<text x="{x + NW / 2:.1f}" y="{y + NH / 2 + 4:.1f}" text-anchor="middle" '
            f'font-size="11" fill="{TEXT[tone]}">{html.escape(label)}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def pdf_for(g: dict, path: Path, *, header: bool = True) -> None:
    """Vector PDF for Overleaf (pdfLaTeX cannot include SVG)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    ids = [n[0] for n in g["nodes"]]
    pos, W, H, back = layout(ids, g["edges"], layers=g.get("layers"))
    title_h = 72 if header else 12
    H_tot = H + title_h
    fig = plt.figure(figsize=(W / 72.0, H_tot / 72.0), dpi=72)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H_tot, 0)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    if header:
        ax.text(PAD, 22, g["title"], fontsize=11, fontweight="bold",
                color="#18181b", va="top")
        ax.text(PAD, 42, f"{g['option']} — {g['note']}", fontsize=8,
                color="#52525b", va="top")

    def anchor(nid: str, incoming: bool):
        x, y = pos[nid]
        y = y + title_h
        if incoming:
            return x + NW / 2, y
        return x + NW / 2, y + NH

    for a, b in g["edges"]:
        sx, sy = anchor(a, False)
        tx, ty = anchor(b, True)
        style = "dashed" if (a, b) in back else "solid"
        if (a, b) in back:
            rad = 0.25
        else:
            rad = 0.0
        arr = FancyArrowPatch(
            (sx, sy), (tx, ty),
            arrowstyle="-|>", mutation_scale=9,
            linewidth=1.1, color="#71717a",
            linestyle=style,
            connectionstyle=f"arc3,rad={rad}",
            shrinkA=0, shrinkB=1,
        )
        ax.add_patch(arr)

    for nid, label, tone in g["nodes"]:
        x, y = pos[nid]
        y = y + title_h
        box = FancyBboxPatch(
            (x, y), NW, NH,
            boxstyle="round,pad=0,rounding_size=5",
            linewidth=1.6 if tone == "changed" else 1.0,
            facecolor=FILL[tone], edgecolor=STROKE[tone],
        )
        ax.add_patch(box)
        ax.text(x + NW / 2, y + NH / 2, label, ha="center", va="center",
                fontsize=8, color=TEXT[tone])

    fig.savefig(path, format="pdf")
    plt.close(fig)


OVERLEAF_FIG = ROOT / "overleaf" / "gate0_discussion" / "figures"


def write_readable_stack(path: Path, boxes: list[tuple[str, str]],
                         *, arrows: bool = True) -> None:
    """Page-width vertical stack so 11pt labels survive includegraphics."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    fig_w = 6.3
    box_h = 0.48
    gap = 0.28
    pad_x, pad_y = 0.12, 0.16
    n = len(boxes)
    fig_h = pad_y + n * box_h + (n - 1) * gap + pad_y
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    box_w = fig_w - 2 * pad_x
    for i, (label, tone) in enumerate(boxes):
        y_top = fig_h - pad_y - i * (box_h + gap)
        y = y_top - box_h
        ax.add_patch(FancyBboxPatch(
            (pad_x, y), box_w, box_h,
            boxstyle="round,pad=0.012,rounding_size=0.06",
            facecolor=FILL[tone], edgecolor=STROKE[tone],
            linewidth=1.8 if tone == "changed" else 1.15,
        ))
        ax.text(fig_w / 2, y + box_h / 2, label, ha="center", va="center",
                fontsize=11, color=TEXT[tone], wrap=True)
        if arrows and i < n - 1:
            ax.annotate(
                "",
                xy=(fig_w / 2, y - gap + 0.05),
                xytext=(fig_w / 2, y - 0.03),
                arrowprops=dict(arrowstyle="-|>", color="#52525b",
                                mutation_scale=12, lw=1.2),
            )
    fig.savefig(path, format="pdf", bbox_inches=None)
    plt.close(fig)


def write_readable_split(path: Path, source: str,
                         branches: list[str], sink: str) -> None:
    """One source, three branches, one sink — storage picture."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    fig_w, fig_h = 6.3, 3.6
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    def box(x, y, w, h, text, tone="default"):
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.012,rounding_size=0.05",
            facecolor=FILL[tone], edgecolor=STROKE[tone], linewidth=1.2,
        ))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=11, color=TEXT[tone])

    bw, bh = 1.85, 0.7
    box(2.22, 2.75, 1.85, bh, source, "input")
    xs = [0.22, 2.22, 4.22]
    for x, lab in zip(xs, branches):
        box(x, 1.45, bw, bh, lab)
        ax.annotate("", xy=(x + bw / 2, 1.45 + bh),
                    xytext=(3.15, 2.75),
                    arrowprops=dict(arrowstyle="-|>", color="#52525b",
                                    mutation_scale=11, lw=1.1))
    box(2.0, 0.22, 2.3, bh, sink)
    for x in xs:
        ax.annotate("", xy=(3.15, 0.22 + bh),
                    xytext=(x + bw / 2, 1.45),
                    arrowprops=dict(arrowstyle="-|>", color="#52525b",
                                    mutation_scale=11, lw=1.1))
    fig.savefig(path, format="pdf")
    plt.close(fig)


def write_readable_baselines(path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    fig_w, fig_h = 6.3, 3.8
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    def box(x, y, w, h, text, tone="default"):
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.012,rounding_size=0.05",
            facecolor=FILL[tone], edgecolor=STROKE[tone], linewidth=1.2,
        ))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=11, color=TEXT[tone])

    items = [
        (0.2, 2.7, "Reference price p0\n(Pink Sheet, 2010 $/t)"),
        (3.3, 2.7, "Climatological harvest\nH_seas(i,t)"),
        (0.2, 1.55, "Two-year spin-up\nof stocks S(i,t)"),
        (3.3, 1.55, "Unshocked twin run\n(tau = 0, mean demand)"),
    ]
    for x, y, t in items:
        box(x, y, 2.8, 0.85, t, "input")
        ax.annotate("", xy=(3.15, 0.95), xytext=(x + 1.4, y),
                    arrowprops=dict(arrowstyle="-|>", color="#52525b",
                                    mutation_scale=11, lw=1.1))
    box(1.5, 0.2, 3.3, 0.75, "Crisis run (harvest shocks + restrictions)")
    fig.savefig(path, format="pdf")
    plt.close(fig)


def write_four_ways(path: Path) -> None:
    """Four ways a world price can be produced. 11pt labels, page width."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    fig, axs = plt.subplots(2, 2, figsize=(6.3, 5.2))
    fig.patch.set_facecolor("white")
    panels = [
        (axs[0, 0], "A.  Current recursion (Gate 0)",
         ["State at t-1", "Two-week\nupdate map", "World price\np(t)"]),
        (axs[0, 1], "B.  Contemporaneous consistency",
         ["Trial price", "Demand, trade,\nscarcity", "Fixed point\np = G(p)"]),
        (axs[1, 0], "C.  Agent optimisation (Agrimate)",
         ["Supplier\nstore vs sell", "Household\nexpenditure", "Purchaser\norigin choice"]),
        (axs[1, 1], "D.  Annual spatial equilibrium",
         ["Lagged\nannual price", "Transport\nprogramme", "Price as\nmultiplier"]),
    ]
    box_w, box_h = 0.26, 0.34
    y0 = 0.22
    xs = [0.04, 0.37, 0.70]
    for ax, title, labels in panels:
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.set_title(title, fontsize=11, loc="left", pad=6)
        for x, lab in zip(xs, labels):
            ax.add_patch(FancyBboxPatch(
                (x, y0), box_w, box_h,
                boxstyle="round,pad=0.01,rounding_size=0.03",
                facecolor="#ffffff", edgecolor="#3f3f46", linewidth=1.15,
                transform=ax.transAxes, clip_on=False,
            ))
            ax.text(x + box_w / 2, y0 + box_h / 2, lab, ha="center",
                    va="center", fontsize=10, transform=ax.transAxes,
                    linespacing=1.25)
        for i in range(2):
            ax.annotate(
                "",
                xy=(xs[i + 1], y0 + box_h / 2),
                xytext=(xs[i] + box_w, y0 + box_h / 2),
                xycoords=ax.transAxes, textcoords=ax.transAxes,
                arrowprops=dict(arrowstyle="-|>", color="#52525b",
                                lw=1.2, mutation_scale=11),
            )
    fig.tight_layout(w_pad=0.8, h_pad=1.1)
    fig.savefig(path, format="pdf")
    plt.close(fig)


INDEX = """# Gate 0 flow figures

Open this folder in the repo: `figures/gate0_flows/`.

Organized writeup (plain + economic + figure): `overleaf/gate0_discussion/`.

Accent (blue) boxes are what an **option** would change relative to the
current fortnight. Dashed arrows are cycles. Agrimate NLPs and the yearly
QP are **different objects**, not a small edit of the spine.

Regenerate: `python scripts/render_gate0_flows.py`

Discussion: [`diagnostics/GATE0_DISCUSSION.md`](../../diagnostics/GATE0_DISCUSSION.md).
Captions / mermaid: [`diagnostics/GATE0_FLOWS.md`](../../diagnostics/GATE0_FLOWS.md).

| File | Family |
|---|---|
| [01_current_fortnight.svg](01_current_fortnight.svg) | Current map |
| [02_baselines_four_objects.svg](02_baselines_four_objects.svg) | Baselines |
| [03_baselines_4year_spinup.svg](03_baselines_4year_spinup.svg) | Baselines |
| [04_baselines_nash_spe_rest.svg](04_baselines_nash_spe_rest.svg) | Baselines |
| [05_price_same_step.svg](05_price_same_step.svg) | Price |
| [06_price_ask_foc.svg](06_price_ask_foc.svg) | Price |
| [07_price_agrimate_nlps.svg](07_price_agrimate_nlps.svg) | Price |
| [08_price_yearly_spe.svg](08_price_yearly_spe.svg) | Price |
| [09_opt_characterize_foc.svg](09_opt_characterize_foc.svg) | Optimization |
| [10_storage_cover_rule.svg](10_storage_cover_rule.svg) | Storage |
| [11_storage_store_vs_sell.svg](11_storage_store_vs_sell.svg) | Storage |
| [12_storage_agrimate_supplier.svg](12_storage_agrimate_supplier.svg) | Storage |
| [13_commercial_rules.svg](13_commercial_rules.svg) | Commercial |
| [14_commercial_three_agents.svg](14_commercial_three_agents.svg) | Commercial |
| [15_commercial_two_prices.svg](15_commercial_two_prices.svg) | Commercial |
| [16_foresight_current.svg](16_foresight_current.svg) | Foresight |
| [17_foresight_this_step_p.svg](17_foresight_this_step_p.svg) | Foresight |
| [18_foresight_country_lean.svg](18_foresight_country_lean.svg) | Foresight |
| [19_foresight_re_off_table.svg](19_foresight_re_off_table.svg) | Foresight (not this) |
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    OVERLEAF_FIG.mkdir(parents=True, exist_ok=True)
    for g in GRAPHS:
        svg_path = OUT / f"{g['file']}.svg"
        pdf_path = OUT / f"{g['file']}.pdf"
        svg_path.write_text(svg_for(g), encoding="utf-8")
        pdf_for(g, pdf_path, header=True)
        pdf_for(g, OVERLEAF_FIG / pdf_path.name, header=False)
        print(svg_path.relative_to(ROOT))
        print(pdf_path.relative_to(ROOT))
    write_four_ways(OUT / "20_four_ways_p.pdf")
    write_four_ways(OVERLEAF_FIG / "20_four_ways_p.pdf")
    write_readable_stack(
        OVERLEAF_FIG / "01_current_fortnight.pdf",
        [
            ("State: lagged world price, offer prices, carry-in stocks", "input"),
            ("Demand d(i,t) at the lagged world price p(t-1)", "default"),
            ("Cover target T(i,t) = lean-season cover + safety stock", "default"),
            ("Export supply O(i,t) after restriction; import demand D(i,t)", "default"),
            ("Bilateral allocation on the FAOSTAT network, price-reweighted", "default"),
            ("Consumption, stock accounting, drawdown above capacity", "default"),
            ("Offer prices q(i,t) adjust to the fill rate and to blockage", "default"),
            ("World price: offer prices blended with scarcity vs the twin", "default"),
            ("Carry price, offer prices, and stocks to period t+1", "default"),
        ],
    )
    write_readable_baselines(OVERLEAF_FIG / "02_baselines_four_objects.pdf")
    write_readable_split(
        OVERLEAF_FIG / "10_storage_cover_rule.pdf",
        "Available grain\navail = S + H",
        ["Consumption\nd(i,t)", "Cover target\nT = L + s", "Export supply\nO(i,t)"],
        "Closing stock\nS(i,t+1)",
    )
    print("overleaf figures: readable 01, 02, 10, 20")
    print("figures/gate0_flows/20_four_ways_p.pdf")
    (OUT / "README.md").write_text(INDEX, encoding="utf-8")
    print((OUT / "README.md").relative_to(ROOT))


if __name__ == "__main__":
    main()
