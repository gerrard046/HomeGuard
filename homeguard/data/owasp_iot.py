"""Definisi kerangka OWASP IoT Top 10 (edisi 2018).

Modul ini menyediakan referensi statis untuk sepuluh kategori risiko keamanan
IoT teratas menurut OWASP. Setiap kategori diberi identitas ``I1``..``I10``
beserta nama dan deskripsi ringkas dalam Bahasa Indonesia, digunakan oleh modul
pemetaan kerentanan (``vulnmap``) dan antarmuka pengguna.

Referensi: OWASP Internet of Things Top 10 (2018).
"""

from __future__ import annotations

# Pemetaan kategori OWASP IoT Top 10 2018.
# Kunci  : kode kategori (I1..I10)
# Nilai  : dict berisi judul (Inggris asli ringkas), nama Indonesia, deskripsi.
OWASP_IOT_TOP_10 = {
    "I1": {
        "judul": "Weak, Guessable, or Hardcoded Passwords",
        "nama": "Kata Sandi Lemah, Mudah Ditebak, atau Tertanam",
        "deskripsi": (
            "Penggunaan kredensial yang mudah ditebak, dapat dibobol secara "
            "brute-force, atau tertanam permanen (hardcoded) di firmware, "
            "termasuk backdoor yang memungkinkan akses tidak sah."
        ),
    },
    "I2": {
        "judul": "Insecure Network Services",
        "nama": "Layanan Jaringan Tidak Aman",
        "deskripsi": (
            "Layanan jaringan yang berjalan pada perangkat dan terekspos, "
            "khususnya yang menghadap internet, yang dapat membahayakan "
            "kerahasiaan, integritas, atau ketersediaan informasi."
        ),
    },
    "I3": {
        "judul": "Insecure Ecosystem Interfaces",
        "nama": "Antarmuka Ekosistem Tidak Aman",
        "deskripsi": (
            "Antarmuka web, API backend, cloud, atau mobile dalam ekosistem "
            "yang tidak aman sehingga membahayakan perangkat atau komponen "
            "terkait, mis. kurangnya autentikasi/otorisasi dan enkripsi."
        ),
    },
    "I4": {
        "judul": "Lack of Secure Update Mechanism",
        "nama": "Tidak Ada Mekanisme Pembaruan Aman",
        "deskripsi": (
            "Ketiadaan kemampuan memperbarui perangkat secara aman: tanpa "
            "validasi firmware, tanpa pengiriman terenkripsi, tanpa anti-"
            "rollback, dan tanpa notifikasi perubahan keamanan."
        ),
    },
    "I5": {
        "judul": "Use of Insecure or Outdated Components",
        "nama": "Komponen Tidak Aman atau Usang",
        "deskripsi": (
            "Penggunaan komponen atau pustaka perangkat lunak yang usang/"
            "rentan, termasuk kustomisasi OS yang tidak aman dan komponen "
            "pihak ketiga dari rantai pasok yang membahayakan perangkat."
        ),
    },
    "I6": {
        "judul": "Insufficient Privacy Protection",
        "nama": "Perlindungan Privasi Tidak Memadai",
        "deskripsi": (
            "Informasi pribadi pengguna yang disimpan pada perangkat atau "
            "ekosistem digunakan secara tidak aman, tidak semestinya, atau "
            "tanpa izin."
        ),
    },
    "I7": {
        "judul": "Insecure Data Transfer and Storage",
        "nama": "Transfer dan Penyimpanan Data Tidak Aman",
        "deskripsi": (
            "Kurangnya enkripsi atau kontrol akses terhadap data sensitif "
            "saat diam (storage), saat transit (transfer), maupun saat "
            "diproses dalam ekosistem."
        ),
    },
    "I8": {
        "judul": "Lack of Device Management",
        "nama": "Tidak Ada Manajemen Perangkat",
        "deskripsi": (
            "Ketiadaan dukungan manajemen keamanan perangkat yang dipasang "
            "di produksi, meliputi manajemen aset, pembaruan, pemantauan, "
            "dan kemampuan respons insiden."
        ),
    },
    "I9": {
        "judul": "Insecure Default Settings",
        "nama": "Pengaturan Bawaan Tidak Aman",
        "deskripsi": (
            "Perangkat atau sistem dikirim dengan pengaturan bawaan yang "
            "tidak aman, atau tidak memberi pengguna kemampuan memodifikasi "
            "konfigurasi agar lebih aman."
        ),
    },
    "I10": {
        "judul": "Lack of Physical Hardening",
        "nama": "Tidak Ada Pengerasan Fisik",
        "deskripsi": (
            "Ketiadaan langkah pengerasan fisik sehingga penyerang potensial "
            "dapat memperoleh informasi sensitif yang membantu serangan jarak "
            "jauh atau mengambil alih kendali perangkat secara lokal."
        ),
    },
}


def get_category(code: str) -> dict:
    """Kembalikan definisi kategori OWASP IoT untuk ``code`` (mis. ``"I2"``).

    Mengembalikan dict kosong jika kode tidak dikenal sehingga pemanggil tetap
    aman dari ``KeyError``.
    """
    return OWASP_IOT_TOP_10.get(code.upper(), {})


def describe(codes) -> list:
    """Kembalikan daftar deskripsi ringkas untuk sekumpulan kode kategori.

    Setiap entri berformat ``"I2 - Layanan Jaringan Tidak Aman"``.
    """
    hasil = []
    for code in codes:
        kategori = get_category(code)
        nama = kategori.get("nama", "Tidak diketahui")
        hasil.append(f"{code.upper()} - {nama}")
    return hasil
