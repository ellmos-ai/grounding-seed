"""Wasser: laufende Versorgung -- der eigene, lokale Speicher.

Vorwaertskompatibel gebaut gegen EIN festgelegtes Zielschema (Ticket-Vorgabe:
"kompatibel bauen geht nur gegen ein bekanntes Zielschema" -- von den vier
genannten Kandidaten wird hier `ellmos.source-resolver.user-config.v1` gewaehlt,
das Rollen-Schema des source-resolver selbst; USMC/Gardener/taskplan sind fuer
diesen Bau bewusst NICHT gewaehlt, siehe README "Was hier bewusst fehlt").

Unterschied zu `source_resolver.store.UserSourceStore`: KEIN Default-Pfad im
Home-Verzeichnis. Ein isoliertes Modul darf nichts ueber die Umgebung annehmen --
der Wurzelpfad ist deshalb ein Pflichtparameter, typischerweise
`<Modulordner>/.grounding-seed/`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_ID = "ellmos.source-resolver.user-config.v1"  # bewusst IDENTISCH zu source-resolver


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class RoleEntry:
    rolle: str
    aktiv: bool
    quelle: dict[str, Any]
    stufe: int  # hier immer 0 -- der lokale Speicher IST Stufe 0
    bestaetigt_am: str
    bestaetigt_von: str
    herkunft: str = "manuell"

    def to_dict(self) -> dict[str, Any]:
        return {
            "rolle": self.rolle, "aktiv": self.aktiv, "quelle": self.quelle,
            "stufe": self.stufe, "bestaetigt_am": self.bestaetigt_am,
            "bestaetigt_von": self.bestaetigt_von, "herkunft": self.herkunft,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "RoleEntry":
        return RoleEntry(
            rolle=data["rolle"], aktiv=bool(data.get("aktiv", True)),
            quelle=data.get("quelle", {}), stufe=int(data.get("stufe", 0)),
            bestaetigt_am=data.get("bestaetigt_am", ""),
            bestaetigt_von=data.get("bestaetigt_von", "user"),
            herkunft=data.get("herkunft", "manuell"),
        )


class LocalStore:
    """Der eigene JSON-Speicher eines isolierten Moduls. `root` ist Pflicht --
    kein globaler Default, siehe Moduldoku oben."""

    def __init__(self, root: Path, *, filename: str = "config.json") -> None:
        self.root = root
        self.path = root / filename

    def _read_raw(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema": SCHEMA_ID, "version": 1, "rollen": {}}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(
                f"grounding-seed Lokalspeicher beschaedigt (kein gueltiges JSON): "
                f"{self.path} -- {error}"
            ) from error

    def _write_raw(self, data: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def get(self, rolle: str) -> RoleEntry | None:
        entry = self._read_raw().get("rollen", {}).get(rolle)
        return RoleEntry.from_dict(entry) if entry is not None else None

    def list_roles(self) -> dict[str, RoleEntry]:
        return {n: RoleEntry.from_dict(d) for n, d in self._read_raw().get("rollen", {}).items()}

    def set(self, entry: RoleEntry) -> None:
        raw = self._read_raw()
        raw.setdefault("rollen", {})[entry.rolle] = entry.to_dict()
        raw["schema"] = SCHEMA_ID
        raw["version"] = raw.get("version", 1)
        self._write_raw(raw)

    def all_entries_sorted(self) -> list[dict[str, Any]]:
        """Kanonisch sortierte Rohliste -- Grundlage fuer Zaehlung/Pruefsumme bei
        einer spaeteren Migration (siehe migration.py)."""
        return [self._read_raw().get("rollen", {}).get(k) for k in sorted(self._read_raw().get("rollen", {}))]
