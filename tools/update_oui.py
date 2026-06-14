#!/usr/bin/env python3
"""Pemutakhir database OUI IEEE untuk HomeGuard.

Mengunduh registri OUI publik IEEE (MA-L) dan menuliskannya ke
``homeguard/data/oui_full.txt`` dalam format ringkas:

    XXXXXX<TAB>Nama Vendor

Berkas hasil unduhan otomatis dipakai oleh modul ``homeguard.data.oui`` dan
diprioritaskan di atas seed bawaan. Berkas ini TIDAK di-commit (lihat
.gitignore) karena berukuran besar (~3 MB) — jalankan skrip ini untuk
menghasilkannya secara lokal.

Hanya memakai pustaka standar (urllib, csv). Membutuhkan akses internet.

Penggunaan:
    python tools/update_oui.py
"""

from __future__ import annotations

import csv
import io
import os
import sys
import urllib.request

# Sumber resmi IEEE (registri MA-L). Tersedia juga mirror .csv.
URL_IEEE = "https://standards-oui.ieee.org/oui/oui.csv"

TUJUAN = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "homeguard", "data", "oui_full.txt",
)


def unduh(url: str = URL_IEEE, timeout: int = 60) -> str:
    """Unduh berkas CSV OUI IEEE dan kembalikan isinya sebagai teks."""
    print(f"Mengunduh database OUI dari: {url}")
    permintaan = urllib.request.Request(
        url, headers={"User-Agent": "HomeGuard-OUI-Updater"}
    )
    with urllib.request.urlopen(permintaan, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def konversi(csv_teks: str) -> dict:
    """Parse CSV IEEE menjadi dict ``{prefix6: vendor}``.

    Kolom CSV IEEE: Registry, Assignment, Organization Name, Organization
    Address. ``Assignment`` adalah 6 heksadigit OUI (mis. ``B827EB``).
    """
    db = {}
    pembaca = csv.reader(io.StringIO(csv_teks))
    header = next(pembaca, None)  # lewati baris header
    for baris in pembaca:
        if len(baris) < 3:
            continue
        prefix = baris[1].strip().upper().replace("-", "").replace(":", "")
        vendor = baris[2].strip()
        if len(prefix) == 6 and vendor:
            db[prefix] = vendor
    return db


def tulis(db: dict, path: str = TUJUAN) -> None:
    """Tulis dict OUI ke berkas dalam format 'prefix<TAB>vendor'."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# Database OUI IEEE (dihasilkan oleh tools/update_oui.py)\n")
        for prefix in sorted(db):
            fh.write(f"{prefix}\t{db[prefix]}\n")
    print(f"Tersimpan {len(db)} entri OUI ke: {path}")


def main() -> int:
    try:
        csv_teks = unduh()
        db = konversi(csv_teks)
    except Exception as exc:  # noqa: BLE001 - ringkas untuk skrip CLI
        print(f"GAGAL: tidak dapat memutakhirkan OUI: {exc}", file=sys.stderr)
        print("Pastikan tersedia akses internet ke standards-oui.ieee.org.",
              file=sys.stderr)
        return 1
    if not db:
        print("GAGAL: tidak ada entri OUI yang berhasil diparse.",
              file=sys.stderr)
        return 1
    tulis(db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
