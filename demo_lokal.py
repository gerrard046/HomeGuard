#!/usr/bin/env python3
"""Demo lokal HomeGuard tanpa perangkat/jaringan nyata.

Skrip ini menyalakan beberapa layanan IoT tiruan pada ``127.0.0.1``
(Telnet, HTTP dengan banner komponen usang, dan RTSP), lalu menjalankan
pipeline HomeGuard terhadapnya dan mencetak laporan. Berguna untuk mencoba
aplikasi dengan aman tanpa memindai jaringan apa pun.

Jalankan:

    python demo_lokal.py

PERINGATAN ETIKA: Pemindaian nyata hanya boleh pada jaringan milik/diizinkan.
"""

from __future__ import annotations

import socket
import threading
import time

from homeguard import HomeGuardScanner

# (port, banner yang dikirim server tiruan, apakah merespons gaya HTTP)
# Memakai port katalog non-privileged agar pemetaan OWASP tampil utuh:
#   2323 -> Telnet (KRITIS, I1/I2/I7)
#   8080 -> HTTP dengan banner komponen usang (lighttpd/1.4.35) -> +I5, naik KRITIS
#   8554 -> RTSP kamera (I2/I7)
LAYANAN_TIRUAN = [
    (2323, b"\xff\xfb\x01login: ", False),                 # Telnet
    (8080, b"HTTP/1.0 200 OK\r\nServer: lighttpd/1.4.35\r\n\r\n", True),
    (8554, b"RTSP/1.0 200 OK\r\nServer: GStreamer/1.14\r\n\r\n", False),
]


def _server(port: int, banner: bytes, http_gaya: bool, stop: threading.Event):
    """Jalankan satu server TCP tiruan yang mengirim banner saat diakses."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(5)
    srv.settimeout(0.3)
    while not stop.is_set():
        try:
            conn, _ = srv.accept()
        except socket.timeout:
            continue
        except OSError:
            break
        try:
            if http_gaya:
                conn.recv(256)
            conn.sendall(banner)
        except OSError:
            pass
        finally:
            conn.close()
    srv.close()


def main() -> None:
    stop = threading.Event()
    threads = []
    for port, banner, http_gaya in LAYANAN_TIRUAN:
        t = threading.Thread(
            target=_server, args=(port, banner, http_gaya, stop), daemon=True
        )
        t.start()
        threads.append(t)
    time.sleep(0.4)  # beri waktu server siap

    ports = [p for p, _, _ in LAYANAN_TIRUAN]
    print("Memindai host tiruan 127.0.0.1 pada port:", ports, "\n")

    scanner = HomeGuardScanner(ports=ports, timeout=0.5)
    host = scanner.scan_host("127.0.0.1")

    print(f"Severity host : {host['severity']}")
    print(f"Skor risiko   : {host['score']}")
    print(f"Kategori OWASP: {', '.join(host['owasp'])}\n")
    for f in host["findings"]:
        print(f"  Port {f['port']}/{f['service']} [{f['severity']}] "
              f"-> {', '.join(f['owasp'])}")
        print(f"     banner     : {f['banner']!r}")
        print(f"     catatan    : {f['note']}")
        print(f"     rekomendasi: {f['recommendation']}\n")

    stop.set()


if __name__ == "__main__":
    main()
