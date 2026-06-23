"""Antarmuka pengguna Streamlit untuk HomeGuard.

Menyediakan UI berbasis web untuk menjalankan pemindaian keamanan jaringan
rumah, menampilkan host yang diurut menurut risiko, mengunduh laporan JSON,
serta panel referensi OWASP IoT Top 10.

Menjalankan::

    streamlit run app.py

PERINGATAN ETIKA: Gunakan HANYA pada jaringan milik sendiri atau yang Anda
miliki izin eksplisit untuk memindainya.
"""

from __future__ import annotations

import json

import streamlit as st

from homeguard import HomeGuardScanner, __version__, discovery
from homeguard.data import owasp_iot
from homeguard.report_pdf import build_pdf_bytes

# Pemetaan severity ke warna untuk badge tampilan.
WARNA_SEVERITY = {
    "AMAN": "#2e7d32",
    "RENDAH": "#0277bd",
    "SEDANG": "#f9a825",
    "TINGGI": "#ad1457",
    "KRITIS": "#c62828",
}


def parse_ports(spek: str):
    """Parse spesifikasi port dari input teks menjadi daftar int (atau None)."""
    spek = (spek or "").strip()
    if not spek:
        return None
    ports = set()
    for bagian in spek.split(","):
        bagian = bagian.strip()
        if not bagian:
            continue
        if "-" in bagian:
            awal, akhir = bagian.split("-", 1)
            ports.update(range(int(awal), int(akhir) + 1))
        else:
            ports.add(int(bagian))
    return sorted(ports)


def badge(severity: str) -> str:
    """Hasilkan potongan HTML badge berwarna untuk sebuah level severity."""
    warna = WARNA_SEVERITY.get(severity, "#555")
    return (
        f"<span style='background:{warna};color:white;padding:2px 8px;"
        f"border-radius:6px;font-weight:600'>{severity}</span>"
    )


def tampilkan_host(host: dict) -> None:
    """Render satu kartu host beserta temuan-temuannya."""
    tipe = host.get("device_type", "")
    judul = (
        f"{host['ip']} - {host.get('vendor') or 'Unknown'}"
        + (f" - {tipe}" if tipe else "")
        + f"  [{host['severity']}] skor {host['score']}"
    )
    with st.expander(judul, expanded=host["score"] >= 75):
        st.markdown(badge(host["severity"]), unsafe_allow_html=True)
        if tipe:
            st.write(f"**Tipe perangkat:** {tipe} "
                     f"(keyakinan {host.get('device_confidence', '-')})")
        if host.get("mac"):
            st.write(f"**MAC:** {host['mac']}")
        if host["owasp"]:
            st.write(f"**Kategori OWASP:** {', '.join(host['owasp'])}")
        if not host["findings"]:
            st.success("Tidak ada port berisiko terdeteksi.")
            return
        for f in host["findings"]:
            st.markdown(
                f"**{f['port']}/{f['service']}** &nbsp; "
                f"{badge(f['severity'])} &nbsp; {', '.join(f['owasp'])}",
                unsafe_allow_html=True,
            )
            st.caption(f["note"])
            if f.get("banner"):
                st.code(f["banner"], language=None)
            st.caption(f"Rekomendasi: {f['recommendation']}")


def panel_owasp() -> None:
    """Render panel referensi OWASP IoT Top 10 pada sidebar/utama."""
    st.subheader("Referensi OWASP IoT Top 10 (2018)")
    for kode, info in owasp_iot.OWASP_IOT_TOP_10.items():
        with st.expander(f"{kode} - {info['nama']}"):
            st.write(info["deskripsi"])


