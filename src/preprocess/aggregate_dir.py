# -*- coding: utf-8 -*-
"""
Robust directory ingestion:
- supports .json / .jsonl / .ndjson / .jl / .json.gz / .gz
- supports top-level array JSON and NDJSON (one JSON per line)
- tolerant field extraction for amazon/knowde
- writes Parquet with all-string columns
- writes provenance stats to provenance/ingest_stats_<src>.json
"""

from __future__ import annotations
import argparse, json, os, gzip
from pathlib import Path
from typing import Dict, Any, Iterable, List, Optional

import pyarrow as pa
import pyarrow.parquet as pq

# ------------------ utils ------------------
FIELDS = [
    "source","source_path","source_record_id",
    "product_name","brand","company_name","link","on_market","entry_date","form",
    "serving_size","serving_unit","net_quantity","net_unit",
    "ingredients","other_ingredients","claims","statements"
]
SCHEMA = pa.schema([(k, pa.large_string()) for k in FIELDS])

def _to_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)

def _open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8") if str(path).lower().endswith((".gz",)) else open(path, "r", encoding="utf-8")

def _iter_records_from_file(path: Path) -> Iterable[Dict[str, Any]]:
    # Try: whole-file JSON -> list -> NDJSON lines
    try:
        with _open_text(path) as f:
            txt = f.read()
        try:
            obj = json.loads(txt)
            if isinstance(obj, dict):
                yield obj
                return
            if isinstance(obj, list):
                for it in obj:
                    if isinstance(it, dict):
                        yield it
                return
        except Exception:
            pass
        # NDJSON line-by-line
        for ln in txt.splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
                if isinstance(o, dict):
                    yield o
            except Exception:
                continue
    except Exception:
        return

def _iter_json_files(root: Path) -> Iterable[Path]:
    exts = (".json",".jsonl",".ndjson",".jl",".json.gz",".gz")
    for r,_,fs in os.walk(root):
        for f in fs:
            if f.lower().endswith(exts):
                yield Path(r)/f

# --------------- tolerant getters ---------------
def get_first(obj: Dict[str, Any], *candidates, default=""):
    for k in candidates:
        if k in obj and obj[k] not in (None, ""):
            return obj[k]
    # try lowercase keys
    lower = {str(k).lower(): v for k, v in obj.items()}
    for k in candidates:
        kk = str(k).lower()
        if kk in lower and lower[kk] not in (None, ""):
            return lower[kk]
    return default

# ---------------- mappers ----------------
def map_dsld(obj: Dict[str, Any], only_on_market: bool = True) -> Optional[Dict[str, Any]]:
    if not isinstance(obj, dict):
        return None
    off_market = obj.get("offMarket")
    if only_on_market and off_market in (1, True, "1", "true"):
        return None

    ing_names: List[str] = []
    for row in obj.get("ingredientRows", []) or []:
        nm = (row or {}).get("name")
        if nm: ing_names.append(str(nm))
        for nested in (row or {}).get("nestedRows", []) or []:
            nname = (nested or {}).get("name")
            if nname: ing_names.append(str(nname))

    other_ings: List[str] = []
    oi = (obj.get("otheringredients") or {}).get("ingredients") or []
    for it in oi:
        nm = (it or {}).get("name")
        if nm: other_ings.append(str(nm))

    serving_size, serving_unit = None, None
    sv = (obj.get("servingSizes") or [])
    if sv:
        s0 = sv[0] or {}
        serving_size = s0.get("minQuantity") or s0.get("quantity")
        serving_unit = s0.get("unit")

    net_qty, net_unit = None, None
    nc = (obj.get("netContents") or [])
    if nc:
        n0 = nc[0] or {}
        net_qty = n0.get("quantity")
        net_unit = n0.get("unit")

    return {
        "source": "DSLD",
        "source_path": obj.get("_file",""),
        "source_record_id": obj.get("upcSku") or obj.get("dsldId") or "",
        "product_name": obj.get("fullName") or "",
        "brand": obj.get("brandName") or "",
        "company_name": obj.get("manufacturerName") or "",
        "link": "",
        "on_market": 0 if off_market in (1, True, "1", "true") else 1,
        "entry_date": obj.get("entryDate") or "",
        "form": (obj.get("physicalState") or {}).get("langualCodeDescription") or "",
        "serving_size": serving_size,
        "serving_unit": serving_unit,
        "net_quantity": net_qty,
        "net_unit": net_unit,
        "ingredients": ", ".join(ing_names) if ing_names else "",
        "other_ingredients": ", ".join(other_ings) if other_ings else "",
        "claims": "; ".join([(c or {}).get("langualCodeDescription","") for c in (obj.get("claims") or []) if (c or {}).get("langualCodeDescription")]) or "",
        "statements": "; ".join([(s or {}).get("notes","") for s in (obj.get("statements") or []) if (s or {}).get("notes")]) or "",
    }

