#!/usr/bin/env python3
"""Antarmuka baris perintah (CLI) HomeGuard.

Menjalankan pipeline pemindaian keamanan jaringan rumah dan mencetak laporan
berwarna ke terminal, dengan opsi mengekspor laporan ke berkas JSON.

Contoh penggunaan::

    python cli.py --subnet 192.168.1.0/24
    python cli.py --host 192.168.1.10 --ports 22,23,80,554
    python cli.py --subnet 192.168.1.0/24 --json laporan.json --nmap

PERINGATAN ETIKA: Gunakan HANYA pada jaringan milik sendiri atau yang Anda
miliki izin eksplisit untuk memindainya.
"""

from __future__ import annotations

import argparse
import json
import sys

from homeguard import HomeGuardScanner, __version__
from homeguard.data import owasp_iot

# Kode warna ANSI untuk pewarnaan terminal.
_WARNA = {
    "AMAN": "\033[92m",     # hijau
    "RENDAH": "\033[96m",   # cyan
    "SEDANG": "\033[93m",   # kuning
    "TINGGI": "\033[95m",   # magenta
    "KRITIS": "\033[91m",   # merah
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
}


def _w(teks: str, kunci: str, aktif: bool) -> str:
    """Bungkus ``teks`` dengan kode warna ``kunci`` bila pewarnaan aktif."""
    if not aktif:
        return teks
    return f"{_WARNA.get(kunci, '')}{teks}{_WARNA['reset']}"


def parse_ports(spek: str) -> list:
    """Parse spesifikasi port (``"22,23,80"`` atau ``"20-25"``) menjadi list."""
    ports = set()
    for bagian in spek.split(","):
        bagian = bagian.strip()
        if not bagian:
            continue
        if "-" in bagian:
            awal, akhir = bagian.split("-", 1)
            ports.update(range(int(awal), int(akhir) + 1))
        else:
            ports.add(int(bagian))
    return sorted(ports)


def cetak_laporan(laporan: dict, warna: bool) -> None:
    """Cetak laporan pemindaian ke stdout dalam format berwarna terbaca."""
    print(_w(f"=== HomeGuard v{laporan['versi']} ===", "bold", warna))
    print(_w(laporan["peringatan"], "dim", warna))
    print(f"Waktu  : {laporan['waktu']}")
    print(f"Target : {laporan['target'] or '(deteksi otomatis)'}")

    ring = laporan["ringkasan"]
    print(
        f"\nRingkasan: {ring['total_host']} host, "
        f"{ring['host_berisiko']} berisiko, "
        f"skor tertinggi {ring['skor_tertinggi']}."
    )

    if not laporan["hosts"]:
        print(_w("\nTidak ada host hidup yang ditemukan.", "SEDANG", warna))
        return

    for h in laporan["hosts"]:
        sev = h["severity"]
        garis = "-" * 60
        print(_w(f"\n{garis}", "dim", warna))
        label = _w(f"[{sev}] skor {h['score']}", sev, warna)
        print(f"{label}  {h['ip']}  ({h.get('vendor') or 'Unknown'})")
        if h.get("mac"):
            print(f"  MAC   : {h['mac']}")
        if h["owasp"]:
            print(f"  OWASP : {', '.join(h['owasp'])}")
        for f in h["findings"]:
            sev_f = f["severity"]
            kepala = _w(f"  - {f['port']}/{f['service']}", sev_f, warna)
            print(f"{kepala} [{sev_f}] {', '.join(f['owasp'])}")
            print(_w(f"      {f['note']}", "dim", warna))
            if f.get("banner"):
                print(_w(f"      banner: {f['banner']}", "dim", warna))
            print(_w(f"      rekomendasi: {f['recommendation']}", "dim", warna))


def cetak_referensi_owasp() -> None:
    """Cetak tabel referensi OWASP IoT Top 10."""
    print("Referensi OWASP IoT Top 10 (2018):")
    for kode, info in owasp_iot.OWASP_IOT_TOP_10.items():
        print(f"  {kode:<4} {info['nama']}")


def build_parser() -> argparse.ArgumentParser:
    """Bangun parser argumen CLI."""
    parser = argparse.ArgumentParser(
        prog="homeguard",
        description=(
            "HomeGuard - pemindai keamanan jaringan rumah untuk perangkat IoT "
            "dengan pemetaan OWASP IoT Top 10. Gunakan hanya pada jaringan "
            "milik/diizinkan."
        ),
    )
    grup = parser.add_mutually_exclusive_group()
    grup.add_argument(
        "--subnet",
        help="Subnet CIDR yang dipindai, mis. 192.168.1.0/24 "
        "(default: deteksi otomatis).",
    )
    grup.add_argument(
        "--host", help="Pindai satu alamat IP host saja."
    )
    parser.add_argument(
        "--ports",
        help="Daftar/rentang port, mis. '22,23,80' atau '1-1024' "
        "(default: katalog port IoT).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="Timeout per koneksi dalam detik (default: 1.0).",
    )
    parser.add_argument(
        "--nmap",
        action="store_true",
        help="Gunakan 'nmap -sV' bila tersedia (fallback otomatis ke socket).",
    )
    parser.add_argument(
        "--json",
        metavar="FILE",
        help="Ekspor laporan ke berkas JSON pada path FILE.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Nonaktifkan pewarnaan keluaran terminal.",
    )
    parser.add_argument(
        "--owasp-ref",
        action="store_true",
        help="Tampilkan referensi OWASP IoT Top 10 lalu keluar.",
    )
    parser.add_argument(
        "--version", action="version", version=f"HomeGuard {__version__}"
    )
    return parser


def main(argv=None) -> int:
    """Titik masuk CLI. Mengembalikan kode keluar proses."""
    parser = build_parser()
    args = parser.parse_args(argv)
    warna = not args.no_color and sys.stdout.isatty()

    if args.owasp_ref:
        cetak_referensi_owasp()
        return 0

    ports = parse_ports(args.ports) if args.ports else None
    scanner = HomeGuardScanner(
        ports=ports, timeout=args.timeout, gunakan_nmap=args.nmap
    )

    print(_w("Memindai... (hanya untuk jaringan milik/diizinkan)", "dim", warna))
    if args.host:
        hasil = [scanner.scan_host(args.host)]
        target = args.host
    else:
        hasil = scanner.scan_subnet(args.subnet)
        target = args.subnet or "(deteksi otomatis)"

    laporan = scanner.build_report(hasil, target=target)
    cetak_laporan(laporan, warna)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(laporan, fh, ensure_ascii=False, indent=2)
        print(_w(f"\nLaporan JSON disimpan ke: {args.json}", "AMAN", warna))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
