#!/usr/bin/env python3
"""Perangkat IoT tiruan untuk lingkungan lab virtual HomeGuard.

Membuka sekumpulan port TCP pada sebuah alamat IP dan mengirim banner
representatif per layanan, sehingga sebuah mesin (VM atau loopback lokal)
berperilaku seperti perangkat IoT nyata di mata pemindai. Skrip ini
memungkinkan pengujian lab pada paper direproduksi secara penuh.

Contoh (satu perangkat pada satu VM):

    python lab/mock_iot_device.py --ip 192.168.56.20 --ports 23,80,554,8080

Untuk mereplikasi SELURUH lab pada satu mesin Linux (via loopback
127.0.0.0/8), gunakan ``lab/run_lab.py`` yang membaca ``ground_truth.json``.

PERINGATAN ETIKA: hanya untuk lab milik sendiri. Jangan mengikat ke alamat
publik.
"""

from __future__ import annotations

import argparse
import socket
import threading
import time

# Banner representatif per port. Dipilih agar HomeGuard dapat memetakan
# layanan dan (untuk beberapa port) mendeteksi komponen usang -> +I5.
BANNER = {
    21: b"220 ProFTPD 1.3.5 Server ready\r\n",
    22: b"SSH-2.0-OpenSSH_7.4\r\n",
    23: b"\xff\xfb\x01login: ",
    80: b"HTTP/1.0 200 OK\r\nServer: lighttpd/1.4.35\r\n\r\n",
    443: b"HTTP/1.0 200 OK\r\nServer: nginx/1.10.3\r\n\r\n",
    554: b"RTSP/1.0 200 OK\r\nServer: GStreamer/1.14\r\n\r\n",
    631: b"HTTP/1.1 200 OK\r\nServer: CUPS/1.7\r\n\r\n",
    1883: b"",  # MQTT: broker biasanya tidak mengirim banner teks.
    1900: b"HTTP/1.1 200 OK\r\nServer: UPnP/1.0\r\n\r\n",
    5555: b"",  # ADB debug: tanpa banner teks.
    8080: b"HTTP/1.0 200 OK\r\nServer: lighttpd/1.4.35\r\n\r\n",
    8443: b"HTTP/1.0 200 OK\r\nServer: nginx/1.10.3\r\n\r\n",
    9100: b"",  # RAW/JetDirect: tanpa banner.
}

# Port yang berperilaku gaya HTTP (menerima request lebih dulu sebelum kirim).
HTTP_STYLE = {80, 443, 631, 1900, 8080, 8443}


def _serve(bind_ip: str, port: int, stop: threading.Event) -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind((bind_ip, port))
    except OSError as exc:
        print(f"  [!] gagal bind {bind_ip}:{port} -> {exc}")
        return
    srv.listen(8)
    srv.settimeout(0.3)
    banner = BANNER.get(port, b"")
    while not stop.is_set():
        try:
            conn, _ = srv.accept()
        except socket.timeout:
            continue
        except OSError:
            break
        try:
            if port in HTTP_STYLE:
                conn.settimeout(0.3)
                try:
                    conn.recv(512)
                except OSError:
                    pass
            if banner:
                conn.sendall(banner)
        except OSError:
            pass
        finally:
            conn.close()
    srv.close()


def start_device(bind_ip: str, ports: list, stop: threading.Event) -> list:
    """Nyalakan seluruh port sebuah perangkat tiruan; kembalikan thread-nya."""
    threads = []
    for port in ports:
        t = threading.Thread(target=_serve, args=(bind_ip, port, stop),
                             daemon=True)
        t.start()
        threads.append(t)
    return threads


def main() -> int:
    ap = argparse.ArgumentParser(description="Perangkat IoT tiruan HomeGuard.")
    ap.add_argument("--ip", default="127.0.0.1", help="alamat bind")
    ap.add_argument("--ports", required=True,
                    help="daftar port dipisah koma, mis. 23,80,554,8080")
    args = ap.parse_args()

    ports = [int(p) for p in args.ports.split(",") if p.strip()]
    stop = threading.Event()
    start_device(args.ip, ports, stop)
    print(f"[*] Perangkat tiruan aktif di {args.ip} pada port {ports}")
    print("    Tekan Ctrl+C untuk berhenti.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop.set()
        print("\n[*] Berhenti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
