# Changelog

All notable changes to this project should be documented in this file.

The format is based on Keep a Changelog, and the project uses Semantic Versioning.

## [0.5.1] - 2026-03-09

### Changed

- Version auf `0.5.1` gesetzt

## [0.6.0] - 2026-03-08

### Added

- Hilfeseite kann direkt in der App bearbeitet werden (`Bearbeiten`, `Speichern`, `Abbrechen`) mit Persistenz nach `docs/HILFE.md`

## [0.5.0] - 2026-03-07

### Added

- Neuer Bereich `Auswertungen` mit SQL-basierten Reports, Ausführung und XLSX-Download
- Neues Report-Modell (`name`, `sql`, `params`, `description`) inkl. Admin und eigener Seite
- Neue Organisationen-Verwaltung bei Personen inkl. FK von Person auf Organisation
- Organisation erweitert um `Bereich`, `Abteilung` und `Kürzel`
- Neue Massnahme-Felder: `Beschreibung Umsetzung`, `Aufwand total`, `Kosten total`
- Neue Controlling-Record-Felder: `Bemerkungen zur Planung`, `Bemerkungen zum Controlling`, `Ampel Allgemein`
- Verlinkte Unterlisten auf Strategieebenen-Detailseiten (Ziele, Massnahmen, Controlling-Records)

### Changed

- Button-Design vereinheitlicht auf die Header-Farbe
- Menüstruktur und Benennungen überarbeitet (inkl. `Controlling`)
- `Strategy.is_active` entfernt; Aktivität wird über `status` gesteuert
- Listen-/Detailansichten für Handlungsfelder, Ziele und Massnahmen weiter bereinigt

## [0.4.0] - 2026-03-06

### Added

- Button in der Controlling-Perioden-Detailansicht zum Erzeugen fehlender Controlling-Records pro Massnahme
- Toast-Meldungen im Hauptlayout fuer Benutzer-Feedback bei Aktionen
- Hilfeseite unter `/hilfe/` mit Markdown-Inhalt aus `docs/HILFE.md`
- Inhaltsverzeichnis in der Hilfeseite auf Basis der Markdown-Ueberschriften
- Neue Felder auf Controlling-Perioden: Erinnerungsmail aktiv, Tage vor Termin, Mailtext Einladung Planung, Mailtext Einladung Controlling

### Changed

- Controlling-Record-Status von statischen Choices auf DB-Codes (`core.Code`, Kategorie-ID `1`) umgestellt
- Status-Codes fuer Controlling-Records eingefuehrt: `Offen`, `Planung laeuft`, `Planung abgeschlossen`, `Controlling laeuft`, `Controlling abgeschlossen`
- Controlling-Periodenliste: Spalten `Beginn`, `Ende`, zusaetzlich `Planung Ende` und `Controlling Ende`
- Controlling-Periodenliste zeigt lange Mailtext-Felder nicht mehr
- Hauptmenue ueberarbeitet: Hilfe als letzter Punkt mit visueller Abtrennung und Emoji-Labels

## [0.3.0] - 2026-03-05

### Added

- Zentrale Stammdatentabellen `CodeCategory` und `Code` inkl. Admin-Ansichten
- Kategorie-spezifische Code-Zugriffe via Proxy-Modelle fuer `initiative_status` und `initiative_role`
- Manuelle Ampel-Felder fuer Controlling-Records: Umsetzungsstand, Ausgaben und Aufwand
- Statusabhaengige Record-Formulare (Planung, Ist-Erfassung, Abgeschlossen)

### Changed

- Ampel-Anzeige verwendet nun effektive Status mit Vorrang fuer manuelle Werte
- Verantwortliche in der Controlling-Record-Liste werden als Kuerzel angezeigt
- Record-Verantwortlichkeiten wurden mit Massnahmen-Verantwortlichkeiten synchronisiert (inkl. Mehrfach-Zuweisungen)
- Dashboard zeigt Aufwand/Kosten ohne Kommastellen; Kosten mit Tausendertrennzeichen (`'`)
- Iommi-Debug-Overlay (`Code`, `Tree`, `Pick`, `Code finder`) ist standardmaessig deaktiviert

## [0.2.0] - 2026-03-04

### Added

- Strategien haben nun eigene Felder fuer `Kuerzel` und `Sortierung`
- Personenfunktionen wurden als Stammdatenmodell `Function` mit Codes, Bezeichnungen und Sortierung eingefuehrt
- Selektiver Demo-Import fuer Personen mit `load_fake_data --replace --person`
- Dashboard-Erweiterung mit periodischen Zusammenfassungen je aktiver Strategie
- Plotly-Scatterplots fuer Kosten und Aufwand pro Controlling-Periode
- Mitarbeitenden-Uebersicht im Dashboard mit Anzahl Massnahmen und Ampelverteilung

### Changed

- Dashboard bezieht sich nun konsequent auf die ausgewaehlte Strategie und zeigt keine Strategie-Auswahl-Tabelle mehr
- Handlungsfelder-, Ziele- und Massnahmenlisten wurden in Reihenfolge und Spaltenbezeichnungen ueberarbeitet
- Die Massnahmenliste zeigt verantwortliche Personen als kommaseparierte Kuerzel
- Die Personenliste zeigt Nachname und Vorname aus dem zugehoerigen Benutzer und erlaubt Sortierung darauf
- Fake-Daten fuer Personen, Funktionen und Verantwortlichkeiten wurden erweitert und vereinheitlicht
- Controlling-Record-Filter fuer Massnahmen zeigen nur noch echte Massnahmen statt uebergeordneter Ebenen

## [0.1.0] - 2026-03-01


### Added

- Initial Django/iommi implementation for strategy management and controlling
- Strategy, hierarchy level, measure type, and responsibility management
- Controlling periods and controlling records
- Dashboard and active strategy selection flow
- Deterministic CSV-based demo data import
- Explicit filter-driven creation flows for goals and measures

## [0.1.4] - 2026-03-03

### Added

- Jahres-Helfer fuer Massnahmen zur Anzeige von Start- und Endjahr
- Backfill fuer bestehende Massnahmen mit Zeitraum 2022 bis 2025
- Management-Command zum Erzeugen von Controlling-Records fuer jede Kombination aus Periode und Massnahme

### Changed

- Ziele werden standardmaessig nach Kuerzel sortiert
- Dropdowns fuer Handlungsfelder, Ziele und Massnahmen zeigen nun `Kuerzel Titel`
- Die Handlungsfeld-Spalte wurde aus der Massnahmenliste entfernt
- Massnahmen verwenden eigene Felder fuer Startdatum, Enddatum und Status
- In der Massnahmenliste werden Jahre als `Jahr von` und `Jahr bis` statt voller Datumswerte angezeigt
- `actuals_deadline` wurde in `controlling_deadline` umbenannt
- `is_locked` wurde aus Controlling-Perioden entfernt
- Die Loeschicons in den Controlling-Listen loeschen Perioden und Records nun direkt aus der Liste
- Die Ziel-Spalte wurde aus der Controlling-Record-Liste entfernt
- Lange Massnahmen-Titel werden in der Controlling-Record-Liste abgekuerzt
