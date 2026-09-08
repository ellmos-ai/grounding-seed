# Security Policy / Sicherheitsrichtlinie

[English](#english) | [Deutsch](#deutsch)

---

## English

### Supported Versions

| Version | Supported          | Security Maintenance Status |
|---------|--------------------|-----------------------------|
| 0.3.x   | :white_check_mark: | Actively supported          |
| < 0.3   | :x:                | End of Life (upgrade)       |

### Reporting a Vulnerability

We take the security of `grounding-seed` seriously. If you identify a potential vulnerability, please report it responsibly rather than opening a public issue.

- **Primary Contact:** [security@open-bricks.org](mailto:security@open-bricks.org)
- **Maintainer:** [lukas@open-bricks.org](mailto:lukas@open-bricks.org)
- **GitHub Advisory:** [ellmos-ai/grounding-seed Advisories](https://github.com/ellmos-ai/grounding-seed/security/advisories)

#### Response Commitments & SLA
- **Initial Response:** Within 48 hours.
- **Triage & Severity Assessment:** Within 5 business days.
- **Remediation & Advisory Release:** Coordinated disclosure after verified fix.

### Core Security Invariants

1. **Local-First & Zero Network Egress:** `grounding-seed` executes completely offline in local environments and makes zero outbound network calls.
2. **Non-Elevation User-Mode:** Operations do not require administrative, root, or elevated privileges. All stores and templates operate within normal user permissions.
3. **Fail-Closed Receipt Integrity & Terminal Quarantine:** Quarantine state (`abwehren`) is strictly terminal. Unconfirmed candidates remain purely informational (`PROPOSED` / Stufe 2) and are never automatically promoted to active configurations without explicit confirmation.
4. **Inert Offline Analysis & Isolated Fallback:** When `source-resolver` is unavailable, `grounding-seed` operates in an isolated, shape-identical fallback ladder without ambient network dependency or untrusted code execution.
5. **Resource Scoping & Path Containment:** All file manipulations and candidate persistence are bounded strictly within the caller-provided directory root (`LocalStore`).

---

## Deutsch

### Unterstützte Versionen

| Version | Unterstützt        | Status                      |
|---------|--------------------|-----------------------------|
| 0.3.x   | :white_check_mark: | Aktiv gepflegt              |
| < 0.3   | :x:                | EOL (Bitte aktualisieren)   |

### Sicherheitslücke melden

Wir nehmen die Sicherheit von `grounding-seed` sehr ernst. Falls Sie eine potenzielle Schwachstelle finden, bitten wir um eine verantwortungsvolle Meldung abseits öffentlicher Issues.

- **Primärer Kontakt:** [security@open-bricks.org](mailto:security@open-bricks.org)
- **Maintainer:** [lukas@open-bricks.org](mailto:lukas@open-bricks.org)
- **GitHub Security Advisories:** [ellmos-ai/grounding-seed Advisories](https://github.com/ellmos-ai/grounding-seed/security/advisories)

#### Reaktionszeiten & SLA
- **Erste Rückmeldung:** Innerhalb von 48 Stunden.
- **Triage & Einstufung:** Innerhalb von 5 Werktagen.
- **Patch & Advisory:** Koordinierte Veröffentlichung nach verifiziertem Fix.

### Sicherheits- und Architektur-Invarianten

1. **Local-First & Zero Network Egress:** `grounding-seed` arbeitet vollständig lokal und sendet keinerlei Daten über das Netzwerk.
2. **User-Mode ohne Sonderrechte:** Es werden keine Root-, Administrator- oder erweiterten Rechte benötigt.
3. **Fail-Closed Integrität & Terminale Quarantäne:** Der Quarantäne-Zustand (`abwehren`) ist unumkehrbar terminal. Nicht bestätigte Kandidaten verbleiben strikt als Vorschläge (`PROPOSED` / Stufe 2) und werden niemals automatisch scharfgeschaltet.
4. **Inerte Offline-Analyse & Isolierte Fallback-Leiter:** Fehlt `source-resolver`, schaltet die Bibliothek auf eine lokale, form-identische Fallback-Stufenordnung um, ohne Netzwerkaufrufe oder unsichere Deserialisierung.
5. **Pfad-Isolation & Speicher-Begrenzung:** Sämtliche Dateioperationen und Kandidatenspeicherungen (`LocalStore`) sind strikt auf den vom Aufrufer definierten Root-Pfad begrenzt.
