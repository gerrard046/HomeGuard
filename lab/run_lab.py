#!/usr/bin/env python3
"""Nyalakan SELURUH lab virtual HomeGuard pada satu mesin Linux.

Membaca ``lab/ground_truth.json`` dan menyalakan kelima perangkat IoT
tiruan sekaligus pada alamat loopback (127.0.0.20, .30, .40, .50, .60).
Pada Linux, seluruh 127.0.0.0/8 adalah loopback sehingga tiap "perangkat"
memperoleh IP berbeda tanpa konfigurasi jaringan tambahan --- memungkinkan
reproduksi penuh pengujian lab pada paper tanpa VirtualBox.

    python lab/run_lab.py            # nyalakan lab, biarkan berjalan
    # di terminal lain:
    python tools/measure_detection.py --targets loopback
    python tools/measure_speed.py    --targets loopback
    python tools/measure_resources.py --targets loopback

Untuk lab VM sungguhan, jalankan ``lab/mock_iot_device.py`` pada tiap VM
dengan IP 192.168.56.x sesuai ground_truth.json.
"""

from __future__ import annotations

import json
import os
import threading
import time

from mock_iot_device import start_device

LAB_DIR = os.path.dirname(os.path.abspath(__file__))
GROUND_TRUTH = os.path.join(LAB_DIR, "ground_truth.json")


def main() -> int:
    with open(GROUND_TRUTH, encoding="utf-8") as fh:
        gt = json.load(fh)

    stop = threading.Event()
    for dev in gt["devices"]:
        ip = dev["loopback_ip"]
        start_device(ip, dev["ports"], stop)
        print(f"[*] {dev['name']:<16} {ip:<14} port {dev['ports']}")

    print("\n[*] Lab virtual aktif (loopback). Tekan Ctrl+C untuk berhenti.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop.set()
        print("\n[*] Lab dihentikan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
