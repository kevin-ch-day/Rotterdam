#!/usr/bin/env python3
"""Utility for capturing and summarizing network traffic from an emulator.

This module provides a light abstraction around ``tcpdump`` or ``mitmproxy``
invoked via ``adb`` to capture packets on an Android emulator before an app
launches. Captured packets are stored as ``pcap`` files which can then be
parsed to look for:

* Unencrypted HTTP requests
* Requests to unexpected domains
* Observed source and destination IP address pairs

The resulting summary can be exported as JSON for later scoring.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Iterable, Optional

from ...devices.adb import _adb_path, _run_adb
from . import intel


# Define HTTP methods to search in packets
HTTP_METHODS = (
    b"GET",
    b"POST",
    b"HEAD",
    b"PUT",
    b"DELETE",
    b"OPTIONS",
    b"TRACE",
    b"PATCH",
)


def sniff_network(apk_path: str) -> list[dict[str, str]]:
    """Return a mocked network flow list for *apk_path*.

    The real project would invoke a sniffer and parse packets. For testing we
    simply return a deterministic example record.
    """
    return [{"source": "127.0.0.1", "destination": "example.com"}]


class NetworkSniffer:
    """Context manager handling capture and analysis of network traffic."""

    def __init__(
        self,
        serial: str,
        *,
        tool: str = "tcpdump",
        output_dir: str | Path = "output/network",
        expected_domains: Optional[Iterable[str]] = None,
        tcpdump_filter: str = "",
    ) -> None:
        """Initialize the network sniffer with required settings."""
        self.serial = serial
        self.tool = tool
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.expected_domains = {d.lower() for d in (expected_domains or [])}
        self.pcap_path = self.output_dir / "capture.pcap"
        self._proc: subprocess.Popen | None = None
        self._device_pcap = "/sdcard/rotterdam_capture.pcap"
        self.tcpdump_filter = tcpdump_filter

    # ------------------------------------------------------------------
    # Capture control methods
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start the capture process before launching the target app."""
        if self.tool == "tcpdump":
            adb = _adb_path()
            cmd = [
                adb,
                "-s",
                self.serial,
                "shell",
                f"tcpdump -i any -p -w {self._device_pcap} {self.tcpdump_filter}",
            ]
            self._proc = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        elif self.tool == "mitmproxy":
            cmd = ["mitmdump", "--tcpdump", str(self.pcap_path)]
            self._proc = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        else:
            raise ValueError(f"Unsupported tool: {self.tool}")

    def stop(self) -> Path:
        """Stop capture and ensure the pcap is available locally."""
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except Exception:
                self._proc.kill()

        if self.tool == "tcpdump":
            adb = _adb_path()
            try:
                _run_adb([adb, "-s", self.serial, "shell", "pkill tcpdump"])
            except Exception:
                # best effort: tcpdump may already be stopped
                pass
            _run_adb([adb, "-s", self.serial, "pull", self._device_pcap, str(self.pcap_path)])
            try:
                _run_adb([adb, "-s", self.serial, "shell", f"rm {self._device_pcap}"])
            except Exception:
                pass
        return self.pcap_path

    # ------------------------------------------------------------------
    # Analysis / reporting methods
    # ------------------------------------------------------------------
    def summarize(self) -> dict:
        """Parse the captured pcap and return a summary dictionary."""
        return parse_pcap(self.pcap_path, self.expected_domains)

    def export(self, path: str | Path) -> Path:
        """Write the summary to ``path`` in JSON format."""
        summary = self.summarize()
        return export_summary(summary, path)

    # ------------------------------------------------------------------
    # Context manager helpers
    # ------------------------------------------------------------------
    def __enter__(self) -> "NetworkSniffer":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()


