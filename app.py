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

# Pemetaan severity ke warna untuk badge tampilan (dipertajam untuk dark mode).
WARNA_SEVERITY = {
    "AMAN": "#22c55e",
    "RENDAH": "#38bdf8",
    "SEDANG": "#fbbf24",
    "TINGGI": "#fb923c",
    "KRITIS": "#f43f5e",
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
    """Hasilkan potongan HTML badge (pill) berwarna untuk sebuah severity."""
    warna = WARNA_SEVERITY.get(severity, "#555")
    return (
        f"<span class='hg-pill' style='background:{warna};"
        f"box-shadow:0 0 0 3px {warna}22'>{severity}</span>"
    )


def chip_owasp(kode: str) -> str:
    """Hasilkan chip kecil berwarna untuk satu kategori OWASP (mis. I1)."""
    return f"<span class='hg-chip'>{kode}</span>"


def tampilkan_host(host: dict) -> None:
    """Render satu kartu host beserta temuan-temuannya."""
    tipe = host.get("device_type", "")
    sev = host["severity"]
    warna = WARNA_SEVERITY.get(sev, "#555")
    skor = host["score"]
    vendor = host.get("vendor") or "Unknown"
    judul = (
        f"{host['ip']} · {vendor}"
        + (f" · {tipe}" if tipe else "")
        + f"   [{sev}] skor {skor}"
    )
    with st.expander(judul, expanded=skor >= 75):
        # Header kartu: strip warna severity + skor besar + score bar
        chips = "".join(chip_owasp(k) for k in host["owasp"])
        meta = []
        if tipe:
            meta.append(f"🔖 {tipe} "
                        f"<small>(keyakinan {host.get('device_confidence','-')})</small>")
        if host.get("mac"):
            meta.append(f"🔗 {host['mac']}")
        meta_html = " &nbsp;·&nbsp; ".join(meta)
        st.markdown(
            f"""
            <div class="hg-host" style="border-left:6px solid {warna}">
              <div class="hg-host-top">
                <div>
                  <span class="hg-host-ip">{host['ip']}</span>
                  <span class="hg-host-vendor">{vendor}</span>
                </div>
                <div style="text-align:right">
                  {badge(sev)}
                  <span class="hg-score" style="color:{warna}">{skor}<small>/100</small></span>
                </div>
              </div>
              <div class="hg-bar"><div class="hg-bar-fill"
                   style="width:{skor}%;background:{warna}"></div></div>
              <div class="hg-meta">{meta_html}</div>
              <div class="hg-chips">{chips or '<span class="hg-muted">tidak ada kategori</span>'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not host["findings"]:
            st.success("✓ Tidak ada port berisiko terdeteksi.")
            return
        for f in host["findings"]:
            fwarna = WARNA_SEVERITY.get(f["severity"], "#555")
            fchips = "".join(chip_owasp(k) for k in f["owasp"])
            banner = (f"<div class='hg-banner'>{_esc(f['banner'])}</div>"
                      if f.get("banner") else "")
            st.markdown(
                f"""
                <div class="hg-find" style="border-left:4px solid {fwarna}">
                  <div class="hg-find-head">
                    <span class="hg-port">{f['port']}/{f['service']}</span>
                    {badge(f['severity'])}
                    <span class="hg-chips">{fchips}</span>
                  </div>
                  <div class="hg-note">{_esc(f['note'])}</div>
                  {banner}
                  <div class="hg-reco">💡 {_esc(f['recommendation'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _esc(teks: str) -> str:
    """Escape karakter HTML agar banner/teks aman ditampilkan."""
    return (str(teks).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def panel_owasp() -> None:
    """Render panel referensi OWASP IoT Top 10 pada sidebar/utama."""
    st.subheader("Referensi OWASP IoT Top 10 (2018)")
    for kode, info in owasp_iot.OWASP_IOT_TOP_10.items():
        with st.expander(f"{kode} - {info['nama']}"):
            st.write(info["deskripsi"])


def inject_css() -> None:
    """Suntikkan CSS tema 'Command Center' dark-cyber untuk HomeGuard."""
    st.markdown(
        """
        <style>
          /* ===== Dasar gelap ===== */
          #MainMenu, footer, header[data-testid="stHeader"] {visibility:hidden;}
          .stApp {background:
            radial-gradient(1200px 600px at 15% -5%, #15204a 0%, #0a0e1f 55%);
            color:#e5ecf5;}
          .block-container {padding-top:1.2rem;}

          /* Label gaya terminal (uppercase + monospace) */
          .hg-label {font-family:'Consolas','Courier New',monospace;
            text-transform:uppercase; letter-spacing:1.5px; font-size:.72rem;
            color:#8a93a8; font-weight:700; margin-bottom:6px;}

          /* ===== Top bar / hero ===== */
          .hg-hero {display:flex; align-items:center; justify-content:space-between;
            background:linear-gradient(90deg,#0d1430 0%,#111a3d 100%);
            border:1px solid #2a3566; border-radius:14px; padding:14px 22px;
            margin-bottom:18px; box-shadow:0 0 0 1px #6d5dfc33,
            0 10px 30px rgba(0,0,0,.35);}
          .hg-hero-logo {font-size:1.5rem; font-weight:800; color:#fff;
            letter-spacing:.5px;}
          .hg-hero-logo span {color:#22d3ee;}
          .hg-hero-nav {font-family:'Consolas',monospace; font-size:.78rem;
            letter-spacing:2px; color:#8a93a8;}
          .hg-hero-nav b {color:#22d3ee;}
          .hg-badge-ver {background:#22d3ee1a; color:#22d3ee; padding:3px 12px;
            border-radius:20px; font-size:.74rem; font-weight:700;
            border:1px solid #22d3ee44; font-family:'Consolas',monospace;}

          .hg-title {font-size:2.4rem; font-weight:800; color:#fff; margin:0;
            letter-spacing:.5px;}
          .hg-subtitle {color:#8a93a8; margin:.1rem 0 1rem;}

          /* ===== Kartu metrik / statistik ===== */
          .hg-stats {display:flex; gap:16px; margin:4px 0 18px;}
          .hg-stat {flex:1; background:#0f1733; border:1px solid #233063;
            border-radius:14px; padding:16px 18px; position:relative;
            box-shadow:0 6px 20px rgba(0,0,0,.25);}
          .hg-stat::before {content:""; position:absolute; left:16px; right:16px;
            top:0; height:2px; background:#22d3ee; border-radius:2px;
            box-shadow:0 0 12px #22d3ee;}
          .hg-stat-label {font-family:'Consolas',monospace; text-transform:uppercase;
            letter-spacing:1.2px; font-size:.72rem; color:#8a93a8; font-weight:700;}
          .hg-stat-val {font-size:2.4rem; font-weight:800; color:#fff;
            line-height:1.15;}

          /* ===== Kotak etika ===== */
          .hg-ethics {background:#1a1606; border:1px solid #5a4a12;
            border-left:4px solid #fbbf24; border-radius:12px; padding:14px 18px;
            margin-bottom:16px;}
          .hg-ethics b {color:#fbbf24;}
          .hg-ethics-t {color:#fbbf24; font-weight:800; margin-bottom:4px;}
          .hg-ethics p {color:#cdb98a; font-size:.88rem; margin:0;}

          /* ===== Tombol ===== */
          .stButton>button, .stDownloadButton>button {border-radius:10px;
            font-weight:700; font-family:'Consolas',monospace; letter-spacing:1px;
            text-transform:uppercase; border:1px solid #22d3ee55;
            background:#22d3ee14; color:#22d3ee; transition:all .2s;}
          .stButton>button:hover, .stDownloadButton>button:hover {
            background:#22d3ee26; box-shadow:0 0 18px #22d3ee55; color:#aef3ff;}
          .stButton>button[kind="primary"] {background:linear-gradient(135deg,
            #22d3ee,#0ea5b7); color:#04222a; border:none;
            box-shadow:0 0 18px #22d3ee66;}

          /* ===== Sidebar ===== */
          section[data-testid="stSidebar"] {background:#0c1230;
            border-right:1px solid #233063;}
          section[data-testid="stSidebar"] h2, .hg-side-h {color:#fff;
            font-weight:800; letter-spacing:.5px;}
          section[data-testid="stSidebar"] label {color:#c3ccde !important;}
          /* Pengelompok di sidebar */
          .hg-side-status {font-family:'Consolas',monospace; font-size:.74rem;
            color:#22d3ee; letter-spacing:1.5px;}
          .hg-side-status::before {content:"● "; color:#22c55e;}

          /* ===== Input ===== */
          input, .stTextInput input, .stNumberInput input {
            background:#0a0f28 !important; color:#7fe7ff !important;
            border:1px solid #2a3566 !important;
            font-family:'Consolas',monospace !important;}

          /* ===== Expander gelap ===== */
          div[data-testid="stExpander"] {border:1px solid #233063 !important;
            border-radius:12px !important; background:#0f1733;
            box-shadow:0 6px 18px rgba(0,0,0,.25); margin-bottom:10px;}
          div[data-testid="stExpander"] summary {font-weight:700;}

          /* ===== Pill & chip ===== */
          .hg-pill {color:#04121a; padding:3px 12px; border-radius:20px;
            font-weight:800; font-size:.74rem; letter-spacing:.6px;
            display:inline-block; font-family:'Consolas',monospace;}
          .hg-chip {display:inline-block; background:#16204a; color:#7fb0ff;
            border:1px solid #2a3a73; padding:1px 9px; border-radius:6px;
            font-size:.72rem; font-weight:700; margin:2px 4px 2px 0;
            font-family:'Consolas',monospace;}

          /* ===== Kartu host ===== */
          .hg-host {background:#0f1733; border:1px solid #233063;
            border-radius:12px; padding:14px 16px; margin:6px 0 14px;}
          .hg-host-top {display:flex; justify-content:space-between;
            align-items:center;}
          .hg-host-ip {font-size:1.3rem; font-weight:800; color:#fff;
            font-family:'Consolas',monospace;}
          .hg-host-vendor {color:#8a93a8; margin-left:8px; font-size:.9rem;}
          .hg-score {font-size:1.8rem; font-weight:800; margin-left:10px;
            vertical-align:middle; font-family:'Consolas',monospace;}
          .hg-score small {font-size:.8rem; color:#5e6b8a; font-weight:600;}
          .hg-bar {height:8px; background:#0a0f28; border-radius:6px;
            margin:10px 0; overflow:hidden; border:1px solid #1c2854;}
          .hg-bar-fill {height:100%; border-radius:6px; transition:width .4s ease;}
          .hg-meta {color:#aab4c8; font-size:.88rem; margin:4px 0;}
          .hg-chips {margin-top:4px;}
          .hg-muted {color:#5e6b8a; font-size:.8rem;}

          /* ===== Kartu temuan ===== */
          .hg-find {background:#0b1230; border:1px solid #1c2854;
            border-radius:10px; padding:10px 14px; margin:8px 0;}
          .hg-find-head {display:flex; align-items:center; gap:8px;
            flex-wrap:wrap;}
          .hg-port {font-weight:800; color:#7fe7ff; font-size:1rem;
            font-family:'Consolas',monospace;}
          .hg-note {color:#aab4c8; font-size:.88rem; margin:6px 0;}
          .hg-banner {background:#040a1e; color:#22d3ee;
            padding:8px 12px; border-radius:8px; border:1px solid #1c2854;
            font-family:'Consolas',monospace; font-size:.82rem; margin:6px 0;
            white-space:pre-wrap; word-break:break-all;}
          .hg-reco {color:#34d399; font-size:.85rem; font-weight:600;
            margin-top:6px;}

          /* ===== Kartu OWASP ===== */
          .hg-owasp-code {font-family:'Consolas',monospace; color:#22d3ee;
            font-size:.72rem; letter-spacing:1px; text-transform:uppercase;}
          h2, h3 {color:#fff;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Titik masuk aplikasi Streamlit."""
    st.set_page_config(page_title="HomeGuard", page_icon="🛡️", layout="wide")
    inject_css()
    # Top bar bergaya command center
    st.markdown(
        f"""
        <div class="hg-hero">
          <div class="hg-hero-logo">🛡️ Home<span>Guard</span></div>
          <div class="hg-hero-nav"><b>SCANNER</b> &nbsp;·&nbsp; LAPORAN
            &nbsp;·&nbsp; OWASP</div>
          <div class="hg-badge-ver">v{__version__}</div>
        </div>
        <div class="hg-title">Pusat Komando</div>
        <div class="hg-subtitle">Gambaran umum keamanan jaringan IoT Anda
          — pemetaan OWASP IoT Top 10 &amp; skor risiko.</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="hg-ethics">
          <div class="hg-ethics-t">⚖️ Etika Penggunaan</div>
          <p>Aplikasi ini dirancang <b>KHUSUS</b> untuk menguji jaringan IoT
          yang Anda miliki atau yang Anda punya izin tertulis untuk mengujinya.
          Pemindaian tanpa otorisasi adalah ilegal dan melanggar hukum.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Sidebar konfigurasi ---
    with st.sidebar:
        st.markdown(
            '<div class="hg-side-h" style="font-size:1.15rem">'
            'Konfigurasi Pemindai</div>'
            '<div class="hg-side-status">SISTEM SIAP</div><br>',
            unsafe_allow_html=True,
        )
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
            skor_max = ring["skor_tertinggi"]
            # Tentukan warna skor tertinggi sesuai ambang severity.
            if skor_max >= 90:
                warna_skor = WARNA_SEVERITY["KRITIS"]
            elif skor_max >= 75:
                warna_skor = WARNA_SEVERITY["TINGGI"]
            elif skor_max >= 50:
                warna_skor = WARNA_SEVERITY["SEDANG"]
            elif skor_max >= 25:
                warna_skor = WARNA_SEVERITY["RENDAH"]
            else:
                warna_skor = WARNA_SEVERITY["AMAN"]
            st.markdown(
                f"""
                <div class="hg-stats">
                  <div class="hg-stat">
                    <div class="hg-stat-label">Total host</div>
                    <div class="hg-stat-val">{ring['total_host']}</div>
                  </div>
                  <div class="hg-stat">
                    <div class="hg-stat-label">Host berisiko</div>
                    <div class="hg-stat-val">{ring['host_berisiko']}</div>
                  </div>
                  <div class="hg-stat" style="border-top:3px solid {warna_skor}">
                    <div class="hg-stat-label">Skor tertinggi</div>
                    <div class="hg-stat-val" style="color:{warna_skor}">
                      {skor_max}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

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
