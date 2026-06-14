# 📋 Catatan Progres HomeGuard

Dokumen ini merangkum **progres pengembangan** aplikasi HomeGuard beserta
**poin paparan untuk dosen** pada setiap milestone. Setiap progres baru akan
ditambahkan ke dokumen ini agar mudah dipresentasikan.

> 🎓 **Cara pakai saat bimbingan:** baca bagian *Ringkasan Eksekutif* dahulu,
> lalu jelaskan tiap milestone memakai poin "💬 Paparan ke dosen".

---

## Ringkasan Eksekutif

Dalam periode pengembangan ini, HomeGuard berkembang **dari nol menjadi
prototipe matang yang siap diuji dan dipresentasikan**. Capaian utama:

- ✅ **Aplikasi fungsional** dengan pipeline 4 modul sesuai paper (network
  discovery → port scanning → service detection → pemetaan OWASP + skor).
- ✅ **Fitur lanjutan:** pemindaian UDP, cek kredensial bawaan (vektor Mirai),
  klasifikasi tipe perangkat, database vendor OUI.
- ✅ **Dua antarmuka:** CLI (laporan berwarna) dan web Streamlit, plus ekspor
  laporan **JSON & PDF**.
- ✅ **Kualitas terjaga:** 30 unit test (semua lulus) + CI otomatis (GitHub
  Actions).
- ✅ **Dokumentasi lengkap:** README detail, panduan kontribusi, lisensi MIT.
- ✅ **Paper LaTeX lengkap & dapat di-compile** (Bab I–VI + diagram + 22
  referensi).

**Angka kunci saat ini:** ~2.000+ baris kode inti · 12 modul Python ·
30 unit test lulus · 18 port IoT terkatalog · 10 kategori OWASP · ~80 vendor
OUI (seed) + opsi database IEEE penuh.

---

## Ikhtisar Milestone

| # | Tanggal | Milestone | Status |
|---|---------|-----------|:---:|
| 1 | 10 Jun | Prototipe inti: pipeline 4 modul + pemetaan OWASP | ✅ |
| 2 | 10 Jun | Penyelarasan katalog port dengan paper | ✅ |
| 3 | 10 Jun | CI otomatis, diagram pipeline, demo lokal | ✅ |
| 4 | 10 Jun | Pemindaian UDP, cek kredensial bawaan, ekspor PDF, UX Streamlit | ✅ |
| 5 | 10 Jun | Justifikasi keberadaan aplikasi + tabel pembanding | ✅ |
| 6 | 10 Jun | Flowchart alur kerja aplikasi | ✅ |
| 7 | 10–11 Jun | Dokumentasi profesional (README, badge, LICENSE, CONTRIBUTING) | ✅ |
| 8 | 14 Jun | Klasifikasi tipe perangkat + database OUI IEEE | ✅ |
| 9 | 14 Jun | Penyusunan paper LaTeX utuh (Bab I–VI) | ✅ |
| 10 | 14 Jun | Paket Overleaf siap-pakai (ZIP + versi satu berkas) | ✅ |

---

## Detail Progres & Poin Paparan

### Milestone 1 — Prototipe Inti (10 Jun)
**Apa:** Membangun aplikasi inti dengan **pipeline 4 modul berurutan** sesuai
rancangan paper: penemuan host (TCP ping tanpa root), pemindaian port (TCP
connect paralel), deteksi layanan (banner grabbing), dan pemetaan ke **OWASP
IoT Top 10 (2018)** dengan skor risiko 0–100. Inti hanya memakai pustaka
standar Python.

> 💬 **Paparan ke dosen:** "Arsitektur aplikasi sudah persis seperti yang saya
> rancang di paper — empat modul berurutan. Yang terpenting, inti pemindaian
> tidak butuh library eksternal maupun akses root, jadi ringan dan portabel
> untuk pengguna rumahan."

### Milestone 2 — Penyelarasan dengan Paper (10 Jun)
**Apa:** Menambahkan port Telnet 2323 (dipindai botnet Mirai) dan SSDP/UPnP
1900 ke katalog agar konsisten dengan studi kasus pada paper.

> 💬 **Paparan ke dosen:** "Saya pastikan katalog port di aplikasi mencerminkan
> ancaman yang saya bahas di tinjauan pustaka, termasuk port 2323 yang
> spesifik dieksploitasi Mirai."

### Milestone 3 — Jaminan Kualitas & Demo (10 Jun)
**Apa:** Menyiapkan **GitHub Actions CI** (menjalankan tes otomatis di Python
3.9–3.12), diagram arsitektur pipeline, dan skrip **demo lokal** yang aman
(tanpa memindai jaringan nyata).

> 💬 **Paparan ke dosen:** "Setiap perubahan kode otomatis diuji oleh CI, jadi
> kualitas terjaga. Saya juga punya skrip demo yang bisa menunjukkan cara kerja
> aplikasi secara aman saat sidang, tanpa perlu jaringan sungguhan."

