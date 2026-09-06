# Changelog

## [Unreleased]

- Der Modulkatalogvertrag wird wieder eingehalten: `state.location` verwendet
  nun den zulässigen Wert `project`, passend zum dokumentierten, vom Aufrufer
  übergebenen projekt-/modullokalen Zustandsroot. 54/54 Tests grün.

## [0.3.1] - 2026-09-06

PR#1-Review-Nachzug (T-20260906-217302993, merge-reviewer-gs/Opus):

- **README-Praezisierung:** Die Prosa zu "Naehrstoffe + Andockstellen" widersprach
  sich scheinbar (`organic-growth` "weiss nichts von grounding-seed" vs. "speist
  ... ein"). Aufgeloest: der Skill kennt kein Modul und ruft nie
  `grounding_seed.fertilizer` auf -- die Bruecke schlaegt der AGENT, der beide
  zur Verfuegung hat, indem er selbst `record_candidate()` aufruft, wenn er die
  vom Skill erkannte Kookkurrenz UND grounding-seeds Merkmechanismus vorfindet.
  Betroffen: README.md, README_de.md, llms.txt, `ellmos-module.v2.json`-Adapternote.
- **Fix: `abwehren` (Quarantaene) ist jetzt terminal.** `dismiss_candidate()`
  konnte eine bestehende `state="abwehren"`-Einstufung stillschweigend zu
  `"koexistieren"` abschwaechen; `confirm_candidate()` haette sie ebenso
  stillschweigend "bestaetigt" (Widerspruch in sich). Beide Funktionen lehnen
  jetzt ueber `_ensure_not_quarantined()` jede Aenderung an einem als
  `abwehren` eingestuften Kandidaten ab (`ValueError`) -- eine
  Risikoeinschaetzung (T-20260815-109780293: "Zustand 3 ist selten und gehoert
  gemeldet") wird nicht routinemaessig zurueckgenommen. Eine bewusste Aufhebung
  der Quarantaene ist ein eigener, expliziter Schritt, nicht Teil dieses
  schmalen Moduls. 2 neue Regressionstests.
- 68/68 Tests gruen mit installiertem `source_resolver` (war 66/66); auf einem
  Host ohne das Paket 60/63 ohne `test_ladder_parity.py` (weiterhin dieselben
  3 vorbestehenden, unabhaengigen Fehlschlaege).

## [0.3.0] - 2026-09-06

Ticket T-20260815-316117714 ("organic-growth: Verbindungen aus der Nutzungsspur
gewinnen"). Nutzerentscheid 2026-09-06: eigenstaendiger Skill UND optionaler
Fertilizer im Seed, Abhaengigkeit ausdruecklich nur in EINE Richtung
(grounding-seed -> organic-growth), konservativer Default (Vorschlag statt
automatischer Bindung).

- Neu: `fertilizer.py` -- optionale dritte Naehrstoffquelle neben Discovery
  (`scan.py`) und gegenseitigem Erkennen (T-20260815-109780293): die
  Nutzungsspur. `record_candidate()`/`list_candidates()`/`confirm_candidate()`/
  `dismiss_candidate()` halten Kookkurrenzen benannter Komponenten aus dem
  aktiven Kontextfenster als Stufe-2/PROPOSED-Kandidaten fest
  (`connections-candidates.json`, getrennt von `connections-config.json`, das
  bereits eine feste, andere Bedeutung traegt -- Migrationsziel+Zeitstempel).
- Vokabular (`link_type: synapse | endplate`, `state: verbinden | koexistieren
  | abwehren`) woertlich aus T-20260815-109780293 uebernommen, kein zweites
  Format erfunden.
- CLI: `grounding-seed fertilizer record|list|confirm|dismiss`.
- Manifest: `organic-growth@0.1.0` als optionaler, einseitig gerichteter
  Seam-Adapter eingetragen (Verweis mit Version, keine eingebettete Kopie).
- Fix waehrend des Baus (advisor-Review): `confirm_candidate()`/
  `dismiss_candidate()` trafen bei zwei Eintraegen gleicher Komponenten-Paarung
  (einer bestaetigt, einer neu offen -- entsteht z. B. nach `confirm()` gefolgt
  von einem erneuten `record_candidate()`) den FALSCHEN, naemlich den ersten
  nach Key statt den offenen. `dismiss_candidate()` konnte dadurch sogar einen
  bereits bestaetigten Eintrag zusaetzlich als `dismissed` markieren
  (`confirmed=True` UND `dismissed=True` gleichzeitig). Beide Funktionen
  filtern jetzt zwingend auf `not confirmed and not dismissed`; zwei
  Regressionstests ergaenzt.
- 12 neue Tests in `test_fertilizer.py` (66/66 gesamt auf einem Host mit
  installiertem `source_resolver`, wie zuvor 54/54). Auf WORKSTATION-LG selbst
  ist `source_resolver` nicht installiert: dort 58/61 gruen ohne
  `test_ladder_parity.py` (3 vorbestehende, von dieser Aenderung unabhaengige
  Fehlschlaege + 1 vorbestehender Collection-Fehler wegen des fehlenden
  Pakets) -- alle 12 neuen Fertilizer-Tests darin gruen.

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
