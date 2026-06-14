"""Pemeriksaan keamanan TLS/HTTPS dan header HTTP — pustaka standar.

Modul ini menambah kedalaman analisis pada layanan web/terenkripsi tanpa
dependensi eksternal (hanya ``ssl`` dan ``socket``):

    - **TLS:** deteksi protokol usang (SSLv3/TLS 1.0/1.1), cipher lemah
      (RC4/3DES/NULL/EXPORT), serta sertifikat kedaluwarsa / akan kedaluwarsa /
      self-signed.
    - **Header HTTP:** deteksi ketiadaan header keamanan penting
      (HSTS, X-Frame-Options, Content-Security-Policy, X-Content-Type-Options).

Temuan dipetakan ke OWASP IoT Top 10: transport tidak aman -> I7
(Insecure Data Transfer and Storage); antarmuka web lemah -> I3
(Insecure Ecosystem Interfaces).

PERINGATAN ETIKA: gunakan hanya pada jaringan milik/diizinkan. Pemeriksaan ini
bersifat pasif/non-intrusif (handshake TLS biasa dan satu permintaan HTTP GET).
"""

from __future__ import annotations

import socket
import ssl

from .data.iot_ports import (
    SEVERITY_RENDAH,
    SEVERITY_SEDANG,
    SEVERITY_TINGGI,
)

# Port yang diperlakukan sebagai TLS dan sebagai HTTP (plaintext) untuk header.
TLS_PORT_DEFAULT = (443, 8443)
HTTP_PORT_PLAIN = (80, 8080, 5000, 9000)

# Protokol TLS yang dianggap usang/lemah.
PROTOKOL_USANG = {"SSLv3", "TLSv1", "TLSv1.1"}
# Substring nama cipher yang dianggap lemah.
CIPHER_LEMAH = ("RC4", "3DES", "DES-", "NULL", "EXP", "MD5", "ANON", "ADH")

# Ambang peringatan sertifikat akan kedaluwarsa (hari).
AMBANG_KEDALUWARSA_HARI = 30


def _temuan(port, severity, owasp, note, rekomendasi, service="tls"):
    """Bentuk dict temuan seragam dengan modul lain."""
    from .vulnmap import SEVERITY_BASE_SCORE
    return {
        "port": port,
        "service": service,
        "severity": severity,
        "owasp": list(owasp),
        "score": SEVERITY_BASE_SCORE[severity],
        "note": note,
        "recommendation": rekomendasi,
        "banner": "",
        "outdated": False,
        "tls": True,
    }


def _nilai_protokol(versi: str, port: int):
    """Kembalikan temuan bila versi protokol TLS usang, atau ``None``."""
    if versi in PROTOKOL_USANG:
        return _temuan(
            port, SEVERITY_TINGGI, ["I7"],
            f"Protokol terenkripsi usang dinegosiasikan ({versi}); rentan "
            "penyadapan/dekripsi.",
            "Nonaktifkan SSLv3/TLS 1.0/1.1, gunakan minimal TLS 1.2.",
        )
    return None


def _nilai_cipher(cipher_name: str, port: int):
    """Kembalikan temuan bila cipher lemah, atau ``None``."""
    if not cipher_name:
        return None
    nama = cipher_name.upper()
    if any(lemah in nama for lemah in CIPHER_LEMAH):
        return _temuan(
            port, SEVERITY_TINGGI, ["I7"],
            f"Cipher suite lemah digunakan ({cipher_name}).",
            "Konfigurasikan cipher modern (AES-GCM/ChaCha20), nonaktifkan "
            "RC4/3DES/NULL/EXPORT.",
        )
    return None


def _periksa_header(header_teks: str, use_tls: bool, port: int):
    """Periksa ketiadaan header keamanan; kembalikan daftar temuan."""
    teks = (header_teks or "").lower()
    wajib = {
        "x-content-type-options": "X-Content-Type-Options",
        "content-security-policy": "Content-Security-Policy",
        "x-frame-options": "X-Frame-Options",
    }
    if use_tls:
        wajib["strict-transport-security"] = "Strict-Transport-Security (HSTS)"
    hilang = [nama for kunci, nama in wajib.items() if kunci not in teks]
    if not hilang:
        return []
    return [_temuan(
        port, SEVERITY_RENDAH, ["I3"],
        "Header keamanan HTTP tidak ada: " + ", ".join(hilang) + ".",
        "Tambahkan header keamanan tersebut pada respons web.",
        service="http",
    )]


