
from grounding_seed.location import detect_ecosystem


def test_detect_ecosystem_connected_when_source_resolver_importable():
    status = detect_ecosystem()
    # source_resolver ist in dieser Testumgebung mitinstalliert (siehe conftest/CI-Setup)
    assert status.connected is True
    assert status.source_resolver_version is not None


def test_detect_ecosystem_hint_findings_are_informational_only(tmp_path, monkeypatch):
    import grounding_seed.location as location_mod

    def _no_import(name):
        raise ImportError("simuliert: nicht installiert")

    monkeypatch.setattr(location_mod.importlib, "import_module", _no_import)
    empty_root = tmp_path / "leer"
    empty_root.mkdir()
    status = detect_ecosystem(hint_root=empty_root)
    assert status.connected is False
    assert status.hint_findings["composition_rules_json"] is False
    assert status.hint_findings["control_center"] is False


def test_detect_ecosystem_without_hint_root_has_no_hint_findings(monkeypatch):
    import grounding_seed.location as location_mod

    def _no_import(name):
        raise ImportError("simuliert")

    monkeypatch.setattr(location_mod.importlib, "import_module", _no_import)
    status = detect_ecosystem()
    assert status.connected is False
    assert status.hint_findings == {}
