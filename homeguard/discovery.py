"""Modul 1 — Penemuan host (host discovery) pada jaringan lokal.

Tanggung jawab modul:
    - TCP ping: deteksi host hidup tanpa hak akses root (pakai socket murni).
    - Parsing tabel ARP sistem (``ip neigh`` di Linux atau ``arp -a``).
    - Normalisasi alamat MAC dari berbagai format pemisah.
    - Lookup vendor dari prefiks OUI alamat MAC.
    - Deteksi subnet lokal secara otomatis.
    - Ekspansi rentang CIDR menjadi daftar IP host (tanpa network/broadcast).

PERINGATAN ETIKA: Gunakan hanya pada jaringan milik sendiri atau yang Anda
miliki izin eksplisit untuk memindainya.
"""

from __future__ import annotations

import ipaddress
import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor

from .data.oui import lookup_oui

# Port yang dicoba saat TCP ping (port umum yang sering terbuka pada perangkat).
PORT_TCP_PING_DEFAULT = (80, 443, 22, 23, 8080, 554, 53)

# Pola heksadigit MAC (12 nibble) tanpa pemisah.
_RE_HEKSA = re.compile(r"^[0-9a-fA-F]{12}$")


def normalize_mac(mac: str):
    """Normalkan alamat MAC ke format kanonik ``AA:BB:CC:DD:EE:FF``.

    Menerima berbagai pemisah: titik dua (``:``), strip (``-``), titik gaya
    Cisco (``b827.eb12.3456``), atau tanpa pemisah sama sekali. Mengembalikan
    string MAC huruf besar dengan pemisah titik dua, atau ``None`` bila input
    bukan MAC valid (jumlah heksadigit bukan 12).
    """
    if not mac or not isinstance(mac, str):
        return None
    # Buang semua karakter selain heksadigit.
    heksa = re.sub(r"[^0-9a-fA-F]", "", mac)
    if not _RE_HEKSA.match(heksa):
        return None
    heksa = heksa.upper()
    return ":".join(heksa[i : i + 2] for i in range(0, 12, 2))


def lookup_vendor(mac: str) -> str:
    """Kembalikan nama vendor untuk ``mac`` berdasarkan prefiks OUI.

    MAC dinormalkan terlebih dahulu; bila tidak valid atau prefiks tidak
    dikenal, mengembalikan ``"Unknown"``.
    """
    normal = normalize_mac(mac)
    if normal is None:
        return "Unknown"
    return lookup_oui(normal)


def is_private_ip(ip: str) -> bool:
    """Kembalikan ``True`` bila ``ip`` berada dalam rentang privat (RFC 1918)."""
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def expand_cidr(cidr: str) -> list:
    """Ekspansi notasi CIDR menjadi daftar alamat IP host (sebagai string).

    Alamat network dan broadcast dikecualikan untuk prefiks <= /30. Untuk /31
    dan /32, seluruh alamat dikembalikan (mengikuti perilaku ``hosts()`` dari
    modul ``ipaddress``). Mengembalikan daftar kosong bila CIDR tidak valid.
    """
    try:
        net = ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return []
    return [str(h) for h in net.hosts()]


# --- Parsing tabel ARP --------------------------------------------------------

# Pola IP versi 4 sederhana.
_RE_IPV4 = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")
# Pola MAC dengan pemisah ':' atau '-' (6 oktet).
_RE_MAC = re.compile(r"\b([0-9a-fA-F]{1,2}(?:[:-][0-9a-fA-F]{1,2}){5})\b")


def parse_ip_neigh(output: str) -> list:
    """Parse keluaran perintah ``ip neigh`` (Linux) menjadi daftar host.

    Format baris tipikal::

        192.168.1.1 dev eth0 lladdr b8:27:eb:12:34:56 REACHABLE
        192.168.1.9 dev eth0 FAILED          # tanpa MAC -> diabaikan

    Mengembalikan daftar dict ``{"ip": ..., "mac": ...}`` dengan MAC ternormal.
    Baris tanpa alamat MAC valid diabaikan.
    """
    hasil = []
    for baris in output.splitlines():
        baris = baris.strip()
        if not baris:
            continue
        m_ip = _RE_IPV4.search(baris)
        if not m_ip:
            continue
        # Cari MAC hanya setelah kata kunci 'lladdr' bila ada, jika tidak,
        # cari di seluruh baris.
        m_mac = _RE_MAC.search(baris)
        if not m_mac:
            continue
        mac = normalize_mac(m_mac.group(1))
        if mac is None:
            continue
        hasil.append({"ip": m_ip.group(1), "mac": mac})
    return hasil


