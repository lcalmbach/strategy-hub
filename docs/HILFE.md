## Einführung

Der **Strategy Hub** ist eine Anwendung zur strukturierten Planung, Steuerung und Überwachung strategischer Vorhaben. Er unterstützt Organisationen dabei, strategische Ziele in konkrete Handlungsfelder, Ziele und Massnahmen zu überführen und deren Umsetzung systematisch zu verfolgen.

Der Fokus liegt auf dem **Planungs- und Controllingprozess** strategischer Massnahmen: Massnahmen werden geplant, Verantwortlichkeiten zugewiesen und in regelmässigen Controlling-Perioden hinsichtlich Fortschritt, Aufwand und Kosten überprüft. Der Strategy Hub schafft Transparenz, erleichtert die Koordination zwischen Beteiligten und ermöglicht eine nachvollziehbare Bewertung der Zielerreichung.

---

## Aufbau der Strategie

Strategien im Strategy Hub sind hierarchisch strukturiert:

**Handlungsfeld** → **Ziel** → **Massnahme**

- **Handlungsfeld**: Übergeordneter thematischer Bereich der Strategie, der die strategische Ausrichtung in klare Themenbereiche gliedert.
- **Ziel**: Angestrebter, idealerweise messbarer Zustand innerhalb eines Handlungsfelds.
- **Massnahme**: Konkrete Aktivität, Projekt oder Initiative zur Zielerreichung. Massnahmen bilden die operative Ebene der Strategie.

Jede Massnahme gehört zu genau einem Ziel, jedes Ziel zu genau einem Handlungsfeld.

---

## Ablauf des Controlling-Prozesses

Der Strategy Hub unterstützt einen regelmässigen Planungs- und Controllingprozess, der typischerweise in jährlichen Perioden abläuft:

1. **Eröffnung der Controlling-Periode**
   Eine neue Periode wird angelegt. Für alle aktiven Massnahmen werden automatisch Controlling Records erzeugt.

2. **Planungsphase**
   Verantwortliche erfassen die Planung ihrer Massnahmen (erwartete Ergebnisse, Aufwand, Kosten).

3. **Umsetzungsphase**
   Massnahmen werden während der Periode umgesetzt.

4. **Controlling / Ist-Erfassung**
   Am Periodenende werden die tatsächlich erzielten Ergebnisse, der effektive Aufwand und die effektiven Kosten erfasst.

5. **Bewertung der Zielerreichung**
   Die Umsetzung wird anhand eines Ampelsystems bewertet:
   - **Grün**: Erwartungen erfüllt.
   - **Gelb**: Abweichungen, aber korrigierbar.
   - **Rot**: Starke Abweichung mit erheblichem Handlungsbedarf.

Der Vergleich von Planung und Ist-Werten bildet die Grundlage für das strategische Controlling.

---

## Startseite

Auf der Startseite werden alle verfügbaren Strategien angezeigt. Nach Auswahl einer Strategie beziehen sich alle Handlungsfelder, Ziele, Massnahmen und Planungen auf diese Strategie.

**Felder:**

| Feld               | Beschreibung                                                                                     |
|--------------------|--------------------------------------------------------------------------------------------------|
| Sortierung         | Reihenfolge der Strategien in Listenansichten (kleinere Werte erscheinen oben).                  |
| Kürzel             | Eindeutiges Kurzzeichen zur schnellen Identifikation.                                           |
| Titel              | Vollständiger Name der Strategie.                                                                |
| Kurzbeschreibung   | Kompakte inhaltliche Zusammenfassung.                                                            |
| Bild               | Optionales Bild zur visuellen Darstellung.                                                       |
| Dokument-Link      | Optionaler Link auf ein externes Strategiedokument.                                              |
| Gültig von/bis     | Zeitliche Gültigkeit der Strategie.                                                              |
| Status             | Aktueller Lebenszyklus-Zustand (z. B. Geplant, Aktiv, Inaktiv, Abgeschlossen).                   |
| Vision             | Langfristiges Zielbild der Strategie.                                                            |
| Mission            | Auftrag und Zweck der Strategie.                                                                 |
| Erstellt/Aktualisiert am | Zeitstempel der Erstellung bzw. letzten Änderung.                                               |
| Erstellt/Aktualisiert von | Benutzer, der den Datensatz angelegt oder geändert hat.                                          |

