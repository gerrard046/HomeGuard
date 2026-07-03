#!/usr/bin/env python3
"""Ukur kinerja waktu pemindaian HomeGuard (mean, std, per-host).

Menjalankan pemindaian seluruh target lab sebanyak N repetisi dan melaporkan
rata-rata total, standar deviasi, waktu per host, tercepat, dan terlama ---
angka pada Tabel 'Kinerja Waktu Pemindaian' dan Gambar kecepatan pada paper.

    python tools/measure_speed.py --targets loopback --repeat 5
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from homeguard import HomeGuardScanner  # noqa: E402
from tools._labtargets import resolve_targets, all_ports  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Kinerja waktu pemindaian.")
    ap.add_argument("--targets", choices=["loopback", "vm"], default="loopback")
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--timeout", type=float, default=0.5)
    ap.add_argument("--json", help="tulis hasil ke berkas JSON")
    args = ap.parse_args()

    targets = resolve_targets(args.targets, include_control=True)
    ports = all_ports(args.targets)
    scanner = HomeGuardScanner(ports=ports, timeout=args.timeout)
    n_host = len(targets)

    durasi = []
    for i in range(args.repeat):
        t0 = time.perf_counter()
        for t in targets:
            scanner.scan_host(t["ip"])
        dt = time.perf_counter() - t0
        durasi.append(dt)
        print(f"  repetisi {i + 1}: {dt:.2f} detik ({dt / n_host:.2f} d/host)")

    mean = statistics.mean(durasi)
    std = statistics.pstdev(durasi)
    hasil = {
        "mode": args.targets,
        "repetisi": args.repeat,
        "jumlah_host": n_host,
        "rata_rata_total_detik": round(mean, 2),
        "standar_deviasi_detik": round(std, 2),
        "waktu_per_host_detik": round(mean / n_host, 2),
        "tercepat_detik": round(min(durasi), 2),
        "terlama_detik": round(max(durasi), 2),
    }
    print("\n=== Ringkasan ===")
    for k, v in hasil.items():
        print(f"  {k:<26}: {v}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(hasil, fh, indent=2, ensure_ascii=False)
        print(f"\n[+] Hasil ditulis ke {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
