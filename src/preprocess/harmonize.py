# import argparse, json
# from pathlib import Path

# def main():
#     ap = argparse.ArgumentParser()
#     ap.add_argument("--dsld", required=True)
#     ap.add_argument("--amazon", required=True)
#     ap.add_argument("--knowde", required=True)
#     ap.add_argument("--internal", required=True)
#     ap.add_argument("--syn", required=True)
#     ap.add_argument("--units", required=True)
#     ap.add_argument("--out", required=True)
#     a = ap.parse_args()

#     # Placeholder: simply write an empty parquet-like marker (CSV here if pyarrow not ready)
#     out = Path(a.out)
#     out.parent.mkdir(parents=True, exist_ok=True)
#     # Real code will normalize and save a dataframe; placeholder writes a JSON label
#     out.with_suffix(".json").write_text(
#         json.dumps({"msg": "harmonized placeholder", "inputs": [a.dsld, a.amazon, a.knowde, a.internal]}, indent=2),
#         encoding="utf-8"
#     )

# if __name__ == "__main__":
#     main()


import argparse
from pathlib import Path
import pyarrow.parquet as pq
import pyarrow as pa

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsld", required=True)
    ap.add_argument("--amazon", required=True)
    ap.add_argument("--knowde", required=True)
    ap.add_argument("--internal", required=True)
    ap.add_argument("--syn", required=True)
    ap.add_argument("--units", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    tables = []
    for fp in [a.dsld, a.amazon, a.knowde, a.internal]:
        if Path(fp).exists():
            tables.append(pq.read_table(fp))
    if tables:
        out_tbl = pa.concat_tables(tables, promote=True)
    else:
        out_tbl = pa.table({k: [] for k in [
            "source","source_path","source_record_id","product_name","brand","company_name","link","on_market","entry_date","form",
            "serving_size","serving_unit","net_quantity","net_unit","ingredients","other_ingredients","claims","statements"
        ]})
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(out_tbl, a.out, compression="snappy")

if __name__ == "__main__":
    main()
