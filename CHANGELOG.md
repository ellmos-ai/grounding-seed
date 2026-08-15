# Changelog

## [0.2.0] - 2026-08-15

Befund aus dem ersten echten Anwendungsfall (T-20260815-205101335,
work-autonomous-Umbau) -- per advisor-Review korrigiert, hier als Fund UEBER
das Template gemeldet, nicht stillschweigend umgangen.

**Kontraktbruch (bewusst, nicht rueckwaertskompatibel):** `self_knowledge.assess()`
remappte bisher `not_found` auf `NeedStatus.EMPTY`. Das war ein Kategorienfehler:
`resolve()` beantwortet nur WO etwas ist, nie WAS dort drinsteht. "Keine Rolle
verortet" heisst "ich weiss nicht, wohin ich fragen soll" -- das ist `unavailable`,
kein geprueftes Leer. `EMPTY` kann nur ein Aufrufer setzen, der eine Rolle
erfolgreich verortet UND danach den Inhalt dort tatsaechlich gelesen hat.

- `assess()` remapped nicht mehr selbst. Der `resolver`-Callable muss den
  fertigen found/empty/unavailable-Status liefern; ein roher `ResolutionStatus`
  (z. B. `"not_found"`, `"resolved"`) loest jetzt `ValueError` aus statt stiller
  Fehlbucherei -- Vertragsbruch beim Aufrufer wird gemeldet, nicht geraten.
- Neu: `status_from_resolution(result) -> "found" | "unavailable"` -- die
  benannte, korrekte Uebersetzung fuer den Fall "ich will nur Verortung, keinen
  Inhalt". Liefert NIE `empty`, per Test abgesichert.
- 53/53 Tests gruen (16 neue/ersetzte Tests in `test_self_knowledge.py`,
  darunter zwei Regressionsanker fuer den behobenen Fehler und ein
  End-to-End-Integrationsmuster fuer `status_from_resolution()`).

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
