
import grounding_seed.ladder as gs_ladder
from grounding_seed.ladder import ResolutionStatus, Stufe, confirm, resolve
from grounding_seed.store import LocalStore, RoleEntry, now_iso


def _force_isolated(monkeypatch):
    """Erzwingt den Minimalfassungs-Pfad, indem die Delegation an source_resolver
    unterdrueckt wird -- source_resolver bleibt in dieser Testumgebung installiert."""
    monkeypatch.setattr(gs_ladder, "_try_source_resolver", lambda rolle, *, scope, query: None)


def test_isolated_stufe0_local_store_wins(tmp_path, monkeypatch):
    _force_isolated(monkeypatch)
    store = LocalStore(tmp_path)
    store.set(RoleEntry(rolle="decisions.ledger", aktiv=True, quelle={"pfad": "/x"}, stufe=0,
                         bestaetigt_am=now_iso(), bestaetigt_von="user", herkunft="manuell"))
    result = resolve("decisions.ledger", store=store)
    assert result.stufe == Stufe.NUTZER_KONFIGURATION
    assert result.quelle == {"pfad": "/x"}


def test_isolated_stufe1_known_providers_from_caller(tmp_path, monkeypatch):
    _force_isolated(monkeypatch)
    target = tmp_path / "gefundenes-modul"
    target.mkdir()
    store = LocalStore(tmp_path / "store")
    result = resolve(
        "capability.video-editing", store=store,
        known_providers={"capability.video-editing": [{"id": "ffmpeg-lokal", "target": str(target)}]},
    )
    assert result.stufe == Stufe.EIGENES_MODUL
    assert result.status == ResolutionStatus.RESOLVED


def test_isolated_stufe2_discovery_is_proposal_not_autoconfirmed(tmp_path, monkeypatch):
    _force_isolated(monkeypatch)
    discovery_root = tmp_path / "irgendwo"
    discovery_root.mkdir()
    (discovery_root / "MY-DECISIONS.md").write_text("x", encoding="utf-8")
    store = LocalStore(tmp_path / "store")
    result = resolve("decisions.ledger", store=store, discovery_roots=[discovery_root])
    assert result.stufe == Stufe.DISCOVERY_VORSCHLAG
    assert result.status == ResolutionStatus.PROPOSED
    assert store.get("decisions.ledger") is None


def test_isolated_stufe4_dialog_when_nothing_found(tmp_path, monkeypatch):
    _force_isolated(monkeypatch)
    store = LocalStore(tmp_path)
    result = resolve("noch.nie.gesehen", store=store)
    assert result.stufe == Stufe.NICHT_GEFUNDEN
    assert result.dialog is not None
    assert "frage_1" in result.dialog
    assert "frage_2_falls_unbekannt" in result.dialog


def test_confirm_promotes_to_stufe0(tmp_path, monkeypatch):
    _force_isolated(monkeypatch)
    store = LocalStore(tmp_path)
    confirm("decisions.ledger", {"pfad": "/gefunden"}, store=store, stufe_herkunft=2)
    result = resolve("decisions.ledger", store=store)
    assert result.stufe == Stufe.NUTZER_KONFIGURATION
    assert result.quelle == {"pfad": "/gefunden"}


def test_delegates_to_real_source_resolver_when_importable(tmp_path):
    """Kein Force-Isolate hier -- source_resolver ist installiert, muss also
    genutzt werden (kein zweiter Resolver, wenn der echte verfuegbar ist)."""
    store = LocalStore(tmp_path)  # wird bei Delegation gar nicht angefasst
    result = resolve("noch.nie.gesehen.beim.echten.resolver", store=store)
    # Kommt vom ECHTEN source_resolver (dort ohne KNOWN_MODULE_PROVIDERS-Eintrag
    # ebenfalls Stufe 4) -- die Delegation hat tatsaechlich stattgefunden.
    assert result.stufe == Stufe.NICHT_GEFUNDEN
    assert result.herkunft == "keine"