def map_amazon(obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(obj, dict):
        return None

    # basic fields
    asin = obj.get("asin") or obj.get("ASIN") or obj.get("id") or ""
    product_name = obj.get("product_name") or obj.get("title") or obj.get("name") or ""
    brand = obj.get("brand") or obj.get("byline") or obj.get("brand_name") or ""
    link = obj.get("product_url") or obj.get("url") or obj.get("link") or obj.get("page_url") or ""
    ingredients = obj.get("ingredients") or obj.get("ingredient_text") or ""

    # serving/unit from unit_count like "120.00 Count"
    serving_size, serving_unit = None, None
    uc = obj.get("unit_count") or obj.get("count") or ""
    if isinstance(uc, str) and uc.strip():
        # split by space, first token is number, rest join as unit
        parts = uc.replace(",", " ").split()
        try:
            serving_size = float(parts[0])
        except Exception:
            serving_size = None
        serving_unit = " ".join(parts[1:]) if len(parts) > 1 else "count"

    # claims from about_this_item (list or str)
    claims = "; ".join(obj.get("about_this_item") or []) if isinstance(obj.get("about_this_item"), list) else (obj.get("about_this_item") or "")

    rec = {
        "source": "Amazon",
        "source_path": obj.get("_file",""),
        "source_record_id": asin,
        "product_name": product_name,
        "brand": brand,
        "company_name": obj.get("company_name") or obj.get("manufacturer") or obj.get("seller") or obj.get("vendor") or "",
        "link": link,
        "on_market": 1,
        "entry_date": obj.get("updated_at") or obj.get("crawl_ts") or obj.get("timestamp") or obj.get("date") or "",
        "form": obj.get("item_form") or obj.get("form") or "",
        "serving_size": serving_size,
        "serving_unit": serving_unit,
        "net_quantity": obj.get("size") or obj.get("unit_price") or "",
        "net_unit": obj.get("count_unit") or "",
        "ingredients": ingredients,
        "other_ingredients": obj.get("other_ingredients") or "",
        "claims": claims,
        "statements": obj.get("warnings") or "",
    }

    # keep record if it has at least a name (or ingredients) or ASIN
    if not any([rec["product_name"], rec["ingredients"], rec["source_record_id"]]):
        return None
    return rec


def map_knowde(obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(obj, dict):
        return None
    details = obj.get("product_details") or obj.get("details") or {}
    rec = {
        "source": "Knowde",
        "source_path": obj.get("_file",""),
        "source_record_id": obj.get("slug") or obj.get("id") or "",
        "product_name": obj.get("product_name") or obj.get("title") or obj.get("name") or "",
        "brand": obj.get("brand") or obj.get("brand_name") or "",
        "company_name": obj.get("company_name") or obj.get("supplier") or "",
        "link": obj.get("link") or obj.get("url") or obj.get("page_url") or "",
        "on_market": 1,
        "entry_date": obj.get("crawl_ts") or obj.get("timestamp") or obj.get("date") or "",
        "form": obj.get("form") or "",
        "serving_size": None,
        "serving_unit": None,
        "net_quantity": None,
        "net_unit": None,
        "ingredients": (details.get("Ingredient Name") or details.get("Ingredient") or details.get("Ingredients") or ""),
        "other_ingredients": "",
        "claims": details.get("Function") or "",
        "statements": details.get("Certifications & Compliance") or details.get("Certifications") or "",
    }
    if not any([rec["product_name"], rec["ingredients"], rec["source_record_id"]]):
        return None
    return rec


def map_internal(obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(obj, dict):
        return None
    # ingredients list → string
    ings = obj.get("ingredients") or []
    if isinstance(ings, list):
        ings = ", ".join(ings)

    rec = {
        "source": "Internal",
        "source_path": obj.get("_file",""),
        "source_record_id": obj.get("id") or obj.get("slug") or "",
        "product_name": obj.get("product_name") or obj.get("title") or obj.get("name") or "",
        "brand": obj.get("brand") or "",
        "company_name": obj.get("company_name") or obj.get("domain") or "",
        "link": obj.get("product_link") or obj.get("url") or "",
        "on_market": 1,
        "entry_date": obj.get("crawl_ts") or obj.get("timestamp") or obj.get("date") or "",
        "form": obj.get("form") or obj.get("product_type") or "",
        "serving_size": None,
        "serving_unit": None,
        "net_quantity": None,
        "net_unit": None,
        "ingredients": ings or "",
        "other_ingredients": "",
        "claims": obj.get("claims") or "",
        "statements": "",
    }
    # internal 允许只有 (name 或 ingredients 或 link) 也入库
    if not any([rec["product_name"], rec["ingredients"], rec["link"]]):
        return None
    return rec


MAPPERS = {"dsld": map_dsld, "amazon": map_amazon, "knowde": map_knowde, "internal": map_internal}

# ---------------- main ingest ----------------
def ingest_dir_to_parquet(src: str, in_dir: Path, out_path: Path, batch_size: int = 2000, only_on_market: bool = True):
    mapper = MAPPERS[src]
    out_path.parent.mkdir(parents=True, exist_ok=True)

    writer: Optional[pq.ParquetWriter] = None
    batch: List[dict] = []
    wrote_any = False

    stats = {"files_seen":0, "records_emitted":0, "files_with_records":0, "files_errors":0}

    for fp in _iter_json_files(in_dir):
        stats["files_seen"] += 1
        had_rec = False
        try:
            for obj in _iter_records_from_file(fp):
                if isinstance(obj, dict):
                    obj["_file"] = str(fp.as_posix())
                rec = mapper(obj, only_on_market) if src == "dsld" else mapper(obj)
                if rec:
                    # coerce to strings for schema
                    safe = {k: _to_str(rec.get(k)) for k in FIELDS}
                    batch.append(safe)
                    stats["records_emitted"] += 1
                    had_rec = True
                if len(batch) >= batch_size:
                    table = pa.Table.from_pylist(batch, schema=SCHEMA)
                    if writer is None:
                        writer = pq.ParquetWriter(out_path, table.schema, compression="snappy")
                    writer.write_table(table)
                    batch.clear()
                    wrote_any = True
            if had_rec:
                stats["files_with_records"] += 1
        except Exception:
            stats["files_errors"] += 1
            continue

    if batch:
        table = pa.Table.from_pylist(batch, schema=SCHEMA)
        if writer is None:
            writer = pq.ParquetWriter(out_path, table.schema, compression="snappy")
        writer.write_table(table)
        wrote_any = True

    if writer is not None:
        writer.close()

    if not wrote_any:
        empty = pa.table({k: pa.array([], type=pa.large_string()) for k in FIELDS})
        pq.write_table(empty, out_path, compression="snappy")

    # write simple stats to provenance
    prov = Path("provenance") / f"ingest_stats_{src}.json"
    try:
        prov.parent.mkdir(parents=True, exist_ok=True)
        prov.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    except Exception:
        pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", choices=["dsld","amazon","knowde","internal"], required=True)
    ap.add_argument("--in_dir", type=Path, required=True)
    ap.add_argument("--out", dest="out_path", type=Path, required=True)
    ap.add_argument("--batch_size", type=int, default=2000)
    ap.add_argument("--only_on_market", action="store_true")
    args = ap.parse_args()

    ingest_dir_to_parquet(
        src=args.src,
        in_dir=args.in_dir,
        out_path=args.out_path,
        batch_size=args.batch_size,
        only_on_market=args.only_on_market
    )

if __name__ == "__main__":
    main()
