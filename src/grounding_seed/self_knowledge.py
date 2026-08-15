"""Selbstkenntnis: was bin ich, was muss ich koennen, was brauche ich dafuer?

Steht laut Nutzer-Nachtrag AM ANFANG, vor jeder Suche: "ERST erkennen, was ich
koennen muss (Selbstkenntnis) -- DANN suchen, was da ist -- DANN fragen."

Diese Datei liefert die Grundlage fuer die found/empty/unavailable-Unterscheidung,
die T-20260815-205101335 an `work-autonomous` fehlt: ein Skill deklariert seinen
Bedarf (`Need`-Liste), `assess()` prueft jeden Bedarf tatsaechlich und meldet einen
von drei Zustaenden -- nie stillschweigend "ergebnislos" fuer zwei verschiedene
Dinge.

KORREKTUR (0.2.0, gefunden beim ersten echten Anwendungsfall work-autonomous,
T-20260815-205101335): `assess()` mappte urspruenglich `not_found` (Stufe 4 --
keine Rolle konnte irgendwo verortet werden) auf EMPTY. Das ist falsch.
`resolve()` beantwortet ausschliesslich WO etwas ist, nie WAS dort drinsteht.
"Keine Rolle verortet" heisst "ich weiss nicht einmal, wohin ich fragen soll"
-- das ist UNAVAILABLE, nicht "befragt und leer". EMPTY kann nur entstehen,
wenn ein Aufrufer eine Rolle erfolgreich verortet UND danach den Inhalt an
dieser Stelle tatsaechlich gelesen hat und dort nichts fand. Das ist Wissen,
das nur der Aufrufer hat -- `assess()` kann es nicht aus einem
`ResolutionResult` allein ableiten.

Deshalb remapped `assess()` nicht mehr selbst. Der uebergebene `resolver`
liefert den fertigen Drei-Werte-Status direkt (`NeedStatus.FOUND/EMPTY/
UNAVAILABLE`). Fuer den haeufigen Fall "ich will nur wissen, ob eine Rolle
ueberhaupt verortet werden konnte" (found/unavailable, nie empty, weil kein
Inhalt gelesen wurde) liefert `status_from_resolution()` die korrekte,
benannte Uebersetzung -- keine eingebaute, aber falsche Annahme mehr.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


class NeedStatus:
    FOUND = "found"
    EMPTY = "empty"  # befragt, nichts da -- der Boden ist tatsaechlich trocken
    UNAVAILABLE = "unavailable"  # Quelle nicht erreichbar/nicht vorhanden -- keine Wurzel dorthin


_VALID_STATUSES = {NeedStatus.FOUND, NeedStatus.EMPTY, NeedStatus.UNAVAILABLE}


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


def status_from_resolution(result: object) -> str:
    """Uebersetzt ein `ResolutionResult`-aehnliches Objekt (source_resolver /
    grounding_seed `resolve()`) in FOUND oder UNAVAILABLE -- NIE EMPTY, weil
    `resolve()` nur die Verortung prueft, nicht den Inhalt.

    resolved/proposed  -> FOUND (eine Stelle wurde verortet, bestaetigt oder
                           als Vorschlag -- der Aufrufer kann dort jetzt lesen)
    alles andere        -> UNAVAILABLE (not_found, adapter_error,
                           module_present_not_callable, no_foreign_providers,
                           unbekannter Status -- in jedem Fall: keine Stelle
                           bekannt oder nicht erreichbar)
    """
    status = getattr(result, "status", None)
    if status in ("resolved", "proposed"):
        return NeedStatus.FOUND
    return NeedStatus.UNAVAILABLE


def assess(
    needs: list[Need],
    *,
    resolver: Callable[[str], object],
) -> GroundingReport:
    """Prueft jeden deklarierten Bedarf ueber den uebergebenen `resolver`.

    Vertrag (seit 0.2.0): `resolver(rolle)` liefert ein Objekt, dessen
    `.status`-Attribut bereits einer der drei `NeedStatus`-Werte ist (found/
    empty/unavailable) -- ODER wirft eine Ausnahme, die als `unavailable`
    gewertet wird. `assess()` selbst entscheidet NICHT mehr, was "leer"
    bedeutet -- das kann nur der Aufrufer wissen, der ggf. tatsaechlich Inhalt
    gelesen hat. Ein Resolver, der eine ungueltige Statuszeichenkette liefert,
    ist ein Programmfehler beim Aufrufer und wird als solcher gemeldet
    (`ValueError`), nicht still auf `unavailable` gebogen.

    Fuer den haeufigen Fall "ich will source_resolver/grounding_seed nur nach
    einer Verortung fragen, ohne Inhalt zu lesen" liefert
    `status_from_resolution()` die passende found/unavailable-Uebersetzung.
    """
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
        if status not in _VALID_STATUSES:
            raise ValueError(
                f"resolver('{need.rolle}') lieferte Status '{status}' -- "
                f"muss einer von {sorted(_VALID_STATUSES)} sein. "
                "assess() rät nicht mehr; der Resolver muss den fertigen "
                "found/empty/unavailable-Wert liefern (ggf. via "
                "status_from_resolution() fuer reine Verortungs-Checks)."
            )
        assessments.append(NeedAssessment(
            rolle=need.rolle, status=status,
            quelle=getattr(result, "quelle", None),
            nachricht=getattr(result, "nachricht", ""),
        ))
    return GroundingReport(assessments=assessments)
