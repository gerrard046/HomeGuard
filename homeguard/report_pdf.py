"""Ekspor laporan HomeGuard ke berkas PDF — implementasi pustaka standar.

Modul ini menghasilkan PDF sederhana (teks multi-halaman, font Helvetica
standar) tanpa dependensi eksternal apa pun, sejalan dengan prinsip inti
HomeGuard yang bebas dependensi wajib. Cocok untuk pelaporan formal hasil
pemindaian.

Penggunaan::

    from homeguard.report_pdf import build_pdf
    build_pdf(laporan, "laporan.pdf")

PERINGATAN ETIKA: Laporan hanya sah untuk jaringan milik sendiri/diizinkan.
"""

from __future__ import annotations

# Dimensi halaman A4 dalam satuan poin (1/72 inci).
LEBAR_HALAMAN = 595
TINGGI_HALAMAN = 842
MARGIN = 50
MARGIN_BAWAH = 60

# Warna teks per level severity (RGB 0-1).
WARNA_SEVERITY = {
    "AMAN": (0.18, 0.49, 0.20),
    "RENDAH": (0.01, 0.47, 0.74),
    "SEDANG": (0.85, 0.55, 0.0),
    "TINGGI": (0.68, 0.08, 0.34),
    "KRITIS": (0.78, 0.16, 0.16),
}


def _escape(teks: str) -> str:
    """Escape karakter khusus PDF dan paksa ke encoding Latin-1 yang aman."""
    teks = teks.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
    return teks.encode("latin-1", "replace").decode("latin-1")


def _wrap(teks: str, size: float, lebar: float) -> list:
    """Bungkus ``teks`` menjadi beberapa baris sesuai lebar yang tersedia."""
    maks = max(1, int(lebar / (size * 0.5)))
    kata = teks.split()
    baris, kini = [], ""
    for k in kata:
        calon = (kini + " " + k).strip()
        if len(calon) > maks and kini:
            baris.append(kini)
            kini = k
        else:
            kini = calon
    if kini:
        baris.append(kini)
    return baris or [""]


class _PDFBuilder:
    """Pembangun PDF teks multi-halaman minimalis (pustaka standar)."""

    def __init__(self):
        self._pages = []          # daftar string konten tiap halaman
        self._buf = []            # perintah konten halaman berjalan
        self._y = TINGGI_HALAMAN - MARGIN

    # --- manajemen halaman ---
    def _new_page(self):
        if self._buf:
            self._pages.append("\n".join(self._buf))
        self._buf = []
        self._y = TINGGI_HALAMAN - MARGIN

    def _ensure(self, butuh: float):
        if self._y - butuh < MARGIN_BAWAH:
            self._new_page()

    # --- penulisan teks ---
    def text(self, teks, size=10, bold=False, color=(0, 0, 0), indent=0):
        """Tulis satu blok teks (dengan pembungkusan) mulai dari posisi y kini."""
        lebar = LEBAR_HALAMAN - 2 * MARGIN - indent
        font = "F2" if bold else "F1"
        for baris in _wrap(teks, size, lebar):
            self._ensure(size + 4)
            x = MARGIN + indent
            r, g, b = color
            self._buf.append(
                f"q {r:.3f} {g:.3f} {b:.3f} rg BT /{font} {size} Tf "
                f"{x} {self._y:.1f} Td ({_escape(baris)}) Tj ET Q"
            )
            self._y -= size + 4

    def spacer(self, tinggi=8):
        """Tambahkan ruang kosong vertikal."""
        self._ensure(tinggi)
        self._y -= tinggi

    def hr(self):
        """Gambar garis horizontal tipis."""
        self._ensure(8)
        y = self._y
        self._buf.append(
            f"q 0.6 0.6 0.6 RG 0.5 w {MARGIN} {y:.1f} m "
            f"{LEBAR_HALAMAN - MARGIN} {y:.1f} l S Q"
        )
        self._y -= 8

    # --- perakitan PDF ---
    def build(self) -> bytes:
        self._new_page()  # finalisasi halaman terakhir
        objek = []

        # Objek tetap: katalog, pohon halaman, dua font.
        n_font1, n_font2 = 3, 4
        # Objek halaman dimulai pada nomor 5.
        n_pages_obj = 2
        konten_objs = []
        page_objs = []
        nomor = 5
        kids = []
        for konten in self._pages:
            n_konten = nomor
            n_page = nomor + 1
            kids.append(n_page)
            stream = konten.encode("latin-1", "replace")
            konten_objs.append(
                (n_konten,
                 f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
                 + stream + b"\nendstream")
            )
            page_objs.append(
                (n_page,
                 (f"<< /Type /Page /Parent {n_pages_obj} 0 R "
                  f"/MediaBox [0 0 {LEBAR_HALAMAN} {TINGGI_HALAMAN}] "
                  f"/Resources << /Font << /F1 {n_font1} 0 R "
                  f"/F2 {n_font2} 0 R >> >> "
                  f"/Contents {n_konten} 0 R >>").encode("latin-1"))
            )
            nomor += 2

        kids_str = " ".join(f"{k} 0 R" for k in kids)
        objek.append((1, b"<< /Type /Catalog /Pages 2 0 R >>"))
        objek.append((2,
                      (f"<< /Type /Pages /Kids [{kids_str}] "
                       f"/Count {len(kids)} >>").encode("latin-1")))
        objek.append((3,
                      b"<< /Type /Font /Subtype /Type1 "
                      b"/BaseFont /Helvetica >>"))
        objek.append((4,
                      b"<< /Type /Font /Subtype /Type1 "
                      b"/BaseFont /Helvetica-Bold >>"))
        objek.extend(konten_objs)
        objek.extend(page_objs)
        objek.sort(key=lambda o: o[0])

        # Rakit berkas + tabel xref.
        out = bytearray(b"%PDF-1.4\n")
        offsets = {}
        for nomor_obj, isi in objek:
            offsets[nomor_obj] = len(out)
            out += f"{nomor_obj} 0 obj\n".encode("latin-1") + isi + b"\nendobj\n"

        xref_pos = len(out)
        total = len(objek) + 1
        out += f"xref\n0 {total}\n".encode("latin-1")
        out += b"0000000000 65535 f \n"
        for nomor_obj in range(1, total):
            out += f"{offsets[nomor_obj]:010d} 00000 n \n".encode("latin-1")
        out += (f"trailer\n<< /Size {total} /Root 1 0 R >>\n"
                f"startxref\n{xref_pos}\n%%EOF").encode("latin-1")
        return bytes(out)


