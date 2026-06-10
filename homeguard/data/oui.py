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
}

# Vendor default ketika prefiks tidak ditemukan dalam seed.
UNKNOWN_VENDOR = "Unknown"


def lookup_oui(mac_prefix: str) -> str:
    """Cari nama vendor dari prefiks OUI sebuah alamat MAC.

    ``mac_prefix`` dapat berupa alamat MAC lengkap atau hanya prefiksnya, dengan
    atau tanpa pemisah (``:`` ``-`` ``.``). Hanya 6 heksadigit pertama yang
    digunakan untuk pencarian. Mengembalikan :data:`UNKNOWN_VENDOR` bila tidak
    dikenal.
    """
    if not mac_prefix:
        return UNKNOWN_VENDOR
    # Buang semua karakter non-heksadesimal lalu ambil 6 karakter pertama.
    bersih = "".join(c for c in mac_prefix if c in "0123456789abcdefABCDEF")
    prefix = bersih[:6].upper()
    if len(prefix) < 6:
        return UNKNOWN_VENDOR
    return OUI_SEED.get(prefix, UNKNOWN_VENDOR)
