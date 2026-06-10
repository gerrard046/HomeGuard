"""Orkestrator pipeline HomeGuard end-to-end.

Menggabungkan empat modul berurutan sesuai paper:

    1. Penemuan host         (discovery)
    2. Pemindaian port       (portscan)
    3. Deteksi layanan/versi (portscan)
    4. Pemetaan OWASP + skor (vulnmap)

Kelas :class:`HomeGuardScanner` menyediakan API tingkat tinggi untuk memindai
seluruh subnet atau satu host, lalu menghasilkan laporan terstruktur yang siap
diekspor ke JSON atau ditampilkan pada CLI/Streamlit.

PERINGATAN ETIKA: Gunakan HANYA pada jaringan milik sendiri atau yang Anda
miliki izin eksplisit untuk memindainya. Pemindaian jaringan tanpa izin dapat
melanggar hukum.
"""

from __future__ import annotations

import datetime

from . import discovery, portscan, vulnmap
from .data import owasp_iot


class HomeGuardScanner:
    """Orkestrator pipeline pemindaian keamanan jaringan rumah.

    Parameter:
        ports        : daftar port yang dipindai (default katalog IoT).
        timeout      : timeout per koneksi (detik).
        gunakan_nmap : coba memakai ``nmap -sV`` (fallback otomatis ke socket).
        max_workers  : jumlah thread maksimum untuk pemindaian paralel.
    """

    def __init__(
        self,
        ports=None,
        timeout: float = 1.0,
        gunakan_nmap: bool = False,
        max_workers: int = 100,
    ):
        self.ports = list(ports) if ports else list(portscan.PORT_DEFAULT)
        self.timeout = timeout
        self.gunakan_nmap = gunakan_nmap
        self.max_workers = max_workers

    # --- Pemindaian per host -------------------------------------------------

    def scan_host(self, ip: str, mac: str = None, vendor: str = None) -> dict:
        """Pindai satu host dan kembalikan penilaian risiko lengkap.

        Menjalankan modul 2-4 untuk satu ``ip`` dan mengembalikan dict berisi
        identitas host, daftar port terbuka, severity, skor, dan temuan OWASP.
        """
        terbuka = portscan.scan_host(
            ip,
            ports=self.ports,
            timeout=self.timeout,
            gunakan_nmap=self.gunakan_nmap,
            max_workers=self.max_workers,
        )
        penilaian = vulnmap.assess_host(terbuka)
        if vendor is None:
            vendor = discovery.lookup_vendor(mac) if mac else "Unknown"
        return {
            "ip": ip,
            "mac": mac,
            "vendor": vendor,
            "severity": penilaian["severity"],
            "score": penilaian["score"],
            "owasp": penilaian["owasp"],
            "open_ports": terbuka,
            "findings": penilaian["findings"],
        }

    # --- Pemindaian subnet ---------------------------------------------------

    def scan_subnet(self, subnet: str = None) -> list:
        """Temukan host hidup pada ``subnet`` lalu nilai masing-masing.

        Bila ``subnet`` ``None``, subnet lokal dideteksi otomatis. Mengembalikan
        daftar hasil host terurut menurun berdasarkan skor risiko.
        """
        hosts = discovery.discover_hosts(
            subnet=subnet,
            timeout=min(self.timeout, 0.5),
            max_workers=self.max_workers,
        )
        hasil = []
        for h in hosts:
            hasil.append(
                self.scan_host(h["ip"], mac=h.get("mac"), vendor=h.get("vendor"))
            )
        hasil.sort(key=lambda r: r["score"], reverse=True)
        return hasil

    # --- Laporan -------------------------------------------------------------

    def build_report(self, hosts: list, target: str = "") -> dict:
        """Susun laporan terstruktur dari daftar hasil host.

        Laporan memuat metadata (waktu, target, ringkasan) dan daftar host yang
        sudah diurutkan menurun berdasarkan skor risiko. Cocok untuk diekspor
        ke JSON.
        """
        hosts_terurut = sorted(hosts, key=lambda r: r["score"], reverse=True)
        total = len(hosts_terurut)
        berisiko = sum(1 for h in hosts_terurut if h["score"] > 0)
        skor_tertinggi = max((h["score"] for h in hosts_terurut), default=0)

        # Hitung distribusi kategori OWASP di seluruh host.
        distribusi = {}
        for h in hosts_terurut:
            for kode in h["owasp"]:
                distribusi[kode] = distribusi.get(kode, 0) + 1

        return {
            "alat": "HomeGuard",
            "versi": _versi(),
            "waktu": datetime.datetime.now().isoformat(timespec="seconds"),
            "target": target,
            "peringatan": (
                "Laporan ini hanya sah untuk jaringan milik sendiri atau yang "
                "diizinkan."
            ),
            "ringkasan": {
                "total_host": total,
                "host_berisiko": berisiko,
                "skor_tertinggi": skor_tertinggi,
                "distribusi_owasp": distribusi,
            },
            "owasp_referensi": owasp_iot.OWASP_IOT_TOP_10,
            "hosts": hosts_terurut,
        }


def _versi() -> str:
    """Ambil versi paket secara lokal untuk menghindari impor melingkar."""
    from . import __version__

    return __version__
