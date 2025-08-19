from sandbox.metrics import compute_runtime_metrics

def test_compute_runtime_metrics():
    perms = [
        "android.permission.INTERNET",
        "android.permission.INTERNET",
        "android.permission.READ_CONTACTS",
    ]
    network = ["https://example.com", "https://example.com", "https://other.com"]
    writes = ["/data/a.txt", "/data/b.txt", "/data/a.txt"]
    metrics = compute_runtime_metrics(perms, network, writes)
    assert metrics["permission_usage_counts"]["android.permission.INTERNET"] == 2
    assert metrics["network_endpoints"] == ["https://example.com", "https://other.com"]
    assert metrics["filesystem_writes"] == ["/data/a.txt", "/data/b.txt"]
    assert metrics["unique_permission_count"] == 2
    assert metrics["network_endpoint_count"] == 2
    assert metrics["filesystem_write_count"] == 2
