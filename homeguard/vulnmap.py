"""Modul 4 — Pemetaan OWASP IoT Top 10 dan penilaian skor risiko.

Modul ini menerjemahkan hasil pemindaian port/layanan menjadi temuan keamanan
yang dipetakan ke kerangka OWASP IoT Top 10 (2018) dan memberikan skor risiko
numerik 0-100 beserta level kualitatif:

    AMAN < RENDAH < SEDANG < TINGGI < KRITIS

Aturan utama (sesuai paper):
    - Telnet (23)        -> KRITIS, kategori I1 + I2 (+I7)
    - HTTP (80)          -> I3 + I7, severity tinggi
    - RTSP (554)         -> I2 + I7
    - Port tak dikenal   -> temuan generik I2, SEDANG
    - Banner komponen usang (mis. "lighttpd/1.4.35", "Apache/2.2.",
      "BusyBox", "OpenSSH_6.") -> tambahkan kategori I5 dan naikkan satu
      tingkat severity.

Skor host dihitung dari severity tertinggi di antara seluruh temuan ditambah
penambah kecil per temuan, dibatasi maksimum 100.
"""

from __future__ import annotations

import re

from .data import iot_ports
from .data.iot_ports import (
    SEVERITY_AMAN,
    SEVERITY_KRITIS,
    SEVERITY_RENDAH,
    SEVERITY_SEDANG,
    SEVERITY_TINGGI,
)

# Urutan severity dari terendah ke tertinggi.
SEVERITY_ORDER = [
    SEVERITY_AMAN,
    SEVERITY_RENDAH,
    SEVERITY_SEDANG,
    SEVERITY_TINGGI,
    SEVERITY_KRITIS,
]

# Skor dasar untuk tiap level severity (0-100).
SEVERITY_BASE_SCORE = {
    SEVERITY_AMAN: 0,
    SEVERITY_RENDAH: 25,
    SEVERITY_SEDANG: 50,
    SEVERITY_TINGGI: 75,
    SEVERITY_KRITIS: 90,
}

# Penambah skor kecil untuk setiap temuan tambahan pada sebuah host.
PENAMBAH_PER_TEMUAN = 3
SKOR_MAKSIMUM = 100

# Pola regex banner komponen usang/rentan -> memicu kategori I5.
# Daftar ini sengaja konservatif untuk prototipe; korelasi CVE penuh ada di
# roadmap (NVD API).
POLA_BANNER_USANG = [
    re.compile(r"lighttpd/1\.4\.(?:[0-2]?[0-9]|3[0-5])\b", re.IGNORECASE),
    re.compile(r"Apache/2\.2\.", re.IGNORECASE),
    re.compile(r"Apache/2\.0\.", re.IGNORECASE),
    re.compile(r"BusyBox", re.IGNORECASE),
    re.compile(r"OpenSSH_[1-6]\b", re.IGNORECASE),
    re.compile(r"OpenSSL/0\.", re.IGNORECASE),
    re.compile(r"OpenSSL/1\.0\.", re.IGNORECASE),
    re.compile(r"nginx/0\.", re.IGNORECASE),
    re.compile(r"vsftpd 2\.", re.IGNORECASE),
    re.compile(r"ProFTPD 1\.[23]\.", re.IGNORECASE),
    re.compile(r"thttpd/2\.2[0-5]", re.IGNORECASE),
    re.compile(r"GoAhead-Webs", re.IGNORECASE),
    re.compile(r"Boa/0\.9", re.IGNORECASE),
]


def naikkan_severity(severity: str, tingkat: int = 1) -> str:
    """Naikkan ``severity`` sebanyak ``tingkat`` level (dibatasi KRITIS)."""
    try:
        idx = SEVERITY_ORDER.index(severity)
    except ValueError:
        idx = 0
    idx = min(idx + tingkat, len(SEVERITY_ORDER) - 1)
    return SEVERITY_ORDER[idx]


def severity_tertinggi(daftar) -> str:
    """Kembalikan severity tertinggi dari kumpulan level severity."""
    tertinggi = SEVERITY_AMAN
    for sev in daftar:
        if SEVERITY_ORDER.index(sev) > SEVERITY_ORDER.index(tertinggi):
            tertinggi = sev
    return tertinggi


