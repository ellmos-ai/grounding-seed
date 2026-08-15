"""Naehrstoffe + Andockstellen: was ist in dieser Umgebung ueberhaupt da?

Zwei Sorten (Ticket-Vorgabe, Punkt 2):
  Wissen/Praeferenzen   -- Konfigurations-/Regeldateien, Entscheidungsablagen.
  Ressourcen/Faehigkeiten -- installierte Programme, erreichbare Dienste.

Bewusst BEGRENZT (siehe README "Was hier bewusst fehlt"): Ressourcen-Scan deckt
aktuell nur "Programm auf PATH gefunden" ab (shutil.which), nicht
Datenbank-/Dienst-Erreichbarkeit -- das waere ein offener, dienstspezifischer
Aufwand und wuerde diesen Bau sprengen.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

# Bekannte Konfigurations-/Regeldateinamen, nach denen im Wissens-Scan gesucht wird.
# Bewusst eine kleine, benannte Liste statt eines Alles-durchsuchen-Freitextmusters.
KNOWN_KNOWLEDGE_FILENAMES = [
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursor/rules",
    "DECISIONS.md", "TODO.md", "AUFGABEN.txt",
]


@dataclass
class ScanResult:
    knowledge_found: list[Path] = field(default_factory=list)
    resources_found: dict[str, str] = field(default_factory=dict)  # name -> Pfad des Programms
    resources_missing: list[str] = field(default_factory=list)


def scan_knowledge(root: Path, *, filenames: list[str] | None = None) -> list[Path]:
    """Sucht bekannte Konfig-/Regeldateien direkt unterhalb von `root` (nicht
    rekursiv -- ein isoliertes Modul durchsucht nicht die ganze Platte)."""
    names = filenames or KNOWN_KNOWLEDGE_FILENAMES
    found = []
    for name in names:
        candidate = root / name
        if candidate.exists():
            found.append(candidate)
    return found


def scan_resources(program_names: list[str]) -> tuple[dict[str, str], list[str]]:
    """Prueft, welche der genannten Programme auf PATH auffindbar sind."""
    found: dict[str, str] = {}
    missing: list[str] = []
    for name in program_names:
        path = shutil.which(name)
        if path:
            found[name] = path
        else:
            missing.append(name)
    return found, missing


def scan(root: Path, *, knowledge_filenames: list[str] | None = None,
          resource_programs: list[str] | None = None) -> ScanResult:
    knowledge = scan_knowledge(root, filenames=knowledge_filenames)
    resources_found, resources_missing = scan_resources(resource_programs or [])
    return ScanResult(
        knowledge_found=knowledge, resources_found=resources_found, resources_missing=resources_missing,
    )
