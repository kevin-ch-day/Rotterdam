from core import renderers


def test_feature_list_renderer(capsys):
    feats = [{"name": "camera", "required": True}]
    renderers.print_feature_list(feats)
    out = capsys.readouterr().out
    assert "camera" in out
    assert "yes" in out


def test_component_table_renderer(capsys):
    comps = {"activity": [{"name": "MainActivity", "exported": True, "permission": ""}]}
    renderers.print_component_table(comps, "activity")
    out = capsys.readouterr().out
    assert "MainActivity" in out
    assert "yes" in out