def inject_css() -> None:
    """Suntikkan CSS khusus agar tampilan lebih modern & profesional."""
    st.markdown(
        """
        <style>
          /* Sembunyikan menu & footer bawaan Streamlit untuk tampilan bersih */
          #MainMenu, footer {visibility: hidden;}

          /* Latar utama */
          .stApp {background: #f7f9fc;}

          /* Hero header bergradien */
          .hg-hero {
            background: linear-gradient(135deg, #0d1b3e 0%, #1b3a6b 60%,
                       #1a9e5a 140%);
            border-radius: 16px; padding: 22px 28px; margin-bottom: 18px;
            box-shadow: 0 8px 24px rgba(13,27,62,.18);
          }
          .hg-hero h1 {color:#fff; margin:0; font-size:2.1rem; font-weight:800;
            letter-spacing:.5px;}
          .hg-hero p {color:#cfddf0; margin:.25rem 0 0; font-size:1rem;}
          .hg-badge-ver {display:inline-block; background:rgba(255,255,255,.15);
            color:#fff; padding:2px 10px; border-radius:20px; font-size:.8rem;
            font-weight:600; margin-left:10px; vertical-align:middle;}

          /* Kartu metrik */
          div[data-testid="stMetric"] {
            background:#fff; border:1px solid #e6ebf2; border-radius:14px;
            padding:14px 18px; box-shadow:0 2px 8px rgba(13,27,62,.05);
          }
          div[data-testid="stMetricValue"] {font-weight:800;}

          /* Expander (kartu host) lebih menonjol */
          div[data-testid="stExpander"] {
            border:1px solid #e6ebf2 !important; border-radius:14px !important;
            box-shadow:0 2px 10px rgba(13,27,62,.06); margin-bottom:10px;
            overflow:hidden;
          }
          div[data-testid="stExpander"] summary {font-weight:700;
            font-size:1.02rem;}

          /* Tombol primer & unduh */
          .stButton>button, .stDownloadButton>button {
            border-radius:10px; font-weight:700; border:none;
          }
          .stButton>button[kind="primary"] {
            background:linear-gradient(135deg,#1a9e5a,#15824a);
          }

          /* Sidebar */
          section[data-testid="stSidebar"] {
            background:#ffffff; border-right:1px solid #e6ebf2;
          }
          section[data-testid="stSidebar"] h2 {color:#0d1b3e; font-weight:800;}

          /* Kotak banner etika */
          div[data-testid="stAlert"] {border-radius:12px;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Titik masuk aplikasi Streamlit."""
    st.set_page_config(page_title="HomeGuard", page_icon="🛡️", layout="wide")
    inject_css()
    st.markdown(
        f"""
        <div class="hg-hero">
          <h1>🛡️ HomeGuard
            <span class="hg-badge-ver">v{__version__}</span>
          </h1>
          <p>Pemindai keamanan jaringan rumah untuk perangkat IoT —
             pemetaan OWASP IoT Top 10 &amp; skor risiko</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.warning(
        "Etika: Gunakan HANYA pada jaringan milik sendiri atau yang Anda "
        "miliki izin eksplisit untuk memindainya."
    )

    # --- Sidebar konfigurasi ---
    with st.sidebar:
        st.header("Konfigurasi")
        mode = st.radio("Mode pemindaian", ["Subnet", "Host tunggal"])
        if mode == "Subnet":
            target = st.text_input(
                "Subnet (CIDR)",
                value="",
                placeholder="kosongkan untuk deteksi otomatis",
            )
        else:
            target = st.text_input("Alamat IP host", value="192.168.1.1")
        ports_teks = st.text_input(
            "Port", value="", placeholder="mis. 22,23,80,554 (default katalog)"
        )
        timeout = st.slider("Timeout (detik)", 0.2, 3.0, 1.0, 0.1)
        gunakan_nmap = st.checkbox(
            "Gunakan nmap -sV (fallback ke socket)", value=False
        )
        udp = st.checkbox("Probe UDP (SSDP/UPnP & mDNS)", value=False)
        tls_check = st.checkbox(
            "Periksa TLS & header keamanan HTTP", value=False
        )
        check_creds = st.checkbox(
            "Uji kredensial bawaan (opt-in)", value=False,
            help="Non-destruktif. Hanya untuk jaringan milik/diizinkan.",
        )
        if check_creds:
            st.warning("Pastikan Anda berwenang menguji target ini.")
        maks_host = st.number_input(
            "Maks host dipindai", min_value=1, max_value=512, value=64,
            help="Batas atas jumlah host untuk membatasi durasi pemindaian.",
        )
        pindai = st.button("Mulai Pindai", type="primary")

    # --- Eksekusi pemindaian ---
    if pindai:
        try:
            ports = parse_ports(ports_teks)
        except ValueError:
            st.error("Format port tidak valid.")
            return
        scanner = HomeGuardScanner(
            ports=ports, timeout=timeout, gunakan_nmap=gunakan_nmap,
            udp=udp, check_creds=check_creds, tls_check=tls_check,
        )
        if mode == "Host tunggal":
            with st.spinner(f"Memindai {target}..."):
                hasil = [scanner.scan_host(target)]
            nama_target = target
        else:
            # Penemuan host dahulu, lalu pemindaian per host dengan
            # progress bar agar UI responsif untuk subnet besar.
            with st.spinner("Menemukan host hidup..."):
                hosts = discovery.discover_hosts(
                    subnet=target or None,
                    timeout=min(timeout, 0.5),
                )
            hosts = hosts[: int(maks_host)]
            nama_target = target or "(deteksi otomatis)"
            hasil = []
            if hosts:
                bar = st.progress(0.0)
                status = st.empty()
                for i, h in enumerate(hosts, start=1):
                    status.text(
                        f"Memindai {h['ip']} ({i}/{len(hosts)})..."
                    )
                    hasil.append(
                        scanner.scan_host(
                            h["ip"], mac=h.get("mac"),
                            vendor=h.get("vendor"),
                        )
                    )
                    bar.progress(i / len(hosts))
                status.text(f"Selesai memindai {len(hosts)} host.")
        laporan = scanner.build_report(hasil, target=nama_target)
        st.session_state["laporan"] = laporan

    # --- Tampilkan hasil ---
    laporan = st.session_state.get("laporan")
    kolom_kiri, kolom_kanan = st.columns([2, 1])

    with kolom_kiri:
        if laporan:
            ring = laporan["ringkasan"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Total host", ring["total_host"])
            c2.metric("Host berisiko", ring["host_berisiko"])
            c3.metric("Skor tertinggi", ring["skor_tertinggi"])

            unduh1, unduh2 = st.columns(2)
            unduh1.download_button(
                "⬇️ Unduh JSON",
                data=json.dumps(laporan, ensure_ascii=False, indent=2),
                file_name="homeguard_laporan.json",
                mime="application/json",
            )
            unduh2.download_button(
                "⬇️ Unduh PDF",
                data=build_pdf_bytes(laporan),
                file_name="homeguard_laporan.pdf",
                mime="application/pdf",
            )

            st.subheader("Host (diurut menurut risiko)")
            if not laporan["hosts"]:
                st.info("Tidak ada host hidup yang ditemukan.")
            for host in laporan["hosts"]:
                tampilkan_host(host)
        else:
            st.info(
                "Konfigurasikan pemindaian pada sidebar lalu tekan "
                "**Mulai Pindai**."
            )

    with kolom_kanan:
        panel_owasp()


if __name__ == "__main__":
    main()
