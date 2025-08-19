"""Runtime metrics collection helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable


def compute_runtime_metrics(
    permission_events: Iterable[str],
    network_events: Iterable[str],
    file_write_events: Iterable[str],
) -> Dict[str, Any]:
    """Aggregate sandbox execution data into simple metrics.

    Parameters
    ----------
    permission_events:
        Iterable of permission names observed at runtime.
    network_events:
        Iterable of network endpoints contacted (e.g., hostnames or URLs).
    file_write_events:
        Iterable of filesystem paths written to during execution.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing aggregated runtime metrics:

        ``permission_usage_counts``
            Mapping of permission name to usage count.
        ``unique_permission_count``
            Number of distinct permissions observed.
        ``network_endpoints`` / ``network_endpoint_count``
            Sorted list of unique network endpoints contacted and their count.
        ``filesystem_writes`` / ``filesystem_write_count``
            Sorted list of unique file paths written to and their count.
    """
    perm_counts = Counter(permission_events)
    endpoints = sorted(set(network_events))
    writes = sorted(set(file_write_events))

    return {
        "permission_usage_counts": dict(perm_counts),
        "unique_permission_count": len(perm_counts),
        "network_endpoints": endpoints,
        "network_endpoint_count": len(endpoints),
        "filesystem_writes": writes,
        "filesystem_write_count": len(writes),
    }
