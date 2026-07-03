"""Helper bersama: resolusi daftar target lab dari ground_truth.json.

Dipakai oleh skrip pengukuran di ``tools/`` agar semuanya membaca sumber
kebenaran (ground truth) yang sama. Mode target:

    loopback : gunakan 127.0.0.x (uji lokal satu mesin, lihat lab/run_lab.py)
    vm       : gunakan 192.168.56.x (lab VirtualBox sungguhan)
"""

from __future__ import annotations

import json
import os

_LAB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "lab", "ground_truth.json")


def load_ground_truth(path: str = _LAB) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def resolve_targets(mode: str = "loopback", include_control: bool = True) -> list:
    """Kembalikan daftar target ``{name, ip, ports}`` sesuai mode.

    ``ports`` adalah ground-truth port yang seharusnya terbuka (untuk
    perhitungan TP/FP/FN). Host kontrol memiliki ports kosong.
    """
    gt = load_ground_truth()
    key = "loopback_ip" if mode == "loopback" else "ip"
    targets = []
    for dev in gt["devices"]:
        targets.append({"name": dev["name"], "ip": dev[key],
                        "ports": list(dev["ports"])})
    if include_control:
        c = gt["control_host"]
        targets.append({"name": c["name"], "ip": c[key], "ports": []})
    return targets


def all_ports(mode: str = "loopback") -> list:
    """Union seluruh port ground-truth (ruang port yang dipindai)."""
    gt = load_ground_truth()
    s = set()
    for dev in gt["devices"]:
        s.update(dev["ports"])
    return sorted(s)
