"""Simple local threat intelligence lookup utilities.

This module loads IP and domain reputation data from plain text feeds such as
Maltrail or AbuseIPDB exports.  Each line of a feed file is expected to contain
an IP address or domain name.  Lines beginning with ``#`` are treated as
comments and ignored.

The reputation model is intentionally minimal: any entry found in the feeds is
assigned a score of ``100`` while unknown entries return ``0``.  The lightweight
interface keeps the module easy to test and sufficient for basic risk scoring
purposes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

# In-memory sets of known-bad indicators populated via :func:`load_feeds`.
BAD_IPS: set[str] = set()
BAD_DOMAINS: set[str] = set()


def load_feeds(paths: Iterable[str | Path]) -> None:
    """Populate :data:`BAD_IPS` and :data:`BAD_DOMAINS` from ``paths``.

    Parameters
    ----------
    paths:
        Iterable of file paths containing newline separated IPs or domains.
    """
    for p in paths:
        path = Path(p)
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if any(c.isalpha() for c in line):
                BAD_DOMAINS.add(line.lower())
            else:
                BAD_IPS.add(line)


def score_ip(ip: str) -> int:
    """Return a simple reputation score for ``ip``.

    The score is ``100`` if the IP appears in the loaded feeds, otherwise ``0``.
    """
    return 100 if ip in BAD_IPS else 0


def score_domain(domain: str) -> int:
    """Return a reputation score for ``domain``.

    The score is ``100`` if the domain appears in the loaded feeds, otherwise
    ``0``.
    """
    return 100 if domain.lower() in BAD_DOMAINS else 0

