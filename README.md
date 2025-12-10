# Ingredients Curation Project

Curates ingredient information for dietary supplement products across four sources:

- **DSLD** (NIH ODS Dietary Supplement Label Database)
- **Amazon** (best sellers pages)
- **Knowde** (supplier product pages)
- **Internal leads** (company domains)

The workflow harmonizes and integrates heterogeneous product/ingredient data, produces quality metrics, and exports two course use-case tables.

> **Use cases**
> - **UC-1 (Products by target ingredient):** a product list filtered by a target ingredient list.
> - **UC-2 (Companies by target ingredient):** an aggregation showing, for each target ingredient, how many brands/products a company offers.

---

## Quick start

1. **Clone**
   ```bash
   git clone https://github.com/jingsu322/ingredients_curation_project
   cd ingredients_curation_project

1. **Install with uv (Python 3.11)**

   ```bash
   uv sync
   ```

2. **Place data**
    Put raw data under the following folders (create if missing):

   ```
   data/raw/dsld_dataset/
   data/raw/amazon_dataset/
   data/raw/knowde_dataset/
   data/raw/internal_dataset/
   ```

   For full dataset (large), see [Box link](https://uofi.box.com/s/ac89dzikmob9eu00xr9zyetg8k24s1lz).

3. **Run the workflow**

   ```bash
   uv run snakemake -j 4 --rerun-incomplete --latency-wait 20
   ```

4. **Find outputs**

   ```
   data/interim/harmonized.parquet
   data/interim/integrated.parquet
   data/curated/uc1_products.csv
   data/curated/uc2_companies.csv
   reports/quality_report.csv
   provenance/{source_manifest.csv,checksums.txt,runs/run_meta.json,ingest_stats_*.json}
   ```

   If something fails, see **Troubleshooting** below.

------

## Environment & reproducibility

- Managed with **uv**; dependencies are locked in `uv.lock`.

- Reproduce on a clean machine:

  ```bash
  uv sync && uv run snakemake -j 4 --rerun-incomplete --latency-wait 20
  ```

- Workflow: **Snakemake** (`Snakefile`) with configuration in `workflow/config.yaml`.

- All important run/provenance artifacts are written under `provenance/`.

------

## Configuration knobs

- `workflow/config.yaml`
   Paths to raw datasets; flags (e.g., `only_on_market` for DSLD).
- `rules/synonyms.csv`
   Seed synonym rules for ingredient normalization (used in harmonization).
- `rules/units.csv`
   Unit canonicalization (e.g., g → mg) and mass conversion factors.
- `workflow/targets.txt`
   The **target ingredient list** used by UC-1/UC-2 (one per line; `#` for comments).
- `curation/company_alias.csv` (optional)
   Brand → company mappings to improve company rollups.

------

## How to run parts of the DAG

```bash
# Aggregate a single source after changing mappers
uv run snakemake -j 2 data/interim/amazon.parquet

# Re-run only quality report and use-case tables
uv run snakemake -j 2 reports/quality_report.csv data/curated/uc1_products.csv data/curated/uc2_companies.csv
```

------

## Outputs

- **`data/interim/harmonized.parquet`**
   Concatenated and normalized records with:
  - `ingredients_norm` (synonyms applied)
  - `serving_unit_canonical`, `serving_size_mg` (unit normalization)
- **`data/interim/integrated.parquet`**
   Adds a stable **`curated_id`** (SHA-256 over key fields) and `company_name_final` (alias mapping).
- **`data/curated/uc1_products.csv`**
   Product-level rows where `ingredients(_norm)` match any `workflow/targets.txt` term.
- **`data/curated/uc2_companies.csv`**
   Company-level aggregation per target ingredient (`brand_count`, `product_count`).
- **`reports/quality_report.csv`**
   Row counts per source, required-field completeness, parse coverage, and target coverage proxy.
- **`provenance/`**
   `source_manifest.csv`, `checksums.txt`, `runs/run_meta.json`, `ingest_stats_*.json`.

------

## Health check

```bash
uv run python - <<'PY'
import duckdb, os
def n(path):
    ext=os.path.splitext(path)[1].lower()
    if ext==".parquet":
        return duckdb.query(f"select count(*) from parquet_scan('{path}')").fetchone()[0]
    elif ext==".csv":
        return duckdb.query(f"select count(*) from read_csv_auto('{path}', header=True)").fetchone()[0]
    else:
        return -1
for p in [
  "data/interim/harmonized.parquet",
  "data/interim/integrated.parquet",
  "data/curated/uc1_products.csv",
  "data/curated/uc2_companies.csv",
]:
    print(p, n(p))
PY
```

