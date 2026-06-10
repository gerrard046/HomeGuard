"""Subpaket data statis HomeGuard.

Berisi basis pengetahuan yang dipakai pipeline pemindaian:
    - ``iot_ports`` : katalog port IoT umum dan profil risikonya
    - ``owasp_iot`` : definisi OWASP IoT Top 10 (2018)
    - ``oui``       : lookup vendor berdasarkan prefiks OUI alamat MAC
"""

from . import iot_ports, oui, owasp_iot

__all__ = ["iot_ports", "oui", "owasp_iot"]
