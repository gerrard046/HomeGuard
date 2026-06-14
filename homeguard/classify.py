"""Klasifikasi tipe perangkat IoT berbasis heuristik.

Menebak jenis perangkat (mis. kamera IP, router, smart plug, printer, NAS,
media/smart TV, asisten suara, single-board computer) dari kombinasi sinyal
yang tersedia tanpa analisis intrusif:

    - **Layanan/port terbuka** (mis. RTSP -> kamera, IPP/JetDirect -> printer)
    - **Vendor** dari lookup OUI alamat MAC (mis. Hikvision -> kamera)

Pendekatan ini menyederhanakan *device fingerprinting* (lih. Sivanathan et al.)
menjadi inferensi berbasis aturan yang transparan dan dapat diaudit, memadai
untuk keperluan penilaian kerentanan rumahan.
"""

from __future__ import annotations

# Tipe perangkat baku.
TIPE_TIDAK_DIKETAHUI = "Tidak diketahui"

# Kata kunci vendor (substring, huruf kecil) -> tipe perangkat.
VENDOR_KE_TIPE = [
    (("hikvision", "dahua", "axis", "ezviz", "reecam", "kamera", "uniview"),
     "Kamera IP / CCTV"),
    (("raspberry pi",), "Single-Board Computer"),
    (("espressif", "esp32", "esp8266"), "Mikrokontroler IoT"),
    (("tp-link", "asus", "netgear", "d-link", "mikrotik", "ralink",
      "mediatek", "sagemcom", "ubiquiti"), "Router / Gateway"),
    (("synology", "qnap"), "NAS / Penyimpanan Jaringan"),
    (("sonos",), "Speaker Pintar / Audio"),
    (("amazon", "google", "nest"), "Asisten Suara / Media"),
    (("philips",), "Pencahayaan Pintar"),
    (("hp", "hewlett", "canon", "epson", "brother", "kyocera"), "Printer"),
    (("withings",), "Perangkat Kesehatan"),
    (("samsung",), "Perangkat Samsung (TV/Mobile)"),
    (("xiaomi",), "Perangkat Xiaomi (IoT)"),
]

# Layanan/port yang menjadi indikator kuat tipe perangkat (prioritas tinggi).
LAYANAN_KE_TIPE = [
    ({"rtsp", "rtsp-alt"}, "Kamera IP / CCTV"),
    ({"jetdirect", "ipp"}, "Printer"),
    ({"smb"}, "NAS / Penyimpanan Jaringan"),
    ({"cast"}, "Media / Smart TV"),
    ({"mqtt"}, "Hub / Broker IoT"),
]
PORT_KE_TIPE = [
    ({554, 8554}, "Kamera IP / CCTV"),
    ({9100, 631}, "Printer"),
    ({445}, "NAS / Penyimpanan Jaringan"),
    ({8009}, "Media / Smart TV"),
    ({1883}, "Hub / Broker IoT"),
]


def _tipe_dari_vendor(vendor: str):
    """Tebak tipe dari nama vendor; ``None`` bila tak ada kecocokan."""
    if not vendor:
        return None
    v = vendor.lower()
    for kunci, tipe in VENDOR_KE_TIPE:
        if any(k in v for k in kunci):
            return tipe
    return None


def _tipe_dari_layanan(services: set, ports: set):
    """Tebak tipe dari layanan/port; ``None`` bila tak ada indikator kuat."""
    for himpunan, tipe in LAYANAN_KE_TIPE:
        if services & himpunan:
            return tipe
    for himpunan, tipe in PORT_KE_TIPE:
        if ports & himpunan:
            return tipe
    return None


def classify_device(open_ports=None, vendor: str = "") -> dict:
    """Klasifikasikan tipe perangkat dari port terbuka dan vendor.

    Parameter:
        open_ports : daftar dict port (dari portscan) atau daftar nomor port.
        vendor     : nama vendor hasil lookup OUI (opsional).

    Mengembalikan dict ``{"tipe", "keyakinan", "alasan"}``. ``keyakinan`` bernilai
    "tinggi" (sinyal layanan + vendor sepakat), "sedang" (salah satu sinyal),
    atau "rendah" (hanya tebakan generik).
    """
    ports = set()
    services = set()
    for item in open_ports or []:
        if isinstance(item, dict):
            if item.get("port") is not None:
                ports.add(int(item["port"]))
            if item.get("service"):
                services.add(str(item["service"]).lower())
        else:
            ports.add(int(item))

    tipe_layanan = _tipe_dari_layanan(services, ports)
    tipe_vendor = _tipe_dari_vendor(vendor)

    # Sepakat -> keyakinan tinggi.
    if tipe_layanan and tipe_vendor and tipe_layanan == tipe_vendor:
        return {"tipe": tipe_layanan, "keyakinan": "tinggi",
                "alasan": "Sinyal layanan dan vendor sepakat."}
    # Indikator layanan kuat diprioritaskan di atas vendor.
    if tipe_layanan:
        return {"tipe": tipe_layanan, "keyakinan": "sedang",
                "alasan": "Berdasarkan layanan/port khas."}
    if tipe_vendor:
        return {"tipe": tipe_vendor, "keyakinan": "sedang",
                "alasan": "Berdasarkan vendor (OUI)."}

    # Tebakan generik dari pola umum.
    if {80, 443, 8080, 8443} & ports and ({53} & ports or {1900, 49152} & ports):
        return {"tipe": "Router / Gateway", "keyakinan": "rendah",
                "alasan": "Pola layanan web + DNS/UPnP."}
    if {23, 2323} & ports:
        return {"tipe": "Perangkat IoT (umum)", "keyakinan": "rendah",
                "alasan": "Telnet terbuka, khas perangkat IoT murah."}
    if ports:
        return {"tipe": "Perangkat IoT (umum)", "keyakinan": "rendah",
                "alasan": "Ada layanan jaringan terbuka."}
    return {"tipe": TIPE_TIDAK_DIKETAHUI, "keyakinan": "rendah",
            "alasan": "Tidak ada sinyal yang cukup."}
