"""Lookup vendor berdasarkan prefiks OUI (Organizationally Unique Identifier).

Tiga oktet pertama alamat MAC (24 bit) ditetapkan oleh IEEE kepada pabrikan dan
disebut OUI. Modul ini menyediakan *seed* kecil dari basis data OUI IEEE untuk
keperluan prototipe; basis data lengkap dapat ditambahkan di kemudian hari
(lihat roadmap pada README).

Catatan: data ini hanya sebagian kecil dan ditujukan untuk demonstrasi serta
pengujian, bukan inventaris vendor yang lengkap.
"""

from __future__ import annotations

# Seed OUI IEEE: prefiks 6 heksadigit (tanpa pemisah, huruf besar) -> vendor.
# Sumber: alokasi publik IEEE (registri MA-L). Hanya sebagian untuk prototipe.
OUI_SEED = {
    "B827EB": "Raspberry Pi Foundation",
    "DCA632": "Raspberry Pi Trading",
    "E45F01": "Raspberry Pi Trading",
    "2CCF67": "Raspberry Pi (Trading) Ltd",
    "001788": "Philips Lighting (Hue)",
    "ECB5FA": "Philips Lighting",
    "0017880": "Philips",
    "00125A": "Microsoft",
    "F0272D": "TP-Link Technologies",
    "50C7BF": "TP-Link Technologies",
    "AC84C6": "TP-Link Technologies",
    "B0BE76": "TP-Link Technologies",
    "001A11": "Google",
    "F4F5D8": "Google",
    "F88FCA": "Google (Nest)",
    "18B430": "Nest Labs",
    "44650D": "Amazon Technologies",
    "FCA183": "Amazon Technologies",
    "F0D2F1": "Amazon Technologies",
    "00166C": "Samsung Electronics",
    "8CC8CD": "Samsung Electronics",
    "BC1485": "Hangzhou Ezviz (Hikvision)",
    "C0560E": "Hangzhou Hikvision",
    "44A642": "Hangzhou Hikvision",
    "001F54": "Dahua Technology",
    "3C1E04": "Dahua Technology",
    "B4A382": "Shenzhen Reecam (kamera IP)",
    "000C43": "Ralink/MediaTek (router/IoT)",
    "001E06": "Wibrain",
    "ACCC8E": "Axis Communications (kamera)",
    "00408C": "Axis Communications",
    "D052A8": "Physical Graph (SmartThings)",
    "246F28": "Espressif Inc. (ESP32)",
    "3C71BF": "Espressif Inc. (ESP32)",
    "5CCF7F": "Espressif Inc. (ESP8266)",
    "A020A6": "Espressif Inc.",
    "BCDDC2": "Espressif Inc.",
    "001132": "Synology",
    "0011D8": "ASUSTek Computer",
    "AC220B": "ASUSTek Computer",
    "B86491": "Apple",
    "F0DBF8": "Apple",
    "001451": "Apple",
    "3C0754": "Apple",
    # Vendor IoT/smart-home & jaringan rumah yang umum (seed tambahan).
    "5C0A5B": "Samsung Electronics",
    "0C47C9": "Amazon Technologies",
    "68DBF5": "Amazon Technologies",
    "286C07": "Xiaomi Communications",
    "640980": "Xiaomi Communications",
    "F8A45F": "Xiaomi Communications",
    "00156D": "Ubiquiti Networks",
    "24A43C": "Ubiquiti Networks",
    "FCECDA": "Ubiquiti Networks",
    "000E58": "Sonos",
    "B8E937": "Sonos",
    "240AC4": "Espressif Inc. (ESP32)",
    "30AEA4": "Espressif Inc. (ESP32)",
    "A4CF12": "Espressif Inc. (ESP32)",
    "CC50E3": "Espressif Inc. (ESP8266)",
    "7C9EBD": "Espressif Inc.",
    "00095B": "Netgear",
    "20E52A": "Netgear",
    "00055D": "D-Link",
    "1C7EE5": "D-Link",
    "B8A386": "D-Link",
    "EC086B": "TP-Link Technologies",
    "1427BB": "TP-Link Technologies",
    "3CEF8C": "Dahua Technology",
    "90B134": "Honeywell",
    "0024E4": "Withings (perangkat kesehatan)",
    "002586": "Sagemcom (router)",
    "001E8F": "Canon (printer)",
    "002673": "Brother Industries (printer)",
    "0017C8": "Kyocera (printer)",
    "3C2AF4": "Brother Industries (printer)",
    "9CD643": "HP (printer)",
    "B499BA": "Hewlett Packard",
    "ECB1D7": "Hewlett Packard",
    "001124": "Hewlett Packard",
}

