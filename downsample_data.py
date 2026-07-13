#!/usr/bin/env python3
"""Downsample an annotated AnnData object to a target cell count.

Stratifies by an obs column (cell type, condition, etc.) so the result keeps
each group's relative proportion instead of a plain random slice that could
wipe out rare groups. This is the same idea used to produce
coronal_downsampled.h5ad from its source data — run this first, then feed
the output into export_data.py to pack it for the browser viewer.

Usage:
    python3 downsample_data.py kidney_injury_repair.h5ad \
        kidney_downsampled.h5ad --n 50000 --groupby celltype
"""
import argparse
import os
import sys

import anndata as ad
import numpy as np

# obs column names to try, in order, if --groupby isn't given
GROUPBY_CANDIDATES = [
    "celltype", "cell_type", "annotation", "cell_type_annotation",
    "cluster", "condition", "injury_status", "timepoint",
]


def pick_groupby(obs, requested):
    if requested:
        if requested not in obs.columns:
            sys.exit(f"--groupby '{requested}' not found in obs. "
                      f"Available columns: {list(obs.columns)}")
        return requested
    for name in GROUPBY_CANDIDATES:
        if name in obs.columns:
            print(f"auto-selected --groupby '{name}'")
            return name
    sys.exit("Could not auto-detect a groupby column. Pass one explicitly "
              f"with --groupby. Available columns: {list(obs.columns)}")


def stratified_indices(labels, n_target, rng, min_per_group=1):
    """Largest-remainder apportionment: proportional quota per group,
    capped at the group's own size, exact total == n_target."""
    labels = np.asarray(labels)
    n_total = len(labels)
    if n_target >= n_total:
        return np.arange(n_total)

    groups, inverse, counts = np.unique(labels, return_inverse=True, return_counts=True)
    raw = counts * (n_target / n_total)
    quota = np.maximum(min_per_group, np.floor(raw)).astype(int)
    quota = np.minimum(quota, counts)  # never ask for more than a group has

    # Distribute the remainder (largest fractional part first) to hit n_target exactly.
    remainder = n_target - quota.sum()
    frac_order = np.argsort(-(raw - np.floor(raw)))
    i = 0
    while remainder > 0 and i < len(frac_order) * 3:
        g = frac_order[i % len(frac_order)]
        if quota[g] < counts[g]:
            quota[g] += 1
            remainder -= 1
        i += 1
    while remainder < 0:
        g = frac_order[i % len(frac_order)]
        if quota[g] > min_per_group:
            quota[g] -= 1
            remainder += 1
        i += 1

    idx = []
    for g_i, g in enumerate(groups):
        pool = np.flatnonzero(inverse == g_i)
        take = min(quota[g_i], len(pool))
        idx.append(rng.choice(pool, size=take, replace=False))
    idx = np.concatenate(idx)
    rng.shuffle(idx)
    return np.sort(idx)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", help="source .h5ad")
    p.add_argument("output", nargs="?", help="output .h5ad "
                    "(default: <input>_downsampled.h5ad)")
    p.add_argument("--n", type=int, default=50000, help="target cell count (default: 50000)")
    p.add_argument("--groupby", default=None,
                    help="obs column to stratify by (auto-detected if omitted)")
    p.add_argument("--min-per-group", type=int, default=1,
                    help="minimum cells kept per group (default: 1)")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    output = args.output or (
        os.path.splitext(args.input)[0] + "_downsampled.h5ad"
    )

    print("reading", args.input)
    a = ad.read_h5ad(args.input)
    print(f"{a.n_obs} cells x {a.n_vars} genes")

    groupby = pick_groupby(a.obs, args.groupby)
    rng = np.random.default_rng(args.seed)
    idx = stratified_indices(a.obs[groupby].values, args.n, rng, args.min_per_group)

    before = a.obs[groupby].value_counts()
    sub = a[idx].copy()
    after = sub.obs[groupby].value_counts()

    print(f"\ndownsampled {a.n_obs} -> {sub.n_obs} cells, stratified by '{groupby}':")
    for g in before.index:
        print(f"  {g:<25} {before[g]:>7} -> {after.get(g, 0):>7}")

    sub.write_h5ad(output)
    print(f"\nwrote {output} ({os.path.getsize(output) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
