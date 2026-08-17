from grounding_seed.store import SCHEMA_ID, LocalStore, RoleEntry, now_iso


def test_root_is_required_no_global_default(tmp_path):
    store = LocalStore(tmp_path / "modul-eigen")
    assert store.get("decisions.ledger") is None
    store.set(RoleEntry(
        rolle="decisions.ledger", aktiv=True, quelle={"pfad": "x"}, stufe=0,
        bestaetigt_am=now_iso(), bestaetigt_von="user", herkunft="manuell",
    ))
    assert store.path.parent == tmp_path / "modul-eigen"


def test_schema_id_matches_source_resolver_schema():
    """Vorwaertskompatibilitaet: identische Schema-Kennung wie source_resolver.store."""
    from source_resolver.store import SCHEMA_ID as SOURCE_RESOLVER_SCHEMA_ID
    assert SCHEMA_ID == SOURCE_RESOLVER_SCHEMA_ID


def test_roundtrip(tmp_path):
    store = LocalStore(tmp_path)
    store.set(RoleEntry(
        rolle="capability.video-editing", aktiv=True, quelle={"programm": "ffmpeg"}, stufe=0,
        bestaetigt_am=now_iso(), bestaetigt_von="user", herkunft="manuell",
    ))
    loaded = store.get("capability.video-editing")
    assert loaded is not None
    assert loaded.quelle == {"programm": "ffmpeg"}


def test_all_entries_sorted_is_deterministic(tmp_path):
    store = LocalStore(tmp_path)
    for rolle in ("z.role", "a.role", "m.role"):
        store.set(RoleEntry(rolle=rolle, aktiv=True, quelle={}, stufe=0,
                             bestaetigt_am=now_iso(), bestaetigt_von="user", herkunft="manuell"))
    entries = store.all_entries_sorted()
    roles_in_order = [e["rolle"] for e in entries]
    assert roles_in_order == sorted(roles_in_order)


def test_corrupted_store_raises_explicit_error(tmp_path):
    (tmp_path).mkdir(exist_ok=True)
    (tmp_path / "config.json").write_text("{broken", encoding="utf-8")
    store = LocalStore(tmp_path)
    try:
        store.get("x")
        assert False, "expected ValueError"
    except ValueError as error:
        assert "beschaedigt" in str(error)
