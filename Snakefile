# Run: uv run snakemake -j 4
configfile: "workflow/config.yaml"

DSLD_PQ     = config["outputs"]["dsld_parquet"]
AMAZON_PQ   = config["outputs"]["amazon_parquet"]
KNOWDE_PQ   = config["outputs"]["knowde_parquet"]
INTERNAL_PQ = config["outputs"]["internal_parquet"]
HARMONIZED  = config["outputs"]["harmonized"]
INTEGRATED  = config["outputs"]["integrated"]
UC1         = config["outputs"]["uc1_path"]
UC2         = config["outputs"]["uc2_path"]
QUALITY     = config["outputs"]["quality_report_path"]
MANIFEST    = config["outputs"]["manifest_path"]
CHECKSUMS   = config["outputs"]["checksums_path"]
RUNMETA     = config["outputs"]["runmeta_path"]

rule all:
    input:
        MANIFEST,
        DSLD_PQ, AMAZON_PQ, KNOWDE_PQ, INTERNAL_PQ,
        HARMONIZED, INTEGRATED,
        QUALITY, UC1, UC2,
        CHECKSUMS, RUNMETA

rule manifest_raw:
    input:
        raw_root = config["inputs"]["raw_root"]     # ← remove directory()
    output:
        MANIFEST
    shell:
        "uv run python -m src.utils.provenance manifest --dir {input.raw_root} --out {output}"

rule aggregate_dsld:
    input:
        in_dir = config["inputs"]["dsld_dir"]       # ← remove directory()
    output:
        DSLD_PQ
    params:
        bs = config["params"]["batch_size"],
        on_market = " --only_on_market" if config["params"].get("only_on_market", False) else ""
    shell:
        "uv run python -m src.preprocess.aggregate_dir --src dsld --in_dir {input.in_dir} --out {output} --batch_size {params.bs}{params.on_market}"

rule aggregate_amazon:
    input:
        in_dir = config["inputs"]["amazon_dir"]
    output:
        AMAZON_PQ
    params:
        bs = config["params"]["batch_size"]
    shell:
        "uv run python -m src.preprocess.aggregate_dir --src amazon --in_dir {input.in_dir} --out {output} --batch_size {params.bs}"

rule aggregate_knowde:
    input:
        in_dir = config["inputs"]["knowde_dir"]
    output:
        KNOWDE_PQ
    params:
        bs = config["params"]["batch_size"]
    shell:
        "uv run python -m src.preprocess.aggregate_dir --src knowde --in_dir {input.in_dir} --out {output} --batch_size {params.bs}"

rule aggregate_internal:
    input:
        in_dir = config["inputs"]["internal_dir"]
    output:
        INTERNAL_PQ
    params:
        bs = config["params"]["batch_size"]
    shell:
        "uv run python -m src.preprocess.aggregate_dir --src internal --in_dir {input.in_dir} --out {output} --batch_size {params.bs}"



# ------------------ Downstream pipeline (stubs you will replace) -----------
rule harmonize:
    input:
        DSLD_PQ, AMAZON_PQ, KNOWDE_PQ, INTERNAL_PQ,
        syn = config["params"]["synonyms_file"],
        units = config["params"]["units_file"]
    output:
        HARMONIZED
    shell:
        ("uv run python -m src.preprocess.harmonize "
         f"--dsld {input[0]} --amazon {input[1]} --knowde {input[2]} --internal {input[3]} "
         f"--syn {input.syn} --units {input.units} --out {output}")

rule integrate:
    input:
        HARMONIZED
    output:
        INTEGRATED
    shell:
        "uv run python -m src.integrate.merge --in {input} --out {output}"

rule validate_curated:
    input:
        curated = INTEGRATED,
        schema  = "metadata/dataset.schema.json"
    output:
        QUALITY
    shell:
        "uv run python -m src.validate.checks --in {input.curated} --schema {input.schema} --out {output}"

rule export_views:
    input:
        curated = INTEGRATED,
        targets = config["params"]["targets_file"]
    output:
        uc1 = UC1,
        uc2 = UC2
    shell:
        "uv run python -m src.views.export --in {input.curated} --targets {input.targets} --uc1 {output.uc1} --uc2 {output.uc2}"

rule run_meta:
    input:
        cfg = "workflow/config.yaml"
    output:
        RUNMETA
    shell:
        "uv run python -m src.utils.provenance runmeta --config {input.cfg} --out {output}"

rule checksums:
    input:
        QUALITY, UC1, UC2
    output:
        CHECKSUMS
    shell:
        "uv run python -m src.utils.provenance checksums --out {output} {input}"
