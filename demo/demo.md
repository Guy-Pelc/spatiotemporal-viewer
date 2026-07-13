# Coronal Aging Atlas — Demo

A quick walkthrough of the in-browser spatial transcriptomics viewer for the
`coronal_downsampled.h5ad` dataset (mouse-brain aging MERFISH data:
49,998 cells × 300 genes).

## What it is

A single-page, dependency-free viewer (`index.html` + canvas rendering) for
exploring spatial and UMAP embeddings of the dataset, coloring cells by
metadata or gene expression, and filtering down to specific subsets.

## Running the demo

```bash
cd viewer
./run.sh            # or: python3 -m http.server 8777
```

Then open `http://localhost:8777/index.html`. `run.sh` regenerates the
`data/` bundle from the source `.h5ad` automatically if it's missing.

## Suggested walkthrough

1. **Switch views** — toggle between **Spatial** (tissue coordinates) and
   **UMAP** in the top-left segmented control.
2. **Color by metadata** — set "Color by" to `celltype` to see cluster
   identities laid out in tissue space, then switch to `region` or
   `subregion` to see anatomical boundaries emerge.
3. **Color by a gene** — search for a gene (e.g. a marker for a cell type
   you just saw) and watch the viridis colorbar show relative expression
   for that gene alone.
4. **Color by a numeric field** — try `age` or `transcript_count` to see
   continuous covariates across the tissue.
5. **Filter** — restrict to a single category value (e.g. one `mouse_id`
   or one `region`) to isolate a subset of cells.
6. **Legend toggling** — click individual cell types in the legend to
   hide/show them; use `reset` to restore all.
7. **Navigate** — scroll to zoom, drag to pan, double-click to reset the
   view, hover any cell to see its full metadata in the tooltip.

## Why it's useful

- No server-side processing or external dependencies — the whole dataset
  is packed into a static binary bundle (`data/coords.bin`, `data/expr.bin`,
  `data/manifest.json`) and rendered client-side.
- Makes it fast to eyeball whether a gene's spatial pattern lines up with
  known anatomical regions or cell-type clusters, without opening Python.

## Regenerating the data bundle

If the source `.h5ad` changes, re-run:

```bash
python3 export_data.py
```

This repacks `coronal_downsampled.h5ad` into the `data/` bundle the viewer
reads.
