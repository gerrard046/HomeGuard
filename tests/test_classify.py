"""Unit test untuk klasifikasi tipe perangkat & lookup OUI (penuh/seed)."""

from homeguard import classify
from homeguard.data import oui


def test_kamera_dari_rtsp():
    """Port RTSP harus diklasifikasikan sebagai kamera IP."""
    hasil = classify.classify_device([{"port": 554, "service": "rtsp"}])
    assert "Kamera" in hasil["tipe"]


def test_printer_dari_port():
    """Port JetDirect/IPP harus diklasifikasikan sebagai printer."""
    hasil = classify.classify_device(
        [{"port": 9100, "service": "jetdirect"}]
    )
    assert hasil["tipe"] == "Printer"


def test_vendor_kamera_keyakinan_tinggi():
    """Layanan + vendor yang sepakat -> keyakinan tinggi."""
    hasil = classify.classify_device(
        [{"port": 554, "service": "rtsp"}], vendor="Hangzhou Hikvision"
    )
    assert "Kamera" in hasil["tipe"]
    assert hasil["keyakinan"] == "tinggi"


def test_router_dari_pola_web_dns():
    """Web + DNS/UPnP tanpa indikator lain -> Router/Gateway (keyakinan rendah)."""
    hasil = classify.classify_device(
        [{"port": 80, "service": "http"}, {"port": 53, "service": "dns"}]
    )
    assert "Router" in hasil["tipe"]


def test_host_tanpa_port_tidak_diketahui():
    """Host tanpa port terbuka -> tipe tidak diketahui."""
    hasil = classify.classify_device([])
    assert hasil["tipe"] == classify.TIPE_TIDAK_DIKETAHUI


def test_oui_fallback_ke_seed_dan_jumlah():
    """Tanpa DB penuh, lookup tetap memakai seed; jumlah entri > 0."""
    assert oui.lookup_oui("B8:27:EB:00:00:00") == "Raspberry Pi Foundation"
    assert oui.lookup_oui("00:15:6D:11:22:33") == "Ubiquiti Networks"
    assert oui.jumlah_entri() >= len(oui.OUI_SEED)
