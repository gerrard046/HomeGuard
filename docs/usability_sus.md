# Protokol Uji Usability HomeGuard (System Usability Scale)

Dokumen ini menyediakan instrumen dan prosedur untuk **membuktikan secara
empiris** klaim inti paper bahwa HomeGuard ramah bagi pengguna awam. Selama ini
klaim tersebut belum divalidasi oleh data pengguna; uji SUS mengisinya.

## Mengapa SUS

*System Usability Scale* (Brooke, 1996) adalah kuesioner 10 item yang menjadi
standar de-facto pengukuran usability. Ringkas (dapat diisi < 3 menit),
tervalidasi lintas domain, dan menghasilkan satu skor 0–100 yang mudah
dibandingkan (rata-rata industri ≈ 68; > 80 tergolong sangat baik).

## Prosedur

1. **Responden.** Rekrut 10–15 orang **non-teknis** (bukan mahasiswa/praktisi
   keamanan). Catat demografi singkat: usia, latar pekerjaan, tingkat
   familiaritas dengan keamanan jaringan (skala 1–5).
2. **Tugas terstandardisasi.** Minta tiap responden, tanpa bantuan, melakukan:
   - (T1) menjalankan pemindaian pada jaringan lab yang disediakan;
   - (T2) mengidentifikasi perangkat paling berisiko dari antarmuka;
   - (T3) menyebutkan satu langkah mitigasi yang direkomendasikan aplikasi;
   - (T4) mengunduh laporan PDF.
   Catat keberhasilan tiap tugas (berhasil/gagal) dan waktu penyelesaian.
3. **Kuesioner SUS.** Segera setelah tugas, responden mengisi 10 pernyataan di
   bawah (skala 1 = sangat tidak setuju … 5 = sangat setuju).
4. **Analisis.** Hitung skor SUS (rumus di bawah), laporkan rata-rata ±
   standar deviasi, dan tingkat keberhasilan tugas (task success rate).

## Instrumen SUS (versi Bahasa Indonesia)

| No | Pernyataan | 1 | 2 | 3 | 4 | 5 |
|----|-----------|---|---|---|---|---|
| 1 | Saya rasa saya ingin sering menggunakan aplikasi ini. | | | | | |
| 2 | Saya merasa aplikasi ini terlalu rumit. | | | | | |
| 3 | Saya rasa aplikasi ini mudah digunakan. | | | | | |
| 4 | Saya rasa saya butuh bantuan teknis untuk bisa memakai aplikasi ini. | | | | | |
| 5 | Saya rasa berbagai fungsi aplikasi ini terpadu dengan baik. | | | | | |
| 6 | Saya rasa terlalu banyak ketidakkonsistenan pada aplikasi ini. | | | | | |
| 7 | Saya rasa kebanyakan orang akan cepat memahami cara memakai aplikasi ini. | | | | | |
| 8 | Saya rasa aplikasi ini sangat merepotkan untuk digunakan. | | | | | |
| 9 | Saya merasa sangat percaya diri saat menggunakan aplikasi ini. | | | | | |
| 10 | Saya perlu belajar banyak hal dulu sebelum bisa memakai aplikasi ini. | | | | | |

## Perhitungan skor

- Item ganjil (1,3,5,7,9): kontribusi = (nilai − 1).
- Item genap (2,4,6,8,10): kontribusi = (5 − nilai).
- Jumlahkan seluruh kontribusi (0–40), lalu kalikan 2,5 → skor SUS (0–100).
- Skor akhir studi = rata-rata skor SUS seluruh responden.

Skrip bantu perhitungan: isi respons ke CSV lalu rata-ratakan; formula di atas
dapat diterapkan langsung di spreadsheet.

## Pelaporan pada paper

Tambahkan subbab "Pengujian Usability" pada bagian Pengujian dan Hasil yang
melaporkan: jumlah & profil responden, task success rate per tugas, skor SUS
rata-rata ± SD, dan interpretasinya terhadap rata-rata industri (68). Kaitkan
temuan dengan klaim edukatif pada Pendahuluan dan Diferensiasi.

> Referensi: J. Brooke, "SUS: A 'quick and dirty' usability scale," in
> *Usability Evaluation in Industry*, 1996, pp. 189–194.
