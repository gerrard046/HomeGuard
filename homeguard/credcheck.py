"""Pemeriksaan kredensial bawaan (default credentials) — OPSIONAL & OPT-IN.

Modul ini menguji apakah sebuah perangkat masih memakai kredensial bawaan
pabrik yang umum (mis. admin/admin) pada layanan Telnet dan HTTP Basic Auth.
Penggunaan kredensial bawaan adalah kategori OWASP IoT I1 (Weak, Guessable,
or Hardcoded Passwords) dan I9 (Insecure Default Settings), serta merupakan
vektor utama yang dieksploitasi botnet Mirai.

SIFAT DAN ETIKA
    - Bersifat NON-DESTRUKTIF: hanya mencoba autentikasi (login) lalu membaca
      respons; tidak mengubah konfigurasi atau data apa pun.
    - Bersifat OPT-IN: hanya dijalankan bila pengguna mengaktifkannya secara
      eksplisit (mis. opsi ``--check-creds``).
    - Daftar kredensial sengaja dibatasi pada kombinasi bawaan yang sangat
      umum untuk menghindari perilaku brute-force.
    - WAJIB hanya digunakan pada perangkat di jaringan milik sendiri atau yang
      Anda miliki izin eksplisit untuk mengujinya. Pengujian tanpa izin dapat
      melanggar hukum.
"""

from __future__ import annotations

import base64
import socket

from .data.iot_ports import SEVERITY_KRITIS

# Daftar kredensial bawaan yang sangat umum (vendor defaults). Dibatasi kecil
# secara sengaja agar tidak menjadi alat brute-force.
DEFAULT_CREDENTIALS = [
    ("admin", "admin"),
    ("admin", ""),
    ("admin", "password"),
    ("admin", "1234"),
    ("root", "root"),
    ("root", ""),
    ("root", "admin"),
    ("user", "user"),
    ("support", "support"),
    ("admin", "12345"),
]

# Port yang diperlakukan sebagai HTTP untuk pemeriksaan Basic Auth.
_PORT_HTTP = {80, 8080, 8000, 5000, 9000}
# Port yang diperlakukan sebagai Telnet.
_PORT_TELNET = {23, 2323}


def _periksa_http_basic(ip: str, port: int, timeout: float):
    """Periksa HTTP Basic Auth dengan kredensial bawaan pada satu port.

    Mengembalikan tuple ``(user, password)`` bila kredensial bawaan diterima,
    atau ``None``. Hanya menangani skema Basic (bukan form/digest).
    """
    def _minta(auth_header: str = "") -> str:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((ip, port))
            permintaan = f"GET / HTTP/1.0\r\nHost: {ip}\r\n"
            if auth_header:
                permintaan += f"Authorization: {auth_header}\r\n"
            permintaan += "Connection: close\r\n\r\n"
            sock.sendall(permintaan.encode("ascii", "ignore"))
            return sock.recv(1024).decode("latin-1", "ignore")
        except OSError:
            return ""
        finally:
            sock.close()

    awal = _minta()
    if not awal:
        return None
    baris_status = awal.splitlines()[0] if awal.splitlines() else ""
    # Hanya lanjut bila server memang meminta Basic Auth.
    if "401" not in baris_status or "basic" not in awal.lower():
        return None

    for user, pwd in DEFAULT_CREDENTIALS:
        token = base64.b64encode(f"{user}:{pwd}".encode()).decode("ascii")
        resp = _minta(f"Basic {token}")
        status = resp.splitlines()[0] if resp.splitlines() else ""
        if any(kode in status for kode in ("200", "301", "302", "303")):
            return (user, pwd)
    return None


def _periksa_telnet(ip: str, port: int, timeout: float):
    """Periksa login Telnet dengan kredensial bawaan (best-effort).

    Mengembalikan tuple ``(user, password)`` bila terindikasi login berhasil,
    atau ``None``. Bersifat heuristik karena prompt Telnet bervariasi.
    """
    # Batasi percobaan untuk menghindari penguncian akun pada perangkat.
    for user, pwd in DEFAULT_CREDENTIALS[:5]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((ip, port))
            awal = sock.recv(1024).decode("latin-1", "ignore").lower()
            if "login" not in awal and "username" not in awal:
                return None
            sock.sendall((user + "\r\n").encode("ascii", "ignore"))
            tanya_pwd = sock.recv(1024).decode("latin-1", "ignore").lower()
            if "password" in tanya_pwd:
                sock.sendall((pwd + "\r\n").encode("ascii", "ignore"))
            hasil = sock.recv(1024).decode("latin-1", "ignore").lower()
            gagal = any(k in hasil for k in
                        ("incorrect", "fail", "denied", "invalid", "login"))
            sukses = any(p in hasil for p in ("#", "$", ">", "welcome"))
            if sukses and not gagal:
                return (user, pwd)
        except OSError:
            pass
        finally:
            sock.close()
    return None


def check_host_credentials(ip: str, open_ports, timeout: float = 2.0) -> list:
    """Periksa kredensial bawaan pada port terbuka relevan sebuah host.

    ``open_ports`` adalah daftar dict port (dari modul portscan). Mengembalikan
    daftar temuan kredensial bawaan; setiap temuan dipetakan ke OWASP I1 & I9
    dengan severity KRITIS dan dapat digabungkan ke penilaian host.
    """
    temuan = []
    for p in open_ports or []:
        port = p.get("port") if isinstance(p, dict) else p
        if port in _PORT_HTTP:
            cred = _periksa_http_basic(ip, port, timeout)
            layanan = "http"
        elif port in _PORT_TELNET:
            cred = _periksa_telnet(ip, port, timeout)
            layanan = "telnet"
        else:
            continue
        if cred:
            user, pwd = cred
            temuan.append({
                "port": port,
                "service": layanan,
                "severity": SEVERITY_KRITIS,
                "owasp": ["I1", "I9"],
                "score": 90,
                "note": (
                    f"Kredensial bawaan diterima pada {layanan} "
                    f"(user='{user}', password='{pwd or '<kosong>'}'). "
                    "Ini vektor utama botnet Mirai."
                ),
                "recommendation": (
                    "SEGERA ganti kredensial bawaan dengan kata sandi kuat "
                    "yang unik dan nonaktifkan akun bawaan bila memungkinkan."
                ),
                "banner": "",
                "outdated": False,
                "default_credential": True,
            })
    return temuan
