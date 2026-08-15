import json

import grounding_seed.ladder as gs_ladder
from grounding_seed.cli import main


def _force_isolated(monkeypatch):
    monkeypatch.setattr(gs_ladder, "_try_source_resolver", lambda rolle, *, scope, query: None)


def test_cli_status_reports_connected(tmp_path, capsys):
    rc = main(["--root", str(tmp_path), "status"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["connected"] is True  # source_resolver ist in dieser Testumgebung installiert


def test_cli_confirm_then_resolve(tmp_path, capsys, monkeypatch):
    _force_isolated(monkeypatch)
    root = tmp_path / "modul"
    quelle_file = tmp_path / "quelle.json"
    quelle_file.write_text(json.dumps({"pfad": "/x"}), encoding="utf-8")
    rc = main(["--root", str(root), "confirm", "decisions.ledger", str(quelle_file)])
    assert rc == 0
    capsys.readouterr()
    rc = main(["--root", str(root), "resolve", "decisions.ledger"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["quelle"] == {"pfad": "/x"}


def test_cli_scan_reports_missing_program(tmp_path, capsys):
    rc = main(["--root", str(tmp_path), "scan", "--program", "this-program-should-never-exist-xyz"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "this-program-should-never-exist-xyz" in out["resources_missing"]
