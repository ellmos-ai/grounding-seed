"""Selbstkenntnis / Sensorik, Teil 1: laufe ich isoliert oder im Oekosystem?

Ein isoliertes Modul darf NICHTS ueber die Umgebung annehmen -- insbesondere keine
absoluten Oekosystem-Pfade (`<HOME>/OneDrive/.TOPICS/...`). Der einzige
annahmefreie Check ist deshalb: laesst sich `source_resolver` importieren? Alles
Weitere ist Zusatzinformation, keine Vorbedingung.

"Nicht gefunden" ist hier ein normaler, erwarteter Zustand -- kein Fehler
(Ticket-Wortlaut, Punkt 1).
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class EcosystemStatus:
    connected: bool
    source_resolver_module: Any | None  # das importierte Modul, oder None
    source_resolver_version: str | None
    hint_findings: dict[str, bool]  # optionale Zusatzsignale, NICHT entscheidend


def detect_ecosystem(*, hint_root: Path | None = None) -> EcosystemStatus:
    """Der einzige entscheidende Check: ist `source_resolver` importierbar?

    `hint_root` ist optional und rein informativ -- ein vom Aufrufer geratener
    Pfad, an dem `.MODULES/composition.rules.json` liegen KOENNTE. Ein Treffer
    oder Fehltreffer dort aendert `connected` NICHT; er landet nur in
    `hint_findings` fuer Diagnose/Logging. Grund: das Erraten von Pfaden ist
    genau die Annahme, die ein isoliertes Modul nicht machen darf.
    """
    try:
        module = importlib.import_module("source_resolver")
        version = getattr(module, "__version__", None)
        connected = True
    except ImportError:
        module = None
        version = None
        connected = False

    hint_findings: dict[str, bool] = {}
    if hint_root is not None:
        hint_findings["composition_rules_json"] = (
            hint_root / ".MODULES" / "composition.rules.json"
        ).exists()
        hint_findings["control_center"] = (hint_root / "_control-center").exists()

    return EcosystemStatus(
        connected=connected,
        source_resolver_module=module,
        source_resolver_version=version,
        hint_findings=hint_findings,
    )
