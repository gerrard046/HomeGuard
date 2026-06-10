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

from homeguard import HomeGuardScanner, __version__
from homeguard.data import owasp_iot

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
    judul = (
        f"{host['ip']} - {host.get('vendor') or 'Unknown'} "
        f"[{host['severity']}] skor {host['score']}"
    )
    with st.expander(judul, expanded=host["score"] >= 75):
        st.markdown(badge(host["severity"]), unsafe_allow_html=True)
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


def main() -> None:
    """Titik masuk aplikasi Streamlit."""
    st.set_page_config(page_title="HomeGuard", page_icon="🛡️", layout="wide")
    st.title("🛡️ HomeGuard")
    st.caption(
        f"Pemindai keamanan jaringan rumah untuk perangkat IoT - v{__version__}"
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
        pindai = st.button("Mulai Pindai", type="primary")

    # --- Eksekusi pemindaian ---
    if pindai:
        try:
            ports = parse_ports(ports_teks)
        except ValueError:
            st.error("Format port tidak valid.")
            return
        scanner = HomeGuardScanner(
            ports=ports, timeout=timeout, gunakan_nmap=gunakan_nmap
        )
        with st.spinner("Memindai jaringan..."):
            if mode == "Host tunggal":
                hasil = [scanner.scan_host(target)]
                nama_target = target
            else:
                hasil = scanner.scan_subnet(target or None)
                nama_target = target or "(deteksi otomatis)"
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

            st.download_button(
                "⬇️ Unduh laporan JSON",
                data=json.dumps(laporan, ensure_ascii=False, indent=2),
                file_name="homeguard_laporan.json",
                mime="application/json",
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
