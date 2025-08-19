from app_utils import status_display


def test_status_lines(capsys):
    status_display.info("hello")
    status_display.good("there")
    status_display.warn("warn")
    status_display.fail("fail")

    out = capsys.readouterr()
    assert "[OK]" in out.out
    assert "[*]" in out.out
    assert "[!]" in out.err
    assert "[X]" in out.err
