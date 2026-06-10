"""Pembangkit diagram arsitektur pipeline HomeGuard (Gambar 1 pada paper).

Menghasilkan berkas ``diagram_pipeline.png`` berisi empat modul berurutan
beserta basis pengetahuan statis. Jalankan:

    python paper/diagram_pipeline.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# Definisi modul pipeline: (judul, subjudul, warna).
MODUL = [
    ("1. Network\nDiscovery", "TCP ping, ARP,\nOUI, CIDR", "#1565c0"),
    ("2. Port\nScanning", "TCP connect\nThreadPool", "#2e7d32"),
    ("3. Service\nDetection", "Banner grab,\nNmap opsional", "#ef6c00"),
    ("4. OWASP Mapping\n& Risk Scoring", "I1..I10,\nskor 0-100", "#c62828"),
]

fig, ax = plt.subplots(figsize=(10, 3.4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 3.4)
ax.axis("off")

lebar, tinggi = 2.0, 1.3
y = 1.7
x_kotak = []
for i, (judul, sub, warna) in enumerate(MODUL):
    x = 0.35 + i * 2.45
    x_kotak.append((x, x + lebar))
    kotak = FancyBboxPatch(
        (x, y), lebar, tinggi,
        boxstyle="round,pad=0.04,rounding_size=0.12",
        linewidth=1.6, edgecolor=warna, facecolor=warna + "22",
    )
    ax.add_patch(kotak)
    ax.text(x + lebar / 2, y + tinggi - 0.36, judul, ha="center",
            va="center", fontsize=11, fontweight="bold", color=warna)
    ax.text(x + lebar / 2, y + 0.30, sub, ha="center", va="center",
            fontsize=8.5, color="#333333")

# Panah antar modul.
for i in range(len(MODUL) - 1):
    panah = FancyArrowPatch(
        (x_kotak[i][1], y + tinggi / 2),
        (x_kotak[i + 1][0], y + tinggi / 2),
        arrowstyle="-|>", mutation_scale=18, linewidth=1.8, color="#555555",
    )
    ax.add_patch(panah)

# Basis pengetahuan statis di bawah.
ax.text(5.0, 0.78, "Basis Pengetahuan Statis:  "
        "iot_ports  |  owasp_iot (2018)  |  oui (OUI IEEE)",
        ha="center", va="center", fontsize=9, style="italic",
        color="#444444",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#f0f0f0",
                  edgecolor="#bbbbbb"))

ax.text(5.0, 3.15, "Arsitektur Pipeline HomeGuard", ha="center",
        va="center", fontsize=13, fontweight="bold", color="#222222")

plt.tight_layout()
out = __file__.rsplit("/", 1)[0] + "/diagram_pipeline.png"
fig.savefig(out, dpi=200, bbox_inches="tight")
print("Diagram tersimpan:", out)