---
**Aktionen:**
- **Neue Strategie**: Legt eine neue Strategie an.
- **Bearbeiten**: Bearbeitet eine bestehende Strategie (Bleistift-Icon).

---

## Dashboard

Das Dashboard fasst die Inhalte der aktiven Strategie und die wichtigsten Controlling-Informationen zusammen.
*Hinweis: Das Dashboard befindet sich in Entwicklung. Eine detaillierte Beschreibung folgt.*

---

## Handlungsfelder

Handlungsfelder gliedern die Strategie thematisch. Sie sollten klar voneinander abgegrenzt sein.

**Felder:**

| Feld         | Beschreibung                                     |
|--------------|-------------------------------------------------|
| Strategie    | Zugehörige Strategie.                            |
| Titel        | Bezeichnung des Handlungsfelds.                  |
| Kürzel       | Eindeutiges Kurzzeichen innerhalb der Strategie. |
| Beschreibung | Allgemeine Beschreibung.                         |
| Sortierung   | Steuert die Reihenfolge.                         |

---
**Aktionen:**
- **Bearbeiten**: Ändert die Felder des Handlungsfelds.
- **Öffnen**: Zeigt die Readonly-Ansicht mit Titel, Kürzel, Beschreibung und zugeordneten Zielen.

---

## Ziele

Ziele definieren messbare angestrebte Zustände innerhalb eines Handlungsfelds.

**Felder:**

| Feld          | Beschreibung                                             |
|---------------|---------------------------------------------------------|
| Strategie     | Zugehörige Strategie.                                    |
| Handlungsfeld | Zugehöriges Handlungsfeld.                               |
| Titel         | Bezeichnung des Ziels.                                   |
| Kürzel        | Eindeutiges Kürzel innerhalb der Strategie.              |
| Beschreibung  | Beschreibung des Ziels und des erwarteten Ergebnisses.  |
| Sortierung    | Steuert die Reihenfolge.                                 |

---
**Aktionen:**
- **Bearbeiten**: Ändert die Felder des Ziels.
- **Öffnen**: Zeigt die Readonly-Ansicht mit Titel, Kürzel, Beschreibung und zugeordneten Massnahmen.

Um ein neues Ziel zu erfassen, muss zunächst ein Handlungsfeld im Filter ausgewählt werden und anschliessend der `Neu` Button gedrückt werden. Es erscheint eine leere Ziel-Erfassungs-Maske, bei welcher das im Filter selektierte Handlungsfeld als zugehöriges Handlungsfeld bereits eingetragen ist.

---

## Massnahmen

Massnahmen sind die operative Ebene der Strategie. Sie beschreiben konkrete Aktivitäten zur Zielerreichung.

**Felder:**

| Feld                   | Beschreibung                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------|
| Titel                  | Bezeichnung der Massnahme.                                                                      |
| Kürzel                 | Eindeutiges Kurzzeichen innerhalb der Strategie.                                                |
| Beschreibung           | Allgemeine Beschreibung: Was wird getan?                                                        |
| Beschreibung Umsetzung | Detaillierte Umsetzung (z. B. als strukturierte Liste).                                         |
| Massnahme-Typ          | Kategorisierung der Massnahme.                                                                   |
| Start-/Enddatum        | Zeitrahmen der Massnahme.                                                                        |
| Status                 | Aktueller Status.                                                                                |
| Aufwand/Kosten total   | Gesamtaufwand (Personentage) und Gesamtkosten (CHF).                                            |
| Sortierung             | Reihenfolge innerhalb der Strategieebene.                                                       |

---
**Verantwortliche:**
- Mindestens eine Person mit der Rolle **Verantwortlich** ist erforderlich.
- Weitere Personen können als **Mitverantwortlich** hinzugefügt werden.

