"""Unit test untuk modul pemindaian port & deteksi layanan (portscan).

Menggunakan server tiruan lokal pada ``127.0.0.1`` agar pengujian
deterministik tanpa bergantung pada jaringan eksternal.
"""

import socket
import threading
import time

from homeguard import portscan


def _mock_tcp(banner: bytes, http: bool = False):
    """Jalankan server TCP tiruan; kembalikan (port, stop_event)."""
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
                if http:
                    conn.recv(256)
                conn.sendall(banner)
            except OSError:
                pass
            finally:
                conn.close()
        srv.close()

    threading.Thread(target=run, daemon=True).start()
    time.sleep(0.15)
    return port, stop


def _port_bebas() -> int:
    """Kembalikan nomor port yang kemungkinan besar tertutup."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_scan_port_terbuka_dengan_banner():
    """Port terbuka harus terdeteksi beserta banner-nya."""
    port, stop = _mock_tcp(b"SSH-2.0-OpenSSH_8.9\r\n")
    try:
        hasil = portscan.scan_port("127.0.0.1", port, timeout=0.5)
        assert hasil["open"] is True
        assert "OpenSSH_8.9" in hasil["banner"]
    finally:
        stop.set()


def test_scan_port_tertutup():
    """Port tertutup harus dilaporkan tidak terbuka."""
    hasil = portscan.scan_port("127.0.0.1", _port_bebas(), timeout=0.3)
    assert hasil["open"] is False


def test_scan_host_socket_kembalikan_port_terbuka():
    """scan_host_socket hanya mengembalikan port yang terbuka."""
    port, stop = _mock_tcp(b"hello\r\n")
    try:
        hasil = portscan.scan_host_socket(
            "127.0.0.1", ports=[port], timeout=0.5
        )
        assert len(hasil) == 1
        assert hasil[0]["port"] == port
    finally:
        stop.set()


def test_parse_nmap_grepable():
    """Parser output grepable nmap hanya mengembalikan port berstatus open."""
    teks = (
        "Host: 192.168.1.5 ()\tPorts: "
        "23/open/tcp//telnet//Linux telnetd/, "
        "80/open/tcp//http//lighttpd 1.4.35/, "
        "443/closed/tcp//https///\n"
    )
    hasil = portscan._parse_nmap_grepable(teks)
    ports = {r["port"] for r in hasil}
    assert ports == {23, 80}
    assert all(r["open"] for r in hasil)


def test_scan_host_fallback_ke_socket(monkeypatch):
    """Bila nmap gagal, scan_host otomatis fallback ke pemindai socket."""
    port, stop = _mock_tcp(b"x\r\n")

    def _gagal(*args, **kwargs):
        raise RuntimeError("nmap tidak tersedia")

    monkeypatch.setattr(portscan, "scan_host_nmap", _gagal)
    try:
        hasil = portscan.scan_host(
            "127.0.0.1", ports=[port], timeout=0.5, gunakan_nmap=True
        )
        assert any(r["port"] == port for r in hasil)
    finally:
        stop.set()


def test_scan_udp_port_terbuka():
    """Port UDP yang merespons probe harus terdeteksi terbuka."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    port = srv.getsockname()[1]
    srv.settimeout(0.3)
    stop = threading.Event()

    def run():
        while not stop.is_set():
            try:
                _, addr = srv.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                break
            srv.sendto(b"pong", addr)
        srv.close()

    threading.Thread(target=run, daemon=True).start()
    time.sleep(0.15)
    try:
        hasil = portscan.scan_udp_port("127.0.0.1", port, timeout=0.5)
        assert hasil["open"] is True
        assert hasil["proto"] == "udp"
    finally:
        stop.set()
