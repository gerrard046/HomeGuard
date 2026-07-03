#!/usr/bin/env python3
"""Ukur akurasi deteksi port HomeGuard terhadap ground truth lab.

Menghasilkan metrik TP/FP/FN, precision, recall, dan F1-score per perangkat
maupun total --- angka yang dilaporkan pada Tabel 'Metrik Akurasi Deteksi
Port per Perangkat' dan Gambar metrik pada paper. Karena membandingkan
port terdeteksi vs ground truth (lab/ground_truth.json), hasilnya dapat
direproduksi siapa pun.

Prasyarat: nyalakan lab lebih dulu (lab/run_lab.py untuk loopback, atau
mock_iot_device.py pada tiap VM).

    python tools/measure_detection.py --targets loopback
    python tools/measure_detection.py --targets vm --json hasil_deteksi.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from homeguard import HomeGuardScanner  # noqa: E402
from tools._labtargets import resolve_targets, all_ports  # noqa: E402


def prf(tp: int, fp: int, fn: int) -> tuple:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) else 0.0)
    return precision, recall, f1


def main() -> int:
    ap = argparse.ArgumentParser(description="Metrik akurasi deteksi port.")
    ap.add_argument("--targets", choices=["loopback", "vm"], default="loopback")
    ap.add_argument("--timeout", type=float, default=0.5)
    ap.add_argument("--json", help="tulis hasil ke berkas JSON")
    args = ap.parse_args()

    targets = resolve_targets(args.targets, include_control=True)
    ports = all_ports(args.targets)
    scanner = HomeGuardScanner(ports=ports, timeout=args.timeout)

    rows = []
    tot_tp = tot_fp = tot_fn = 0
    dev_tp = dev_fp = dev_fn = 0  # metrik tingkat-perangkat (host up/down)

    print(f"{'Perangkat':<16}{'TP':>4}{'FP':>4}{'FN':>4}{'P':>8}{'R':>8}{'F1':>8}")
    print("-" * 56)
    for t in targets:
        host = scanner.scan_host(t["ip"])
        detected = {p["port"] for p in host["open_ports"]}
        expected = set(t["ports"])

        tp = len(detected & expected)
        fp = len(detected - expected)
        fn = len(expected - detected)
        tot_tp += tp
        tot_fp += fp
        tot_fn += fn

        # Tingkat-perangkat: perangkat "terdeteksi" bila ada >=1 port terbuka.
        is_device = len(expected) > 0
        found = len(detected) > 0
        if is_device and found:
            dev_tp += 1
        elif is_device and not found:
            dev_fn += 1
        elif (not is_device) and found:
            dev_fp += 1

        p, r, f1 = prf(tp, fp, fn)
        rows.append({"name": t["name"], "ip": t["ip"], "tp": tp, "fp": fp,
                     "fn": fn, "precision": round(p, 4), "recall": round(r, 4),
                     "f1": round(f1, 4)})
        print(f"{t['name']:<16}{tp:>4}{fp:>4}{fn:>4}{p:>8.4f}{r:>8.4f}{f1:>8.4f}")

    p, r, f1 = prf(tot_tp, tot_fp, tot_fn)
    dp, dr, df1 = prf(dev_tp, dev_fp, dev_fn)
    print("-" * 56)
    print(f"{'TOTAL (port)':<16}{tot_tp:>4}{tot_fp:>4}{tot_fn:>4}"
          f"{p:>8.4f}{r:>8.4f}{f1:>8.4f}")
    print(f"\nTingkat perangkat: precision={dp:.4f} recall={dr:.4f} F1={df1:.4f}"
          f"  (TP={dev_tp} FP={dev_fp} FN={dev_fn})")

    hasil = {
        "mode": args.targets,
        "per_perangkat": rows,
        "total_port": {"tp": tot_tp, "fp": tot_fp, "fn": tot_fn,
                       "precision": round(p, 4), "recall": round(r, 4),
                       "f1": round(f1, 4)},
        "tingkat_perangkat": {"tp": dev_tp, "fp": dev_fp, "fn": dev_fn,
                              "precision": round(dp, 4), "recall": round(dr, 4),
                              "f1": round(df1, 4)},
    }
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(hasil, fh, indent=2, ensure_ascii=False)
        print(f"\n[+] Hasil ditulis ke {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