def build_pdf_bytes(laporan: dict) -> bytes:
    """Bangun isi PDF laporan dan kembalikan sebagai ``bytes``."""
    pdf = _PDFBuilder()
    pdf.text("Laporan Pemindaian HomeGuard", size=18, bold=True)
    pdf.spacer(4)
    pdf.text(f"Versi {laporan.get('versi', '-')}  |  "
             f"Waktu: {laporan.get('waktu', '-')}", size=9,
             color=(0.4, 0.4, 0.4))
    pdf.text(f"Target: {laporan.get('target', '-')}", size=9,
             color=(0.4, 0.4, 0.4))
    pdf.text(laporan.get("peringatan", ""), size=8, color=(0.6, 0.2, 0.2))
    pdf.spacer(6)
    pdf.hr()

    ring = laporan.get("ringkasan", {})
    pdf.text("Ringkasan", size=13, bold=True)
    pdf.text(f"Total host: {ring.get('total_host', 0)}   "
             f"Host berisiko: {ring.get('host_berisiko', 0)}   "
             f"Skor tertinggi: {ring.get('skor_tertinggi', 0)}", size=10)
    distribusi = ring.get("distribusi_owasp", {})
    if distribusi:
        teks = ", ".join(f"{k}={v}" for k, v in sorted(distribusi.items()))
        pdf.text(f"Distribusi OWASP: {teks}", size=10)
    pdf.spacer(6)
    pdf.hr()

    pdf.text("Host (diurut menurut risiko)", size=13, bold=True)
    pdf.spacer(2)
    for h in laporan.get("hosts", []):
        warna = WARNA_SEVERITY.get(h["severity"], (0, 0, 0))
        judul = (f"{h['ip']}  -  {h.get('vendor') or 'Unknown'}  "
                 f"[{h['severity']}]  skor {h['score']}")
        pdf.text(judul, size=11, bold=True, color=warna)
        if h.get("mac"):
            pdf.text(f"MAC: {h['mac']}", size=9, indent=12,
                     color=(0.3, 0.3, 0.3))
        if h.get("owasp"):
            pdf.text(f"OWASP: {', '.join(h['owasp'])}", size=9, indent=12,
                     color=(0.3, 0.3, 0.3))
        for f in h.get("findings", []):
            pdf.text(f"- {f['port']}/{f['service']} [{f['severity']}] "
                     f"{', '.join(f['owasp'])}", size=9, indent=12)
            pdf.text(f["note"], size=8, indent=24, color=(0.35, 0.35, 0.35))
            pdf.text(f"Rekomendasi: {f['recommendation']}", size=8, indent=24,
                     color=(0.35, 0.35, 0.35))
        pdf.spacer(6)
    return pdf.build()


def build_pdf(laporan: dict, path: str) -> str:
    """Tulis laporan ke berkas PDF pada ``path`` dan kembalikan ``path``."""
    with open(path, "wb") as fh:
        fh.write(build_pdf_bytes(laporan))
    return path
