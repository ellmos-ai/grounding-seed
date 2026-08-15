# Changelog

## [0.1.0] - 2026-08-15

Erstversion. Gebaut fuer Ticket T-20260815-371628859 ("Standalone-Bootstrap-Template"),
inklusive aller drei Nutzer-Nachtraege (GROUNDING-Lebenszyklus, NAME/REIHENFOLGE/
GLIEDERUNG). Reihenfolge verbindlich VOR T-20260815-205101335 (work-autonomous-Umbau,
das Ticket wird darauf folgen, nicht parallel).

- Zehn Phasen der Pflanzenmetapher als Gliederung: Selbstkenntnis, Sensorik,
  Erde/Boden, Wasser, Naehrstoffe, Licht, Andockstellen, Gedaechtnis, Rueckgabe,
  Verpflanzung -- jede mit technischer Entsprechung, "Licht" praezisiert statt
  schwammig gelassen (advisor-Review + Team-lead-Vorgabe 2026-08-15).
- `self_knowledge.py`: Need-Deklaration + found/empty/unavailable-Assessment --
  die geteilte Grundlage fuer T-20260815-205101335.
- `location.py`: einziger annahmefreier Selbstverortungs-Check (`source_resolver`
  importierbar?), keine geratenen Oekosystem-Pfade.
- `store.py`: lokaler Speicher, vorwaertskompatibel gegen `source_resolver`s
  eigenes Rollen-Schema (`ellmos.source-resolver.user-config.v1`, SCHEMA_ID
  identisch, per Test verifiziert). Kein globaler Default-Pfad.
- `scan.py`: Wissens- + Ressourcen-Scan (bewusst auf "Programm auf PATH"
  begrenzt).
- `transplant.py`: billiges Verpflanzungs-Signal (Hostname/Pfade/Intervall),
  KEIN Vollscan als Trigger.
- `migration.py`: archiviert-nicht-geloescht, Zaehlung+Pruefsumme statt
  "kein Fehler", Rollback-durch-Nicht-Aktivierung, connections-config mit
  Ziel+Zeitstempel. Getestet gegen temporaere Verzeichnisse (kein Live-Zielspeicher).
- `ladder.py`: KEIN zweiter Resolver -- delegiert an `source_resolver`, wenn
  importierbar; sonst Minimalfassung derselben Stufenordnung, form-identisch
  getestet (`test_ladder_parity.py`, inkl. Stufe/Status-Vokabular,
  dialog-Struktur, confirm()-Signatur).
- 45/45 Tests gruen.
- Bewusst nicht gebaut: Ressourcen-Erreichbarkeitschecks jenseits PATH, echte
  Migrations-Zieladapter, Fremdanbieter-Beispiel, Wrapper-Selbstheilung (liegt
  bei source-resolver), work-autonomous-Umbau selbst (Folgeticket).
