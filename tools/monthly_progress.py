"""月度对账进度（interim reconciliation progress）。

对 2027-03-01 正式对账的月度预演：下载最新 Nextstrain ncov open 元数据，
提取预测窗口（2026-09-01 起）内已首次出现的 RBD 突变，对照各注册系统
（v1/、v2/ 的 top-10 / top-50 提名清单）累计命中。只追加进度文件，
不修改任何注册内容。

真值口径与注册协议一致（同 0037 管道）：
  - date 长度 < 10 的行跳过（同口径）；
  - aaSubstitutions 列解析 S:<wt><pos><aa>，pos ∈ [331, 531]；
  - 窗口内每 (pos, aa) 取最早日期。

运行：python tools/monthly_progress.py --metadata <metadata.tsv.zst>
输出：reconciliation/progress_YYYY-MM-DD.json（追加式，每运行一个文件）
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
WINDOW_START = "2026-09-01"
WINDOW_END = "2027-02-28"
REGISTRATIONS = {
    "v1": ["predictions_v3_linear", "predictions_v3_lm"],
    "v2": ["predictions_bloom_esc", "predictions_bloom_full", "predictions_bloom_zeroshot",
           "predictions_v3_linear", "predictions_v3_lm"],
}


def rbd_first_in_window(meta_path: Path) -> tuple[dict[tuple[int, str], str], int]:
    first: dict[tuple[int, str], str] = {}
    n_rows = 0
    usecols = ["date", "aaSubstitutions"]
    for chunk in pd.read_csv(meta_path, sep="\t", usecols=usecols, dtype=str,
                             chunksize=1_000_000, compression="zstd",
                             on_bad_lines="skip"):
        d = chunk["date"].fillna("")
        mask = (d.str.len() >= 10) & (d >= WINDOW_START) & (d <= WINDOW_END)
        for date, subs in zip(chunk.loc[mask, "date"], chunk.loc[mask, "aaSubstitutions"]):
            n_rows += 1
            if not isinstance(subs, str):
                continue
            for m in subs.split(","):
                if m.startswith("S:"):
                    mut = m[2:]
                    if len(mut) >= 3 and mut[1:-1].isdigit():
                        pos = int(mut[1:-1])
                        if 331 <= pos <= 531:
                            key = (pos, mut[-1])
                            if key not in first or date < first[key]:
                                first[key] = date
    return first, n_rows


def score_registration(version: str, systems: list[str], first) -> list[dict]:
    out = []
    for name in systems:
        path = REPO / version / f"{name}.csv"
        if not path.exists():
            out.append({"file": f"{version}/{name}.csv", "missing": True})
            continue
        df = pd.read_csv(path)
        rec = {"file": f"{version}/{name}.csv", "missing": False}
        for k in (10, 50):
            nom = df[df[f"in_top{k}"] == 1]["mutation"].tolist()
            hits = []
            for mut in nom:
                pos, aa = int(mut[:-1]), mut[-1]
                if (pos, aa) in first:
                    hits.append({"mutation": mut, "first_date": first[(pos, aa)]})
            rec[f"nominations_top{k}"] = len(nom)
            rec[f"hits_top{k}"] = len(hits)
            rec[f"hit@{k}_so_far"] = round(len(hits) / k, 4)
            rec[f"hit_details_top{k}"] = hits
        out.append(rec)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", type=str, default="data/metadata.tsv.zst")
    args = ap.parse_args()
    t0 = time.perf_counter()

    meta_path = Path(args.metadata)
    first, n_rows = rbd_first_in_window(meta_path)
    print(f"窗口内扫描行 {n_rows}  首现 RBD 突变 {len(first)}")

    report = {
        "run_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "kind": "interim_progress",
        "window": {"start": WINDOW_START, "end": WINDOW_END},
        "metadata_file": meta_path.name,
        "rows_in_window": n_rows,
        "distinct_rbd_mutations_seen": len(first),
        "note": "月度进度快照；正式对账 2027-03-01 按注册协议重算，本文件不构成对账结果",
        "systems": {},
    }
    for version, systems in REGISTRATIONS.items():
        report["systems"][version] = score_registration(version, systems, first)
        for rec in report["systems"][version]:
            if not rec.get("missing"):
                print(f"{rec['file']:42s} hit@10={rec['hit@10_so_far']:.2f} "
                      f"({rec['hits_top10']}/10)  hit@50={rec['hit@50_so_far']:.3f} "
                      f"({rec['hits_top50']}/50)")

    out_dir = REPO / "reconciliation"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"progress_{time.strftime('%Y-%m-%d')}.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写出 {out_path.relative_to(REPO)}  耗时 {time.perf_counter() - t0:.0f}s")


if __name__ == "__main__":
    main()
