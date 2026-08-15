"""Ruecgabe/Verpflanzung, der heikle Teil: bei spaeterem Fund migrieren.

Vier Mindestanforderungen aus dem Ticket, wortwoertlich uebernommen:
  1. ARCHIVIEREN heisst archivieren, nicht loeschen -- lesbar bis verifiziert.
  2. Migration gilt erst als abgeschlossen, wenn die Daten am Ziel NACHWEISLICH
     vollstaendig sind (Zaehlung/Pruefsumme), nicht "kein Fehler aufgetreten".
  3. Fehlschlag = zurueck zum lokalen Bestand, nicht halb hier, halb dort.
  4. connections-config haelt fest, WOHIN verbunden wurde und SEIT WANN.

BEWUSSTER SCHNITT (siehe README): kein Adapter fuer einen echten Zielspeicher
(USMC/Gardener/etc.) wird hier mitgeliefert -- nur die Schnittstelle
(`TargetWriter`-Protokoll) plus diese Mechanik, getestet gegen temporaere
Verzeichnisse. Ein Anschluss an einen LEBENDEN Zielspeicher ist ausdruecklich
NICHT Teil dieses Baus.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


class TargetWriter(Protocol):
    """Schnittstelle fuer einen Migrationsziel-Speicher. Kein konkreter Adapter
    hier -- Aufrufer implementieren das gegen ihren echten Zielspeicher."""

    def write_entries(self, entries: list[dict[str, Any]]) -> None: ...
    def read_entries(self) -> list[dict[str, Any]]: ...
    def describe(self) -> str: ...  # menschenlesbare Zielbeschreibung fuer connections-config


def _checksum(entries: list[dict[str, Any]]) -> str:
    canonical = json.dumps(entries, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class MigrationResult:
    status: str  # "completed" | "verification_failed" | "no_data"
    archived_to: str | None
    target_description: str | None
    verified_count: int | None
    verified_checksum: str | None
    message: str


def migrate(
    local_root: Path, entries: list[dict[str, Any]], target: TargetWriter,
    *, connections_config_path: Path | None = None,
) -> MigrationResult:
    """Schreibt `entries` zum Ziel, VERIFIZIERT dort Zaehlung+Pruefsumme, und
    archiviert erst DANACH den lokalen Bestand. Bei jedem Fehlschlag bleibt der
    lokale Bestand unveraendert aktiv -- das IST das Rollback (nie geloescht, nie
    umgezogen, bevor die Verifikation steht)."""
    if not entries:
        return MigrationResult("no_data", None, None, None, None, "Keine Eintraege zu migrieren.")

    local_checksum = _checksum(entries)
    target.write_entries(entries)

    remote_entries = target.read_entries()
    remote_checksum = _checksum(remote_entries)

    if len(remote_entries) != len(entries) or remote_checksum != local_checksum:
        return MigrationResult(
            "verification_failed", None, target.describe(), len(remote_entries), remote_checksum,
            f"Verifikation fehlgeschlagen: lokal {len(entries)} Eintraege "
            f"(Pruefsumme {local_checksum[:12]}...), Ziel {len(remote_entries)} "
            f"(Pruefsumme {remote_checksum[:12]}...). Lokaler Bestand bleibt aktiv, NICHT archiviert.",
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_dir = local_root / ".archive" / timestamp
    archive_dir.mkdir(parents=True, exist_ok=True)
    for item in list(local_root.iterdir()):
        if item.name == ".archive":
            continue
        shutil.move(str(item), str(archive_dir / item.name))

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn_path = connections_config_path or (local_root / "connections-config.json")
    conn_path.parent.mkdir(parents=True, exist_ok=True)
    conn_path.write_text(json.dumps({
        "target": target.describe(), "migrated_at": now_iso,
        "archived_to": str(archive_dir), "verified_count": len(remote_entries),
        "verified_checksum": remote_checksum,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    return MigrationResult(
        "completed", str(archive_dir), target.describe(), len(remote_entries), remote_checksum,
        f"{len(remote_entries)} Eintraege verifiziert migriert nach {target.describe()}; "
        f"lokaler Bestand archiviert nach {archive_dir}.",
    )
