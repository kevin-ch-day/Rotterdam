"""Tests for network capture helpers."""

from pathlib import Path

import pytest


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("scapy") is None,
    reason="scapy is not available",
)
def test_parse_pcap_tracks_ip_flows(tmp_path: Path) -> None:
    """``parse_pcap`` should record IP flow information for packets."""
    from scapy.all import IP, TCP, Raw, wrpcap  # type: ignore
    from sandbox import intel
    from sandbox.network import parse_pcap

    # Load a simple reputation feed with a known bad IP and domain
    feed = tmp_path / "feed.txt"
    feed.write_text("93.184.216.34\nexample.com\n")
    intel.load_feeds([feed])

    pkt = (
        IP(src="10.1.1.1", dst="93.184.216.34")
        / TCP(sport=12345, dport=80)
        / Raw(b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
    )
    pcap_path = tmp_path / "test.pcap"
    wrpcap(str(pcap_path), [pkt])

    summary = parse_pcap(pcap_path, expected_domains=["allowed.com"])

    assert summary["unencrypted_http_request_count"] == 1
    assert summary["ip_flow_count"] == 1
    flow = summary["ip_flows"][0]
    assert flow["src"] == "10.1.1.1" and flow["dst"] == "93.184.216.34"
    assert flow["src_rep"] == 0 and flow["dst_rep"] == 100
    assert set(summary["unique_ips"]) == {"10.1.1.1", "93.184.216.34"}
    req = summary["unencrypted_http_requests"][0]
    assert req["src_ip"] == "10.1.1.1"
    assert req["dst_ip"] == "93.184.216.34"
    assert req["reputation"] == 100
    assert summary["unexpected_domains"] == ["example.com"]
    assert summary["malicious_ip_count"] == 1
    assert summary["malicious_domain_count"] == 1

    # Reset global intel state for other tests
    intel.BAD_IPS.clear()
    intel.BAD_DOMAINS.clear()