# ----------------------------------------------------------------------
# PCAP parsing helpers
# ----------------------------------------------------------------------
def parse_pcap(pcap: str | Path, expected_domains: Optional[Iterable[str]] = None) -> dict:
    """Return summary information about ``pcap`` including IP flows.

    Parameters
    ----------
    pcap:
        Path to the capture file.
    expected_domains:
        Iterable of domain names that are allowed. Any HTTP request with a host
        not in this set will be flagged as unexpected.
    """
    expected = {d.lower() for d in (expected_domains or [])}
    summary = {
        "unencrypted_http_requests": [],  # list of dicts
        "unexpected_domains": [],  # list of domain strings
        "unencrypted_http_request_count": 0,
        "unexpected_domain_count": 0,
        "unique_ips": [],
        "unique_ip_count": 0,
        "ip_flows": [],  # list of dicts with src/dst/count and reputation
        "ip_flow_count": 0,
        "malicious_ips": [],
        "malicious_ip_count": 0,
        "malicious_domains": [],
        "malicious_domain_count": 0,
        "malicious_endpoint_count": 0,
    }

    try:
        from scapy.all import TCP, Raw, IP, rdpcap  # type: ignore
    except Exception:
        return summary  # scapy not available

    packets = rdpcap(str(pcap))
    seen_unexpected: set[str] = set()
    unique_ips: set[str] = set()
    flow_counts: dict[tuple[str, str], int] = {}
    malicious_domains: set[str] = set()

    for pkt in packets:
        src = dst = ""
        if pkt.haslayer(IP):
            src = pkt[IP].src
            dst = pkt[IP].dst
            unique_ips.add(src)
            unique_ips.add(dst)
            key = (src, dst)
            flow_counts[key] = flow_counts.get(key, 0) + 1

        if pkt.haslayer(TCP) and pkt.haslayer(Raw):
            payload: bytes = bytes(pkt[Raw].load)
            if any(payload.startswith(m + b" ") for m in HTTP_METHODS):
                host_match = re.search(br"(?i)\r\nHost:\s*([^\r\n]+)", payload)
                host = host_match.group(1).decode("utf-8", "ignore") if host_match else ""
                first_line = payload.split(b"\r\n", 1)[0].decode("utf-8", "ignore")
                parts = first_line.split()
                method = parts[0] if parts else ""
                path = parts[1] if len(parts) > 1 else ""
                host_rep = intel.score_domain(host) if host else 0
                summary["unencrypted_http_requests"].append(
                    {
                        "method": method,
                        "host": host,
                        "path": path,
                        "src_ip": src,
                        "dst_ip": dst,
                        "reputation": host_rep,
                    }
                )
                h_lower = host.lower()
                if host_rep:
                    malicious_domains.add(h_lower)
                if h_lower and h_lower not in expected:
                    seen_unexpected.add(h_lower)

    ip_reputation = {ip: intel.score_ip(ip) for ip in unique_ips}
    malicious_ips = {ip for ip, score in ip_reputation.items() if score > 0}

    summary["unexpected_domains"] = sorted(seen_unexpected)
    summary["unencrypted_http_request_count"] = len(summary["unencrypted_http_requests"])
    summary["unexpected_domain_count"] = len(summary["unexpected_domains"])
    summary["unique_ips"] = sorted(unique_ips)
    summary["unique_ip_count"] = len(unique_ips)
    summary["malicious_ips"] = sorted(malicious_ips)
    summary["malicious_ip_count"] = len(malicious_ips)
    summary["malicious_domains"] = sorted(malicious_domains)
    summary["malicious_domain_count"] = len(malicious_domains)
    summary["malicious_endpoint_count"] = summary["malicious_ip_count"] + summary["malicious_domain_count"]
    summary["ip_flows"] = [
        {
            "src": s,
            "dst": d,
            "count": c,
            "src_rep": ip_reputation.get(s, 0),
            "dst_rep": ip_reputation.get(d, 0),
        }
        for (s, d), c in sorted(flow_counts.items())
    ]
    summary["ip_flow_count"] = len(flow_counts)
    return summary


def export_summary(summary: dict, path: str | Path) -> Path:
    """Convenience helper to export ``summary`` to JSON file at ``path``."""
    out_path = Path(path)
    out_path.write_text(json.dumps(summary, indent=2))
    return out_path


def _build_arg_parser() -> argparse.ArgumentParser:
    """Return an ``argparse.ArgumentParser`` for the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True, help="ADB serial of target emulator")
    parser.add_argument("--tool", choices=["tcpdump", "mitmproxy"], default="tcpdump")
    parser.add_argument(
        "--expected-domain",
        action="append",
        dest="expected_domains",
        default=[],
        help="Domain that is expected; may be repeated",
    )
    parser.add_argument("--output-dir", default="output/network")
    parser.add_argument("--tcpdump-filter", default="", help="Optional tcpdump filter expression")
    parser.add_argument(
        "--duration", type=int, default=10, help="Seconds to capture before stopping"
    )
    parser.add_argument(
        "--json", help="Path to export summary JSON; default prints to stdout"
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Simple CLI for ad-hoc captures."""
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    with NetworkSniffer(
        args.serial,
        tool=args.tool,
        output_dir=args.output_dir,
        expected_domains=args.expected_domains,
        tcpdump_filter=args.tcpdump_filter,
    ) as sniffer:
        time.sleep(max(args.duration, 0))
        summary = sniffer.summarize()
    if args.json:
        export_summary(summary, args.json)
    else:
        print(json.dumps(summary, indent=2))
    return 0
