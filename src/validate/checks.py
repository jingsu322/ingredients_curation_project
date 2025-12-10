import argparse, json, csv
from pathlib import Path
import pyarrow.parquet as pq
import pandas as pd

def read_df(parquet_path: str) -> pd.DataFrame:
    tbl = pq.read_table(parquet_path)
    try:
        # Prefer the fast path; avoid extension string dtype conversion issues
        return tbl.to_pandas(strings_to_categorical=False)
    except Exception:
        # Fallback: convert via pure Python lists (slower but robust)
        return pd.DataFrame(tbl.to_pylist())

def nonempty_ratio(series: pd.Series) -> float:
    if series is None or series.size == 0:
        return 0.0
    s = series.astype(str).fillna("").str.strip()
    return float((s != "").mean())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--out", dest="out", required=True)
    a = ap.parse_args()

    df = read_df(a.inp).fillna("")

    # Ensure expected columns exist (avoid KeyErrors)
    for col in ["source","product_name","brand","ingredients","serving_size","serving_unit"]:
        if col not in df.columns:
            df[col] = ""

    # Load schema to check requireds (best-effort)
    required = []
    try:
        sch = json.loads(Path(a.schema).read_text(encoding="utf-8"))
        required = list(sch.get("required", []))
    except Exception:
        pass

    metrics = []
    metrics.append({"metric": "records_total", "value": int(len(df))})

    # Per-source counts
    if "source" in df.columns:
        vc = df["source"].astype(str).value_counts(dropna=False)
        for src, cnt in vc.items():
            metrics.append({"metric": f"records_source_{src}", "value": int(cnt)})

    # Required fields non-empty ratio
    for col in required:
        if col in df.columns:
            metrics.append({"metric": f"required_nonempty_ratio::{col}",
                            "value": round(nonempty_ratio(df[col]), 4)})

    # Parse-success proxies
    for col in ["ingredients", "serving_size", "serving_unit"]:
        if col in df.columns:
            metrics.append({"metric": f"parse_nonempty_ratio::{col}",
                            "value": round(nonempty_ratio(df[col]), 4)})

    # Cross-source consistency for (product_name,brand) on 'ingredients'
    needed = {"product_name","brand","ingredients","source"}
    if needed.issubset(df.columns):
        g = df.groupby(["product_name","brand"], dropna=False)
        multi = g.filter(lambda x: x["source"].astype(str).nunique() > 1)
        if len(multi):
            def consistent(sub):
                vals = sub["ingredients"].astype(str).fillna("").str.strip().unique()
                return int(len(vals) == 1)
            rate = multi.groupby(["product_name","brand"]).apply(consistent).mean()
            metrics.append({"metric":"cross_source_consistency_rate_on_ingredients",
                            "value": round(float(rate), 4)})
        else:
            metrics.append({"metric":"cross_source_consistency_rate_on_ingredients",
                            "value": "N/A"})

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["metric","value"])
        w.writeheader()
        for m in metrics:
            w.writerow(m)

if __name__ == "__main__":
    main()
