import builtins

import pytest

from core import display
from cli import menu as cli_menu


def test_render_menu_formatting():
    out = display.render_menu(
        "Device Menu",
        ["Option A", "Option B"],
        exit_label="Back",
        serial="XYZ",
    )
    assert "Device Menu (serial: XYZ)" in out
    assert "[1] Option A" in out
    assert out.splitlines()[0].startswith("╭")


def test_prompt_choice_loop(monkeypatch, capsys):
    inputs = iter(["abc", "99", "2"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    choice = display.prompt_choice({"1", "2"})
    assert choice == "2"
    assert "Invalid choice" in capsys.readouterr().err


def test_prompt_choice_quit(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "q")
    assert display.prompt_choice({"1"}) == "q"


def test_device_menu_offline(monkeypatch, capsys):
    monkeypatch.setattr(cli_menu, "device_online", lambda serial: False)
    cli_menu.run_device_menu("abc")
    assert "no longer online" in capsys.readouterr().err.lower()


def test_main_menu_json():
    data = cli_menu.run_main_menu(json_mode=True)
    assert data["title"] == "Main Menu"
    assert any(opt["label"] == "Check for connected devices" for opt in data["options"])

