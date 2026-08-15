"""Verpflanzung: Umgebungswechsel loest eine NEUE Suche aus -- aber billig erkannt.

Technisch anspruchsvoller Punkt aus dem Nachtrag: "immer wieder neu suchen"
braucht eine Frequenzbegrenzung, sonst scannt jeder Lauf die halbe Platte. Ein
voller Scan als Trigger waere absurd -- es braucht ein guenstiges Signal zuerst.

Diese Datei liefert genau das billige Signal, keinen Scan. Erst wenn es anschlaegt,
ruft der Aufrufer scan()/resolve() erneut auf (idempotent/frequenzbegrenzt/
guard-geschuetzt, wie in ~/CLAUDE.md fuer Bulk-/Hintergrundaktionen verlangt).
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class TransplantSignal:
    should_rescan: bool
    reason: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def check_transplant(
    marker_path: Path, *, min_interval_hours: float = 24.0, known_paths: list[Path] | None = None,
) -> TransplantSignal:
    """Guenstiger Check, ob eine neue Suche noetig ist. Liest/schreibt einen kleinen
    Marker (`hostname`, `checked_at`, `known_paths_ok`). KEIN Scan -- nur Vergleich."""
    hostname = socket.gethostname()
    now = _now()

    if not marker_path.exists():
        _write_marker(marker_path, hostname=hostname, checked_at=now)
        return TransplantSignal(True, "Kein vorheriger Marker -- Erstlauf, Suche noetig.")

    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        _write_marker(marker_path, hostname=hostname, checked_at=now)
        return TransplantSignal(True, "Marker beschaedigt -- sicherheitshalber neu suchen.")

    if marker.get("hostname") != hostname:
        _write_marker(marker_path, hostname=hostname, checked_at=now)
        return TransplantSignal(True, f"Hostname geaendert ({marker.get('hostname')} -> {hostname}).")

    if known_paths is not None:
        missing = [str(p) for p in known_paths if not p.exists()]
        if missing:
            _write_marker(marker_path, hostname=hostname, checked_at=now)
            return TransplantSignal(True, f"Bekannte Pfade nicht mehr gueltig: {missing}.")

    checked_at_raw = marker.get("checked_at")
    if checked_at_raw:
        try:
            checked_at = datetime.fromisoformat(checked_at_raw)
        except ValueError:
            checked_at = None
        if checked_at is not None:
            elapsed_hours = (now - checked_at).total_seconds() / 3600
            if elapsed_hours < min_interval_hours:
                return TransplantSignal(
                    False, f"Letzter Check vor {elapsed_hours:.1f}h -- unter dem Intervall "
                           f"({min_interval_hours}h), keine erneute Suche."
                )

    _write_marker(marker_path, hostname=hostname, checked_at=now)
    return TransplantSignal(True, "Intervall abgelaufen -- Suche faellig.")


def _write_marker(marker_path: Path, *, hostname: str, checked_at: datetime) -> None:
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(
        json.dumps({"hostname": hostname, "checked_at": checked_at.isoformat(timespec="seconds")}),
        encoding="utf-8",
    )
