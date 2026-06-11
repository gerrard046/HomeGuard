# Panduan Kontribusi & Pengembangan HomeGuard

Terima kasih atas minat Anda mengembangkan HomeGuard. Dokumen ini menjelaskan
cara menyiapkan lingkungan, konvensi proyek, serta cara menambah fitur umum.

> ⚠️ **Etika:** Setiap pengembangan/pengujian pemindaian hanya boleh dilakukan
> pada jaringan milik sendiri atau yang Anda miliki izin eksplisit.

---

## Daftar Isi
1. [Menyiapkan Lingkungan](#1-menyiapkan-lingkungan)
2. [Menjalankan & Menulis Tes](#2-menjalankan--menulis-tes)
3. [Konvensi Proyek](#3-konvensi-proyek)
4. [Arsitektur Singkat](#4-arsitektur-singkat)
5. [Resep: Menambah Fitur Umum](#5-resep-menambah-fitur-umum)
6. [Alur Git & Pull Request](#6-alur-git--pull-request)

---

## 1. Menyiapkan Lingkungan

Membutuhkan **Python ≥ 3.9**.

```bash
git clone <url-repo> && cd HomeGuard
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # streamlit + pytest (opsional)
```

Inti pemindaian **tidak butuh dependensi apa pun** — cukup pustaka standar.
`requirements.txt` hanya untuk UI Streamlit dan pytest.

---

## 2. Menjalankan & Menulis Tes

```bash
pytest -q                      # jalankan seluruh 24 tes
pytest tests/test_vulnmap.py   # satu berkas
pytest -k "telnet"             # tes yang namanya mengandung 'telnet'
```

**Aturan emas:** setiap perubahan logika **wajib** disertai/menyesuaikan tes,
dan `pytest -q` harus **hijau** sebelum membuat PR. CI (GitHub Actions) akan
menjalankan tes pada Python 3.9–3.12 secara otomatis.

Tes jaringan (`test_portscan.py`, `test_scanner.py`) memakai **server tiruan
lokal** pada `127.0.0.1` agar deterministik — ikuti pola yang sama bila menulis
tes baru yang melibatkan socket (lihat helper `_mock_tcp` / `_mock_http`).

---

## 3. Konvensi Proyek

- **Bahasa:** komentar, *docstring*, dan teks UI dalam **Bahasa Indonesia**;
  nama identifikasi publik mengikuti yang sudah ada.
- **Dependensi inti = nol.** Modul di `homeguard/` (kecuali yang murni UI)
  **tidak boleh** mengimpor pustaka pihak ketiga. Streamlit hanya di `app.py`;
  pytest hanya di `tests/`. Ekspor PDF pun memakai pustaka standar.
- **Tanpa root.** Hindari operasi yang memerlukan hak istimewa (mis. *raw
  socket*/ICMP). Gunakan TCP connect & UDP biasa.
- **Non-intrusif.** Jangan menambah eksploitasi aktif. Fitur sensitif (mis.
  cek kredensial) harus **opt-in** dan **non-destruktif**.
- **Gaya kode:** ikuti PEP 8, baris ≤ ~79 kolom, fungsi kecil & teruji.
- **Docstring** wajib untuk fungsi/kelas publik (gaya yang sudah dipakai).

---

## 4. Arsitektur Singkat

Pipeline 4 modul (lihat README untuk detail & diagram):

```
discovery.py → portscan.py → portscan.py → vulnmap.py
 (Modul 1)      (Modul 2)     (Modul 3)     (Modul 4)
                    └──── scanner.py (orkestrator) ────┘
```

Basis pengetahuan statis ada di `homeguard/data/` (`iot_ports.py`,
`owasp_iot.py`, `oui.py`). **Sebagian besar penyesuaian aturan cukup
dilakukan di berkas data ini tanpa menyentuh logika.**

---

## 5. Resep: Menambah Fitur Umum

### a) Menambah aturan port baru
Edit `homeguard/data/iot_ports.py`, tambahkan entri pada dict `IOT_PORTS`:

```python
8888: {
    "service": "http-admin",
    "owasp": ["I3", "I7"],          # kategori OWASP IoT yang relevan
    "severity": SEVERITY_TINGGI,     # AMAN/RENDAH/SEDANG/TINGGI/KRITIS
    "note": "Panel admin alternatif tanpa enkripsi.",
    "recommendation": "Gunakan HTTPS & autentikasi kuat.",
},
```
Port otomatis ikut dipindai (masuk `PORT_DEFAULT`) dan dinilai. Tambah tes di
`tests/test_vulnmap.py` bila perlu.

### b) Menambah pola banner usang (memicu I5)
Edit daftar `POLA_BANNER_USANG` di `homeguard/vulnmap.py`:

```python
re.compile(r"Server: Old/1\.0", re.IGNORECASE),
```
Banner yang cocok akan menambah kategori **I5** dan menaikkan severity satu
tingkat secara otomatis.

### c) Menambah vendor OUI
Edit `OUI_SEED` di `homeguard/data/oui.py` (kunci = 6 heksadigit huruf besar):

```python
"AABBCC": "Nama Vendor",
```

### d) Menambah probe UDP / port UDP
Edit `homeguard/portscan.py`: tambah port pada `UDP_PORT_DEFAULT` dan logika
payload pada `scan_udp_port` (lihat contoh SSDP & mDNS).

### e) Menambah kombinasi kredensial bawaan
Edit `DEFAULT_CREDENTIALS` di `homeguard/credcheck.py`. Tetap **kecil &
terdokumentasi** (hindari menjadikannya alat brute-force).

---

## 6. Alur Git & Pull Request

1. Buat branch fitur: `git checkout -b fitur/nama-singkat`.
2. Lakukan perubahan + **tambah/sesuaikan tes**.
3. Pastikan `pytest -q` hijau dan kode mengikuti konvensi.
4. Commit dengan pesan deskriptif (Bahasa Indonesia dianjurkan).
5. Buka Pull Request ke `main`; CI akan berjalan otomatis.
6. PR di-*merge* setelah tes hijau & ditinjau.

Terima kasih telah berkontribusi! 🛡️
