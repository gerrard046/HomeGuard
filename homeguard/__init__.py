"""HomeGuard — pemindai keamanan jaringan rumah untuk perangkat IoT.

HomeGuard adalah prototipe pemindai keamanan yang mengidentifikasi kerentanan
perangkat IoT pada jaringan Wi-Fi rumah, lalu memetakan temuan ke kerangka
OWASP IoT Top 10 (2018) dan menghitung skor risiko 0-100.

Pipeline terdiri atas empat modul berurutan:
    1. Penemuan host          (:mod:`homeguard.discovery`)
    2. Pemindaian port        (:mod:`homeguard.portscan`)
    3. Deteksi layanan/versi  (:mod:`homeguard.portscan`)
    4. Pemetaan OWASP + skor   (:mod:`homeguard.vulnmap`)

Inti pemindaian hanya memakai pustaka standar Python (socket murni), tanpa hak
akses root dan tanpa dependensi wajib.

PERINGATAN ETIKA: Gunakan HANYA pada jaringan milik sendiri atau yang Anda
miliki izin eksplisit untuk memindainya.
"""

from .scanner import HomeGuardScanner

__version__ = "0.1.0"

__all__ = ["HomeGuardScanner", "__version__"]
