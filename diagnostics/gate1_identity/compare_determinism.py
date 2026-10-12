#!/usr/bin/env python3
"""Compare determinism_t2.jl dumps. Prints max abs/rel and bitwise identity."""
from __future__ import annotations

import sys
from pathlib import Path

GROUPS = {
    "price_index": ("price_index",),
    "expected_sales": ("expected_sales", "expected_sales_domestic", "expected_sales_foreign"),
    "expected_price": ("expected_price", "expected_price_domestic", "expected_price_foreign"),
    "optimal_sales": ("optimal_sales", "optimal_sales_domestic", "optimal_sales_foreign"),
}


def decode(h: str) -> float:
    return struct_unpack(h)


def struct_unpack(h: str) -> float:
    import struct
    # Julia prints reinterpret(UInt64, x) in hex, i.e. the IEEE bits as an integer.
    return struct.unpack(">d", bytes.fromhex(h.zfill(16)))[0]


def load(path: Path):
    """Return header lines and records (t, name, region, floats, hexs)."""
    header = []
    rows = []
    crop = None
    for line in path.read_text().splitlines():
        if line.startswith("#") or line.startswith("label ") or line.startswith("mode ") or line.startswith("focus ") or line.startswith("blas_") or line.startswith("nthreads ") or line.startswith("JULIA_") or line.startswith("OPENBLAS_"):
            header.append(line)
            continue
        if line.startswith("crop "):
            crop = line.split()[1]
            continue
        if line.startswith("order "):
            # Region names contain spaces; keep the raw line.
            rows.append(("order", line, crop))
            continue
        if line.startswith("val ") or line.startswith("vec "):
            kind = "val" if line.startswith("val ") else "vec"
            left, rest = line[4:].rsplit(" ", 1)
            t_s, name, region = left.split(" ", 2)
            hexs = [rest] if kind == "val" else ([h for h in rest.split(",") if h])
            rows.append((kind, int(t_s), name, region, [struct_unpack(h) for h in hexs], hexs, crop))
    return header, rows


def index(rows, crop_filter):
    out = {}
    for rec in rows:
        if rec[0] == "order":
            continue
        _, t, name, region, vals, hexs, crop = rec
        if crop_filter is not None and crop not in (None, crop_filter):
            # coupled dumps tag a crop on a preceding line stored in the row
            if crop != crop_filter:
                continue
        out[(t, name, region)] = (vals, hexs)
    return out


def orders(rows, crop_filter):
    found = []
    for rec in rows:
        if rec[0] != "order":
            continue
        line = rec[1]
        parts = line.split(" ", 4)
        # order T producer|consumer IDS
        # order 0 CROP producer|consumer IDS
        if len(parts) >= 5 and parts[2] in ("wheat", "rice", "maize"):
            if crop_filter and parts[2] != crop_filter:
                continue
            found.append(line)
        elif crop_filter is None or rec[2] in (None, crop_filter):
            found.append(line)
    return found


def is_multi(rows):
    return any(r[0] != "order" and r[6] is not None for r in rows)


def compare(a_path, b_path, crop):
    ha, ra = load(a_path)
    hb, rb = load(b_path)
    multi_a, multi_b = is_multi(ra), is_multi(rb)
    A = index(ra, crop if multi_a else None)
    B = index(rb, crop if multi_b else None)
    keys = sorted(set(A) & set(B))
    only_a = sorted(set(A) - set(B))
    only_b = sorted(set(B) - set(A))
    print(f"\n== {a_path.name} vs {b_path.name}  crop={crop}  shared={len(keys)} only_a={len(only_a)} only_b={len(only_b)}")
    oa, ob = orders(ra, crop if multi_a else None), orders(rb, crop if multi_b else None)
    same_order = oa == ob
    print(f"iteration-order lines identical: {same_order}")
    if not same_order:
        for x, y in zip(oa, ob):
            if x != y:
                print("  order A", x[:180])
                print("  order B", y[:180])
                break
        if len(oa) != len(ob):
            print(f"  order line count {len(oa)} vs {len(ob)}")
    bitwise = True
    first = None
    by = {g: [0.0, 0.0, True] for g in GROUPS}
    for key in keys:
        t, name, region = key
        va, ha_ = A[key]
        vb, hb_ = B[key]
        n = min(len(va), len(vb))
        group = next(g for g, names in GROUPS.items() if name in names)
        for i in range(n):
            same = ha_[i] == hb_[i]
            if not same:
                bitwise = False
                by[group][2] = False
                diff = abs(va[i] - vb[i])
                den = max(abs(va[i]), abs(vb[i]))
                rel = 0.0 if den == 0 else diff / den
                if diff > by[group][0]:
                    by[group][0] = diff
                if rel > by[group][1]:
                    by[group][1] = rel
                if first is None:
                    first = (t, name, region, i, va[i], vb[i], diff, rel)
        if len(va) != len(vb):
            bitwise = False
            by[group][2] = False
    print(f"bitwise identical: {bitwise and not only_a and not only_b and same_order}")
    if first:
        t, name, region, i, xa, xb, diff, rel = first
        print(f"first bit difference: t={t} {name}[{i}] {region}  {xa:.16g} vs {xb:.16g}  abs={diff:.3g} rel={rel:.3g}")
    print(f"{'group':22s} {'max_abs':14s} {'max_rel':14s} bitwise")
    for g, (mx, rel, bit) in by.items():
        print(f"{g:22s} {mx:.6g} {rel:.6g} {bit}")


def main():
    folder = Path(sys.argv[1])
    pairs = sys.argv[2:]
    # pairs are labelA labelB crop
    if len(pairs) % 3 != 0:
        sys.exit("usage: compare_determinism.py DIR labelA labelB crop [...]")
    for i in range(0, len(pairs), 3):
        a, b, crop = pairs[i:i+3]
        compare(folder / f"dump_{a}.txt", folder / f"dump_{b}.txt", crop)


if __name__ == "__main__":
    main()
