#!/usr/bin/env python3
"""Konversi paper LaTeX HomeGuard menjadi berkas Word (.docx).

Memakai pandoc (via paket ``pypandoc_binary`` yang sudah membundel binernya):

    pip install pypandoc_binary
    python paper/build_docx.py

Menghasilkan ``paper/HomeGuard_paper.docx`` dari ``paper/main.tex`` (lengkap
dengan seluruh bab, tabel, gambar, dan daftar pustaka). Berkas Word ini cocok
untuk pembaruan berkala dan pelacakan perubahan (Track Changes / Compare).

Alur pembaruan yang disarankan:
    1. Edit sumber LaTeX (paper/*.tex) seperti biasa.
    2. Jalankan skrip ini untuk menghasilkan .docx terbaru.
    3. Di Word: Review -> Compare untuk melihat perbedaan vs versi sebelumnya.
"""

from __future__ import annotations

import os
import sys

PAPER_DIR = os.path.dirname(os.path.abspath(__file__))
SUMBER = os.path.join(PAPER_DIR, "main.tex")
TUJUAN = os.path.join(PAPER_DIR, "HomeGuard_paper.docx")


def main() -> int:
    try:
        import pypandoc
    except ImportError:
        print("Butuh pypandoc. Jalankan: pip install pypandoc_binary",
              file=sys.stderr)
        return 1

    # Konversi dari direktori paper agar \input & gambar (relatif) ter-resolve.
    cwd = os.getcwd()
    os.chdir(PAPER_DIR)
    try:
        pypandoc.convert_file(
            "main.tex", "docx", outputfile=TUJUAN,
            extra_args=["--resource-path=.", "--toc", "--toc-depth=3"],
        )
    except Exception as exc:  # noqa: BLE001 - ringkas untuk skrip CLI
        print(f"GAGAL konversi: {exc}", file=sys.stderr)
        return 1
    finally:
        os.chdir(cwd)

    print(f"Berhasil: {TUJUAN} ({os.path.getsize(TUJUAN)} byte)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
