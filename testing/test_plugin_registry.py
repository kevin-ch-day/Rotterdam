import pytest

from core import plugins


@pytest.fixture(autouse=True)
def clear_registry():
    plugins.clear()
    yield
    plugins.clear()


def test_register_and_get():
    def sample():
        return 1
    plugins.register("sample", sample)
    assert plugins.get("sample")() == 1


def test_decorator_register():
    @plugins.analyzer("decorated")
    def decorated():
        return 2
    assert plugins.get("decorated")() == 2


def test_duplicate_register_raises():
    def dup():
        pass
    plugins.register("dup", dup)
    with pytest.raises(KeyError):
        plugins.register("dup", dup)


def test_load_entry_point_plugins(monkeypatch):
    class EP:
        def __init__(self, name):
            self.name = name
        def load(self):
            return lambda: "loaded"

    class Eps:
        def select(self, group):
            assert group == "rotterdam.analyzers"
            return [EP("ep1")]

    monkeypatch.setattr(plugins.metadata, "entry_points", lambda: Eps())
    plugins.load_entry_point_plugins()
    assert "ep1" in plugins.available()
