"""
Provenance helpers for manifests, checksums, and run metadata.

CLI:
  uv run python -m src.utils.provenance manifest --dir data/raw --out provenance/source_manifest.csv
  uv run python -m src.utils.provenance checksums --out provenance/checksums.txt reports/quality_report.csv data/curated/uc1_products.csv data/curated/uc2_companies.csv
  uv run python -m src.utils.provenance runmeta --config workflow/config.yaml --out provenance/runs/run_meta.json
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, platform, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

def sha256_of_file(p: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()

def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_manifest(dir_path: Path, out_csv: Path) -> None:
    rows = []
    for root, _, files in os.walk(dir_path):
        for name in sorted(files):
            p = Path(root) / name
            try:
                stat = p.stat()
                rows.append({
                    "path": str(p.as_posix()),
                    "size_bytes": stat.st_size,
                    "sha256": sha256_of_file(p),
                    "mtime_iso": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                })
            except Exception as ex:
                rows.append({
                    "path": str(p.as_posix()),
                    "size_bytes": "",
                    "sha256": "",
                    "mtime_iso": "",
                    "error": repr(ex)
                })
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "size_bytes", "sha256", "mtime_iso", "error"])
        w.writeheader()
        for r in rows:
            if "error" not in r: r["error"] = ""
            w.writerow(r)

def write_checksums(files: list[str], out_txt: Path) -> None:
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    with out_txt.open("w", encoding="utf-8") as f:
        for fp in files:
            p = Path(fp)
            if p.exists() and p.is_file():
                f.write(f"{sha256_of_file(p)}  {p.as_posix()}\n")
            else:
                f.write(f"MISS                     {p.as_posix()}\n")

def write_runmeta(config_path: Path, out_json: Path) -> None:
    meta = {
        "timestamp_utc": iso_now(),
        "git_commit": git_commit(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "argv": sys.argv,
        "config_path": str(config_path),
    }
    try:
        meta["config_sha256"] = sha256_of_file(config_path)
    except Exception:
        meta["config_sha256"] = ""
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_m = sub.add_parser("manifest", help="Write CSV manifest for a directory")
    ap_m.add_argument("--dir", required=True, type=Path)
    ap_m.add_argument("--out", required=True, type=Path)

    ap_c = sub.add_parser("checksums", help="Write checksums for listed files")
    ap_c.add_argument("--out", required=True, type=Path)
    ap_c.add_argument("files", nargs="+", help="Files to hash")

    ap_r = sub.add_parser("runmeta", help="Write run metadata JSON")
    ap_r.add_argument("--config", required=True, type=Path)
    ap_r.add_argument("--out", required=True, type=Path)

    args = ap.parse_args()
    if args.cmd == "manifest":
        write_manifest(args.dir, args.out)
    elif args.cmd == "checksums":
        write_checksums(args.files, args.out)
    elif args.cmd == "runmeta":
        write_runmeta(args.config, args.out)

if __name__ == "__main__":
    main()
