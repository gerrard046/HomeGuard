"""Katalog port IoT umum dan pemetaannya ke kategori OWASP IoT Top 10.

Setiap entri memetakan nomor port ke informasi:
    - ``service``        : nama layanan yang lazim
    - ``owasp``          : daftar kategori OWASP IoT (mis. ``["I1", "I2"]``)
    - ``severity``       : tingkat keparahan awal (AMAN/RENDAH/SEDANG/TINGGI/KRITIS)
    - ``note``           : penjelasan singkat mengapa port berisiko
    - ``recommendation`` : rekomendasi mitigasi

Katalog ini menjadi basis pengetahuan modul ``vulnmap`` saat menilai sebuah
port terbuka. Port yang tidak terdapat di katalog diperlakukan sebagai temuan
generik (lihat ``vulnmap.assess_port``).
"""

from __future__ import annotations

# Tingkat keparahan, diurut dari paling rendah ke paling tinggi.
SEVERITY_AMAN = "AMAN"
SEVERITY_RENDAH = "RENDAH"
SEVERITY_SEDANG = "SEDANG"
SEVERITY_TINGGI = "TINGGI"
SEVERITY_KRITIS = "KRITIS"

# Katalog port -> profil risiko.
IOT_PORTS = {
    21: {
        "service": "ftp",
        "owasp": ["I2", "I7"],
        "severity": SEVERITY_TINGGI,
        "note": "FTP mengirim kredensial dan data tanpa enkripsi.",
        "recommendation": "Nonaktifkan FTP atau ganti dengan SFTP/FTPS.",
    },
    22: {
        "service": "ssh",
        "owasp": ["I2"],
        "severity": SEVERITY_SEDANG,
        "note": "SSH terbuka; berisiko bila memakai kredensial lemah/bawaan.",
        "recommendation": "Pakai autentikasi kunci, nonaktifkan login root, "
        "perbarui versi server.",
    },
    23: {
        "service": "telnet",
        "owasp": ["I1", "I2", "I7"],
        "severity": SEVERITY_KRITIS,
        "note": "Telnet mengirim kredensial dalam teks polos dan kerap memakai "
        "kata sandi bawaan/hardcoded pada perangkat IoT.",
        "recommendation": "Nonaktifkan Telnet sepenuhnya dan gunakan SSH.",
    },
    2323: {
        "service": "telnet-alt",
        "owasp": ["I1", "I2", "I7"],
        "severity": SEVERITY_KRITIS,
        "note": "Telnet pada port alternatif 2323 dipindai aktif oleh botnet "
        "Mirai dan variannya; kredensial polos/bawaan sangat rentan.",
        "recommendation": "Nonaktifkan Telnet sepenuhnya dan gunakan SSH.",
    },
    25: {
        "service": "smtp",
        "owasp": ["I2", "I7"],
        "severity": SEVERITY_SEDANG,
        "note": "SMTP terbuka dapat disalahgunakan sebagai relai.",
        "recommendation": "Batasi akses dan wajibkan autentikasi + TLS.",
    },
    53: {
        "service": "dns",
        "owasp": ["I2"],
        "severity": SEVERITY_RENDAH,
        "note": "Layanan DNS terbuka dapat menjadi vektor amplifikasi.",
        "recommendation": "Batasi rekursi DNS hanya untuk jaringan lokal.",
    },
    80: {
        "service": "http",
        "owasp": ["I3", "I7"],
        "severity": SEVERITY_TINGGI,
        "note": "Antarmuka web HTTP tanpa enkripsi; kredensial dan data "
        "dikirim polos serta sering memakai pengaturan bawaan tidak aman.",
        "recommendation": "Gunakan HTTPS, ubah kredensial bawaan, terapkan "
        "autentikasi yang kuat.",
    },
    443: {
        "service": "https",
        "owasp": ["I3"],
        "severity": SEVERITY_SEDANG,
        "note": "Antarmuka web HTTPS; tetap berisiko bila kredensial bawaan "
        "atau sertifikat lemah.",
        "recommendation": "Ubah kredensial bawaan, gunakan sertifikat valid.",
    },
    554: {
        "service": "rtsp",
        "owasp": ["I2", "I7"],
        "severity": SEVERITY_TINGGI,
        "note": "RTSP (streaming kamera) sering tanpa autentikasi sehingga "
        "umpan video dapat diakses dan dikirim tanpa enkripsi.",
        "recommendation": "Aktifkan autentikasi RTSP, batasi akses jaringan.",
    },
    1883: {
        "service": "mqtt",
        "owasp": ["I2", "I7"],
        "severity": SEVERITY_TINGGI,
        "note": "Broker MQTT tanpa autentikasi/TLS membuka kontrol perangkat.",
        "recommendation": "Aktifkan autentikasi MQTT dan TLS (port 8883).",
    },
    1900: {
        "service": "ssdp/upnp",
        "owasp": ["I2"],
        "severity": SEVERITY_SEDANG,
        "note": "SSDP/UPnP (port 1900) mengindikasikan smart device dan kerap "
        "mengekspos deskripsi layanan tanpa autentikasi.",
        "recommendation": "Nonaktifkan UPnP/SSDP bila tidak diperlukan, batasi "
        "ke jaringan lokal.",
    },
    5353: {
        "service": "mdns",
        "owasp": ["I2", "I6"],
        "severity": SEVERITY_RENDAH,
        "note": "mDNS (port 5353) mengumumkan layanan & nama perangkat di "
        "jaringan lokal, berpotensi membocorkan informasi perangkat.",
        "recommendation": "Batasi mDNS ke segmen tepercaya bila tidak "
        "diperlukan untuk penemuan layanan.",
    },
    5000: {
        "service": "upnp/http-alt",
        "owasp": ["I2", "I3"],
        "severity": SEVERITY_SEDANG,
        "note": "Layanan HTTP alternatif/UPnP dapat mengekspos API perangkat.",
        "recommendation": "Nonaktifkan bila tak diperlukan, batasi akses.",
    },
    8080: {
        "service": "http-proxy",
        "owasp": ["I3", "I7"],
        "severity": SEVERITY_TINGGI,
        "note": "Antarmuka web/proxy alternatif tanpa enkripsi.",
        "recommendation": "Gunakan HTTPS dan autentikasi yang kuat.",
    },
    8443: {
        "service": "https-alt",
        "owasp": ["I3"],
        "severity": SEVERITY_SEDANG,
        "note": "Antarmuka web HTTPS alternatif; periksa kredensial bawaan.",
        "recommendation": "Ubah kredensial bawaan, gunakan sertifikat valid.",
    },
    8554: {
        "service": "rtsp-alt",
        "owasp": ["I2", "I7"],
        "severity": SEVERITY_TINGGI,
        "note": "RTSP pada port alternatif; risiko serupa kamera tanpa "
        "autentikasi.",
        "recommendation": "Aktifkan autentikasi RTSP, batasi akses jaringan.",
    },
    9000: {
        "service": "http-alt",
        "owasp": ["I3"],
        "severity": SEVERITY_SEDANG,
        "note": "Panel admin/HTTP alternatif yang umum pada perangkat IoT.",
        "recommendation": "Batasi akses dan terapkan autentikasi kuat.",
    },
    445: {
        "service": "smb",
        "owasp": ["I2", "I7"],
        "severity": SEVERITY_TINGGI,
        "note": "Berbagi berkas SMB terbuka (umum pada NAS) berisiko akses "
        "tak sah & eksploitasi protokol.",
        "recommendation": "Batasi SMB ke jaringan tepercaya, wajibkan "
        "autentikasi, nonaktifkan SMBv1.",
    },
    631: {
        "service": "ipp",
        "owasp": ["I2", "I3"],
        "severity": SEVERITY_RENDAH,
        "note": "Layanan cetak IPP (printer) terekspos.",
        "recommendation": "Batasi akses printer ke jaringan lokal.",
    },
    8009: {
        "service": "cast",
        "owasp": ["I2"],
        "severity": SEVERITY_RENDAH,
        "note": "Protokol Google Cast (Chromecast/smart TV) terbuka.",
        "recommendation": "Batasi akses dan gunakan jaringan tepercaya.",
    },
    9100: {
        "service": "jetdirect",
        "owasp": ["I2"],
        "severity": SEVERITY_SEDANG,
        "note": "Port cetak mentah (JetDirect/RAW) printer sering tanpa "
        "autentikasi sehingga rentan penyalahgunaan.",
        "recommendation": "Batasi akses printer, nonaktifkan port mentah bila "
        "tak diperlukan.",
    },
    49152: {
        "service": "upnp",
        "owasp": ["I2"],
        "severity": SEVERITY_SEDANG,
        "note": "Port UPnP dinamis yang sering mengekspos layanan internal.",
        "recommendation": "Nonaktifkan UPnP bila tidak diperlukan.",
    },
}


def get_port_profile(port: int) -> dict:
    """Kembalikan profil risiko untuk ``port`` dari katalog, atau ``None``.

    ``None`` menandakan port tidak ada di katalog dan harus ditangani sebagai
    temuan generik oleh modul penilai.
    """
    return IOT_PORTS.get(int(port))