------

## Project structure

```
ingredients_curation_project/
├── Snakefile
├── pyproject.toml
├── uv.lock
├── src/
│   ├── preprocess/
│   │   ├── aggregate_dir.py     
│   │   └── harmonize.py         
│   ├── integrate/
│   │   └── merge.py     
│   ├── validate/
│   │   └── checks.py             # quality metrics CSV
│   └── views/
│       └── export.py             # UC-1 / UC-2 exports
├── workflow/
│   ├── config.yaml
│   └── targets.txt
├── rules/
│   ├── synonyms.csv
│   └── units.csv    
├── data/
│   ├── raw/{dsld_dataset,amazon_dataset,knowde_dataset,internal_dataset}/
│   ├── interim/*.parquet 
│   └── curated/{uc1_products.csv,uc2_companies.csv}
├── reports/quality_report.csv
├── provenance/
│   ├── source_manifest.csv
│   ├── checksums.txt
│   ├── runs/run_meta.json
│   └── ingest_stats_*.json
├── metadata/datacite.json
├── docs/
│   ├── TERMS.md
│   ├── data_dictionary.md
│   ├── codebook.csv
│   └── final_report.md  
└── CITATION.cff
```

------

## Provenance & transparency

- **Automation:** Snakemake encodes the full DAG; `uv.lock` pins the Python stack.
- **Traceability:** `provenance/source_manifest.csv` (input inventory), `ingest_stats_*.json` (per-source counts/errors), `checksums.txt` (output hashes), `runs/run_meta.json` (config + timestamp).
- **Reproducibility:** a clean machine can reproduce by following **Quick start** with the same data placement.

------

## Troubleshooting

- **CSV read error in DuckDB (“No magic bytes…”)** — Use `read_csv_auto(...)` for CSV and `parquet_scan(...)` for Parquet (see Health check).

- **0 rows in amazon/knowde/internal Parquet** — Ensure raw files exist under `data/raw/...` and re-run:

  ```bash
  uv run snakemake -j 4 -R aggregate_amazon aggregate_knowde aggregate_internal --latency-wait 20
  ```

- **NumPy/PyArrow mismatch in a different Python** — Always run via `uv run ...` to use the pinned environment.

- **Filesystem latency on macOS** — Add `--latency-wait 20`.

------

## Terms of use & acknowledgments

This project uses publicly available information for research and teaching. Please respect each source’s terms of use.

- DSLD (NIH ODS Dietary Supplement Label Database)
- Amazon (public product pages)
- Knowde (supplier product pages)
- Internal leads from company domains (course scope only)

Details: see `docs/TERMS.md`.

------

## Metadata & citation

- DataCite-style metadata: `metadata/datacite.json`
- Data dictionary / codebook: `docs/data_dictionary.md`
- Citation (APA-friendly): `CITATION.cff`

------

## Checklist

- **Lifecycle:** Ingest → Harmonize → Integrate → Validate → Disseminate (automated in Snakemake).
- **Ethics/Policy:** Documented in `docs/TERMS.md` and README; access to protected/full data via Box.
- **Models/Abstractions:** Common schema across sources; Parquet; stable `curated_id`.
- **Cleaning/Integration:** Synonym and unit normalization; brand→company aliasing.
- **Metadata:** DataCite JSON; data dictionary with variables/units/semantics.
- **Identity:** `source_record_id` + SHA-256 based `curated_id`.
- **Standards:** Parquet/CSV; JSON; simple schema validation in validation step.
- **Reproducibility/Provenance:** `uv.lock`, Snakemake DAG, checksums, manifests, run metadata.
- **Dissemination:** This repository + Box link; all artifacts organized and documented.

------

## References

National Institutes of Health, Office of Dietary Supplements. (n.d.). *Dietary Supplement Label Database (DSLD)*. https://dsld.od.nih.gov/

LanguaL™. (n.d.). *LanguaL™—The International Framework for Food Description*. https://www.langual.org/

U.S. Department of Agriculture, Agricultural Research Service. (n.d.). *Dietary Supplement Ingredient Database (DSID)*. https://dietarysupplementdatabase.usda.nih.gov/

Köster, J., & Rahmann, S. (2012). Snakemake—a scalable bioinformatics workflow engine. *Bioinformatics*, 28(19), 2520–2522. https://doi.org/10.1093/bioinformatics/bts480
