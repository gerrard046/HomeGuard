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

## Versi Word (.docx) untuk pembaruan berkala

Selain PDF (LaTeX), tersedia versi **Word** untuk pembaruan berkala dan
pelacakan perubahan.

- Berkas siap pakai: **`HomeGuard_paper.docx`** (dihasilkan dari `main.tex`).
- Regenerasi setelah mengubah sumber LaTeX:

  ```bash
  pip install pypandoc_binary
  python paper/build_docx.py        # -> paper/HomeGuard_paper.docx
  ```

**Melihat "apa yang berubah" antar versi (di Microsoft Word):**
1. Simpan `.docx` versi lama (mis. `HomeGuard_paper_v1.docx`).
2. Setelah update, hasilkan `.docx` baru.
3. Word → tab **Review → Compare → Compare...** → pilih dokumen lama & baru →
   Word menampilkan **redline** (tambahan/hapusan disorot).
4. Saat Anda mengedit langsung di Word, aktifkan **Review → Track Changes**
   agar setiap perubahan tercatat.

> Sumber kebenaran tetap berkas LaTeX (`*.tex`) yang ter-versioning di Git;
> `.docx` adalah turunan untuk kemudahan kolaborasi/review di Word.

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
