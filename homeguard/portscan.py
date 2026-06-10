"""Modul 2 & 3 — Pemindaian port (TCP connect) dan deteksi layanan/versi.

Fitur:
    - TCP connect scan paralel memakai ``ThreadPoolExecutor`` (tanpa root).
    - Banner grabbing: membaca banner layanan dan, untuk HTTP, mengirim
      permintaan ``HEAD`` sederhana untuk memperoleh header ``Server``.
    - Deteksi layanan + versi dari banner dan dari katalog port IoT.
    - Integrasi OPSIONAL dengan ``nmap -sV``; bila nmap tidak tersedia atau
      gagal, otomatis fallback ke pemindai socket murni.

PERINGATAN ETIKA: Pindai hanya host pada jaringan milik/diizinkan.
"""

from __future__ import annotations

import re
import shutil
import socket
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

from .data.iot_ports import IOT_PORTS

# Daftar port default yang dipindai (port IoT umum dari katalog).
PORT_DEFAULT = sorted(IOT_PORTS.keys())

# Port yang diperlakukan sebagai layanan HTTP untuk banner grabbing khusus.
PORT_HTTP = {80, 8080, 5000, 9000}


def _grab_banner(sock: socket.socket, port: int, timeout: float) -> str:
    """Ambil banner dari soket yang sudah terkoneksi.

    Untuk port HTTP dikirim permintaan ``HEAD`` agar server membalas header.
    Untuk port lain, langsung membaca banner yang dikirim server (mis. SSH,
    FTP, Telnet). Mengembalikan string banner yang sudah dirapikan, atau
    string kosong.
    """
    sock.settimeout(timeout)
    try:
        if port in PORT_HTTP:
            permintaan = (
                "HEAD / HTTP/1.0\r\nHost: scan\r\n"
                "User-Agent: HomeGuard\r\n\r\n"
            )
            sock.sendall(permintaan.encode("ascii", "ignore"))
        data = sock.recv(1024)
    except OSError:
        return ""
    teks = data.decode("latin-1", "ignore").strip()
    if port in PORT_HTTP:
        # Ambil baris header 'Server:' bila ada untuk banner yang ringkas.
        for baris in teks.splitlines():
            if baris.lower().startswith("server:"):
                return baris.split(":", 1)[1].strip()
        # Bila tak ada header Server, kembalikan baris status pertama.
        baris_pertama = teks.splitlines()[0] if teks.splitlines() else ""
        return baris_pertama
    return teks


def _deteksi_versi(banner: str) -> str:
    """Ekstrak indikasi versi sederhana dari banner (mis. ``Apache/2.4.7``)."""
    if not banner:
        return ""
    m = re.search(r"([A-Za-z][\w.+-]*[/_]\d[\w.]*)", banner)
    return m.group(1) if m else ""


def scan_port(ip: str, port: int, timeout: float = 1.0) -> dict:
    """Pindai satu port pada ``ip`` dengan TCP connect dan banner grabbing.

    Mengembalikan dict ``{"port", "open", "service", "version", "banner"}``.
    ``open`` bernilai ``False`` bila port tertutup/terfilter.
    """
    hasil = {
        "port": port,
        "open": False,
        "service": "",
        "version": "",
        "banner": "",
    }
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        if sock.connect_ex((ip, port)) != 0:
            return hasil
        hasil["open"] = True
        banner = _grab_banner(sock, port, timeout)
        hasil["banner"] = banner
        hasil["version"] = _deteksi_versi(banner)
        profil = IOT_PORTS.get(port)
        hasil["service"] = profil["service"] if profil else ""
    except OSError:
        return hasil
    finally:
        sock.close()
    return hasil


def scan_host_socket(
    ip: str,
    ports=PORT_DEFAULT,
    timeout: float = 1.0,
    max_workers: int = 100,
) -> list:
    """Pindai banyak port pada ``ip`` memakai socket murni secara paralel.

    Mengembalikan daftar dict port yang TERBUKA (terurut menurut nomor port).
    """
    terbuka = []

    def _cek(port):
        return scan_port(ip, port, timeout=timeout)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for hasil in pool.map(_cek, ports):
            if hasil["open"]:
                terbuka.append(hasil)

    terbuka.sort(key=lambda r: r["port"])
    return terbuka


# --- Integrasi nmap opsional --------------------------------------------------

def nmap_tersedia() -> bool:
    """Kembalikan ``True`` bila biner ``nmap`` tersedia di PATH."""
    return shutil.which("nmap") is not None


def _parse_nmap_grepable(teks: str) -> list:
    """Parse keluaran nmap format grepable (``-oG``) menjadi daftar port.

    Mencari baris ``Ports:`` lalu mengekstrak entri
    ``port/state/proto//service//version/``. Hanya port berstatus ``open``
    yang dikembalikan.
    """
    terbuka = []
    for baris in teks.splitlines():
        if "Ports:" not in baris:
            continue
        bagian_ports = baris.split("Ports:", 1)[1]
        for entri in bagian_ports.split(","):
            kolom = entri.strip().split("/")
            if len(kolom) < 5:
                continue
            try:
                port = int(kolom[0])
            except ValueError:
                continue
            state = kolom[1]
            if state != "open":
                continue
            service = kolom[4]
            version = kolom[6] if len(kolom) > 6 else ""
            terbuka.append(
                {
                    "port": port,
                    "open": True,
                    "service": service,
                    "version": version.strip(),
                    "banner": version.strip(),
                }
            )
    terbuka.sort(key=lambda r: r["port"])
    return terbuka


def scan_host_nmap(
    ip: str,
    ports=PORT_DEFAULT,
    timeout: float = 1.0,
) -> list:
    """Pindai ``ip`` dengan ``nmap -sV`` dan kembalikan daftar port terbuka.

    Memunculkan ``RuntimeError`` bila nmap tidak tersedia atau gagal dieksekusi
    sehingga pemanggil dapat melakukan fallback ke socket.
    """
    if not nmap_tersedia():
        raise RuntimeError("nmap tidak tersedia di sistem")

    daftar_port = ",".join(str(p) for p in ports)
    with tempfile.NamedTemporaryFile(suffix=".gnmap") as berkas:
        perintah = [
            "nmap",
            "-sV",
            "-Pn",
            "-p",
            daftar_port,
            "-oG",
            berkas.name,
            ip,
        ]
        try:
            subprocess.run(
                perintah,
                capture_output=True,
                text=True,
                timeout=max(30, int(timeout * len(ports)) + 30),
                check=False,
            )
            with open(berkas.name, "r", encoding="utf-8", errors="ignore") as fh:
                keluaran = fh.read()
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError(f"eksekusi nmap gagal: {exc}") from exc
    return _parse_nmap_grepable(keluaran)


def scan_host(
    ip: str,
    ports=PORT_DEFAULT,
    timeout: float = 1.0,
    gunakan_nmap: bool = False,
    max_workers: int = 100,
) -> list:
    """Pindai ``ip`` memakai nmap (bila diminta & tersedia) atau socket murni.

    Bila ``gunakan_nmap=True`` namun nmap gagal/tidak ada, otomatis fallback ke
    pemindai socket murni. Mengembalikan daftar dict port terbuka.
    """
    if gunakan_nmap:
        try:
            return scan_host_nmap(ip, ports=ports, timeout=timeout)
        except RuntimeError:
            # Fallback otomatis ke socket murni.
            pass
    return scan_host_socket(
        ip, ports=ports, timeout=timeout, max_workers=max_workers
    )
