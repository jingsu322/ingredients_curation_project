# Use this Snakefile with:  uv run snakemake -j 4

configfile: "workflow/config.yaml"

# Build the list of final outputs from config
FINAL_UC1 = config["outputs"]["uc1_path"]
FINAL_UC2 = config["outputs"]["uc2_path"]
QUALITY   = config["outputs"]["quality_report_path"]
MANIFEST  = config["outputs"]["manifest_path"]
CHECKSUMS = config["outputs"]["checksums_path"]
RUNMETA   = "provenance/runs/run_meta.json"

rule all:
    input:
        MANIFEST,
        QUALITY,
        FINAL_UC1,
        FINAL_UC2,
        CHECKSUMS,
        RUNMETA

rule manifest_raw:
    """
    Create a machine-readable manifest of raw inputs with size, sha256, and mtime.
    This is transparency, not redistribution.
    """
    input:
        raw_dir = directory(config["inputs"]["raw_dir"])
    output:
        MANIFEST
    shell:
        "uv run python -m src.utils.provenance manifest --dir {input.raw_dir} --out {output}"

rule profile_dsld:
    """
    Lightweight profiling of DSLD sample (missingness, counts, ranges).
    """
    input:
        dsld = config["inputs"]["dsld"]
    output:
        "reports/profiling.csv"
    shell:
        "uv run python -m src.preprocess.profile --in {input.dsld} --out {output}"

rule harmonize:
    """
    Normalize ingredients and units into canonical shapes.
    """
    input:
        dsld   = config["inputs"]["dsld"],
        amazon = config["inputs"]["amazon"],
        knowde = config["inputs"]["knowde"],
        internal = config["inputs"]["internal"],
        synonyms = config["params"]["synonyms_file"],
        units    = config["params"]["units_file"]
    output:
        "data/interim/harmonized.parquet"
    shell:
        ("uv run python -m src.preprocess.harmonize "
         "--dsld {input.dsld} --amazon {input.amazon} --knowde {input.knowde} --internal {input.internal} "
         "--syn {input.synonyms} --units {input.units} --out {output}")

rule integrate:
    """
    Merge sources, anchor to DSLD/INCI where possible, and assign stable IDs.
    """
    input:
        "data/interim/harmonized.parquet"
    output:
        "data/interim/integrated.parquet"
    shell:
        "uv run python -m src.integrate.merge --in {input} --out {output}"

rule validate_curated:
    """
    Validate structure against JSON Schema and emit a compact quality report.
    """
    input:
        curated = "data/interim/integrated.parquet",
        schema  = "metadata/dataset.schema.json"
    output:
        QUALITY
    shell:
        "uv run python -m src.validate.checks --in {input.curated} --schema {input.schema} --out {output}"

rule export_views:
    """
    Export UC-1 (Ingredient→Products) and UC-2 (Ingredient→Companies).
    """
    input:
        curated = "data/interim/integrated.parquet",
        targets = config["params"]["targets_file"]
    output:
        uc1 = FINAL_UC1,
        uc2 = FINAL_UC2
    shell:
        "uv run python -m src.views.export --in {input.curated} --targets {input.targets} --uc1 {output.uc1} --uc2 {output.uc2}"

rule run_meta:
    """
    Save run metadata: timestamp, git commit, python version, and config digest.
    """
    input:
        cfg = "workflow/config.yaml"
    output:
        RUNMETA
    shell:
        "uv run python -m src.utils.provenance runmeta --config {input.cfg} --out {output}"

rule checksums:
    """
    Compute checksums for key deliverables (quality report and views).
    """
    input:
        QUALITY, FINAL_UC1, FINAL_UC2
    output:
        CHECKSUMS
    shell:
        "uv run python -m src.utils.provenance checksums --out {output} {input}"
