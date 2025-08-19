from core import status


def test_status_lines(capsys):
    status.info("hello")
    status.good("there")
    status.warn("warn")
    status.fail("fail")

    out = capsys.readouterr()
    assert "[OK]" in out.out
    assert "[*]" in out.out
    assert "[!]" in out.err
    assert "[X]" in out.err
