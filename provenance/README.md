# Provenance Contents

- `source_manifest.csv` — inventory of files discovered under `data/raw/**`.
- `checksums.txt` — SHA-256 checksums for key outputs to verify integrity.
- `runs/run_meta.json` — execution metadata (timestamp, config, environment).
- `ingest_stats_*.json` — per-source ingestion stats (files_seen, records_emitted, errors).

To verify a run: compare `checksums.txt` across machines, the values should match.
