"""Unit test untuk pemeriksaan TLS & header keamanan HTTP (tlscheck)."""

import socket
import threading
import time

from homeguard import tlscheck


def test_protokol_usang_terdeteksi():
    """Versi TLS usang harus menghasilkan temuan I7 (TINGGI)."""
    t = tlscheck._nilai_protokol("TLSv1", 443)
    assert t is not None
    assert t["severity"] == "TINGGI"
    assert "I7" in t["owasp"]


def test_protokol_modern_aman():
    """TLS 1.2/1.3 tidak menghasilkan temuan."""
    assert tlscheck._nilai_protokol("TLSv1.2", 443) is None
    assert tlscheck._nilai_protokol("TLSv1.3", 443) is None


def test_cipher_lemah_terdeteksi():
    """Cipher lemah (RC4/3DES) harus menghasilkan temuan I7."""
    assert tlscheck._nilai_cipher("ECDHE-RSA-RC4-SHA", 443) is not None
    assert tlscheck._nilai_cipher("DES-CBC3-SHA", 443) is not None
    assert tlscheck._nilai_cipher("ECDHE-RSA-AES256-GCM-SHA384", 443) is None


def test_header_hilang_terdeteksi():
    """Header keamanan yang hilang menghasilkan satu temuan I3."""
    resp = "HTTP/1.1 200 OK\r\nServer: test\r\n"
    temuan = tlscheck._periksa_header(resp, use_tls=True, port=443)
    assert len(temuan) == 1
    assert "I3" in temuan[0]["owasp"]
    # HSTS termasuk yang diperiksa saat use_tls.
    assert "HSTS" in temuan[0]["note"]


def test_header_lengkap_tidak_ada_temuan():
    """Bila semua header keamanan ada, tidak ada temuan."""
    resp = (
        "HTTP/1.1 200 OK\r\n"
        "X-Content-Type-Options: nosniff\r\n"
        "Content-Security-Policy: default-src 'self'\r\n"
        "X-Frame-Options: DENY\r\n"
        "Strict-Transport-Security: max-age=31536000\r\n"
    )
    assert tlscheck._periksa_header(resp, use_tls=True, port=443) == []


def test_check_http_headers_integrasi():
    """check_http_headers (plaintext) mendeteksi header yang hilang."""
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    port = srv.getsockname()[1]
    srv.listen(5)
    srv.settimeout(0.3)
    stop = threading.Event()

    def run():
        while not stop.is_set():
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                conn.recv(512)
                conn.sendall(b"HTTP/1.0 200 OK\r\nServer: x\r\n\r\n<html>")
            except OSError:
                pass
            finally:
                conn.close()
        srv.close()

    threading.Thread(target=run, daemon=True).start()
    time.sleep(0.15)
    try:
        temuan = tlscheck.check_http_headers(
            "127.0.0.1", port, timeout=0.5, use_tls=False
        )
        assert temuan and "I3" in temuan[0]["owasp"]
    finally:
        stop.set()
