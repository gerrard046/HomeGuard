# Catatan Revisi Paper — Konsistensi dengan Implementasi

Dokumen ini mencatat penyesuaian kalimat pada paper utama agar konsisten
dengan implementasi nyata HomeGuard.

## 1. Integrasi Nmap (Bab II.C.1 — Prinsip Network Scanning)

**Alasan:** Paper menyebut integrasi Nmap melalui *library* `python-nmap`,
sedangkan implementasi memakai pemanggilan biner Nmap via `subprocess`
dengan *fallback* otomatis ke pemindai *socket* murni. Pendekatan ini
dipilih agar aplikasi tetap berfungsi penuh **tanpa dependensi eksternal
wajib** (prinsip portabilitas inti).

### Kalimat ASLI (di paper)
> Dalam konteks penelitian ini, Nmap diintegrasikan melalui library
> python-nmap yang menyediakan antarmuka pemrograman untuk mengontrol dan
> mengolah hasil pemindaian secara programatik.

### Kalimat REVISI yang disarankan
> Dalam konteks penelitian ini, Nmap diintegrasikan secara opsional melalui
> pemanggilan proses (subprocess) terhadap perintah `nmap -sV` dan
> pem-*parsing*-an keluaran format *grepable* (`-oG`). Bila Nmap tidak
> tersedia pada sistem, aplikasi secara otomatis melakukan *fallback* ke
> pemindai berbasis *socket* murni, sehingga inti pemindaian tidak
> bergantung pada dependensi eksternal wajib.

## 2. Review akhir — tautan GitHub & pemutakhiran angka pengujian

**Alasan:** Paper wajib mencantumkan tautan repositori GitHub, dan jumlah
kasus uji pada paper (12) sudah tertinggal dari kondisi repositori
(36 tes pada 6 modul: `vulnmap`, `discovery`, `classify`, `portscan`,
`scanner`, `tlscheck` — semuanya lulus).

Perubahan yang diterapkan (di `main.tex`, `homeguard_overleaf.tex`,
`homeguard_bagian_lanjutan.tex`):

1. Tautan `https://github.com/gerrard046/HomeGuard` ditambahkan di
   **abstrak**, akhir **Kesimpulan**, dan **daftar pustaka** (rujukan
   `[b23]`); paket `url` ditambahkan ke preamble.
2. Bagian Pengujian Unit diperbarui: 12/12 → **36/36** kasus uji pada
   enam modul; tabel diubah menjadi "kasus uji representatif".
3. Kalimat kesimpulan "Pengujian unit (12/12 lulus)" → "(36/36 lulus)".
4. `HomeGuard_paper.docx` di-regenerate dari sumber LaTeX terbaru.

## 3. (Opsional) Penyebutan port Telnet Mirai

Pada Bab II.B.3 disebut Mirai memindai Telnet pada port **23 dan 2323**.
Implementasi kini memetakan **kedua** port tersebut sebagai KRITIS
(kategori I1, I2, I7), sehingga sudah konsisten dengan paper. Tidak perlu
revisi, cukup dipastikan tabel katalog port menyertakan 2323.
