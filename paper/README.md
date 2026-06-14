# Folder Paper HomeGuard

Berkas LaTeX & gambar untuk menyusun paper menjadi satu PDF utuh.

## Isi

| Berkas | Keterangan |
|---|---|
| `main.tex` | **Berkas utama** (IEEEtran). Merangkai semua bagian via `\input` & `\includegraphics`. |
| `homeguard_bagian_lanjutan.tex` | Bab Metodologi, Perancangan & Implementasi, Pengujian & Hasil, Kesimpulan. |
| `justifikasi_diferensiasi.tex` | Sub-bab justifikasi keberadaan aplikasi + tabel pembanding. |
| `diagram_pipeline.png` / `.py` | Gambar arsitektur pipeline (+ generator). |
| `flowchart_alur.png` / `.py` | Gambar diagram alir penggunaan (+ generator). |
| `catatan_revisi_paper.md` | Saran revisi kalimat agar konsisten dengan implementasi. |

## Cara compile (disarankan: Overleaf, tanpa instalasi)

1. Buka [overleaf.com](https://www.overleaf.com) → **New Project** → **Upload Project**.
2. Unggah **seluruh isi folder `paper/`** (semua `.tex` dan `.png`).
3. Set **Menu → Compiler → pdfLaTeX**, dan **Main document → `main.tex`**.
4. Tempel naskah Anda (Bab I Pendahuluan & Bab II Tinjauan Pustaka) pada
   penanda `% >>> TEMPEL ...` di `main.tex`.
5. Klik **Recompile** → satu PDF utuh.

## Cara compile (lokal)

```bash
# Butuh distribusi TeX (mis. TeX Live / MiKTeX)
cd paper
pdflatex main.tex && pdflatex main.tex   # dua kali untuk referensi silang
```

## Catatan

- Bab III–VI dirangkai otomatis dari `homeguard_bagian_lanjutan.tex`.
- Daftar pustaka (22 referensi) sudah tertanam di `main.tex`.
- Bila punya berkas `.tex` naskah asli (Bab I & II), gabungkan isinya ke
  bagian yang ditandai pada `main.tex`.
