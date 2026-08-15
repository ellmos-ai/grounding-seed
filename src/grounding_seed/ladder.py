"""Andockstellen: dieselbe Stufenordnung wie source-resolver, in zwei Betriebsarten.

KEIN zweiter Resolver (Ticket-Vorgabe). Reihenfolge:

  1. Ist `source_resolver` importierbar? -> VOLLSTAENDIG dorthin delegieren. Das
     ist der Normalfall im Oekosystem und nutzt dessen echte KNOWN_MODULE_PROVIDERS
     samt Adaptern (z.B. policy.registry -> policy-registry CLI).
  2. Sonst: die hier mitgebrachte Minimalfassung laeuft. Sie produziert
     ABSICHTLICH dieselbe Ergebnisform (gleiche Feldnamen, gleiches
     Stufe/ResolutionStatus-Vokabular) wie `source_resolver.ladder` -- geprueft in
     tests/test_ladder_parity.py, damit ein Skill sich in beiden Betriebsarten
     gleich verhaelt und nur die Bezugsquelle wechselt.

Unterschied zur echten source-resolver-Leiter: KEIN modul-weites
KNOWN_MODULE_PROVIDERS-Register (ein isoliertes Modul kennt unsere Oekosystem-Pfade
nicht). Stattdessen nimmt `resolve()` `known_providers` als Parameter entgegen --
der Aufrufer (das Skill, das grounding-seed einbettet) liefert, was ES kennt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any

from grounding_seed.store import LocalStore, RoleEntry, now_iso

# Identisch zu source_resolver.ladder.Stufe / .ResolutionStatus -- bewusst dupliziert
# (Formgleichheit ist der Vertrag, siehe Moduldoku oben), nicht importiert, damit
# diese Datei auch OHNE source_resolver installiert lauffaehig bleibt.


class Stufe(IntEnum):
    NUTZER_KONFIGURATION = 0
    EIGENES_MODUL = 1
    DISCOVERY_VORSCHLAG = 2
    FREMDANBIETER = 3
    NICHT_GEFUNDEN = 4


class ResolutionStatus:
    RESOLVED = "resolved"
    PROPOSED = "proposed"
    MODULE_PRESENT_NOT_CALLABLE = "module_present_not_callable"
    NO_FOREIGN_PROVIDERS = "no_foreign_providers"
    NOT_FOUND = "not_found"
    ADAPTER_ERROR = "adapter_error"


@dataclass
class ResolutionResult:
    rolle: str
    stufe: Stufe
    status: str
    quelle: dict[str, Any] | None
    herkunft: str
    nachricht: str
    kandidaten: list[dict[str, Any]] = field(default_factory=list)
    dialog: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rolle": self.rolle, "stufe": int(self.stufe), "stufe_name": self.stufe.name,
            "status": self.status, "quelle": self.quelle, "herkunft": self.herkunft,
            "nachricht": self.nachricht, "kandidaten": self.kandidaten, "dialog": self.dialog,
        }


def _try_source_resolver(rolle: str, *, scope: str | None, query: str):
    try:
        import source_resolver
    except ImportError:
        return None
    result = source_resolver.resolve(rolle, scope=scope, query=query)
    # source_resolver.ladder.ResolutionResult hat dieselben Felder -- direkt weiterreichen.
    return ResolutionResult(
        rolle=result.rolle, stufe=Stufe(int(result.stufe)), status=result.status,
        quelle=result.quelle, herkunft=result.herkunft, nachricht=result.nachricht,
        kandidaten=result.kandidaten, dialog=result.dialog,
    )


def _try_known_providers(rolle: str, known_providers: dict[str, list[dict[str, Any]]]) -> ResolutionResult | None:
    for candidate in known_providers.get(rolle, []):
        target = candidate.get("target") or candidate.get("module_path")
        if target is None:
            continue
        path = Path(str(target))
        if not path.exists():
            continue
        return ResolutionResult(
            rolle=rolle, stufe=Stufe.EIGENES_MODUL, status=ResolutionStatus.RESOLVED,
            quelle={"id": candidate.get("id", "unbekannt"), "target": str(path)},
            herkunft="eigenes-modul", nachricht=f"Rolle '{rolle}' via bekannten Provider aufgeloest.",
        )
    return None


def discover(rolle: str, roots: list[Path], *, max_depth: int = 2) -> list[dict[str, Any]]:
    """Identisch zur Discovery-Logik in source_resolver.ladder -- siehe dort fuer
    die Begruendung (begrenzt, nicht rekursiv unbegrenzt, keine OneDrive-weite Suche)."""
    terms = [p.lower() for p in rolle.split(".") if p]
    found: list[dict[str, Any]] = []
    for root in roots:
        if not root.exists():
            continue
        stack = [(root, 0)]
        while stack:
            current, depth = stack.pop()
            try:
                entries = list(current.iterdir())
            except (PermissionError, OSError):
                continue
            for entry in entries:
                if any(term in entry.name.lower() for term in terms):
                    found.append({"pfad": str(entry), "gefundene_begriffe": terms})
                if entry.is_dir() and depth < max_depth:
                    stack.append((entry, depth + 1))
    return found


def resolve(
    rolle: str,
    *,
    store: LocalStore,
    scope: str | None = None,
    query: str = "",
    known_providers: dict[str, list[dict[str, Any]]] | None = None,
    discovery_roots: list[Path] | None = None,
) -> ResolutionResult:
    # Schritt 1: source_resolver bevorzugen, falls importierbar (kein zweiter Resolver).
    delegated = _try_source_resolver(rolle, scope=scope, query=query)
    if delegated is not None:
        return delegated

    # Schritt 2: Minimalfassung. Stufe 0 -- eigener lokaler Speicher.
    entry = store.get(rolle)
    if entry is not None and entry.aktiv:
        return ResolutionResult(
            rolle=rolle, stufe=Stufe.NUTZER_KONFIGURATION, status=ResolutionStatus.RESOLVED,
            quelle=entry.quelle, herkunft=entry.herkunft,
            nachricht=f"Rolle '{rolle}' durch lokale Konfiguration festgelegt "
                      f"(bestaetigt {entry.bestaetigt_am} von {entry.bestaetigt_von}).",
        )

    # Stufe 1 -- nur wenn der Aufrufer eigene bekannte Provider mitgibt.
    if known_providers:
        hit = _try_known_providers(rolle, known_providers)
        if hit is not None:
            return hit

    # Stufe 2 -- Discovery
    if discovery_roots:
        kandidaten = discover(rolle, discovery_roots)
        if kandidaten:
            return ResolutionResult(
                rolle=rolle, stufe=Stufe.DISCOVERY_VORSCHLAG, status=ResolutionStatus.PROPOSED,
                quelle=None, herkunft="discovery",
                nachricht=f"{len(kandidaten)} Kandidat(en) fuer Rolle '{rolle}' gefunden -- "
                          f"Vorschlag, per confirm() zu bestaetigen.",
                kandidaten=kandidaten,
            )

    # Stufe 3 -- Fremdanbieter. Bewusst leer, wie im Original.
    # (Kein FOREIGN_PROVIDERS-Register hier -- ein isoliertes Modul bringt keine
    # vorkonfigurierten Fremdquellen mit; das waere selbst wieder eine Annahme.)

    # Stufe 4 -- Dialog.
    known_ids = [c.get("id", "?") for c in (known_providers or {}).get(rolle, [])]
    return ResolutionResult(
        rolle=rolle, stufe=Stufe.NICHT_GEFUNDEN, status=ResolutionStatus.NOT_FOUND,
        quelle=None, herkunft="keine", nachricht=f"Rolle '{rolle}' konnte nicht aufgeloest werden.",
        dialog={
            "frage_1": (
                f"Fuer die Rolle '{rolle}' wurde nichts gefunden. Welcher Ort/welche Datei/"
                f"welches Werkzeug ist fuer dich hier massgeblich?"
            ),
            "frage_2_falls_unbekannt": (
                "Falls du das nicht benennen kannst: sollen wir dafuer etwas Eigenes anlegen? "
                + (f"Bekannte Kandidaten: {', '.join(known_ids)}." if known_ids else
                   "Fuer diese Rolle ist noch kein Kandidat bekannt.")
            ),
        },
    )


def confirm(
    rolle: str, quelle: dict[str, Any], *, store: LocalStore,
    stufe_herkunft: int, bestaetigt_von: str = "user",
) -> RoleEntry:
    # KEIN Default fuer stufe_herkunft -- Formgleichheit mit source_resolver.ladder.confirm(),
    # das dieselbe Disziplin erzwingt (Herkunft der Bestaetigung soll nie stillschweigend
    # geraten werden). Siehe tests/test_ladder_parity.py.
    herkunft = {0: "manuell", 1: "eigenes-modul-bestaetigt", 2: "discovery-bestaetigt",
                3: "fremdanbieter-bestaetigt"}.get(stufe_herkunft, "manuell")
    entry = RoleEntry(
        rolle=rolle, aktiv=True, quelle=quelle, stufe=0,
        bestaetigt_am=now_iso(), bestaetigt_von=bestaetigt_von, herkunft=herkunft,
    )
    store.set(entry)
    return entry
