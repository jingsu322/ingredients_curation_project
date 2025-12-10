# Project Lifecycle & Compliance Plan

## 1. Purpose and Scope

This project curates **ingredient-centric** information for dietary supplements and related ingredient products. The central question is simple to state yet rich in practice: *given an ingredient (including synonyms), which products contain it, and which companies market those products?* We operationalize this through three lightweight use cases:

- **UC-1 (Ingredient → Products):** A curated view listing products that contain the specified ingredient, including dosage/units and links.
- **UC-2 (Ingredient → Companies):** A company/brand summary derived from the product view.
- **UC-3 (Quality & Coverage):** A small, honest report on coverage, parsing success, and cross-source consistency.

We keep the scope intentionally modest so a **single person** can deliver an end-to-end, reproducible pipeline. All artifacts and documentation live in a public GitHub repository (or exported Zip) with small **sample data** only; large or restricted data are not redistributed.

**Data sources (samples only):**

- **DSLD** (on-market, 2023–2025 subset).
- **Amazon** (public product pages; tiny, rate-limited samples).
- **Knowde** (ingredient marketplace pages; INCI, functions, compliance).
- **Internal leads** (scraped from the organization’s own domain; shared as a small de-identified subset).

------

## 2. Lifecycle Model and Project Flow

We align with well-known curation lifecycles (USGS Science Data Lifecycle; DCC Curation Lifecycle) and adapt them to a pragmatic, automation-friendly pipeline (USGS, n.d.; Higgins, 2008). The flow is implemented as **Snakemake** rules (with optional Make targets) and executed in a pinned Python environment (Mölder et al., 2021).

### 2.1 Plan

- Define the **use cases** (UC-1/UC-2/UC-3) and the **target ingredient set** in `workflow/targets.txt`.
- Establish an **abstract schema** that spans sources: `Ingredient`, `Product`, `Company`, and relationships like `USES` and `MARKETS`.
- Produce an initial **codebook** describing fields, semantics, and examples (`docs/codebook.csv`).
- Choose identifier strategy: keep **source IDs** (e.g., `asin`, `upcSku`, URLs) and assign internal **UUIDv7** or **hashes** for integrated records.

This stage ensures shared terminology and explicit boundaries. It also sets acceptance criteria (e.g., “we can regenerate UC-1/UC-2 tables from raw samples with one command”).

### 2.2 Acquire

- Use existing sample files under `data/raw/` (DSLD, Amazon, Knowde, Internal).
- Track provenance in `provenance/source_manifest.csv`: URL, retrieval timestamp, HTTP status, content hash, and extractor name.
- Never bulk-redistribute page content. For classroom reproducibility, we provide **tiny samples** plus transparent **instructions** to regenerate locally (respecting ToS and robots).

Acquisition is deliberately conservative: we do just enough to prove the workflow and quality methods without creating legal or operational risk.

### 2.3 Process (Profile, Parse, Normalize)

- **Profile:** generate lightweight summaries (`reports/profiling.csv`): missingness, unique keys, value ranges.
- **Parse & normalize:**
  - Ingredients: split/trim; map via **synonyms** (`rules/synonyms.csv`).
  - Units: normalize to **canonical mass in mg** where applicable (`rules/units.csv`); do **not** force conversions for `IU` unless an ingredient-specific mapping is explicitly provided.
  - Serving and package fields: standardize forms (Capsule/Softgel/Tablet) and counts.
- Persist intermediate data in `data/interim/`.

Some records will fail parsing. We treat those failures as first-class outputs (`logs/parse_failures.csv`) so they can be audited and improved later.

### 2.4 Integrate (Model, Link, Disambiguate)

- Use **DSLD/INCI** names as anchors where possible.
- Merge sources into a single integrated table, preserving **source IDs** and links.
- Perform **brand → company** disambiguation using a minimal whitelist (`curation/company_alias.csv`) plus simple heuristics (e.g., domain cues).
- Assign or compute **stable identifiers** for integrated entities (e.g., UUIDv7; or a hash over normalized name + source ID).

Integration focuses on transparency over perfection: ambiguous matches are flagged with confidence notes and can be reviewed.

### 2.5 Validate (Schema, Quality, Consistency)

- Enforce a **JSON Schema** for curated outputs (`metadata/dataset.schema.json`).
- Emit a concise **quality report** (`reports/quality_report.csv`) with three indicators:
  1. **Coverage** (how many targets appear across sources),
  2. **Parsing success rate**, and
  3. **Cross-source consistency** (e.g., ingredient presence or obvious unit conflicts).

Validation is small but visible. It proves we can measure—and communicate—quality.

### 2.6 Preserve (Versioning, Formats, Metadata)

- Store curated results in durable, open formats (CSV/Parquet and, if helpful, SQLite) under `data/curated/`.
- Record **checksums** (`provenance/checksums.txt`) and environment details for each run.
- Author **DataCite metadata** (`metadata/datacite.json`) and embed a `schema.org/Dataset` JSON-LD snippet in the README (DataCite Metadata Working Group, 2021; Schema.org, n.d.).

