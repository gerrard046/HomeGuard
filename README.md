# 🛡️ HomeGuard

**Pemindai keamanan jaringan rumah untuk mengidentifikasi kerentanan perangkat
IoT pada jaringan Wi-Fi domestik**, dengan pemetaan ke kerangka **OWASP IoT
Top 10 (2018)** dan penilaian skor risiko.

Proyek ini merupakan prototipe implementasi paper tugas kuliah
(**Politeknik Siber dan Sandi Negara**).

> ⚠️ **PERINGATAN ETIKA**
> Gunakan HomeGuard **HANYA pada jaringan milik sendiri atau yang Anda miliki
> izin eksplisit** untuk memindainya. Pemindaian jaringan tanpa izin dapat
> melanggar hukum dan etika. Alat ini ditujukan untuk tujuan edukasi dan
> pengujian defensif.

---

## Arsitektur

HomeGuard menjalankan **pipeline 4 modul berurutan** sesuai paper:

```
  [1] Network Discovery  ->  [2] Port Scanning  ->  [3] Service Detection  ->  [4] OWASP Mapping + Risk Score
       (discovery.py)            (portscan.py)          (portscan.py)               (vulnmap.py)
```

| Modul | Berkas | Tanggung jawab |
|-------|--------|----------------|
| 1. Penemuan host | `homeguard/discovery.py` | TCP ping (tanpa root), parsing tabel ARP (`ip neigh` / `arp -a`), normalisasi MAC, lookup vendor (OUI), deteksi subnet otomatis, ekspansi CIDR (tanpa network/broadcast). |
| 2. Pemindaian port | `homeguard/portscan.py` | TCP connect scan paralel (`ThreadPoolExecutor`). |
| 3. Deteksi layanan | `homeguard/portscan.py` | Banner grabbing, deteksi service + versi, integrasi **opsional** `nmap -sV` dengan **fallback otomatis** ke socket (parsing output `-oG`). |
| 4. Pemetaan OWASP + skor | `homeguard/vulnmap.py` | `assess_port()` / `assess_host()`, skor 0–100, level AMAN/RENDAH/SEDANG/TINGGI/KRITIS, deteksi banner usang → tambah kategori I5 & naikkan severity. |
| Orkestrator | `homeguard/scanner.py` | Menyatukan modul 1–4 menjadi pipeline end-to-end + penyusunan laporan. |

Basis pengetahuan statis berada di `homeguard/data/`:

- `iot_ports.py` — katalog port IoT umum → `{service, owasp[], severity, note, recommendation}`.
- `owasp_iot.py` — definisi OWASP IoT Top 10 2018 (I1..I10).
- `oui.py` — lookup vendor dari prefiks MAC (seed OUI IEEE).

> **Inti pemindaian hanya memakai pustaka standar Python** (socket murni, tanpa
> root, tanpa dependensi wajib). Streamlit & pytest hanya untuk UI dan tes.

---

## Struktur File

```
HomeGuard/
├── app.py                      # UI Streamlit
├── cli.py                      # CLI + ekspor JSON
├── requirements.txt
├── README.md
├── .gitignore
├── homeguard/
│   ├── __init__.py             # ekspor HomeGuardScanner, __version__
│   ├── discovery.py            # Modul 1: host discovery
│   ├── portscan.py             # Modul 2 & 3: port scan (TCP+UDP) + layanan
│   ├── vulnmap.py              # Modul 4: pemetaan OWASP + skor risiko
│   ├── credcheck.py            # Cek kredensial bawaan (opt-in, I1/I9)
│   ├── report_pdf.py           # Ekspor laporan PDF (pustaka standar)
│   ├── scanner.py              # orkestrator pipeline end-to-end
│   └── data/
│       ├── __init__.py
│       ├── iot_ports.py        # katalog port IoT
│       ├── owasp_iot.py        # OWASP IoT Top 10 2018
│       └── oui.py              # lookup vendor OUI
└── tests/
    ├── test_vulnmap.py         # 6 test
    └── test_discovery.py       # 6 test
```

---

## Instalasi

Membutuhkan **Python ≥ 3.9**.

```bash
# 1) Klon repositori
git clone <url-repo> && cd HomeGuard

# 2) (Opsional) buat virtual environment
python -m venv .venv && source .venv/bin/activate

# 3) Pasang dependensi opsional (UI & tes). Inti CLI tidak butuh ini.
pip install -r requirements.txt
```

Karena inti pemindaian hanya memakai pustaka standar, **CLI dapat langsung
dijalankan tanpa memasang apa pun**.

---

## Penggunaan

### 1) CLI

```bash
# Pindai subnet (deteksi otomatis bila --subnet tidak diberikan)
python cli.py --subnet 192.168.1.0/24

# Pindai satu host dengan daftar port tertentu
python cli.py --host 192.168.1.10 --ports 22,23,80,554

# Gunakan nmap bila tersedia (otomatis fallback ke socket) + ekspor JSON & PDF
python cli.py --subnet 192.168.1.0/24 --nmap --json laporan.json --pdf laporan.pdf

# Aktifkan probe UDP (SSDP/UPnP & mDNS)
python cli.py --host 192.168.1.10 --udp

# OPT-IN: uji kredensial bawaan (hanya jaringan milik/diizinkan)
python cli.py --host 192.168.1.10 --check-creds

# Nonaktifkan warna (mis. untuk berkas log)
python cli.py --host 192.168.1.10 --no-color

# Tampilkan referensi OWASP IoT Top 10
python cli.py --owasp-ref
```

