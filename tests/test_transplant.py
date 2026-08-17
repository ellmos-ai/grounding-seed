import json
from datetime import datetime, timedelta, timezone

from grounding_seed.transplant import check_transplant


def test_first_run_triggers_rescan(tmp_path):
    signal = check_transplant(tmp_path / "marker.json")
    assert signal.should_rescan is True
    assert "Erstlauf" in signal.reason


def test_second_run_within_interval_skips_rescan(tmp_path):
    marker = tmp_path / "marker.json"
    check_transplant(marker)  # Erstlauf, schreibt Marker
    signal = check_transplant(marker, min_interval_hours=24.0)
    assert signal.should_rescan is False


def test_hostname_change_forces_rescan(tmp_path):
    marker = tmp_path / "marker.json"
    check_transplant(marker)
    data = json.loads(marker.read_text(encoding="utf-8"))
    data["hostname"] = "ein-ganz-anderer-host"
    marker.write_text(json.dumps(data), encoding="utf-8")
    signal = check_transplant(marker)
    assert signal.should_rescan is True
    assert "Hostname" in signal.reason


def test_missing_known_path_forces_rescan(tmp_path):
    marker = tmp_path / "marker.json"
    check_transplant(marker)
    missing_path = tmp_path / "does-not-exist-anymore"
    signal = check_transplant(marker, known_paths=[missing_path])
    assert signal.should_rescan is True
    assert "Pfade" in signal.reason


def test_expired_interval_forces_rescan(tmp_path):
    marker = tmp_path / "marker.json"
    check_transplant(marker)
    data = json.loads(marker.read_text(encoding="utf-8"))
    old = datetime.now(timezone.utc) - timedelta(hours=48)
    data["checked_at"] = old.isoformat(timespec="seconds")
    marker.write_text(json.dumps(data), encoding="utf-8")
    signal = check_transplant(marker, min_interval_hours=24.0)
    assert signal.should_rescan is True
    assert "Intervall" in signal.reason


def test_corrupted_marker_forces_rescan_not_crash(tmp_path):
    marker = tmp_path / "marker.json"
    marker.write_text("{not valid", encoding="utf-8")
    signal = check_transplant(marker)
    assert signal.should_rescan is True
