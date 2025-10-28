import argparse, json, csv
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    a = ap.parse_args()

    p = Path(a.inp)
    stats = {"input_file": p.as_posix(), "size_bytes": p.stat().st_size}
    # Minimal “profile”
    with open(a.inp, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            stats["top_level_keys"] = list(data)[:10] if isinstance(data, dict) else None
        except Exception as ex:
            stats["error"] = repr(ex)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sorted(stats.keys()))
        w.writeheader()
        w.writerow(stats)

if __name__ == "__main__":
    main()
