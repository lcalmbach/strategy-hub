# Changelog

All notable changes to this project should be documented in this file.

The format is based on Keep a Changelog, and the project uses Semantic Versioning.

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
