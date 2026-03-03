# Technical Design: Strategy Hub

## Zweck
Dieses Dokument leitet aus der fachlichen Projektbeschreibung eine erste technische Zielarchitektur fuer die Implementierung mit Django, iommi und PostgreSQL ab.

Ziele des Dokuments:
- klare Struktur fuer die erste Implementierung definieren
- Datenmodell und App-Schnitt festlegen
- Berechtigungen und Kernablaufe technisch abbilden
- einen realistischen MVP-Umfang festhalten

## Leitentscheidungen
- Django ist das zentrale Web-Framework.
- iommi wird fuer Listen, Formulare, Filter, CRUD-Seiten und Teile des Dashboards verwendet.
- PostgreSQL ist die Ziel-Datenbank.
- `uv` wird fuer virtuelle Umgebungen, Abhaengigkeiten und Task-Ausfuehrung verwendet.
- Die erste Version priorisiert robuste Stammdaten- und Controlling-Funktionen vor komplexen Workflows.

## Projektstruktur
Empfohlene Django-Projektstruktur:

- `config`
- `core`
- `people`
- `strategies`
- `controlling`
- `dashboard`

### `config`
Technische Projektkonfiguration:
- Django-Settings
- URL-Konfiguration
- WSGI/ASGI
- Umgebungsabhaengige Konfiguration

### `core`
Querschnittsfunktionen:
- abstrakte Basismodelle
- gemeinsame Mixins
- Hilfsfunktionen
- zentrale Konstanten
- Audit-Felder

### `people`
Benutzernahe Fachobjekte:
- Personenprofil
- Rollenmitgliedschaften
- spaeter optional Organisationsstruktur

### `strategies`
Strategische Stammdaten:
- Strategie
- StrategieEbene
- Massnahmenverantwortlichkeit
- Stammdaten wie MassnahmeTyp

### `controlling`
Operative Steuerung:
- ControllingPeriode
- ControllingRecord
- ControllingRecordVerantwortlichkeit
- Services fuer Periodenerzeugung und Statuswechsel

### `dashboard`
Aggregierte Auswertungen und Startseite:
- Kennzahlen
- Aufgabenlisten
- Plan/Ist-Abweichungen

## Basismodelle
Folgende abstrakte Basismodelle sind sinnvoll:

### `TimestampedModel`
- `created_at`
- `updated_at`

### `UserStampedModel`
- `created_by`
- `updated_by`

### `OrderedModel`
- `sort_order`

Nicht jedes Fachmodell braucht alle Mixins. Fuer `Strategie`, `StrategieEbene` und `ControllingRecord` sind `TimestampedModel` und `UserStampedModel` jedoch sinnvoll.

## Datenmodell

### App `people`

#### Modell `Person`
Erweitert den Django-User per One-to-One.

Felder:
- `user`: OneToOneField zu `settings.AUTH_USER_MODEL`
- `short_code`: CharField, eindeutig
- `function_title`: CharField
- `organizational_unit`: CharField, optional
- `is_active_profile`: BooleanField

Constraints:
- `short_code` eindeutig

Hinweis:
- Fuer die erste Version ist ein separates Profilmodell besser als ein vollstaendig eigenes User-Modell, solange keine tiefen Auth-Anpassungen benoetigt werden.

### App `strategies`

#### Modell `Strategy`
Felder:
- `title`: CharField
- `short_description`: TextField
- `image`: ImageField, optional
- `document_url`: URLField, optional
- `valid_from`: DateField
- `valid_until`: DateField, optional
- `status`: CharField mit Choices
- `vision`: TextField
- `mission`: TextField
- `is_active`: BooleanField

Choices `status`:
- `planned`
- `active`
- `inactive`
- `completed`

Constraints:
- `valid_until >= valid_from`, falls `valid_until` gesetzt ist

Indizes:
- Index auf `status`
- Index auf `valid_from`

#### Modell `MeasureType`
Stammdatenmodell fuer Massnahmenarten.

Felder:
- `code`: CharField, eindeutig
- `label`: CharField
- `is_active`: BooleanField

#### Modell `StrategyLevel`
Generisches Hierarchiemodell fuer Handlungsfeld, Ziel und Massnahme.