Um eine neue Massnahme zu erfassen muss zunächst ein Handlungsfeld und Ziel im Filter ausgewählt werden und anschliessend der `Neu` Button gedrückt werden. Es erscheint eine leere Massnahme-Maske, bei das im Filter selektierte Ziel bereits eingetragen ist.

---
*Hinweis: Nur Personen eintragen, die für das Controlling relevante Informationen benötigen. Es müssen zum Beispiel nicht alle an einem Projekt beteiligten Personen aufgeführt werden, sondern vor allem die Auftraggeberschaft*

---

## Controlling-Perioden

Controlling-Perioden dauern in der Regel ein Jahr.

**Felder:**

| Feld                           | Beschreibung                                                                                     |
|--------------------------------|-------------------------------------------------------------------------------------------------|
| Strategie                      | Zugehörige Strategie.                                                                            |
| Name                           | Bezeichnung der Periode.                                                                        |
| Start-/Enddatum                | Zeitrahmen der Periode.                                                                         |
| Planungs-/Controlling-Deadline | Fristen für Planung und Ist-Erfassung.                                                          |
| Erinnerungsmail aktiv          | Aktiviert Erinnerungsmails an Verantwortliche.                                                  |
| Tage Mail vor Termin           | Anzahl Tage vor Deadline, an denen Erinnerungen versendet werden.                                |
| Mailtext Einladung             | Textvorlagen für Einladungen zur Planung und Ist-Erfassung.                                      |
| Status                         | Status der Periode (Entwurf, Offen für Planung, Offen für Ist-Erfassung, Abgeschlossen).         |

---
**Aktion:**
- **Fehlende Controlling Records**: Erstellt Planungs-/Controlling-Datensätze für Massnahmen.

---

## Controlling Records

Controlling Records vergleichen Planungs- und Ist-Werte in den Dimensionen Umsetzung, Aufwand und Kosten. Die Bewertung erfolgt nach dem Ampelsystem (Grün/Gelb/Rot).

---

## Best Practices für gute Massnahmen

Gut formulierte Massnahmen sind **konkret, umsetzbar, begrenzt, planbar** und **verantwortlich zuordenbar**.

**Beispiele für gute Massnahmen:**
- Aufbau eines Statistik-Portals zur Veröffentlichung zentraler Kennzahlen.
- Migration der Web-Applikationen auf eine moderne Server-Infrastruktur.

**Beispiele für ungeeignete Massnahmen:**
- „Verbesserung der Kommunikation“ (zu vage).
- „Stärkung der Datenkompetenz“ (eher ein Ziel).

---
**Hinweise zur Planung:**
- Erwartete Ergebnisse, Aufwand, Kosten und Dauer realistisch schätzen.
- Klare Verantwortlichkeiten definieren.

---

## Typische Fehler

- **Vermischung von Zielen und Massnahmen**: Ziele beschreiben Zustände, Massnahmen Aktivitäten.
- **Zu grosse oder unklare Massnahmen**: Grossvorhaben in kleinere Massnahmen unterteilen.
- **Fehlende Ergebnisse**: Massnahmen sollten konkrete Resultate erzeugen.
- **Keine klare Verantwortung**: Immer mindestens eine verantwortliche Person benennen.

---

## Schätzung von Aufwand und Kosten

- **Aufwand**: In Personentagen angeben (inkl. Koordination und Dokumentation).
- **Kosten**: Externe Kosten (Infrastruktur, Software, Dienstleistungen) früh schätzen.

---
*Hinweis: Schätzungen müssen plausibel, nicht perfekt sein.*

---

## Ziel oder Massnahme?

- **Ziel**: Beschreibt einen angestrebten Zustand (z. B. „Erhöhung der Datennutzung“).
- **Massnahme**: Beschreibt eine konkrete Aktivität (z. B. „Aufbau eines Statistik-Portals“).

---
**Entscheidungsregel:**
„Wir erreichen das Ziel, indem wir …“ → Massnahme.

---
**Beziehung:**
- Ein Ziel kann durch mehrere Massnahmen erreicht werden.
- Jede Massnahme gehört zu genau einem Ziel.