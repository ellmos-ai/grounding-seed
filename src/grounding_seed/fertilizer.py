"""Fertilizer/Duenger: die dritte Naehrstoffquelle -- die Nutzungsspur.

Herkunft: T-20260815-316117714. Der Nutzer stellt Verbindungen im Alltag oft
schon selbst her, indem er sie im selben Auftrag NENNT ("nutze USMC und mach
das und das und die Policies dafuer"). Diese Spur ist kein Discovery-Fund
(niemand hat gesucht) und keine gegenseitige Erkennung (T-20260815-109780293) --
sie ist BELEG: Der Nutzer hat die Verbindung bereits gezogen.

Bewusst BEGRENZT auf das, was dieses Ticket tatsaechlich entschieden hat:
  - Quelle ist ausschliesslich das AKTIVE KONTEXTFENSTER des aufrufenden Skills
    (`organic-growth`, skills/infrastructure/organic-growth). Dieses Modul liest
    selbst NICHTS -- es nimmt Komponenten + Belegstelle entgegen, die das Modell
    bereits im Gespraech gesehen hat. Kein Transkript-Scan, kein Batch-Lauf.
  - Konservativer Default (Nutzerentscheid 2026-09-06): eine Nutzungsspur wird
    NUR als KANDIDAT abgelegt (Stufe 2 / PROPOSED der bestehenden Stufenordnung
    aus ladder.py -- siehe dort), nie direkt als kanonische Stufe-0-Bindung.
    Automatische Bindung bei hoher Evidenz ist eine eigene, noch offene
    Nutzerfrage und wird hier NICHT vorweggenommen.
  - "Kein zweites Format erfinden" (Ticket-Vorgabe): die Felder `link_type`
    (synapse | endplate) und `state` (verbinden | koexistieren | abwehren)
    sind woertlich aus T-20260815-109780293 uebernommen, nicht neu erfunden.
    Trotzdem ein EIGENES File (`connections-candidates.json`, nicht
    `connections-config.json`): Letzteres hat in migration.py bereits eine
    feste, getestete Bedeutung (EIN abgeschlossenes Migrations-Ereignis) --
    das waere kein zweites Format, sondern eine Kollision mit einem
    bestehenden.

Kein automatischer Aufstieg zu einer RoleEntry (store.py): eine Komponenten-
Kookkurrenz ("X und Y zusammen genannt") ist keine Rollenaufloesung ("wer
erfuellt Rolle X"). Beides zu vermengen waere ein neues Missverstaendnis, kein
Feature.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from grounding_seed.ladder import ResolutionStatus, Stufe

DEFAULT_FILENAME = "connections-candidates.json"

# Woertlich aus T-20260815-109780293 (Nachtrag "Motorische Endplatte statt
# 'halbe Synapse'" und "Drei Zustaende statt zwei") -- keine eigene Taxonomie.
VALID_LINK_TYPES = ("synapse", "endplate")
VALID_STATES = ("verbinden", "koexistieren", "abwehren")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalized_key(components: list[str]) -> tuple[str, ...]:
    return tuple(sorted({c.strip().lower() for c in components if c.strip()}))


@dataclass
class ConnectionCandidate:
    components: list[str]
    evidence: str
    link_type: str = "synapse"
    state: str = "verbinden"
    stufe: int = int(Stufe.DISCOVERY_VORSCHLAG)
    status: str = ResolutionStatus.PROPOSED
    herkunft: str = "organic-growth"
    first_seen: str = ""
    last_seen: str = ""
    times_observed: int = 1
    confirmed: bool = False
    confirmed_at: str | None = None
    confirmed_von: str | None = None
    dismissed: bool = False
    dismissed_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "components": self.components, "evidence": self.evidence,
            "link_type": self.link_type, "state": self.state,
            "stufe": self.stufe, "status": self.status, "herkunft": self.herkunft,
            "first_seen": self.first_seen, "last_seen": self.last_seen,
            "times_observed": self.times_observed,
            "confirmed": self.confirmed, "confirmed_at": self.confirmed_at,
            "confirmed_von": self.confirmed_von,
            "dismissed": self.dismissed, "dismissed_reason": self.dismissed_reason,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ConnectionCandidate:
        return ConnectionCandidate(
            components=list(data.get("components", [])), evidence=data.get("evidence", ""),
            link_type=data.get("link_type", "synapse"), state=data.get("state", "verbinden"),
            stufe=int(data.get("stufe", int(Stufe.DISCOVERY_VORSCHLAG))),
            status=data.get("status", ResolutionStatus.PROPOSED),
            herkunft=data.get("herkunft", "organic-growth"),
            first_seen=data.get("first_seen", ""), last_seen=data.get("last_seen", ""),
            times_observed=int(data.get("times_observed", 1)),
            confirmed=bool(data.get("confirmed", False)), confirmed_at=data.get("confirmed_at"),
            confirmed_von=data.get("confirmed_von"),
            dismissed=bool(data.get("dismissed", False)), dismissed_reason=data.get("dismissed_reason"),
        )


def _path(root: Path, filename: str) -> Path:
    return root / filename


def _read_all(root: Path, filename: str) -> list[ConnectionCandidate]:
    path = _path(root, filename)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(
            f"grounding-seed Fertilizer-Ablage beschaedigt (kein gueltiges JSON): {path} -- {error}"
        ) from error
    return [ConnectionCandidate.from_dict(item) for item in raw.get("candidates", [])]


def _write_all(root: Path, filename: str, candidates: list[ConnectionCandidate]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    path = _path(root, filename)
    data = {"schema": "ellmos.grounding-seed.connections-candidates.v1",
            "candidates": [c.to_dict() for c in candidates]}
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def record_candidate(
    root: Path, components: list[str], evidence: str,
    *, link_type: str = "synapse", state: str = "verbinden", filename: str = DEFAULT_FILENAME,
) -> ConnectionCandidate:
    """Haelt eine im aktiven Kontextfenster beobachtete Nutzungsspur fest.

    Schwelle (Ticket-Vorgabe, klein angefangen): mindestens ZWEI benannte
    Komponenten in einem Auftrag. Eine Kookkurrenz aus zwei Komponenten, die
    schon einmal (unbestaetigt/nicht verworfen) beobachtet wurde, wird
    aktualisiert (times_observed++, last_seen, evidence nachgefuehrt) statt
    dupliziert -- "einmal giessen macht keine Wurzel" gilt hier nicht als
    Sperre (im Kontextfenster gibt es keine Session-uebergreifende Statistik,
    siehe Modul-Docstring), aber Wiederholungen sollen trotzdem nicht als
    separate Eintraege wuchern.
    """
    if len(components) < 2:
        raise ValueError("Eine Verbindung braucht mindestens zwei benannte Komponenten.")
    if link_type not in VALID_LINK_TYPES:
        raise ValueError(f"link_type muss einer von {VALID_LINK_TYPES} sein, nicht {link_type!r}.")
    if state not in VALID_STATES:
        raise ValueError(f"state muss einer von {VALID_STATES} sein, nicht {state!r}.")

    candidates = _read_all(root, filename)
    key = _normalized_key(components)
    now = now_iso()

    for existing in candidates:
        if _normalized_key(existing.components) == key and not existing.confirmed and not existing.dismissed:
            existing.times_observed += 1
            existing.last_seen = now
            existing.evidence = evidence
            _write_all(root, filename, candidates)
            return existing

    new_candidate = ConnectionCandidate(
        components=list(components), evidence=evidence, link_type=link_type, state=state,
        first_seen=now, last_seen=now,
    )
    candidates.append(new_candidate)
    _write_all(root, filename, candidates)
    return new_candidate


def list_candidates(
    root: Path, *, include_confirmed: bool = True, include_dismissed: bool = False,
    filename: str = DEFAULT_FILENAME,
) -> list[ConnectionCandidate]:
    candidates = _read_all(root, filename)
    return [
        c for c in candidates
        if (include_confirmed or not c.confirmed) and (include_dismissed or not c.dismissed)
    ]


def confirm_candidate(
    root: Path, components: list[str], *, bestaetigt_von: str = "user", filename: str = DEFAULT_FILENAME,
) -> ConnectionCandidate:
    """Menschliche/agentische Bestaetigung einer Nutzungsspur (Stufe 2 ->
    'geprueft und fuer richtig befunden'). Hebt NICHT automatisch auf eine
    kanonische Stufe-0-Bindung -- das waere die staerkere, noch offene
    Nutzerfrage aus dem Ticket ('automatische Bindung bei hoher Evidenz').
    Wer eine bestaetigte Verbindung tatsaechlich als Rolle binden will, tut das
    bewusst ueber store.py/ladder.confirm() -- ein eigener, expliziter Schritt.
    """
    candidates = _read_all(root, filename)
    key = _normalized_key(components)
    for existing in candidates:
        if _normalized_key(existing.components) == key and not existing.dismissed:
            existing.confirmed = True
            existing.confirmed_at = now_iso()
            existing.confirmed_von = bestaetigt_von
            _write_all(root, filename, candidates)
            return existing
    raise ValueError(f"Kein offener Kandidat fuer Komponenten {components!r} gefunden.")


def dismiss_candidate(
    root: Path, components: list[str], *, reason: str | None = None, filename: str = DEFAULT_FILENAME,
) -> ConnectionCandidate:
    """Verwirft eine Nutzungsspur bewusst als 'koexistieren' (friedlicher
    Organismus, T-20260815-109780293 Nachtrag) -- PERSISTIERT, damit dieselbe
    Kookkurrenz nicht bei jedem Lauf erneut vorgeschlagen wird. Kein 'abwehren'
    (Quarantaene): das ist eine Risikoeinschaetzung, die dieses schmale Modul
    nicht trifft -- wer eine Bedrohung erkennt, setzt `state` beim naechsten
    `record_candidate()`-Aufruf explizit auf 'abwehren'.
    """
    candidates = _read_all(root, filename)
    key = _normalized_key(components)
    for existing in candidates:
        if _normalized_key(existing.components) == key:
            existing.dismissed = True
            existing.dismissed_reason = reason
            existing.state = "koexistieren"
            _write_all(root, filename, candidates)
            return existing
    raise ValueError(f"Kein Kandidat fuer Komponenten {components!r} gefunden.")
