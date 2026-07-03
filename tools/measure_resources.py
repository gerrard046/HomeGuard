#!/usr/bin/env python3
"""Ukur konsumsi sumber daya (CPU & RAM) HomeGuard selama pemindaian.

Melakukan sampling CPU dan RSS memori proses selama beberapa repetisi
pemindaian lab, lalu melaporkan rata-rata dan puncak --- angka pada Tabel
'Konsumsi Sumber Daya' dan Gambar sumber daya pada paper.

Memakai ``psutil`` bila tersedia; jika tidak, jatuh ke pembacaan
``/proc/self/stat`` dan ``/proc/self/status`` (khusus Linux).

    python tools/measure_resources.py --targets loopback --repeat 5
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from homeguard import HomeGuardScanner  # noqa: E402
from tools._labtargets import resolve_targets, all_ports  # noqa: E402


class _Sampler(threading.Thread):
    """Sampling CPU% dan RAM(MB) proses ini pada interval tetap."""

    def __init__(self, interval: float = 0.1):
        super().__init__(daemon=True)
        self.interval = interval
        self.cpu = []
        self.ram = []
        self._stopev = threading.Event()
        try:
            import psutil
            self._proc = psutil.Process()
            self._proc.cpu_percent(None)  # priming
            self._psutil = True
        except Exception:  # noqa: BLE001
            self._psutil = False

    def _sample_fallback(self):
        # RSS via /proc/self/status (Linux).
        ram_mb = 0.0
        try:
            with open("/proc/self/status") as fh:
                for line in fh:
                    if line.startswith("VmRSS:"):
                        ram_mb = int(line.split()[1]) / 1024.0
                        break
        except OSError:
            pass
        return None, ram_mb

    def run(self):
        while not self._stopev.is_set():
            if self._psutil:
                self.cpu.append(self._proc.cpu_percent(None))
                self.ram.append(self._proc.memory_info().rss / (1024 * 1024))
            else:
                _, ram = self._sample_fallback()
                self.ram.append(ram)
            time.sleep(self.interval)

    def stop(self):
        self._stopev.set()
        self.join(timeout=2)


def main() -> int:
    ap = argparse.ArgumentParser(description="Konsumsi sumber daya pemindaian.")
    ap.add_argument("--targets", choices=["loopback", "vm"], default="loopback")
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--timeout", type=float, default=0.5)
    ap.add_argument("--json", help="tulis hasil ke berkas JSON")
    args = ap.parse_args()

    targets = resolve_targets(args.targets, include_control=True)
    ports = all_ports(args.targets)
    scanner = HomeGuardScanner(ports=ports, timeout=args.timeout)

    sampler = _Sampler()
    sampler.start()
    for _ in range(args.repeat):
        for t in targets:
            scanner.scan_host(t["ip"])
    time.sleep(0.2)
    sampler.stop()

    cpu = sampler.cpu
    ram = sampler.ram
    hasil = {
        "mode": args.targets,
        "sampler": "psutil" if sampler._psutil else "proc-fallback",
        "cpu_rata_rata_persen": round(sum(cpu) / len(cpu), 2) if cpu else None,
        "cpu_puncak_persen": round(max(cpu), 2) if cpu else None,
        "ram_rata_rata_mb": round(sum(ram) / len(ram), 2) if ram else None,
        "ram_puncak_mb": round(max(ram), 2) if ram else None,
        "jumlah_sampel": len(ram),
    }
    if not cpu:
        hasil["_catatan_cpu"] = ("psutil tidak tersedia; CPU% tidak terukur. "
                                 "Pasang psutil untuk metrik CPU.")
    print("=== Konsumsi Sumber Daya ===")
    for k, v in hasil.items():
        print(f"  {k:<24}: {v}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(hasil, fh, indent=2, ensure_ascii=False)
        print(f"\n[+] Hasil ditulis ke {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