Felder:
- `strategy`: ForeignKey auf `Strategy`
- `level`: CharField mit Choices
- `title`: CharField
- `short_code`: CharField
- `description`: TextField
- `parent`: ForeignKey auf `self`, optional
- `sort_order`: PositiveIntegerField
- `is_active`: BooleanField
- `measure_type`: ForeignKey auf `MeasureType`, optional

Choices `level`:
- `handlungsfeld`
- `ziel`
- `massnahme`

Constraints:
- `UniqueConstraint(strategy, short_code)`
- Parent muss zur gleichen Strategie gehoeren
- `measure_type` nur erlaubt, wenn `level = massnahme`
- `parent IS NULL` nur erlaubt, wenn `level = handlungsfeld`
- `level = ziel` verlangt Parent mit `level = handlungsfeld`
- `level = massnahme` verlangt Parent mit `level = ziel`

Empfehlung:
- Die Hierarchieregeln in `clean()` und zusaetzlich soweit moeglich per `CheckConstraint` absichern.

#### Modell `MeasureResponsibility`
Dauerhafte Verantwortlichkeit auf einer Massnahme.

Felder:
- `measure`: ForeignKey auf `StrategyLevel`
- `person`: ForeignKey auf `people.Person`
- `role`: CharField mit Choices
- `valid_from`: DateField, optional
- `valid_until`: DateField, optional

Choices `role`:
- `responsible`
- `co_responsible`
- `supporting`
- `approver`

Constraints:
- `measure.level` muss `massnahme` sein

### App `controlling`

#### Modell `ControllingPeriod`
Technisches und fachliches Klammerobjekt fuer einen Zyklus.

Felder:
- `name`: CharField
- `year`: PositiveIntegerField
- `month`: PositiveIntegerField, optional
- `start_date`: DateField
- `end_date`: DateField
- `planning_deadline`: DateField, optional
- `controlling_deadline`: DateField, optional
- `status`: CharField mit Choices

Choices `status`:
- `draft`
- `open_for_planning`
- `open_for_actuals`
- `closed`

Constraints:
- `end_date >= start_date`
- `UniqueConstraint(year, month)` falls monatliche Perioden verwendet werden

Entscheid:
- Eine eigene Periode ist technisch sauberer als Periodendaten nur direkt auf `ControllingRecord`.

#### Modell `ControllingRecord`
Felder:
- `period`: ForeignKey auf `ControllingPeriod`
- `measure`: ForeignKey auf `strategies.StrategyLevel`
- `status`: CharField mit Choices
- `plan_result_description`: TextField, optional
- `plan_effort_person_days`: DecimalField
- `plan_effort_description`: TextField, optional
- `plan_cost_chf`: DecimalField
- `plan_cost_description`: TextField, optional
- `actual_fulfillment_percent`: DecimalField
- `actual_result_description`: TextField, optional
- `actual_effort_person_days`: DecimalField
- `actual_effort_description`: TextField, optional
- `actual_cost_chf`: DecimalField
- `actual_cost_description`: TextField, optional

Choices `status`:
- `open`
- `planning_in_progress`
- `ready_for_actuals`
- `completed`

Constraints:
- `UniqueConstraint(period, measure)`
- `measure.level` muss `massnahme` sein
- `actual_fulfillment_percent` zwischen 0 und 100

Indizes:
- Index auf `status`
- Index auf `period`
- Index auf `measure`

Abgeleitete Kennzahlen:
- `cost_delta_chf = actual_cost_chf - plan_cost_chf`
- `effort_delta_days = actual_effort_person_days - plan_effort_person_days`

Hinweis:
- Die Delta-Werte muessen nicht als Spalten persistiert werden; fuer die erste Version reichen Annotationen in QuerySets.

#### Modell `ControllingRecordResponsibility`
Periodenspezifische Verantwortung.

Felder:
- `controlling_record`: ForeignKey auf `ControllingRecord`
- `person`: ForeignKey auf `people.Person`
- `role`: CharField mit Choices

Zweck:
- Bei Periodenstart koennen Verantwortlichkeiten aus `MeasureResponsibility` kopiert werden.

## Model-Validierung

### In `Strategy.clean()`
- `valid_until` darf nicht vor `valid_from` liegen.

### In `StrategyLevel.clean()`
- Parent muss dieselbe Strategie haben.
- Handlungsfeld darf keinen Parent besitzen.
- Ziel braucht Parent vom Typ Handlungsfeld.
- Massnahme braucht Parent vom Typ Ziel.
- `measure_type` darf nur bei Massnahmen gesetzt sein.

