"""Unit test untuk modul pemetaan OWASP IoT + skor risiko (vulnmap)."""

from homeguard import vulnmap


def test_telnet_kritis_i1_i2():
    """Telnet (23) harus dinilai KRITIS dan memetakan I1 serta I2."""
    temuan = vulnmap.assess_port(23)
    assert temuan["severity"] == "KRITIS"
    assert "I1" in temuan["owasp"]
    assert "I2" in temuan["owasp"]


def test_http_i3_i7():
    """HTTP (80) harus memetakan I3 dan I7 dengan severity tinggi."""
    temuan = vulnmap.assess_port(80)
    assert "I3" in temuan["owasp"]
    assert "I7" in temuan["owasp"]
    assert temuan["severity"] == "TINGGI"


def test_rtsp_i2_i7():
    """RTSP (554) harus memetakan I2 dan I7."""
    temuan = vulnmap.assess_port(554)
    assert "I2" in temuan["owasp"]
    assert "I7" in temuan["owasp"]


def test_port_tak_dikenal_i2_sedang():
    """Port tak dikenal harus menghasilkan temuan generik I2 dengan SEDANG."""
    temuan = vulnmap.assess_port(34567)
    assert temuan["owasp"] == ["I2"]
    assert temuan["severity"] == "SEDANG"


def test_banner_usang_tambah_i5_dan_naikkan_severity():
    """Banner usang harus menambah I5 dan menaikkan satu tingkat severity."""
    dasar = vulnmap.assess_port(80)  # TINGGI tanpa banner
    usang = vulnmap.assess_port(80, banner="lighttpd/1.4.35")
    assert "I5" in usang["owasp"]
    assert usang["outdated"] is True
    # Severity naik dari TINGGI menjadi KRITIS.
    assert vulnmap.SEVERITY_ORDER.index(usang["severity"]) == (
        vulnmap.SEVERITY_ORDER.index(dasar["severity"]) + 1
    )
    assert usang["severity"] == "KRITIS"


def test_assess_host_gabungan_dan_host_kosong():
    """Host Telnet+HTTP+RTSP -> KRITIS dengan gabungan I1/I2/I3/I7;
    host tanpa port -> AMAN dengan skor 0."""
    host = vulnmap.assess_host(
        [{"port": 23}, {"port": 80}, {"port": 554}]
    )
    assert host["severity"] == "KRITIS"
    for kode in ("I1", "I2", "I3", "I7"):
        assert kode in host["owasp"]
    assert host["score"] > 0

    kosong = vulnmap.assess_host([])
    assert kosong["severity"] == "AMAN"
    assert kosong["score"] == 0