def banner_usang(banner: str):
    """Periksa apakah ``banner`` mengindikasikan komponen usang/rentan.

    Mengembalikan pola yang cocok (sebagai string) bila ditemukan, atau ``None``.
    """
    if not banner:
        return None
    for pola in POLA_BANNER_USANG:
        m = pola.search(banner)
        if m:
            return m.group(0)
    return None


def assess_port(port: int, banner: str = "", service: str = "") -> dict:
    """Nilai sebuah port terbuka dan petakan ke kategori OWASP IoT.

    Parameter:
        port    : nomor port yang terbuka.
        banner  : banner layanan hasil banner grabbing (opsional).
        service : nama layanan terdeteksi (opsional; menimpa katalog bila ada).

    Mengembalikan dict temuan berisi: ``port``, ``service``, ``severity``,
    ``owasp`` (daftar kode), ``score``, ``note``, ``recommendation``,
    ``banner``, dan ``outdated`` (bool).
    """
    port = int(port)
    banner = banner or ""
    profil = iot_ports.get_port_profile(port)

    if profil is not None:
        nama_service = service or profil["service"]
        owasp = list(profil["owasp"])
        severity = profil["severity"]
        note = profil["note"]
        recommendation = profil["recommendation"]
    else:
        # Port tak dikenal -> temuan generik I2, SEDANG.
        nama_service = service or "tidak diketahui"
        owasp = ["I2"]
        severity = SEVERITY_SEDANG
        note = (
            "Port terbuka tidak dikenal yang mengekspos layanan jaringan tak "
            "teridentifikasi."
        )
        recommendation = (
            "Identifikasi layanan, tutup port bila tidak diperlukan, dan "
            "batasi akses jaringan."
        )

    # Deteksi banner usang -> tambah I5 dan naikkan severity satu tingkat.
    outdated = False
    cocok = banner_usang(banner)
    if cocok:
        outdated = True
        if "I5" not in owasp:
            owasp.append("I5")
        severity = naikkan_severity(severity, 1)
        note = f"{note} Komponen usang terdeteksi: '{cocok}'."
        recommendation = (
            f"{recommendation} Perbarui komponen '{cocok}' ke versi terbaru "
            "yang didukung."
        )

    return {
        "port": port,
        "service": nama_service,
        "severity": severity,
        "owasp": owasp,
        "score": SEVERITY_BASE_SCORE[severity],
        "note": note,
        "recommendation": recommendation,
        "banner": banner,
        "outdated": outdated,
    }


def assess_host(open_ports) -> dict:
    """Nilai sebuah host dari daftar port terbukanya.

    Parameter ``open_ports`` adalah daftar dict, masing-masing minimal memuat
    kunci ``port`` dan opsional ``banner`` serta ``service``. Boleh juga berupa
    daftar nomor port (int) untuk kemudahan.

    Mengembalikan dict ringkasan host berisi: ``severity`` (level tertinggi),
    ``score`` (0-100), ``owasp`` (gabungan kode unik, terurut), dan ``findings``
    (daftar temuan per port). Host tanpa port terbuka -> AMAN, skor 0.
    """
    findings = []
    for item in open_ports or []:
        if isinstance(item, dict):
            port = item.get("port")
            banner = item.get("banner", "") or ""
            service = item.get("service", "") or ""
        else:
            port = item
            banner = ""
            service = ""
        if port is None:
            continue
        findings.append(assess_port(port, banner=banner, service=service))

    if not findings:
        return {
            "severity": SEVERITY_AMAN,
            "score": 0,
            "owasp": [],
            "findings": [],
        }

    # Gabungkan kategori OWASP unik (terurut: I1, I2, ... I10).
    set_owasp = set()
    for f in findings:
        set_owasp.update(f["owasp"])
    owasp_gabungan = sorted(set_owasp, key=lambda c: int(c[1:]))

    sev_host = severity_tertinggi(f["severity"] for f in findings)
    skor = SEVERITY_BASE_SCORE[sev_host] + PENAMBAH_PER_TEMUAN * len(findings)
    skor = min(skor, SKOR_MAKSIMUM)

    return {
        "severity": sev_host,
        "score": skor,
        "owasp": owasp_gabungan,
        "findings": findings,
    }