# Vendor default ketika prefiks tidak ditemukan dalam seed.
UNKNOWN_VENDOR = "Unknown"

# Berkas database OUI IEEE penuh (opsional). Dihasilkan oleh skrip
# ``tools/update_oui.py`` dengan format per baris: "XXXXXX<TAB>Nama Vendor".
# Bila ada, database ini diprioritaskan di atas seed. Tidak di-commit ke repo
# karena berukuran besar (lihat .gitignore).
import os

_FULL_DB_PATH = os.path.join(os.path.dirname(__file__), "oui_full.txt")
_full_db = None          # cache hasil pemuatan (dict), None bila belum dimuat
_full_db_dicoba = False  # penanda agar pemuatan hanya dicoba sekali


def _muat_db_penuh() -> dict:
    """Muat database OUI penuh dari berkas (lazy, sekali saja).

    Mengembalikan dict ``{prefix6: vendor}``; dict kosong bila berkas tidak ada
    atau gagal dibaca, sehingga pencarian otomatis jatuh kembali ke seed.
    """
    global _full_db, _full_db_dicoba
    if _full_db_dicoba:
        return _full_db or {}
    _full_db_dicoba = True
    db = {}
    try:
        with open(_FULL_DB_PATH, "r", encoding="utf-8", errors="ignore") as fh:
            for baris in fh:
                baris = baris.rstrip("\n")
                if not baris or baris.startswith("#"):
                    continue
                bagian = baris.split("\t", 1)
                if len(bagian) == 2:
                    db[bagian[0].strip().upper()] = bagian[1].strip()
    except OSError:
        db = {}
    _full_db = db
    return db


def database_tersedia() -> bool:
    """Kembalikan ``True`` bila database OUI IEEE penuh berhasil dimuat."""
    return bool(_muat_db_penuh())


def jumlah_entri() -> int:
    """Kembalikan jumlah total entri OUI yang dapat dicari (penuh + seed)."""
    return len(set(_muat_db_penuh()) | set(OUI_SEED))


def lookup_oui(mac_prefix: str) -> str:
    """Cari nama vendor dari prefiks OUI sebuah alamat MAC.

    ``mac_prefix`` dapat berupa alamat MAC lengkap atau hanya prefiksnya, dengan
    atau tanpa pemisah (``:`` ``-`` ``.``). Hanya 6 heksadigit pertama yang
    digunakan untuk pencarian. Database IEEE penuh (bila tersedia) diprioritaskan
    di atas seed bawaan. Mengembalikan :data:`UNKNOWN_VENDOR` bila tidak dikenal.
    """
    if not mac_prefix:
        return UNKNOWN_VENDOR
    # Buang semua karakter non-heksadesimal lalu ambil 6 karakter pertama.
    bersih = "".join(c for c in mac_prefix if c in "0123456789abcdefABCDEF")
    prefix = bersih[:6].upper()
    if len(prefix) < 6:
        return UNKNOWN_VENDOR
    db = _muat_db_penuh()
    if prefix in db:
        return db[prefix]
    return OUI_SEED.get(prefix, UNKNOWN_VENDOR)