### In `MeasureResponsibility.clean()`
- Referenzierte `measure` muss Ebene `massnahme` sein.
- `valid_until` darf nicht vor `valid_from` liegen.

### In `ControllingPeriod.clean()`
- `end_date` darf nicht vor `start_date` liegen.
- Deadlines sollten innerhalb oder nach der Periode konsistent sein.

### In `ControllingRecord.clean()`
- Referenzierte `measure` muss Ebene `massnahme` sein.
- `actual_fulfillment_percent` muss im Intervall 0 bis 100 liegen.
- Ist-Eingaben koennen optional durch Status oder Periodenstatus eingeschraenkt werden.

## Services und Domain-Logik
Bestimmte Fachlogik sollte nicht in Views oder Forms leben.

### `controlling.services.open_period(period)`
Aufgaben:
- aktive Massnahmen ermitteln
- pro Massnahme einen `ControllingRecord` erzeugen
- Verantwortlichkeiten kopieren
- optional Benachrichtigungen ausloesen

### `controlling.services.transition_record_status(record, actor)`
Aufgaben:
- erlaubte Statusuebergaenge pruefen
- fachliche Pflichtfelder vor Wechsel validieren
- Audit-Felder pflegen

### `dashboard.services.get_dashboard_metrics(user)`
Aufgaben:
- Kennzahlen aggregieren
- offene Aufgaben nutzerspezifisch filtern

## Berechtigungskonzept
Fuer den MVP reicht ein gruppenbasiertes Modell ueber Django Groups und Permissions.

Empfohlene Gruppen:
- `admins`
- `strategy_managers`
- `controllers`
- `measure_owners`
- `readers`

Rechtevorschlag:

`admins`
- Vollzugriff auf alle Modelle und Administrationsaktionen

`strategy_managers`
- Strategien und Strategieebenen lesen, erstellen, bearbeiten
- keine technischen Administrationseinstellungen

`controllers`
- Perioden eroeffnen und schliessen
- Controlling-Records vollstaendig lesen
- Plan- und Ist-Daten korrigieren

`measure_owners`
- nur zugewiesene Controlling-Records sehen
- Plan- und Ist-Felder auf zugewiesenen Records bearbeiten
- keine Stammdaten aendern

`readers`
- reine Leserechte auf Strategien, Ebenen und Auswertungen

Technische Umsetzung:
- grobe Rechte ueber Django Permissions
- objektbezogene Sichtbarkeit ueber QuerySet-Filter in iommi

## iommi-Architektur
Die erste Version sollte iommi konsequent fuer Standardseiten nutzen.

### Listen
Fuer folgende Modelle werden iommi-Tabellen benoetigt:
- `Strategy`
- `StrategyLevel`
- `ControllingPeriod`
- `ControllingRecord`
- `Person`

Wichtige Filter:
- Strategie-Status
- Ebene
- Verantwortliche Person
- Periode
- Record-Status

### Formulare
Fuer folgende Objekte werden iommi-Forms benoetigt:
- Strategie
- Strategieebene
- Controlling-Periode
- Controlling-Record
- Verantwortlichkeiten

Form-Logik:
- Felder dynamisch ein-/ausblenden, z.B. `measure_type` nur bei Massnahmen
- schreibgeschuetzte Felder je nach Rolle und Status

### Detailseiten
Empfohlene Detailseiten:
- Strategie mit Baumansicht aller Ebenen
- Massnahme mit Historie aller Controlling-Records
- Controlling-Periode mit Vollstaendigkeitsstatus

### Dashboard
Das Dashboard kann in der ersten Version als klassische Django-View mit iommi-Tabellen fuer Teillisten gebaut werden.

Inhalte:
- Kennzahlenkarten
- offene Aufgaben des aktuellen Benutzers
- aktuelle Plan/Ist-Abweichungen
- letzte geaenderte Controlling-Records

## URL-Design
Vorschlag:

- `/`
- `/strategies/`
- `/strategies/<id>/`
- `/levels/`
- `/levels/<id>/`
- `/measures/<id>/`
- `/controlling/periods/`
- `/controlling/periods/<id>/`
- `/controlling/records/`
- `/controlling/records/<id>/`
- `/people/`
- `/admin-tools/`

