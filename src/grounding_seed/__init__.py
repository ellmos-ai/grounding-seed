"""grounding-seed -- Standalone-Bootstrap-Muster fuer isolierte Module/Skills/Repos.

Ein Samen bringt mit, was er zum Keimen in unbekanntem Boden braucht. Genau das
macht dieses Template: es wird in ein Repo kopiert und macht es dort -- auch ohne
unser Oekosystem -- lauffaehig: Selbstkenntnis, Suche, eigener Speicher, Nutzerfrage,
Selbstversorgung, spaetere Migration bei Fund. Siehe README.md fuer die volle
Spezifikation (die Pflanzenmetapher ist dort die Gliederung, nicht die Illustration).

KEIN zweiter Resolver: wo `source_resolver` importierbar ist, wird vollstaendig
dorthin delegiert. Nur wenn das fehlschlaegt, laeuft die hier mitgebrachte
Minimalfassung derselben Stufenordnung -- geprueft auf Ergebnis-Gleichheit in
tests/test_ladder_parity.py.
"""

from grounding_seed.fertilizer import (
    ConnectionCandidate,
    confirm_candidate,
    dismiss_candidate,
    list_candidates,
    record_candidate,
)
from grounding_seed.ladder import ResolutionResult, ResolutionStatus, Stufe, resolve
from grounding_seed.location import detect_ecosystem
from grounding_seed.self_knowledge import (
    GroundingReport,
    Need,
    NeedAssessment,
    NeedStatus,
    assess,
    status_from_resolution,
)
from grounding_seed.store import LocalStore

__version__ = "0.3.2"
TEMPLATE_NAME = "grounding-seed"

# Welche source-resolver CONTRACT_VERSION diese Minimalfassung nachbildet (siehe
# ladder.py). Muss bei jeder Formaenderung an source_resolver.CONTRACT_VERSION
# nachgezogen werden -- das ist der Preis der bewusst sanktionierten Kopie.
SOURCE_RESOLVER_CONTRACT_VERSION = "1"


def template_stamp() -> str:
    """Versionsstempel fuer mitkopierte Fassungen (Ticket-Punkt 6: Standardisiert und
    versioniert). In die eigene Config/den Skill-Header eintragen, z.B.:
    `grounding_seed_template: grounding-seed@0.1.0`."""
    return f"{TEMPLATE_NAME}@{__version__}"


__all__ = [
    "SOURCE_RESOLVER_CONTRACT_VERSION",
    "TEMPLATE_NAME",
    "ConnectionCandidate",
    "GroundingReport",
    "LocalStore",
    "Need",
    "NeedAssessment",
    "NeedStatus",
    "ResolutionResult",
    "ResolutionStatus",
    "Stufe",
    "__version__",
    "assess",
    "confirm_candidate",
    "detect_ecosystem",
    "dismiss_candidate",
    "list_candidates",
    "record_candidate",
    "resolve",
    "status_from_resolution",
    "template_stamp",
]
