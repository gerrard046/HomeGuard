"""Unit test untuk orkestrator (scanner), kredensial bawaan, dan ekspor PDF."""

import base64
import socket
import threading
import time

from homeguard import HomeGuardScanner
from homeguard.report_pdf import build_pdf_bytes


def _mock_http(port: int, banner_200: bytes, perlu_auth: bool = False,
               cred_valid=("admin", "admin")):
    """Server HTTP tiruan. Bila perlu_auth, balas 401 kecuali Basic cocok."""
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(5)
    srv.settimeout(0.3)
    stop = threading.Event()
    token = base64.b64encode(f"{cred_valid[0]}:{cred_valid[1]}".encode()).decode()

    def run():
        while not stop.is_set():
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                req = conn.recv(1024).decode("latin-1", "ignore")
                if perlu_auth and f"Basic {token}" not in req:
                    conn.sendall(
                        b"HTTP/1.0 401 Unauthorized\r\n"
                        b"WWW-Authenticate: Basic realm=x\r\n\r\n"
                    )
                else:
                    conn.sendall(banner_200)
            except OSError:
                pass
            finally:
                conn.close()
        srv.close()

    threading.Thread(target=run, daemon=True).start()
    time.sleep(0.2)
    return stop


def test_agregasi_kosong():
    """Tanpa temuan -> AMAN, skor 0."""
    a = HomeGuardScanner._agregasi([])
    assert a["severity"] == "AMAN"
    assert a["score"] == 0


def test_agregasi_gabungan_owasp_dan_severity():
    """Agregasi mengambil severity tertinggi & menggabungkan OWASP unik."""
    findings = [
        {"severity": "KRITIS", "owasp": ["I1", "I2"]},
        {"severity": "TINGGI", "owasp": ["I3"]},
    ]
    a = HomeGuardScanner._agregasi(findings)
    assert a["severity"] == "KRITIS"
    assert set(a["owasp"]) == {"I1", "I2", "I3"}


def test_build_report_terurut_menurut_risiko():
    """Laporan mengurutkan host menurun berdasarkan skor & menghitung ringkasan."""
    sc = HomeGuardScanner()
    hosts = [
        {"ip": "a", "score": 10, "severity": "RENDAH", "owasp": ["I2"],
         "findings": [], "open_ports": []},
        {"ip": "b", "score": 90, "severity": "KRITIS", "owasp": ["I1"],
         "findings": [], "open_ports": []},
    ]
    rep = sc.build_report(hosts, target="x")
    assert rep["hosts"][0]["ip"] == "b"
    assert rep["ringkasan"]["total_host"] == 2
    assert rep["ringkasan"]["skor_tertinggi"] == 90


def test_scan_host_http_banner_usang():
    """Integrasi: HTTP dengan banner usang -> KRITIS dan menambahkan I5."""
    stop = _mock_http(
        8080, b"HTTP/1.0 200 OK\r\nServer: lighttpd/1.4.35\r\n\r\n"
    )
    try:
        sc = HomeGuardScanner(ports=[8080], timeout=0.5)
        h = sc.scan_host("127.0.0.1")
        assert h["severity"] == "KRITIS"
        assert "I5" in h["owasp"]
    finally:
        stop.set()


def test_scan_host_kredensial_bawaan():
    """Integrasi: kredensial bawaan terdeteksi -> temuan KRITIS I1/I9."""
    stop = _mock_http(
        9000, b"HTTP/1.0 200 OK\r\nServer: x\r\n\r\n", perlu_auth=True
    )
    try:
        sc = HomeGuardScanner(ports=[9000], timeout=0.8, check_creds=True)
        h = sc.scan_host("127.0.0.1")
        cred = [f for f in h["findings"] if f.get("default_credential")]
        assert cred, "kredensial bawaan seharusnya terdeteksi"
        assert h["severity"] == "KRITIS"
        assert "I1" in h["owasp"] and "I9" in h["owasp"]
    finally:
        stop.set()


def test_ekspor_pdf_valid():
    """build_pdf_bytes menghasilkan berkas PDF yang valid secara struktur."""
    laporan = {
        "versi": "0.1.0", "waktu": "2026-01-01", "target": "demo",
        "peringatan": "uji", "ringkasan": {
            "total_host": 1, "host_berisiko": 1, "skor_tertinggi": 90,
            "distribusi_owasp": {"I1": 1},
        },
        "hosts": [{
            "ip": "1.2.3.4", "vendor": "X", "mac": None,
            "severity": "KRITIS", "score": 90, "owasp": ["I1"],
            "findings": [{
                "port": 23, "service": "telnet", "severity": "KRITIS",
                "owasp": ["I1"], "note": "n", "recommendation": "r",
            }],
        }],
    }
    data = build_pdf_bytes(laporan)
    assert data[:8] == b"%PDF-1.4"
    assert data.rstrip().endswith(b"%%EOF")