Hinweis:
- Separate Pfade fuer `measures` koennen auf `StrategyLevel` mit Filter `massnahme` zeigen.

## Navigation
Empfohlene Hauptnavigation:
- Dashboard
- Strategien
- Handlungsfelder
- Ziele
- Massnahmen
- Controlling
- Personen
- Administration

## Datenbank- und Query-Strategie
- `select_related()` fuer `strategy`, `parent`, `measure_type`, `period`
- `prefetch_related()` fuer Verantwortlichkeiten
- Indizes auf haeufige Filterspalten
- Aggregationen fuer Dashboard in dedizierten Service-Funktionen kapseln

## Dateiuploads und Medien
- Strategie-Bilder werden ueber Django Media Storage verwaltet.
- Fuer die erste Version reicht lokaler Medien-Speicher in Entwicklung und konfigurierbarer Storage spaeter.

## Benachrichtigungen
MVP:
- Benachrichtigungsschnittstelle als Service definieren
- Versand via E-Mail kann initial no-op oder Console-Backend sein

Service-Vorschlag:
- `notifications.send_period_opened(record_ids)`
- `notifications.send_planning_reminder(record_ids)`
- `notifications.send_actuals_reminder(record_ids)`

## Tests
Von Beginn an sollten folgende Testarten enthalten sein:

### Model-Tests
- Validierung der Hierarchie
- Validierung von Perioden
- Unique Constraints
- Prozent- und Datumsgrenzen

### Service-Tests
- Periodenerzeugung erstellt genau einen Record je aktiver Massnahme
- Verantwortlichkeiten werden korrekt kopiert
- Statuswechsel respektieren Regeln

### View-/Integrationstests
- Rollenbasierte Sichtbarkeit
- Formularvalidierung
- Dashboard liefert erwartete Kennzahlen

## MVP-Scope
Der erste lauffaehige Meilenstein sollte enthalten:
- Login
- Personenprofil
- Strategien anlegen und bearbeiten
- Strategieebenen anlegen und bearbeiten
- Controlling-Periode anlegen und oeffnen
- automatische Erstellung der Controlling-Records
- Plan- und Ist-Erfassung
- Dashboard mit Kernkennzahlen

## Bewusste Verschiebung nach MVP
- echte Workflow-Freigaben mit mehreren Stufen
- komplexe Benachrichtigungslogik
- Excel-Import/-Export
- Historisierung und Versionierung von Strategien
- Mandantenfaehigkeit

## Empfohlene Reihenfolge der Implementierung

### Phase 1: Projektgrundlage
- Django-Projekt mit `uv` initialisieren
- Apps `core`, `people`, `strategies`, `controlling`, `dashboard` anlegen
- PostgreSQL-Konfiguration vorbereiten
- iommi integrieren

### Phase 2: Stammdaten
- `Person`, `Strategy`, `MeasureType`, `StrategyLevel`, `MeasureResponsibility`
- Admin und erste iommi-CRUD-Seiten

### Phase 3: Controlling
- `ControllingPeriod`, `ControllingRecord`, `ControllingRecordResponsibility`
- Service fuer Periodenerzeugung
- Bearbeitungsseiten fuer Plan und Ist

### Phase 4: Auswertung
- Dashboard
- Plan/Ist-Differenzen
- offene Aufgabenlisten

### Phase 5: Härtung
- Berechtigungen
- Tests
- E-Mail-Benachrichtigung
- Datenqualitaetschecks

## Entscheidungen fuer die Umsetzung
Fuer den Start empfehle ich folgende Festlegungen, damit der Code zuegig geschrieben werden kann:
- keine Strategie-Versionierung im MVP
- eigene Tabelle `ControllingPeriod`
- dauerhafte und periodenspezifische Verantwortlichkeiten beide vorsehen
- gruppenbasiertes Berechtigungskonzept
- Delta-Kennzahlen nicht persistieren

## Naechster technischer Schritt
Auf Basis dieses Dokuments kann direkt mit der Implementierung begonnen werden. Der erste konkrete Schritt sollte sein:
- Django-Projektstruktur erzeugen
- Abhaengigkeiten mit `uv` definieren
- initiale Apps und Modelle anlegen
- erste Migrationen erstellen
