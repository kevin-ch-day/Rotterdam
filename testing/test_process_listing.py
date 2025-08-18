from device_analysis.process_listing import parse_ps


def test_parse_ps_parses_lines():
    sample = (
        "USER PID PPID VSIZE RSS WCHAN ADDR S NAME\n"
        "u0_a123 12345 100 123456 1234 ffffffff 00000000 S com.example.app\n"
        "system 1 0 1234 123 - 0 S init\n"
    )
    procs = parse_ps(sample)
    assert procs[0] == {"user": "u0_a123", "pid": "12345", "name": "com.example.app"}
    assert procs[1]["name"] == "init"
