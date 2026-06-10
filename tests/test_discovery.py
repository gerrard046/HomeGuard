"""Unit test untuk modul penemuan host (discovery)."""

from homeguard import discovery


def test_normalisasi_mac_berbagai_pemisah():
    """MAC dengan berbagai pemisah dinormalkan ke format kanonik."""
    target = "B8:27:EB:12:34:56"
    assert discovery.normalize_mac("B8:27:EB:12:34:56") == target
    assert discovery.normalize_mac("b8-27-eb-12-34-56") == target
    assert discovery.normalize_mac("b827.eb12.3456") == target
    assert discovery.normalize_mac("b827eb123456") == target


def test_mac_invalid_ditolak():
    """MAC tidak valid (panjang salah / bukan heksa) dikembalikan None."""
    assert discovery.normalize_mac("bukan-mac") is None
    assert discovery.normalize_mac("b8:27:eb:12:34") is None  # kurang oktet
    assert discovery.normalize_mac("") is None
    assert discovery.normalize_mac("ZZ:27:EB:12:34:56") is None


def test_lookup_vendor():
    """Prefiks Raspberry Pi dikenali; prefiks tak dikenal -> Unknown."""
    assert discovery.lookup_vendor("B8:27:EB:12:34:56") == (
        "Raspberry Pi Foundation"
    )
    assert discovery.lookup_vendor("00:00:00:11:22:33") == "Unknown"


def test_parse_ip_neigh_dan_arp_a():
    """Parsing `ip neigh` dan `arp -a`; baris tanpa MAC diabaikan."""
    keluaran_neigh = (
        "192.168.1.1 dev eth0 lladdr b8:27:eb:12:34:56 REACHABLE\n"
        "192.168.1.9 dev eth0 FAILED\n"
    )
    hasil_neigh = discovery.parse_ip_neigh(keluaran_neigh)
    assert hasil_neigh == [{"ip": "192.168.1.1", "mac": "B8:27:EB:12:34:56"}]

    keluaran_arp = (
        "router (192.168.1.1) at b8:27:eb:12:34:56 [ether] on eth0\n"
        "? (192.168.1.7) at <incomplete> on eth0\n"
    )
    hasil_arp = discovery.parse_arp_a(keluaran_arp)
    assert hasil_arp == [{"ip": "192.168.1.1", "mac": "B8:27:EB:12:34:56"}]


def test_expand_cidr_30_dan_32():
    """Ekspansi /30 menghasilkan 2 host; /32 menghasilkan 1 host."""
    assert discovery.expand_cidr("192.168.1.0/30") == [
        "192.168.1.1",
        "192.168.1.2",
    ]
    assert discovery.expand_cidr("192.168.1.5/32") == ["192.168.1.5"]


def test_deteksi_ip_privat():
    """Deteksi alamat IP privat vs publik."""
    assert discovery.is_private_ip("192.168.1.1") is True
    assert discovery.is_private_ip("10.0.0.5") is True
    assert discovery.is_private_ip("8.8.8.8") is False
    assert discovery.is_private_ip("bukan-ip") is False
