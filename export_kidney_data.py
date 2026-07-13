#!/usr/bin/env python3
"""Pack kidneys_downsampled.h5ad into compact files the browser viewer can load.

Same format as export_data.py, but for the kidney injury/repair dataset:
outputs into kidney/data/:
  coords.bin   Float32: [spatial_x(n), spatial_y(n), umap_x(n), umap_y(n)]
  expr.bin     Uint8, gene-major: expr[g*n + c] = log1p-scaled expression (0..255)
  manifest.json  everything else (genes, categorical codes, numeric fields, ranges)
"""
import json
import os
import numpy as np
import anndata as ad

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "kidneys_downsampled.h5ad")
OUT = os.path.join(HERE, "kidney", "data")
os.makedirs(OUT, exist_ok=True)

print("reading", SRC)
a = ad.read_h5ad(SRC)
n = a.n_obs
genes = list(map(str, a.var_names))
print(f"{n} cells x {len(genes)} genes")

# --- coordinates -----------------------------------------------------------
spatial = np.asarray(a.obsm["spatial"], dtype=np.float32)
umap = np.asarray(a.obsm["X_umap"], dtype=np.float32)
coords = np.concatenate([
    spatial[:, 0], spatial[:, 1], umap[:, 0], umap[:, 1]
]).astype(np.float32)
coords.tofile(os.path.join(OUT, "coords.bin"))

# --- expression: log1p then per-gene min-max to 0..255 ---------------------
X = a.X
if not isinstance(X, np.ndarray):
    X = X.toarray()
X = np.asarray(X, dtype=np.float32)
Xl = np.log1p(X)
gmax = Xl.max(axis=0)
gmax[gmax == 0] = 1.0
Xq = np.clip(np.round(Xl / gmax * 255.0), 0, 255).astype(np.uint8)
Xq_gm = np.ascontiguousarray(Xq.T)  # shape (genes, n), gene-major
Xq_gm.tofile(os.path.join(OUT, "expr.bin"))

raw_max = X.max(axis=0)

# --- categorical + numeric metadata ---------------------------------------
def cat(col):
    s = a.obs[col].astype("category")
    return {
        "categories": [str(x) for x in s.cat.categories],
        "codes": s.cat.codes.astype(np.int16).tolist(),
    }

categoricals = {c: cat(c) for c in
                ["celltype_plot", "region", "time", "CN", "ident"]}

def num(col):
    return np.asarray(a.obs[col], dtype=np.float32).tolist()

numeric = {c: num(c) for c in ["n_counts", "n_genes"]}

manifest = {
    "n": int(n),
    "genes": genes,
    "gene_raw_max": [round(float(x), 3) for x in raw_max],
    "coords": {
        "spatial": {
            "xmin": float(spatial[:, 0].min()), "xmax": float(spatial[:, 0].max()),
            "ymin": float(spatial[:, 1].min()), "ymax": float(spatial[:, 1].max()),
        },
        "umap": {
            "xmin": float(umap[:, 0].min()), "xmax": float(umap[:, 0].max()),
            "ymin": float(umap[:, 1].min()), "ymax": float(umap[:, 1].max()),
        },
    },
    "categoricals": categoricals,
    "numeric": numeric,
}
with open(os.path.join(OUT, "manifest.json"), "w") as f:
    json.dump(manifest, f)

def mb(p):
    return os.path.getsize(os.path.join(OUT, p)) / 1e6

print(f"wrote coords.bin ({mb('coords.bin'):.1f} MB), "
      f"expr.bin ({mb('expr.bin'):.1f} MB), "
      f"manifest.json ({mb('manifest.json'):.1f} MB)")
