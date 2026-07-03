#!/usr/bin/env python3
"""Benchmark HomeGuard vs Nmap pada topologi lab yang sama.

Menjalankan HomeGuard (pemindai socket murni, tanpa root) dan Nmap
(``nmap -sT``, TCP connect, juga tanpa root) terhadap target lab yang
identik, lalu membandingkan precision/recall/F1 deteksi port serta waktu
total. Tujuannya menyediakan baseline kuantitatif terhadap perkakas mapan
--- menjawab kritik umum reviewer bahwa perbandingan hanya kualitatif.

Prasyarat: lab menyala (lab/run_lab.py atau VM) dan ``nmap`` terpasang.

    python tools/benchmark_nmap.py --targets loopback --json benchmark.json

Catatan: seluruh angka dihasilkan saat dijalankan; skrip ini TIDAK memuat
hasil tetap. Jalankan pada lab Anda untuk memperoleh angka yang dapat
Anda pertanggungjawabkan.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from homeguard import HomeGuardScanner  # noqa: E402
from tools._labtargets import resolve_targets, all_ports  # noqa: E402


def prf(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return round(p, 4), round(r, 4), round(f1, 4)


def run_homeguard(targets, ports, timeout):
    scanner = HomeGuardScanner(ports=ports, timeout=timeout)
    t0 = time.perf_counter()
    detected = {}
    for t in targets:
        host = scanner.scan_host(t["ip"])
        detected[t["ip"]] = {p["port"] for p in host["open_ports"]}
    return detected, time.perf_counter() - t0


def run_nmap(targets, ports):
    port_arg = ",".join(str(p) for p in ports)
    detected = {}
    t0 = time.perf_counter()
    for t in targets:
        try:
            out = subprocess.run(
                ["nmap", "-sT", "-Pn", "-p", port_arg, "-oG", "-", t["ip"]],
                capture_output=True, text=True, timeout=120,
            ).stdout
        except (subprocess.SubprocessError, OSError) as exc:
            print(f"  [!] nmap gagal untuk {t['ip']}: {exc}")
            out = ""
        open_ports = set()
        for m in re.finditer(r"(\d+)/open/", out):
            open_ports.add(int(m.group(1)))
        detected[t["ip"]] = open_ports
    return detected, time.perf_counter() - t0


def score(detected, targets):
    tp = fp = fn = 0
    for t in targets:
        exp = set(t["ports"])
        det = detected.get(t["ip"], set())
        tp += len(det & exp)
        fp += len(det - exp)
        fn += len(exp - det)
    p, r, f1 = prf(tp, fp, fn)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}


def main() -> int:
    ap = argparse.ArgumentParser(description="Benchmark HomeGuard vs Nmap.")
    ap.add_argument("--targets", choices=["loopback", "vm"], default="loopback")
    ap.add_argument("--timeout", type=float, default=0.5)
    ap.add_argument("--json", help="tulis hasil ke berkas JSON")
    args = ap.parse_args()

    targets = resolve_targets(args.targets, include_control=True)
    ports = all_ports(args.targets)

    print("[*] Menjalankan HomeGuard ...")
    hg_det, hg_time = run_homeguard(targets, ports, args.timeout)
    hg = score(hg_det, targets)
    hg["waktu_total_detik"] = round(hg_time, 2)

    result = {"mode": args.targets, "homeguard": hg}

    if shutil.which("nmap"):
        print("[*] Menjalankan Nmap (-sT -Pn) ...")
        nm_det, nm_time = run_nmap(targets, ports)
        nm = score(nm_det, targets)
        nm["waktu_total_detik"] = round(nm_time, 2)
        result["nmap"] = nm
    else:
        print("[!] nmap tidak terpasang; hanya melaporkan HomeGuard.")
        result["nmap"] = None

    print("\n=== Benchmark Deteksi Port ===")
    hdr = f"{'Alat':<12}{'TP':>4}{'FP':>4}{'FN':>4}{'P':>8}{'R':>8}{'F1':>8}{'Waktu(s)':>10}"
    print(hdr)
    print("-" * len(hdr))
    print(f"{'HomeGuard':<12}{hg['tp']:>4}{hg['fp']:>4}{hg['fn']:>4}"
          f"{hg['precision']:>8}{hg['recall']:>8}{hg['f1']:>8}"
          f"{hg['waktu_total_detik']:>10}")
    if result["nmap"]:
        nm = result["nmap"]
        print(f"{'Nmap':<12}{nm['tp']:>4}{nm['fp']:>4}{nm['fn']:>4}"
              f"{nm['precision']:>8}{nm['recall']:>8}{nm['f1']:>8}"
              f"{nm['waktu_total_detik']:>10}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        print(f"\n[+] Hasil ditulis ke {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
