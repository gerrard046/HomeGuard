#!/usr/bin/env python3
"""Konversi paper LaTeX HomeGuard menjadi PDF tanpa instalasi LaTeX.

Memakai pandoc (pypandoc_binary) dengan mesin PDF WeasyPrint (HTML/CSS),
sehingga tidak memerlukan distribusi TeX:

    pip install pypandoc_binary weasyprint
    python paper/build_pdf.py        # -> paper/HomeGuard_paper_preview.pdf

CATATAN: keluaran ini adalah PDF *preview* satu kolom untuk pemeriksaan cepat.
Untuk versi final berformat IEEE dua kolom, compile ``main.tex`` dengan
pdfLaTeX (mis. via Overleaf) — lihat paper/README.md.
"""

from __future__ import annotations

import os
import sys

PAPER_DIR = os.path.dirname(os.path.abspath(__file__))
TUJUAN = os.path.join(PAPER_DIR, "HomeGuard_paper_preview.pdf")

_CSS = """
@page { size: A4; margin: 2cm; }
body { font-family: 'DejaVu Serif', serif; font-size: 11pt; line-height: 1.45;
       text-align: justify; }
h1 { font-size: 16pt; } h2 { font-size: 13pt; } h3 { font-size: 11.5pt; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; }
th, td { border: 1px solid #555; padding: 3px 5px; }
img { max-width: 100%; }
"""


def main() -> int:
    try:
        import pypandoc
    except ImportError:
        print("Butuh pypandoc & weasyprint. Jalankan:\n"
              "  pip install pypandoc_binary weasyprint", file=sys.stderr)
        return 1

    css_path = os.path.join(PAPER_DIR, "_preview.css")
    with open(css_path, "w", encoding="utf-8") as fh:
        fh.write(_CSS)

    cwd = os.getcwd()
    os.chdir(PAPER_DIR)
    try:
        pypandoc.convert_file(
            "main.tex", "pdf", outputfile=TUJUAN,
            extra_args=["--pdf-engine=weasyprint", "--resource-path=.",
                        "--toc", "--toc-depth=3", "-c", "_preview.css"],
        )
    except Exception as exc:  # noqa: BLE001
        print(f"GAGAL konversi PDF: {exc}", file=sys.stderr)
        return 1
    finally:
        os.chdir(cwd)

    print(f"Berhasil: {TUJUAN} ({os.path.getsize(TUJUAN)} byte)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
