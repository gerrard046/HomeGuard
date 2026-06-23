#!/usr/bin/env python3
"""Server IoT tiruan yang tetap hidup, untuk demo UI Streamlit HomeGuard.

Berbeda dengan ``demo_lokal.py`` (yang memindai lalu langsung keluar), skrip
ini hanya MENYALAKAN layanan IoT tiruan pada ``127.0.0.1`` dan MEMBIARKANNYA
TETAP BERJALAN. Dengan begitu Anda dapat memindainya dari antarmuka web
Streamlit (atau CLI) di jendela terminal lain, lalu mengambil tangkapan layar
hasil "KRITIS" yang menarik untuk presentasi.

Cara pakai (dua jendela terminal):

    # Terminal 1 -> biarkan tetap terbuka:
    python demo_server.py

    # Terminal 2:
    python -m streamlit run app.py
    # Di UI: mode "Host tunggal", IP 127.0.0.1, Port 2323,8080,8554

Tekan Ctrl+C pada Terminal 1 untuk menghentikan server tiruan.

PERINGATAN ETIKA: Pemindaian nyata hanya boleh pada jaringan milik/diizinkan.
"""

from __future__ import annotations

import socket
import threading
import time

# (port, banner yang dikirim server tiruan, apakah merespons gaya HTTP)
#   2323 -> Telnet (KRITIS, I1/I2/I7)
#   8080 -> HTTP dengan banner komponen usang (lighttpd/1.4.35) -> +I5, KRITIS
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
    for port, banner, http_gaya in LAYANAN_TIRUAN:
        t = threading.Thread(
            target=_server, args=(port, banner, http_gaya, stop), daemon=True
        )
        t.start()
    time.sleep(0.4)  # beri waktu server siap

    ports = ", ".join(str(p) for p, _, _ in LAYANAN_TIRUAN)
    print("=" * 60)
    print(" Server IoT tiruan AKTIF pada 127.0.0.1")
    print(f" Port    : {ports}")
    print(" Pindai  : mode 'Host tunggal', IP 127.0.0.1, port di atas")
    print(" Berhenti: tekan Ctrl+C")
    print("=" * 60)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nMenghentikan server tiruan...")
        stop.set()
        time.sleep(0.5)


if __name__ == "__main__":
    main()
