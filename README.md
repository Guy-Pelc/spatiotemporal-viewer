# Coronal Aging — Spatial Viewer

An in-browser viewer for `coronal_downsampled.h5ad` (mouse-brain aging spatial
transcriptomics: 49,998 cells × 300 genes).

## Run

```bash
cd viewer
./run.sh            # or: python3 -m http.server 8777
# open http://localhost:8777/index.html
```

`run.sh` regenerates the data bundle automatically if it's missing.

## Features

- **Views**: Spatial (tissue coordinates) and UMAP, toggle top-left.
- **Color by**: any categorical (`celltype`, `region`, `subregion`, `batch`,
  `mouse_id`, `slide_id`), any numeric field (`age`, `transcript_count`, …), or
  any of the **300 genes** (searchable) with a viridis colorbar.
- **Filter**: restrict to one category value (e.g. only `STR`, or one mouse).
- **Mouse age**: a slider that steps through the 20 discrete ages (each maps to
  one mouse), oldest to the right. Combines with the other controls, so you can
  watch a gene or cell type across the aging timeline. The ▶ button animates
  through the ages automatically.
- **Legend**: click a cell type to hide/show it; `reset` restores all.
- **Navigation**: scroll to zoom, drag to pan, double-click to reset view,
  hover a cell for its full metadata.

## Files

| File | What it is |
|------|-----------|
| `export_data.py` | Packs the `.h5ad` into the `data/` bundle below. |
| `data/manifest.json` | Genes, categorical codes, numeric fields, coord ranges. |
| `data/coords.bin` | Float32 spatial + UMAP coordinates. |
| `data/expr.bin` | Uint8, gene-major, log1p per-gene-scaled expression (~15 MB). |
| `index.html` | The viewer (canvas rendering, no external dependencies). |

## Notes

- Expression is `log1p`-transformed then scaled 0–255 **per gene** for display,
  so the colorbar shows *relative* expression within each gene.
- Re-run `python3 export_data.py` after changing the source `.h5ad`.
