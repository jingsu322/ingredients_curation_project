import argparse
from pathlib import Path
import pyarrow.parquet as pq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    a = ap.parse_args()

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    tbl = pq.read_table(a.inp)
    pq.write_table(tbl, a.out, compression="snappy")

if __name__ == "__main__":
    main()
