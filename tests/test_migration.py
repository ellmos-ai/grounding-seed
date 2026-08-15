import json

from grounding_seed.migration import migrate


class _FakeTarget:
    """Test-Double fuer TargetWriter -- KEIN echter Zielspeicher-Adapter (bewusster
    Schnitt, siehe migration.py Moduldoku)."""

    def __init__(self, *, corrupt_write=False, drop_entries=0):
        self._entries: list[dict] = []
        self._corrupt_write = corrupt_write
        self._drop_entries = drop_entries

    def write_entries(self, entries):
        if self._corrupt_write:
            # simuliert eine Schreibkorruption: Werte werden verfaelscht
            self._entries = [{**e, "korrumpiert": True} for e in entries]
        else:
            stored = list(entries)
            if self._drop_entries:
                stored = stored[: -self._drop_entries]
            self._entries = stored

    def read_entries(self):
        return self._entries

    def describe(self):
        return "fake-target"


ENTRIES = [
    {"rolle": "decisions.ledger", "quelle": {"pfad": "/x"}},
    {"rolle": "user.model", "quelle": {"pfad": "/y"}},
]


def test_no_data_short_circuits(tmp_path):
    result = migrate(tmp_path, [], _FakeTarget())
    assert result.status == "no_data"


def test_successful_migration_archives_and_writes_connections_config(tmp_path):
    (tmp_path / "config.json").write_text(json.dumps({"rollen": {}}), encoding="utf-8")
    target = _FakeTarget()
    result = migrate(tmp_path, ENTRIES, target)
    assert result.status == "completed"
    assert result.verified_count == 2
    # Requirement 1: archiviert, nicht geloescht -- der lokale Bestand liegt noch da.
    archived = tmp_path / ".archive"
    assert archived.exists()
    archived_config = list(archived.rglob("config.json"))
    assert len(archived_config) == 1
    assert archived_config[0].exists()
    # Requirement 4: connections-config haelt WOHIN + SEIT WANN fest.
    conn = json.loads((tmp_path / "connections-config.json").read_text(encoding="utf-8"))
    assert conn["target"] == "fake-target"
    assert "migrated_at" in conn
    assert conn["verified_count"] == 2


def test_verification_failure_on_dropped_entries_keeps_local_intact(tmp_path):
    """Requirement 2+3: Zaehlung stimmt nicht -> gilt NICHT als abgeschlossen,
    kein Archivieren, lokaler Bestand bleibt aktiv."""
    marker = tmp_path / "config.json"
    marker.write_text(json.dumps({"rollen": {}}), encoding="utf-8")
    target = _FakeTarget(drop_entries=1)
    result = migrate(tmp_path, ENTRIES, target)
    assert result.status == "verification_failed"
    assert not (tmp_path / ".archive").exists()
    assert marker.exists()  # lokaler Bestand unangetastet -- das IST das Rollback


def test_verification_failure_on_checksum_mismatch_keeps_local_intact(tmp_path):
    marker = tmp_path / "config.json"
    marker.write_text(json.dumps({"rollen": {}}), encoding="utf-8")
    target = _FakeTarget(corrupt_write=True)
    result = migrate(tmp_path, ENTRIES, target)
    assert result.status == "verification_failed"
    assert not (tmp_path / ".archive").exists()
    assert marker.exists()


def test_verification_uses_checksum_not_just_error_absence(tmp_path):
    """Requirement 2 woertlich: 'nachweislich vollstaendig', nicht 'kein Fehler
    aufgetreten'. write_entries() wirft hier bewusst KEINEN Fehler, liefert aber
    kaputte Daten zurueck -- die Pruefsumme muss das trotzdem fangen."""
    marker = tmp_path / "config.json"
    marker.write_text(json.dumps({"rollen": {}}), encoding="utf-8")
    target = _FakeTarget(corrupt_write=True)
    result = migrate(tmp_path, ENTRIES, target)
    assert result.status == "verification_failed"
    assert result.message  # Grund ist benannt, kein stilles Scheitern