Preservation here means anyone can pick up the repo, install the environment, and regenerate the same outputs—months from now.

### 2.7 Publish & Disseminate

- Publish the repository (or Zip) with a clear **“Reproduce in 5 steps”** section at the top of the README.
- Optionally create a tagged release. If external archiving is desired, export a release package with metadata and checksums.
- Keep the narrative report short and precise; the **artifacts** do the heavy lifting.

------

## 3. Ethical, Legal, and Policy Considerations

### 3.1 Website Terms and Robots

- We respect **Terms of Service** and the **Robots Exclusion Protocol** (RFC 9309) by default (Koster & Pebesma, 2022).
- Classroom deliverables contain **tiny** samples only. The repository includes **code and manifests** to reproduce acquisition in a compliant, rate-limited manner, rather than redistributing large volumes of source content.
- For copyrighted pages, we extract and store **factual fields** needed for curation (e.g., ingredient names, amounts, INCI). We do **not** republish full page content, images, or sensitive assets.

### 3.2 Privacy and PII

- The project curates **product/ingredient** data exclusively. No personal data are collected.
- Internal leads are de-identified and limited to company-level signals (e.g., domain), ensuring that no personally identifiable information is processed or shared.

### 3.3 Licensing and Reuse

- Source content remains under its original license/terms. We redistribute only **derived, factual summaries** and small samples for teaching.
- Project code and derived datasets will be released under a permissive open-source license (e.g., **MIT** or **Apache-2.0**). The README will carry a clear disclaimer: not medical advice; no warranties; users must independently verify suitability.

### 3.4 Reproducibility and Transparency

- Every step is automated or documented for **deterministic** reproduction (Snakemake DAG + pinned Python environment).
- We capture **run-time provenance**: timestamps, git commit, parameters, input and output paths, and file hashes.
- When conversions are domain-sensitive (e.g., `IU` → mass), we prefer conservative defaults: *do nothing automatically* and provide a plug-in table if evidence-based factors are later justified.

------

## 4. Minimal Success Criteria

- One-command regeneration of UC-1/UC-2 outputs from raw samples.
- A visible, machine-checked **schema validation** step.
- A small yet honest **quality report** with coverage and parsing rates.
- End-to-end provenance (hashes, parameters, commit).
- Clear **metadata** (DataCite + schema.org) and a 5-step reproduction guide.

------

## 5. Risks and Mitigations

- **Heterogeneity across sources.** *Mitigation:* a thin abstraction layer (codebook + JSON Schema), synonym tables, and unit normalization rules.
- **Ambiguous brand/company mapping.** *Mitigation:* whitelist mapping, domain-based cues, and explicit **uncertainty flags**.
- **Terms-of-Service constraints.** *Mitigation:* samples only, transparent manifests, no redistribution of bulk content, and throttle limits in acquisition scripts.
- **Single-person delivery.** *Mitigation:* keep the pipeline narrow, prefer simple rules over complex ML, and prioritize artifacts that maximize rubric points (workflow automation, metadata, and reproducibility).

------

## 6. Repository Contract (What lives where)

- **`data/raw/`** – tiny samples only; instructions to regenerate.
- **`data/interim/`** – normalized/intermediate artifacts.
- **`data/curated/`** – final views for UC-1/UC-2 (+ CSV/Parquet/SQLite).
- **`docs/`** – this plan, the codebook, the QA notes, and the project report.
- **`metadata/`** – `datacite.json` and `dataset.schema.json`.
- **`provenance/`** – run logs, manifests, and checksums.
- **`rules/`** – `synonyms.csv` and `units.csv`.
- **`workflow/`** – `targets.txt`, Snakemake config, and (optionally) Make targets.
- **`src/`** – modular Python code (`ingest/`, `preprocess/`, `integrate/`, `validate/`, `views/`, `utils/`).

------

## References

DataCite Metadata Working Group. (2021). *DataCite metadata schema documentation for the publication and citation of research data* (Version 4.4). DataCite. https://schema.datacite.org/

Higgins, S. (2008). The DCC Curation Lifecycle Model. *International Journal of Digital Curation, 3*(1), 134–140. https://doi.org/10.2218/ijdc.v3i1.48

Koster, M., & Pebesma, E. (2022). *Robots Exclusion Protocol* (RFC 9309). IETF. https://doi.org/10.17487/RFC9309

Mölder, F., Jablonski, K. P., Letcher, B., … & Köster, J. (2021). Sustainable data analysis with Snakemake. *F1000Research, 10*, 33. https://doi.org/10.12688/f1000research.29032.2

Schema.org. (n.d.). *Schema.org vocabulary*. Retrieved October 2025, from https://schema.org/

U.S. Geological Survey (USGS). (n.d.). *USGS Science Data Lifecycle*. Retrieved October 2025, from https://www.usgs.gov/