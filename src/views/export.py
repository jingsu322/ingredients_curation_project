# import argparse, csv
# from pathlib import Path

# def main():
#     ap = argparse.ArgumentParser()
#     ap.add_argument("--in", dest="inp", required=True)
#     ap.add_argument("--targets", required=True)
#     ap.add_argument("--uc1", required=True)
#     ap.add_argument("--uc2", required=True)
#     a = ap.parse_args()

#     # Placeholder UC-1 / UC-2 CSVs
#     Path(a.uc1).parent.mkdir(parents=True, exist_ok=True)
#     with open(a.uc1, "w", newline="", encoding="utf-8") as f:
#         w = csv.DictWriter(f, fieldnames=["ingredient", "product_name", "brand", "link"])
#         w.writeheader()
#         w.writerow({"ingredient": "Vitamin D3", "product_name": "TBD", "brand": "TBD", "link": "TBD"})

#     with open(a.uc2, "w", newline="", encoding="utf-8") as f:
#         w = csv.DictWriter(f, fieldnames=["ingredient", "company_name", "brand_count"])
#         w.writeheader()
#         w.writerow({"ingredient": "Vitamin D3", "company_name": "TBD Co.", "brand_count": 1})

# if __name__ == "__main__":
#     main()

# src/views/export.py
import argparse, csv
from pathlib import Path
import pyarrow.parquet as pq
import pandas as pd

def read_df(parquet_path: str) -> pd.DataFrame:
    tbl = pq.read_table(parquet_path)
    try:
        return tbl.to_pandas(strings_to_categorical=False)
    except Exception:
        return pd.DataFrame(tbl.to_pylist())

def load_targets(p: Path) -> list[str]:
    lines = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines()]
    return [t for t in lines if t and not t.startswith("#")]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--targets", required=True)
    ap.add_argument("--uc1", required=True)
    ap.add_argument("--uc2", required=True)
    a = ap.parse_args()

    targets = load_targets(Path(a.targets))
    df = read_df(a.inp).fillna("")

    # Ensure expected columns
    for col in ["ingredients","product_name","brand","company_name","form","serving_size","serving_unit","link","source"]:
        if col not in df.columns:
            df[col] = ""

    df["_ingredients_lc"] = df["ingredients"].astype(str).str.lower()

    uc1_rows = []
    for t in targets:
        t_lc = t.lower()
        hit = df[df["_ingredients_lc"].str.contains(t_lc, na=False)]
        for _, r in hit.iterrows():
            uc1_rows.append({
                "ingredient": t,
                "product_name": r["product_name"],
                "brand": r["brand"],
                "company_name": r["company_name"],
                "form": r["form"],
                "serving_size": r["serving_size"],
                "serving_unit": r["serving_unit"],
                "link": r["link"],
                "source": r["source"],
            })

    Path(a.uc1).parent.mkdir(parents=True, exist_ok=True)
    with open(a.uc1, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "ingredient","product_name","brand","company_name","form",
            "serving_size","serving_unit","link","source"
        ])
        w.writeheader()
        w.writerows(uc1_rows)

    if uc1_rows:
        df1 = pd.DataFrame(uc1_rows)
        grp = df1.groupby(["ingredient","company_name"], dropna=False).agg(
            brand_count=("brand", "nunique"),
            product_count=("product_name","nunique")
        ).reset_index()
    else:
        grp = pd.DataFrame(columns=["ingredient","company_name","brand_count","product_count"])

    with open(a.uc2, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ingredient","company_name","brand_count","product_count"])
        w.writeheader()
        for _, row in grp.iterrows():
            w.writerow({
                "ingredient": row["ingredient"],
                "company_name": row["company_name"],
                "brand_count": int(row["brand_count"]) if row["brand_count"] != "" else 0,
                "product_count": int(row["product_count"]) if row["product_count"] != "" else 0,
            })

if __name__ == "__main__":
    main()
