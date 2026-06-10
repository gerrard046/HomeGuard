"""Pembangkit flowchart alur kerja penggunaan aplikasi HomeGuard.

Menghasilkan ``flowchart_alur.png`` — diagram alir (flowchart) tahap demi
tahap saat aplikasi dijalankan, dari input target hingga laporan akhir.
Berguna sebagai bahan presentasi/sidang.

Jalankan:

    python paper/flowchart_alur.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon

# Warna per modul (selaras dengan diagram pipeline).
C_START = "#455a64"
C_M1 = "#1565c0"
C_M2 = "#2e7d32"
C_M3 = "#ef6c00"
C_M4 = "#c62828"
C_DEC = "#6a1b9a"
C_SIDE = "#00838f"

fig, ax = plt.subplots(figsize=(9.2, 15))
ax.set_xlim(0, 10)
ax.set_ylim(0, 31)
ax.axis("off")

CX = 4.2          # sumbu tengah (spine)
SX = 8.0          # kolom samping untuk hasil percabangan
W, H = 4.6, 1.25  # ukuran kotak proses standar


def kotak(cx, cy, teks, warna, w=W, h=H, fontsize=10.5, bold=True):
    """Gambar kotak proses (rounded) berlabel di tengah (cx, cy)."""
    p = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.04,rounding_size=0.14",
        linewidth=1.6, edgecolor=warna, facecolor=warna + "1f",
    )
    ax.add_patch(p)
    ax.text(cx, cy, teks, ha="center", va="center", fontsize=fontsize,
            color="#1a1a1a", fontweight="bold" if bold else "normal", wrap=True)
    return cy - h / 2, cy + h / 2  # (bawah, atas)


def oval(cx, cy, teks, warna, w=3.6, h=1.05):
    """Gambar terminal (mulai/selesai) berbentuk kapsul."""
    p = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.04,rounding_size=0.5",
        linewidth=1.8, edgecolor=warna, facecolor=warna + "26",
    )
    ax.add_patch(p)
    ax.text(cx, cy, teks, ha="center", va="center", fontsize=11,
            color="#1a1a1a", fontweight="bold")
    return cy - h / 2, cy + h / 2


def belah(cx, cy, teks, w=3.2, h=1.5):
    """Gambar simpul keputusan berbentuk belah ketupat (diamond)."""
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2),
           (cx - w / 2, cy)]
    ax.add_patch(Polygon(pts, closed=True, linewidth=1.6,
                         edgecolor=C_DEC, facecolor=C_DEC + "1f"))
    ax.text(cx, cy, teks, ha="center", va="center", fontsize=9.8,
            color="#1a1a1a", fontweight="bold")
    return {"bawah": cy - h / 2, "atas": cy + h / 2,
            "kiri": cx - w / 2, "kanan": cx + w / 2, "cy": cy}


def panah(x1, y1, x2, y2, teks="", warna="#555555", rad=0.0):
    """Gambar panah berarah dari (x1,y1) ke (x2,y2) dengan label opsional."""
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16,
        linewidth=1.6, color=warna,
        connectionstyle=f"arc3,rad={rad}"))
    if teks:
        ax.text((x1 + x2) / 2 + 0.18, (y1 + y2) / 2, teks, fontsize=9,
                color=warna, fontweight="bold", ha="left", va="center")


y = 30.2
# 0. Mulai
b, t = oval(CX, y, "MULAI — pilih CLI / Streamlit", C_START)
prev = b

# 1. Input target
y -= 2.4
b, t = kotak(CX, y, "Input target:\nsubnet (CIDR) atau satu host", C_START,
             fontsize=10)
panah(CX, prev, CX, t); prev = b

# 2. Modul 1: subnet
y -= 2.4
b, t = kotak(CX, y, "MODUL 1 — Deteksi subnet otomatis\n& ekspansi CIDR ke daftar IP",
             C_M1, fontsize=10)
panah(CX, prev, CX, t); prev = b

# 3. TCP ping
y -= 2.4
b, t = kotak(CX, y, "TCP ping paralel ke tiap IP\n(tanpa root)", C_M1,
             fontsize=10)
panah(CX, prev, CX, t); prev = b

# 4. Decision host hidup
y -= 2.5
d = belah(CX, y, "Host\nhidup?")
panah(CX, prev, CX, d["atas"])
# Tidak -> abaikan
kotak(SX, y, "Abaikan IP", C_START, w=2.6, h=0.9, fontsize=9)
panah(d["kanan"], d["cy"], SX - 1.3, y, "Tidak", warna=C_DEC)
prev = d["bawah"]

# 5. ARP/OUI
y -= 2.3
b, t = kotak(CX, y, "Baca tabel ARP -> MAC ->\nvendor (lookup OUI)", C_M1,
             fontsize=10)
panah(CX, prev, CX, t, "Ya", warna=C_DEC); prev = b

# 6. Modul 2: port scan
y -= 2.4
b, t = kotak(CX, y, "MODUL 2 — TCP connect scan\n(+ probe UDP SSDP/mDNS, opsional)",
             C_M2, fontsize=10)
panah(CX, prev, CX, t); prev = b

# 7. Modul 3: service detection
y -= 2.4
b, t = kotak(CX, y, "MODUL 3 — Banner grabbing &\ndeteksi layanan/versi\n(Nmap opsional -> fallback socket)",
             C_M3, fontsize=9.5)
panah(CX, prev, CX, t); prev = b

# 8. Modul 4: mapping
y -= 2.5
b, t = kotak(CX, y, "MODUL 4 — Petakan tiap port ke\nOWASP IoT Top 10", C_M4,
             fontsize=10)
panah(CX, prev, CX, t); prev = b

# 9. Decision banner usang
y -= 2.5
d = belah(CX, y, "Banner\nusang?")
panah(CX, prev, CX, d["atas"])
kotak(SX, y, "+ kategori I5,\nnaikkan severity", C_SIDE, w=2.8, h=1.0,
      fontsize=8.5)
panah(d["kanan"], d["cy"], SX - 1.4, y, "Ya", warna=C_DEC)
prev = d["bawah"]

# 10. Decision cek kredensial
y -= 2.5
d = belah(CX, y, "Kredensial\nbawaan?")
panah(CX, prev, CX, d["atas"], "Tidak", warna=C_DEC)
kotak(SX, y, "+ I1/I9 KRITIS\n(opt-in)", C_SIDE, w=2.8, h=1.0, fontsize=8.5)
panah(d["kanan"], d["cy"], SX - 1.4, y, "Ya", warna=C_DEC)
prev = d["bawah"]

# 11. Skor
y -= 2.4
b, t = kotak(CX, y, "Hitung skor host\nSkor = min(100, B_max + 3 x n)", C_M4,
             fontsize=10)
panah(CX, prev, CX, t, "Tidak", warna=C_DEC); prev = b

# 12. Decision host lain
y -= 2.5
d = belah(CX, y, "Masih ada\nhost?")
panah(CX, prev, CX, d["atas"])
# Ya -> loop balik ke modul 2 (panah melengkung ke kiri-atas)
ax.add_patch(FancyArrowPatch(
    (d["kiri"], d["cy"]), (CX - W / 2, y + 9.7),
    arrowstyle="-|>", mutation_scale=16, linewidth=1.6, color=C_DEC,
    connectionstyle="arc3,rad=-0.32"))
ax.text(0.5, y + 5.0, "Ya:\nhost\nberikutnya", fontsize=9, color=C_DEC,
        fontweight="bold", ha="center", va="center")
prev = d["bawah"]

# 13. Urutkan + laporan
y -= 2.4
b, t = kotak(CX, y, "Urutkan host menurut risiko\n& susun laporan", C_START,
             fontsize=10)
panah(CX, prev, CX, t, "Tidak", warna=C_DEC); prev = b

# 14. Selesai
y -= 2.3
b, t = oval(CX, y, "SELESAI — tampilkan + ekspor JSON/PDF", C_START, w=4.6)
panah(CX, prev, CX, t)

ax.text(CX, 30.95, "Alur Kerja Penggunaan Aplikasi HomeGuard",
        ha="center", va="center", fontsize=15, fontweight="bold",
        color="#222222")

plt.tight_layout()
out = __file__.rsplit("/", 1)[0] + "/flowchart_alur.png"
fig.savefig(out, dpi=170, bbox_inches="tight")
print("Flowchart tersimpan:", out)