Argumen: `--subnet`, `--host`, `--ports`, `--timeout`, `--nmap`,
`--json FILE`, `--pdf FILE`, `--udp`, `--check-creds`, `--no-color`.

### Coba tanpa jaringan nyata (demo lokal)

```bash
python demo_lokal.py
```

Skrip ini menyalakan layanan IoT tiruan (Telnet, HTTP banner usang, RTSP)
di `localhost` lalu memindainya — aman untuk mencoba aplikasi tanpa
memindai jaringan apa pun.

### 2) Streamlit

```bash
streamlit run app.py
```

Konfigurasi pemindaian ada di **sidebar**; hasil host ditampilkan **diurut
menurut risiko**, dengan **tombol unduh laporan JSON** dan **panel referensi
OWASP IoT Top 10**.

### 3) Sebagai pustaka

```python
from homeguard import HomeGuardScanner

scanner = HomeGuardScanner(timeout=1.0, gunakan_nmap=False)

# Pindai satu host
hasil = scanner.scan_host("192.168.1.10")
print(hasil["severity"], hasil["score"], hasil["owasp"])

# Pindai seluruh subnet lalu susun laporan
hosts = scanner.scan_subnet("192.168.1.0/24")
laporan = scanner.build_report(hosts, target="192.168.1.0/24")
```

Penilaian per port/host juga dapat dipakai langsung:

```python
from homeguard import vulnmap

vulnmap.assess_port(23)                       # Telnet -> KRITIS, I1/I2/I7
vulnmap.assess_port(80, banner="lighttpd/1.4.35")  # +I5, severity naik
vulnmap.assess_host([{"port": 23}, {"port": 80}])  # ringkasan host
```

---

## Penjelasan Skor Risiko

Setiap port terbuka dipetakan ke satu atau lebih kategori OWASP IoT dan diberi
**level severity**:

| Level | Skor dasar |
|-------|-----------|
| AMAN | 0 |
| RENDAH | 25 |
| SEDANG | 50 |
| TINGGI | 75 |
| KRITIS | 90 |

**Aturan pemetaan utama:**

- **Telnet (23)** → **KRITIS**, kategori **I1 + I2 + I7** (kredensial polos /
  bawaan + layanan tidak aman).
- **HTTP (80)** → **I3 + I7**, severity **TINGGI** (antarmuka & transfer tidak
  aman).
- **RTSP (554)** → **I2 + I7** (streaming kamera tanpa enkripsi/autentikasi).
- **Port tak dikenal** → temuan generik **I2**, severity **SEDANG**.
- **Banner komponen usang** (mis. `lighttpd/1.4.35`, `Apache/2.2.`,
  `BusyBox`, `OpenSSH_6.`) → tambahkan kategori **I5** dan **naikkan satu
  tingkat severity**.

**Skor host** = skor severity tertinggi di antara seluruh temuan + penambah
kecil per temuan, dibatasi maksimum **100**. Host tanpa port terbuka dinilai
**AMAN** dengan skor **0**.

---

## Menjalankan Pengujian

Terdapat **24 unit test** (`pytest`) yang seluruhnya harus **LULUS**:

```bash
pip install pytest
pytest -q
```

- `tests/test_vulnmap.py` (6): Telnet KRITIS + I1/I2; HTTP I3/I7; RTSP I2/I7;
  port tak dikenal → I2; banner usang → +I5 & severity naik; host gabungan →
  KRITIS & host tanpa port → AMAN/skor 0.
- `tests/test_discovery.py` (6): normalisasi MAC; MAC invalid ditolak; lookup
  vendor (Raspberry Pi vs Unknown); parsing `ip neigh` & `arp -a`; ekspansi
  CIDR /30 & /32; deteksi IP privat.
- `tests/test_portscan.py` (6): scan port terbuka/tertutup + banner;
  `scan_host_socket`; parsing output grepable nmap; fallback nmap → socket;
  probe UDP terbuka.
- `tests/test_scanner.py` (6): agregasi severity/OWASP; pengurutan laporan;
  integrasi banner usang → +I5; deteksi kredensial bawaan → I1/I9; PDF valid.

---

## Roadmap

1. ✅ **GitHub Actions CI** untuk menjalankan `pytest` otomatis
   (`.github/workflows/ci.yml`).
2. **Korelasi versi → CVE (kategori I5)** melalui **NVD API**, memperkaya
   deteksi komponen usang dengan referensi CVE nyata.
3. ✅ **Ekspor laporan PDF** (selain JSON) — `homeguard/report_pdf.py`.
4. **Database OUI lengkap IEEE** menggantikan seed kecil saat ini untuk
   identifikasi vendor yang akurat.
5. **Pendalaman UDP** (CoAP, profil mDNS lengkap) dan deteksi tipe perangkat.

---

## Lisensi & Tanggung Jawab

Prototipe edukasi. Pengguna bertanggung jawab penuh memastikan setiap
pemindaian dilakukan **hanya pada jaringan yang sah dimiliki atau diizinkan**.