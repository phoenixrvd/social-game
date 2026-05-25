---
state: implemented
---

# SG-012: Editierbarer Scene Context

## Kontext
In der Web-GUI kann der NPC-szenenspezifische Scene Context der aktiven Sitzung bearbeitet werden.
Der Scene Context ist die fuer den aktiven NPC und die aktive Szene gespeicherte Kontextdatei unter `.overrides/npcs/<npc>/scenes/<scene>/scene.md`.

## Annahmen
- Die Bearbeitung bezieht sich ausschliesslich auf den NPC-szenenspezifischen Scene Context der aktiven Sitzung.
- Character-Beschreibung, allgemeine Szenenbeschreibung und Zustandsdaten sind nicht Bestandteil dieser Anforderung.
- Das Generieren eines neuen Contexts ist eine Vorschauaktion und speichert den erzeugten Inhalt nicht automatisch.

## Offene Fragen
- Keine

## Anforderungen

### Bearbeitungszugang im Dialogkontext
**Typ:** Funktional  
**Beschreibung:** Das System muss den Scene Context direkt aus der zugehoerigen Kontext-Message heraus zur Bearbeitung anbieten.  
**Akzeptanzkriterien:**
- In der Kontext-Message des Scene Contexts ist eine Bearbeiten-Aktion sichtbar.
- Die Bearbeiten-Aktion wird als Icon-Button mit Pencil-Icon dargestellt.
- Beim Ausloesen der Bearbeiten-Aktion oeffnet sich der Optionsdialog.
- Der Optionsdialog zeigt direkt das Formular zur Bearbeitung des Scene Contexts.

**Referenzen:** `doc/requirements/sg-011-web-gui.md`

### Formular zur Scene-Context-Bearbeitung
**Typ:** Funktional  
**Beschreibung:** Das System muss in der Web-GUI ein eigenes Formular zur Bearbeitung des Scene Contexts bereitstellen.  
**Akzeptanzkriterien:**
- Das Formular enthaelt eine Textarea fuer den Scene Context.
- Beim Oeffnen ist die Textarea mit dem aktuell gespeicherten Scene Context der aktiven Sitzung vorbelegt.
- Das Formular enthaelt die Aktion `Neuen Kontext aus Eingabe generieren`.
- Das Formular enthaelt die Aktion `Kontext speichern`.

### Neuen Context aus Eingabe generieren
**Typ:** Funktional  
**Beschreibung:** Das System muss aus der aktuellen Textarea-Eingabe einen neuen Scene Context erzeugen koennen, ohne ihn automatisch zu speichern.  
**Akzeptanzkriterien:**
- Die Aktion `Neuen Kontext aus Eingabe generieren` verwendet den aktuellen Textarea-Inhalt als Eingabe.
- Die Aktion nutzt fachlich dieselbe LLM-gestuetzte Context-Erzeugung, die beim Anlegen einer Szene fuer den NPC-szenenspezifischen Scene Context verwendet wird.
- Nach erfolgreicher Generierung ersetzt der erzeugte Scene Context den Inhalt der Textarea.
- Die Generierung speichert den erzeugten Scene Context nicht dauerhaft.
- Scheitert die Generierung, bleibt der bisherige Textarea-Inhalt unveraendert.

**Referenzen:** `engine/services/npc_scene_service.py`, `prompts/npc_scene_create_text.md`

### Scene Context speichern
**Typ:** Funktional  
**Beschreibung:** Das System muss den bearbeiteten Scene Context fuer den aktiven NPC und die aktive Szene speichern koennen.  
**Akzeptanzkriterien:**
- Die Aktion `Kontext speichern` speichert den aktuellen Textarea-Inhalt als Scene Context der aktiven Sitzung.
- Der gespeicherte Scene Context wird unter `.overrides/npcs/<npc>/scenes/<scene>/scene.md` abgelegt.
- Nach erfolgreichem Speichern wird der Optionsdialog geschlossen.
- Nach erfolgreichem Speichern zeigt die Kontext-Message im Dialog den aktualisierten Scene Context an.
- Bei einem Fehler bleibt der zuletzt erfolgreich gespeicherte Scene Context erhalten.

**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Fehler- und Ladezustand
**Typ:** Funktional  
**Beschreibung:** Das System muss Generieren und Speichern des Scene Contexts mit nachvollziehbaren Lade- und Fehlerzustaenden begleiten.  
**Akzeptanzkriterien:**
- Waehrend Generieren oder Speichern laeuft, verhindert das Formular parallele Context-Aktionen.
- Bei Fehlern zeigt das Formular einen verstaendlichen Fehlerhinweis an.
- Fehler beim Generieren oder Speichern schliessen den Optionsdialog nicht.
- Fehler beim Generieren oder Speichern veraendern den gespeicherten Scene Context nicht.

**Referenzen:** `doc/guidelines/error-handling.md`
