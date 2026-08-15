"""Selbstkenntnis: was bin ich, was muss ich koennen, was brauche ich dafuer?

Steht laut Nutzer-Nachtrag AM ANFANG, vor jeder Suche: "ERST erkennen, was ich
koennen muss (Selbstkenntnis) -- DANN suchen, was da ist -- DANN fragen."

Diese Datei liefert die Grundlage fuer die found/empty/unavailable-Unterscheidung,
die T-20260815-205101335 an `work-autonomous` fehlt: ein Skill deklariert seinen
Bedarf (`Need`-Liste), `assess()` prueft jeden Bedarf tatsaechlich und meldet einen
von drei Zustaenden -- nie stillschweigend "ergebnislos" fuer zwei verschiedene
Dinge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


class NeedStatus:
    FOUND = "found"
    EMPTY = "empty"  # befragt, nichts da -- der Boden ist tatsaechlich trocken
    UNAVAILABLE = "unavailable"  # Quelle nicht erreichbar/nicht vorhanden -- keine Wurzel dorthin


@dataclass
class Need:
    """Ein deklarierter Bedarf: 'ich brauche Rolle X fuer mein Urteil'."""

    rolle: str
    kritisch: bool = True  # beeinflusst, wie der Aufrufer mit unavailable umgeht
    beschreibung: str = ""


@dataclass
class NeedAssessment:
    rolle: str
    status: str  # NeedStatus.*
    quelle: dict | None
    nachricht: str


@dataclass
class GroundingReport:
    """Ergebnis von `assess()` ueber die volle Need-Liste."""

    assessments: list[NeedAssessment] = field(default_factory=list)

    def by_status(self, status: str) -> list[NeedAssessment]:
        return [a for a in self.assessments if a.status == status]

    def all_answerable(self) -> bool:
        """True, wenn JEDE deklarierte Rolle tatsaechlich befragt werden konnte
        (found ODER empty) -- keine einzige unavailable. Nur dann darf ein
        Aufrufer wie work-autonomous ein 'ich habe alles geprueft'-Urteil fällen."""
        return len(self.by_status(NeedStatus.UNAVAILABLE)) == 0

    def unavailable_roles(self) -> list[str]:
        return [a.rolle for a in self.by_status(NeedStatus.UNAVAILABLE)]


def assess(
    needs: list[Need],
    *,
    resolver: Callable[[str], object],
) -> GroundingReport:
    """Prueft jeden deklarierten Bedarf ueber den uebergebenen `resolver`
    (typischerweise `grounding_seed.resolve` oder direkt `source_resolver.resolve`,
    als Callable(rolle) -> ResolutionResult-aehnliches Objekt mit `.status`).

    Mapping von ResolutionStatus auf NeedStatus:
      resolved/proposed                          -> FOUND (etwas wurde gefunden,
                                                     ob bestaetigt oder Vorschlag)
      not_found (Stufe 4, echt befragt & leer)    -> EMPTY
      module_present_not_callable/adapter_error/
      no_foreign_providers                        -> UNAVAILABLE (Quelle da, aber
                                                     nicht auskunftsfaehig -- oder
                                                     Aufrufer-Fehler, in jedem Fall
                                                     KEIN geprueftes Leer-Ergebnis)
    """
    found_like = {"resolved", "proposed"}
    empty_like = {"not_found"}
    assessments: list[NeedAssessment] = []
    for need in needs:
        try:
            result = resolver(need.rolle)
        except Exception as error:  # pragma: no cover -- defensiv, Resolver darf nicht crashen
            assessments.append(NeedAssessment(
                rolle=need.rolle, status=NeedStatus.UNAVAILABLE, quelle=None,
                nachricht=f"Resolver-Aufruf fuer '{need.rolle}' fehlgeschlagen: {error}",
            ))
            continue
        status = getattr(result, "status", None)
        if status in found_like:
            assessments.append(NeedAssessment(
                rolle=need.rolle, status=NeedStatus.FOUND,
                quelle=getattr(result, "quelle", None),
                nachricht=getattr(result, "nachricht", ""),
            ))
        elif status in empty_like:
            assessments.append(NeedAssessment(
                rolle=need.rolle, status=NeedStatus.EMPTY, quelle=None,
                nachricht=getattr(result, "nachricht", ""),
            ))
        else:
            assessments.append(NeedAssessment(
                rolle=need.rolle, status=NeedStatus.UNAVAILABLE, quelle=None,
                nachricht=getattr(result, "nachricht", f"Status '{status}' zaehlt als unavailable."),
            ))
    return GroundingReport(assessments=assessments)
