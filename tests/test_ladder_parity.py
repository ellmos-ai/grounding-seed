"""Beweist die Kernbehauptung aus dem Ticket: die isolierte Minimalfassung
produziert DIESELBE Ergebnisform wie source_resolver.ladder -- gleiche Feldnamen,
gleiches Stufe/Status-Vokabular, gleiche dialog-Struktur bei Stufe 4. Ohne diesen
Beweis waere "ein Skill verhaelt sich in beiden Betriebsarten gleich" nur eine
Behauptung, keine getestete Eigenschaft (advisor-Review 2026-08-15)."""

import grounding_seed.ladder as gs_ladder
import source_resolver.ladder as sr_ladder
from grounding_seed.ladder import resolve as gs_resolve
from grounding_seed.store import LocalStore as GsLocalStore
from source_resolver.ladder import resolve as sr_resolve
from source_resolver.store import UserSourceStore as SrStore


def _force_isolated(monkeypatch):
    monkeypatch.setattr(gs_ladder, "_try_source_resolver", lambda rolle, *, scope, query: None)


def test_stufe_enum_values_identical():
    assert [s.value for s in gs_ladder.Stufe] == [s.value for s in sr_ladder.Stufe]
    assert [s.name for s in gs_ladder.Stufe] == [s.name for s in sr_ladder.Stufe]


def test_status_vocabulary_identical():
    gs_statuses = {v for k, v in vars(gs_ladder.ResolutionStatus).items() if not k.startswith("_")}
    sr_statuses = {v for k, v in vars(sr_ladder.ResolutionStatus).items() if not k.startswith("_")}
    assert gs_statuses == sr_statuses


def test_not_found_dialog_shape_identical(tmp_path, monkeypatch):
    _force_isolated(monkeypatch)
    gs_store = GsLocalStore(tmp_path / "gs")
    sr_store = SrStore(tmp_path / "sr" / "config.json")
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()

    gs_result = gs_resolve("noch.nie.gesehene.rolle", store=gs_store)
    sr_result = sr_resolve("noch.nie.gesehene.rolle", store=sr_store, home=fake_home)

    assert gs_result.stufe.value == sr_result.stufe.value
    assert gs_result.status == sr_result.status
    assert set(gs_result.dialog.keys()) == set(sr_result.dialog.keys())
    assert set(gs_result.to_dict().keys()) == set(sr_result.to_dict().keys())


def test_stufe0_result_shape_identical(tmp_path, monkeypatch):
    _force_isolated(monkeypatch)
    from grounding_seed.ladder import confirm as gs_confirm
    from source_resolver.ladder import confirm as sr_confirm

    gs_store = GsLocalStore(tmp_path / "gs")
    sr_store = SrStore(tmp_path / "sr" / "config.json")
    gs_confirm("decisions.ledger", {"pfad": "/x"}, store=gs_store, stufe_herkunft=2)
    sr_confirm("decisions.ledger", {"pfad": "/x"}, store=sr_store, stufe_herkunft=2)

    fake_home = tmp_path / "fake-home2"
    fake_home.mkdir()
    gs_result = gs_resolve("decisions.ledger", store=gs_store)
    sr_result = sr_resolve("decisions.ledger", store=sr_store, home=fake_home)

    assert gs_result.stufe.value == sr_result.stufe.value == 0
    assert gs_result.status == sr_result.status == "resolved"
    assert gs_result.quelle == sr_result.quelle == {"pfad": "/x"}
    assert set(gs_result.to_dict().keys()) == set(sr_result.to_dict().keys())


def test_confirm_requires_explicit_stufe_herkunft_in_both(tmp_path):
    """Regressionsanker fuer den beim Testlauf gefundenen Signatur-Drift: beide
    confirm()-Funktionen muessen stufe_herkunft VERLANGEN, kein stiller Default."""
    from grounding_seed.ladder import confirm as gs_confirm
    from source_resolver.ladder import confirm as sr_confirm

    gs_store = GsLocalStore(tmp_path / "gs2")
    sr_store = SrStore(tmp_path / "sr2" / "config.json")
    try:
        gs_confirm("x", {}, store=gs_store)
        assert False, "grounding_seed.confirm() sollte stufe_herkunft verlangen"
    except TypeError:
        pass
    try:
        sr_confirm("x", {}, store=sr_store)
        assert False, "source_resolver.confirm() sollte stufe_herkunft verlangen"
    except TypeError:
        pass
