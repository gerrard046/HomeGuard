# Reproduksibilitas Hasil Paper HomeGuard

Dokumen ini memetakan **setiap tabel dan gambar hasil pada paper** ke skrip
yang menghasilkannya, sehingga seluruh angka dapat direproduksi dan
dipertanggungjawabkan. Ini menjawab salah satu kriteria kualitas terpenting
dalam evaluasi artefak ilmiah (*design science research*): hasil harus dapat
diverifikasi ulang oleh pihak ketiga.

> **PENTING — jangan salin angka loopback ke paper.** Mode `loopback` (satu
> mesin, 127.0.0.x) disediakan agar pipeline dapat diuji cepat tanpa VM. Karena
> tidak ada latensi/kehilangan paket jaringan, mode ini cenderung menghasilkan
> deteksi sempurna (F1 = 1,0) dan waktu sangat singkat. **Angka yang dilaporkan
> di paper HARUS berasal dari mode `vm`** (lingkungan VirtualBox
> `192.168.56.0/24`), yang merefleksikan kondisi jaringan nyata (timeout,
> false positive/negative). Loopback hanya untuk memverifikasi bahwa skrip
> berjalan benar.

## 0. Prasyarat

```bash
pip install -r requirements.txt      # inti HomeGuard (pustaka standar)
pip install psutil                   # untuk metrik CPU pada measure_resources
sudo apt-get install nmap            # untuk benchmark_nmap (opsional)
```

## 1. Menyalakan lingkungan lab

**Opsi A — lab VirtualBox sungguhan (untuk angka paper).** Pada tiap VM,
jalankan perangkat tiruan dengan IP sesuai `lab/ground_truth.json`:

```bash
# di VM 192.168.56.20 (CCTV):
python lab/mock_iot_device.py --ip 192.168.56.20 --ports 23,80,554,8080
# ulangi untuk .30 .40 .50 .60 sesuai ground_truth.json
```

**Opsi B — reproduksi lokal cepat (uji pipeline, Linux).** Seluruh 5 perangkat
dinyalakan sekaligus pada loopback:

```bash
python lab/run_lab.py     # biarkan berjalan di satu terminal
```

## 2. Menghasilkan tiap hasil paper

| Hasil di paper | Skrip | Perintah (mode VM) |
|---|---|---|
| Tabel *Metrik Akurasi Deteksi Port* & Gambar metrik | `tools/measure_detection.py` | `python tools/measure_detection.py --targets vm --json det.json` |
| Tabel *Kinerja Waktu Pemindaian* & Gambar kecepatan | `tools/measure_speed.py` | `python tools/measure_speed.py --targets vm --repeat 5 --json speed.json` |
| Tabel *Konsumsi Sumber Daya* & Gambar sumber daya | `tools/measure_resources.py` | `python tools/measure_resources.py --targets vm --repeat 5 --json res.json` |
| **Baseline vs Nmap** (poin plus baru) | `tools/benchmark_nmap.py` | `python tools/benchmark_nmap.py --targets vm --json bench.json` |
| Pengujian fungsional localhost (Tabel CLI) | `demo_lokal.py` | `python demo_lokal.py` |
| Pengujian unit (36/36) | `pytest` | `pytest -v` |
| Gambar arsitektur pipeline | `paper/diagram_pipeline.py` | `python paper/diagram_pipeline.py` |

Untuk reproduksi lokal, ganti `--targets vm` menjadi `--targets loopback`.

## 3. Benchmark terhadap Nmap

`tools/benchmark_nmap.py` menjalankan HomeGuard (socket murni, tanpa root) dan
`nmap -sT -Pn` (TCP connect, tanpa root) terhadap **target yang sama**, lalu
membandingkan precision/recall/F1 deteksi port dan waktu total. Ini memberi
baseline kuantitatif terhadap perkakas mapan — bukan sekadar perbandingan fitur
kualitatif. Angka dihasilkan saat dijalankan; skrip tidak memuat hasil tetap.

## 4. Studi usability (SUS)

Instrumen dan prosedur untuk mengukur klaim "ramah pengguna awam" secara
empiris tersedia pada [`docs/usability_sus.md`](usability_sus.md). Hasil SUS
mengubah klaim edukatif dari asumsi menjadi temuan terukur — pembeda kuat dari
paper pemindai jaringan lain.