### Milestone 4 — Fitur Keamanan Lanjutan (10 Jun)
**Apa:** Menambahkan (a) **pemindaian UDP** (SSDP/UPnP & mDNS), (b) **cek
kredensial bawaan** opt-in & non-destruktif (pemetaan I1/I9 — vektor utama
Mirai), (c) **ekspor laporan PDF** (pustaka standar murni), dan (d) perbaikan
UX Streamlit (progress bar, tombol unduh).

> 💬 **Paparan ke dosen:** "Aplikasi kini bisa mendeteksi kredensial bawaan
> seperti admin/admin — ini langsung membuktikan teori serangan Mirai di paper.
> Laporan juga bisa diekspor ke PDF untuk dokumentasi formal."

### Milestone 5 — Justifikasi Keilmuan (10 Jun)
**Apa:** Menulis sub-bab + **tabel pembanding** terhadap alat sejenis (Nmap,
Nessus/OpenVAS, Fing, Bitdefender) untuk menegaskan kebaruan: integrasi
open-source + lokal + pemetaan OWASP + edukatif.

> 💬 **Paparan ke dosen:** "Untuk menjawab 'sudah banyak aplikasi serupa', saya
> tegaskan kontribusinya bukan teknik scanning baru, melainkan integrasi unik
> yang tidak dimiliki tool lain — terutama pemetaan OWASP IoT dan operasi lokal
> demi privasi."

### Milestone 6 — Visualisasi Alur (10 Jun)
**Apa:** Membuat **flowchart** alur kerja aplikasi (input target → discovery →
scan → assessment → laporan) sebagai bahan presentasi.

> 💬 **Paparan ke dosen:** "Ini diagram alir cara kerja aplikasi dari awal
> sampai keluar laporan — memudahkan menjelaskan logika sistem."

### Milestone 7 — Dokumentasi Profesional (10–11 Jun)
**Apa:** README sangat detail (cara kerja per modul, rumus skor, skema JSON,
API), **badge** status (CI, tes, OWASP), berkas **LICENSE (MIT)**, dan
**CONTRIBUTING.md** (panduan pengembang).

> 💬 **Paparan ke dosen:** "Repositori sudah berstandar proyek open-source
> sungguhan — ada dokumentasi, lisensi, dan panduan kontribusi — sehingga layak
> dirilis publik sebagai instrumen penelitian."

### Milestone 8 — Identifikasi Perangkat (14 Jun)
**Apa:** **Klasifikasi tipe perangkat** (kamera/router/printer/NAS/dll) dari
kombinasi layanan-port + vendor OUI, serta **database OUI IEEE** (seed
diperluas + loader untuk database penuh ~30k vendor).

> 💬 **Paparan ke dosen:** "Aplikasi tidak hanya menemukan IP, tapi juga menebak
> jenis perangkatnya — misalnya mengenali kamera CCTV dari port RTSP dan vendor
> Hikvision. Ini menyederhanakan device fingerprinting (Sivanathan et al.) jadi
> aturan yang transparan."

### Milestone 9 — Penyusunan Paper (14 Jun)
**Apa:** Menyusun **paper LaTeX utuh** (IEEEtran): Bab I–II direkonstruksi,
Bab III–VI (Metodologi, Implementasi, Pengujian, Kesimpulan) ditulis sesuai
implementasi, plus gambar dan 22 referensi — siap di-compile jadi satu PDF.

> 💬 **Paparan ke dosen:** "Paper sudah lengkap enam bab dan bisa langsung
> di-compile di Overleaf. Bagian metodologi dan pengujian saya tulis benar-benar
> mengacu pada kode yang sudah jalan, bukan sekadar rencana."

### Milestone 10 — Paket Overleaf Siap-Pakai (14 Jun)
**Apa:** Menyediakan **versi satu berkas** (`paper/homeguard_overleaf.tex`,
seluruh bab digabung) dan paket ZIP berisi `.tex` + gambar agar paper dapat
langsung diunggah dan di-compile di Overleaf tanpa konfigurasi manual.

> 💬 **Paparan ke dosen:** "Papernya sudah dalam bentuk yang siap di-compile —
> tinggal unggah ke Overleaf dan klik compile, langsung jadi PDF utuh."

---

## Cara Memverifikasi (bila dosen ingin membuktikan)

```bash
# 1) Jalankan seluruh unit test (harus 30 lulus)
pytest -q

# 2) Demo aman tanpa jaringan nyata
python demo_lokal.py

# 3) Lihat referensi OWASP yang dipakai
python cli.py --owasp-ref
```

---

## Rencana Selanjutnya (Roadmap)

- [ ] Korelasi versi komponen → CVE nyata via **NVD API** (kategori I5).
- [ ] Screenshot antarmuka Streamlit asli untuk lampiran paper.
- [ ] Pengujian dunia nyata pada jaringan rumah + pengisian tabel hasil paper.
- [ ] (Opsional) Abstract versi Inggris & slide presentasi sidang.

---

*Dokumen ini diperbarui setiap ada progres baru. Terakhir diperbarui:
14 Juni 2026.*
