# Ingredients Curation Project

This repository curates ingredient information across four sources (DSLD, Amazon, Knowde, internal leads) and produces:
- harmonized and integrated Parquet datasets,
- quality metrics,
- two deliverables for the use cases (UC-1 products, UC-2 companies).

## Quick start (5 steps)

1. **Clone and enter**
   ```bash
   git clone https://github.com/jingsu322/ingredients_curation_project
   cd ingredients_curation_project

2. **Install with uv**
   ```bash
   uv sync

3. **Place data**
- Put raw data under:
    ```
    data/raw/dsld_dataset/
    data/raw/amazon_dataset/
    data/raw/knowde_dataset/
    data/raw/internal_dataset/
- For full dataset (large), see [Box link](https://uofi.box.com/s/ac89dzikmob9eu00xr9zyetg8k24s1lz).

4. **Run the workflow**
   ```
   uv run snakemake -j 4 --rerun-incomplete --latency-wait 20
   

5. **Find outputs**
   ```
   data/interim/harmonized.parquet
    data/interim/integrated.parquet
    data/curated/uc1_products.csv
    data/curated/uc2_companies.csv
    reports/quality_report.csv
    provenance/{source_manifest.csv,checksums.txt,runs/run_meta.json}
   

## Workflow

### Preprocessing

- **harmonize**: harmonize data from different sources
- **integrate**: integrate data from different sources
- **curate**: curate data for use cases

### Quality

data/interim/harmonized.parquet
data/interim/integrated.parquet
data/curated/uc1_products.csv
data/curated/uc2_companies.csv
reports/quality_report.csv
provenance/{source_manifest.csv,checksums.txt,runs/run_meta.json}