def check_tls_port(ip: str, port: int, timeout: float = 3.0) -> list:
    """Periksa keamanan TLS pada satu port; kembalikan daftar temuan."""
    temuan = []

    # 1) Handshake permisif untuk membaca versi & cipher yang dinegosiasikan.
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.minimum_version = ssl.TLSVersion.TLSv1  # izinkan deteksi versi tua
    except (ValueError, OSError):
        pass
    try:
        with socket.create_connection((ip, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=ip) as ss:
                versi = ss.version() or ""
                cipher = (ss.cipher() or ("",))[0]
    except (OSError, ssl.SSLError, ValueError):
        return temuan  # bukan layanan TLS / gagal handshake

    for t in (_nilai_protokol(versi, port), _nilai_cipher(cipher, port)):
        if t:
            temuan.append(t)

    # 2) Handshake dengan validasi rantai (tanpa cek hostname, karena target IP)
    #    untuk mendeteksi sertifikat kedaluwarsa / self-signed / akan kedaluwarsa.
    ctx_v = ssl.create_default_context()
    ctx_v.check_hostname = False
    try:
        with socket.create_connection((ip, port), timeout=timeout) as sock:
            with ctx_v.wrap_socket(sock, server_hostname=ip) as ss:
                cert = ss.getpeercert() or {}
        # Tervalidasi: cek masa berlaku tersisa.
        not_after = cert.get("notAfter")
        if not_after:
            import time
            sisa = (ssl.cert_time_to_seconds(not_after) - time.time()) / 86400
            if sisa < AMBANG_KEDALUWARSA_HARI:
                temuan.append(_temuan(
                    port, SEVERITY_RENDAH, ["I7"],
                    f"Sertifikat akan kedaluwarsa dalam {int(sisa)} hari.",
                    "Perbarui sertifikat sebelum kedaluwarsa.",
                ))
    except ssl.SSLCertVerificationError as exc:
        alasan = str(exc).lower()
        if "expired" in alasan:
            temuan.append(_temuan(
                port, SEVERITY_SEDANG, ["I7"],
                "Sertifikat TLS sudah kedaluwarsa.",
                "Terbitkan/instal sertifikat yang masih berlaku.",
            ))
        elif "self" in alasan and "signed" in alasan:
            temuan.append(_temuan(
                port, SEVERITY_RENDAH, ["I7"],
                "Sertifikat TLS self-signed (tidak tepercaya).",
                "Gunakan sertifikat dari CA tepercaya bila perangkat "
                "menghadap publik.",
            ))
    except (OSError, ssl.SSLError, ValueError):
        pass

    return temuan


def check_http_headers(ip: str, port: int, timeout: float = 3.0,
                       use_tls: bool = False) -> list:
    """Ambil respons HTTP dan periksa header keamanannya."""
    permintaan = (
        f"GET / HTTP/1.0\r\nHost: {ip}\r\n"
        "User-Agent: HomeGuard\r\nConnection: close\r\n\r\n"
    ).encode("ascii", "ignore")
    try:
        raw = socket.create_connection((ip, port), timeout=timeout)
    except OSError:
        return []
    try:
        if use_tls:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(raw, server_hostname=ip)
        else:
            sock = raw
        sock.settimeout(timeout)
        sock.sendall(permintaan)
        data = b""
        while b"\r\n\r\n" not in data and len(data) < 8192:
            potongan = sock.recv(2048)
            if not potongan:
                break
            data += potongan
    except (OSError, ssl.SSLError):
        return []
    finally:
        try:
            sock.close()
        except (OSError, UnboundLocalError, NameError):
            raw.close()
    header_teks = data.split(b"\r\n\r\n", 1)[0].decode("latin-1", "ignore")
    return _periksa_header(header_teks, use_tls, port)


def check_host_tls(ip: str, open_ports, timeout: float = 3.0) -> list:
    """Jalankan pemeriksaan TLS & header pada port relevan sebuah host.

    ``open_ports`` adalah daftar dict port (dari portscan). Mengembalikan daftar
    temuan untuk digabungkan ke penilaian host.
    """
    temuan = []
    ports = set()
    for p in open_ports or []:
        ports.add(p.get("port") if isinstance(p, dict) else p)

    for port in sorted(p for p in ports if p in TLS_PORT_DEFAULT):
        temuan += check_tls_port(ip, port, timeout=timeout)
        temuan += check_http_headers(ip, port, timeout=timeout, use_tls=True)
    for port in sorted(p for p in ports if p in HTTP_PORT_PLAIN):
        temuan += check_http_headers(ip, port, timeout=timeout, use_tls=False)
    return temuan
