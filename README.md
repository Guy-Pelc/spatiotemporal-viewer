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

---

# MERFISH Browser — Streamlit App (spec & roadmap)

An interactive browser for exploring MERFISH spatial transcriptomics data across
a mouse-aging timecourse. Built at a hackathon — optimize for a working demo,
not architecture.

## What we're building

A Streamlit app that lets someone pick a "timepoint" (mouse age) and region, then
look at where cells are in space, what type they are, and how gene expression
shifts with age. Think: a scrubbable, filterable spatial viewer, not a full
analysis pipeline.

> **Important framing:** this is a **cross-sectional** aging study, not a
> longitudinal one. Each mouse was profiled once, at one age, then sacrificed —
> there's no single animal followed across time. "Multiple timepoints" means
> multiple mice at different ages, not a movie of one tissue changing. Don't
> build UI that implies otherwise (e.g. no "animal X over time" trajectory view
> without clearing it with the team first).

## Data

**Source:** Sun, Zhou, Hauptschein et al., "Spatial transcriptomic clocks reveal
cell proximity effects in brain ageing," *Nature* 638 (2025). Full dataset on
Zenodo: <https://zenodo.org/records/13883177> (`aging_coronal.h5ad`).

For this hackathon, pull the data from the sibling lab repo rather than
re-downloading:

- **Dev/demo dataset (use this by default):**
  `../temporal_casei/data/anndata/coronal_downsampled.h5ad` — 50K cells, ~26MB,
  loads in seconds.
- **Full dataset (only if we need it for a final polish pass):**
  `../temporal_casei/data/anndata/aging_coronal.h5ad` — 1.45M cells, ~4.2GB. CPU
  rendering of all 1.45M points will be sluggish — downsample or use a
  WebGL/datashader-backed plot if we go there.

Do **not** copy either `.h5ad` into this repo — read it from the relative path,
and add `*.h5ad` to `.gitignore` here too in case anyone drops a local copy in
for testing.

## Schema (`adata`, anndata object)

- **`adata.X`**: raw integer-valued transcript counts, not normalized/log1p'd —
  300 genes. Normalize (`sc.pp.normalize_total` + `sc.pp.log1p`) before showing
  expression values, or the "expression by age" plots will be dominated by
  count-depth noise.
- **`adata.obs` columns:**
  - `age` — float, in months. 20 distinct values in the downsampled set (3.4 to
    34.5). This is the timepoint axis.
  - `mouse_id`, `slide_id`, `cohort`, `batch` — one mouse = one age = one or more
    slides. 20 mice total in the downsampled set.
  - `celltype` — 18 categories (Neuron-Excitatory, Neuron-Inhibitory, Microglia,
    Astrocyte, Oligodendrocyte, OPC, Endothelial, Pericyte, VSMC, VLMC,
    Macrophage, T cell, B cell, Neutrophil, …).
  - `region` — 4 coarse regions: CTX, STR, CC/ACO, VEN. `subregion` has finer
    labels (e.g. `CTX_L1/MEN`).
  - `center_x`, `center_y`, `volume`, `transcript_count`, `num_detected_genes` —
    per-cell QC/geometry fields.
- **`adata.obsm['spatial']`**: `(x, y)` cell centroid coordinates in tissue-slide
  space (matches `center_x`/`center_y`). Coordinates are **not aligned across
  slides/ages** — don't overlay two ages on the same spatial axes and expect
  anatomy to line up; filter to one slide/section at a time for the spatial view,
  and pick a comparable region across ages by region/subregion label instead.
- **`adata.obsm['X_pca']`, `adata.obsm['X_umap']`**: precomputed embeddings,
  ready to plot directly.

## Stack

- **Streamlit** for the app shell — fastest path to an interactive multi-control
  UI for a hackathon timeline.
- **Plotly** (`scattergl`) for the spatial scatter and gene-vs-age plots —
  handles 50K points fine, gives free pan/zoom/hover.
- **scanpy / anndata** for loading and any normalization.
- Cache the loaded AnnData with `st.cache_resource` (it's a big mutable object,
  not `st.cache_data`); cache derived/filtered DataFrames with `st.cache_data`.

## Structure (as it fills in)

```
app.py                 # entry point, top-level layout + sidebar controls
pages/                 # additional Streamlit pages if we go multipage
lib/
  data.py              # load_adata(), normalize(), cached accessors
  plots.py             # spatial scatter, expression-vs-age, celltype composition
requirements.txt
.gitignore             # must exclude *.h5ad, .venv/, __pycache__/
```

Keep `lib/data.py` as the **single place that knows the schema above** — plotting
code should never reach into `adata.obs['...']` directly by column name outside
of it, so a schema change (e.g. swapping in the full dataset) is a one-file fix.

## Running it

```bash
python -m venv .venv
source .venv/Scripts/activate   # Git Bash on Windows
pip install -r requirements.txt
streamlit run app.py
```

If teammates already have `temporal_casei/.venv` set up (torch, scanpy, anndata,
CPU-only), reusing it is faster than building a fresh one — just add `streamlit`
and `plotly` to it.

## Features

### Alignment View

Add an **Alignment** page for comparing two ages after computational alignment.

> **Important:** this is a cross-sectional study. Each age is a different mouse.
> The alignment is only for **visual comparison**, not tracking the same tissue or
> cells over time.

- Select reference age and target age.
- Select region.
- Select one cell type or a pair of cell types.
- Toggle **Original vs Aligned** coordinates.
- Display an interactive Plotly ScatterGL overlay with different colors for each
  age.
- Adjust point size and opacity.

Keep all alignment-specific logic inside `lib/data.py` (e.g.,
`get_aligned_coordinates()`), so the plotting code only requests coordinates and
never knows how they were computed. **Never modify or overwrite the original
spatial coordinates.**

### Gene / gene-module coloring

- Dropdown menu for coloring cells by expression of groups of **indicator genes**
  for different cell types.
- **Gene module coloring:** color cells by the **average expression of predefined
  indicator gene sets**.
- Choose brain region to display.
- Compare plots between brain regions.

### Cell-type composition vs age

Stacked area/bar of the 18 cell-type fractions across ages. Real biology
(microglia up, neurons down), one aggregation, very readable.

### "Top aging genes" ranked list

Precompute each gene's correlation with age (optionally per cell type), surface a
clickable leaderboard that populates the spatial + gene-vs-age panels. Turns a
browser into a discovery tool.

### Young-vs-old dual panel

Two mice side by side, matched by region/subregion label (never overlaid on
shared axes — coords aren't aligned across slides). Clean "before/after."

## Hackathon conventions

- Prioritize a demoable slider-driven view over correctness of every stat. It's
  fine to hardcode a gene list, a default region, etc.
- Commit early and often; don't wait for a feature to be "done." Small commits >
  one big one at the end.
- Don't commit data files, the PDF paper, or venv/cache directories.
- If someone plugs in the full 1.45M-cell dataset and it's slow, downsample in
  `lib/data.py` (`adata[adata.obs.sample(n=...).index]`) rather than trying to
  optimize rendering under time pressure.