def parse_arp_a(output: str) -> list:
    """Parse keluaran perintah ``arp -a`` menjadi daftar host.

    Format baris tipikal::

        router (192.168.1.1) at b8:27:eb:12:34:56 [ether] on eth0
        ? (192.168.1.7) at <incomplete> on eth0   # tanpa MAC -> diabaikan

    Mengembalikan daftar dict ``{"ip": ..., "mac": ...}`` dengan MAC ternormal.
    Baris tanpa alamat MAC valid (mis. ``<incomplete>``) diabaikan.
    """
    hasil = []
    for baris in output.splitlines():
        baris = baris.strip()
        if not baris:
            continue
        m_ip = _RE_IPV4.search(baris)
        if not m_ip:
            continue
        m_mac = _RE_MAC.search(baris)
        if not m_mac:
            continue
        mac = normalize_mac(m_mac.group(1))
        if mac is None:
            continue
        hasil.append({"ip": m_ip.group(1), "mac": mac})
    return hasil


def baca_tabel_arp() -> dict:
    """Baca tabel ARP sistem dan kembalikan pemetaan ``ip -> mac``.

    Mencoba ``ip neigh`` lebih dahulu (Linux modern), lalu fallback ke
    ``arp -a``. Mengembalikan dict kosong bila keduanya gagal (mis. perintah
    tidak tersedia).
    """
    pemetaan = {}
    perintah_parser = [
        (["ip", "neigh"], parse_ip_neigh),
        (["arp", "-a"], parse_arp_a),
    ]
    for perintah, parser in perintah_parser:
        try:
            keluaran = subprocess.run(
                perintah,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        for entri in parser(keluaran):
            pemetaan.setdefault(entri["ip"], entri["mac"])
        if pemetaan:
            break
    return pemetaan


# --- Deteksi subnet & TCP ping ------------------------------------------------

def detect_local_subnet(prefix: int = 24):
    """Deteksi subnet lokal secara otomatis (default /24).

    Menggunakan trik socket UDP: membuka koneksi semu ke alamat publik untuk
    mengetahui IP lokal yang dipakai sistem (tanpa benar-benar mengirim data).
    Mengembalikan string CIDR (mis. ``"192.168.1.0/24"``) atau ``None`` bila
    gagal.
    """
    ip_lokal = None
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_lokal = s.getsockname()[0]
    except OSError:
        ip_lokal = None
    finally:
        s.close()
    if not ip_lokal:
        return None
    try:
        jaringan = ipaddress.ip_network(f"{ip_lokal}/{prefix}", strict=False)
    except ValueError:
        return None
    return str(jaringan)


def tcp_ping(ip: str, ports=PORT_TCP_PING_DEFAULT, timeout: float = 0.5) -> bool:
    """Deteksi apakah ``ip`` hidup dengan mencoba koneksi TCP ke ``ports``.

    Mengembalikan ``True`` segera setelah salah satu port menerima koneksi
    (host hidup), atau ``False`` bila seluruh percobaan gagal/timeout. Metode
    ini tidak memerlukan hak akses root.
    """
    for port in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            if s.connect_ex((ip, port)) == 0:
                return True
        except OSError:
            pass
        finally:
            s.close()
    return False


def discover_hosts(
    subnet: str = None,
    ports=PORT_TCP_PING_DEFAULT,
    timeout: float = 0.5,
    max_workers: int = 50,
) -> list:
    """Temukan host hidup pada ``subnet`` (CIDR) memakai TCP ping paralel.

    Bila ``subnet`` tidak diberikan, subnet lokal dideteksi otomatis. Hasil
    diperkaya dengan informasi MAC dan vendor dari tabel ARP sistem bila
    tersedia.

    Mengembalikan daftar dict host ``{"ip", "mac", "vendor"}`` terurut menurut
    alamat IP.

    PERINGATAN: Jalankan hanya pada jaringan milik/diizinkan.
    """
    if subnet is None:
        subnet = detect_local_subnet()
    if not subnet:
        return []

    daftar_ip = expand_cidr(subnet)
    if not daftar_ip:
        return []

    tabel_arp = baca_tabel_arp()
    hidup = []

    def _cek(ip):
        return ip if tcp_ping(ip, ports=ports, timeout=timeout) else None

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for ip in pool.map(_cek, daftar_ip):
            if ip:
                hidup.append(ip)

    hosts = []
    for ip in hidup:
        mac = tabel_arp.get(ip)
        vendor = lookup_vendor(mac) if mac else "Unknown"
        hosts.append({"ip": ip, "mac": mac, "vendor": vendor})

    hosts.sort(key=lambda h: tuple(int(o) for o in h["ip"].split(".")))
    return hosts
