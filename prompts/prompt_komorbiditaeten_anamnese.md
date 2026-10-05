Du bist ein Experte für die Analyse medizinischer Anamnesen. Deine Aufgabe ist es, den folgenden Arztbrief auf Informationen zur Krankengeschichte und zu psychiatrischen Komorbiditäten zu überprüfen. Analysiere den Text sorgfältig und begründe jede Entscheidung.

Gib deine Analyse ausschließlich im folgenden JSON-Format aus.

**WICHTIGE ANWEISUNGEN:**
1.  **Abhängigkeiten:** Die Extraktionen für `depression_nennung_kontext`, `depression_schweregrad` und `depression_status` hängen direkt von der Extraktion für `depression` ab.
2.  **Zitat_Nennung:** Gib immer das exakte Zitat an, das deine Extraktion stützt. Wenn keine Information vorhanden ist, schreibe "Text enthält keine Informationen".
3.  **Begründung_Extraktion:** Erkläre kurz, warum du dich für die Extraktion entschieden hast.

**ANALYSIERE DIE FOLGENDEN PUNKTE:**

**1. Krankengeschichte Schlaganfall:**
   - **`ja`**: Der Patient hat in den letzten 12 Monaten einen Schlaganfall erlitten.
   - **`nein`**: Ein Schlaganfall in den letzten 12 Monaten wird explizit ausgeschlossen oder verneint.
   - **`fehlt`**: Das Thema Schlaganfall wird im Text nicht erwähnt.

**2. Krankengeschichte epileptischer Anfall:**
   - **`ja`**: Der Patient hat in den letzten 12 Monaten einen epileptischen Anfall erlitten.
   - **`nein`**: Ein epileptischer Anfall in den letzten 12 Monaten wird explizit ausgeschlossen oder verneint.
   - **`fehlt`**: Das Thema epileptischer Anfall wird im Text nicht erwähnt.

**3. Depression:**
   - **`ja`**: Eine Depression wird explizit genannt (z.B. "Depression", "depressive Episode").
   - **`nein`**: Eine Depression wird explizit ausgeschlossen.
   - **`fehlt`**: Das Thema Depression wird im Text nicht erwähnt.

**4. Depression Nennung Kontext:**
   - **Anweisung:** Wähle eine oder mehrere der folgenden Optionen, um die Quelle der Information für das Vorhandensein einer Depression zu beschreiben. Wenn bei `depression` die Antwort `nein` oder `fehlt` ist, gib eine leere Liste `[]` zurück.
   - **Gültige Optionen:**
     - **`Explizite aerztliche Nennung einer gesicherten Diagnose`**: Eine Depression, rezidivierende depressive Störung oder depressive Episode wird explizit im Ton einer gesicherten Diagnose genannt.
     - **`Symptombeschreibung`**: Symptome werden beschrieben, aber nicht im Ton einer gesicherten Depressionsdiagnose.
     - **`Behandlung (Medikamentoes)`**: Es wird eine medikamentöse Behandlung erwähnt, welche explizit auf die depressive Symptomatik abzielt (Achtung: Manchmal werden Antidepressiva auch zur Behandlung nicht-depressiver Symptomatiken eingesetzt.).
     - **`Behandlung (Psychotherapie)`**: Es wird eine Psychotherapie für eine depressive Symptomatik erwähnt.
     - **`Neuropsychiatrisches Interview (NPI-Q)`**: Depression wird im Rahmen des NPI-Q erwähnt.
     - **`Patient Health Questionaire (PHQ)`**: Depression wird im Rahmen des PHQ erwähnt.
     - **`Anderer Kontext`**: Der Schweregrad wird im Rahmen eines anderen Kontextes genannt.

**5. Depression Schweregrad:**
   - **`keine_depression`**: Wenn bei `depression` die Antwort `nein` oder `fehlt` war.
   - **`fehlt`**: Eine Depression wird erwähnt, aber ohne Angabe des Schweregrades.
   - **`leicht`**: Eine leichte Depression liegt vor.
   - **`mittel`**: Eine mittelgradige Depression liegt vor.
   - **`schwer`**: Eine schwere Depression liegt vor.

**6. Depression Schweregrad Nennung Kontext:**
   - **Anweisung:** Wähle eine oder mehrere der folgenden Optionen, um die Quelle der Information für den Schweregrad der Depression zu beschreiben. Ziel ist es zu erfahren, ob die Quelle des Schweregrades z.B. nur das Neuropsychiatrische Interview (NPI-Q) ist (dies würden wir anders interpretieren). Wenn bei `depression` die Antwort `nein` oder `fehlt` ist, gib eine leere Liste `[]` zurück.
   - **Gültige Optionen:**
     - **`Neuropsychiatrisches Interview (NPI-Q)`**: Der Schweregrad wird im Rahmen des NPI-Q erwähnt.
     - **`Patient Health Questionaire (PHQ)`**: Der Schweregrad wird im Rahmen des PHQ erwähnt.
     - **`Anderer Kontext`**: Der Schweregrad wird im Rahmen eines anderen Kontextes genannt.

**7. Depression Status:**
   - **`keine_depression`**: Wenn bei `depression` die Antwort `nein` oder `fehlt` war.
   - **`fehlt`**: Eine Depression wird erwähnt, aber ohne Angabe des Status.
   - **`aktuell`**: Die Depression ist zum Zeitpunkt des Verfassens des Textes aktuell.
   - **`remittiert`**: Eine Depression bestand in der Vergangenheit, aber zum Zeitpunkt des Verfassens des Textes nicht mehr. ("Zustand nach" gilt nur bei expliziter Nennung von Remission).

**JSON-AUSGABEFORMAT:**
```json
{
  "krankengeschichte_schlaganfall": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "ja|nein|fehlt"
  },
  "krankengeschichte_epileptischer_anfall": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "ja|nein|fehlt"
  },
  "depression": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "ja|nein|fehlt"
  },
  "depression_diagnose_nennung_kontext": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": []
  },
  "depression_schweregrad": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "keine_depression|fehlt|leicht|mittel|schwer"
  },
  "depression_schweregrad_nennung_kontext": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": []
  },
  "depression_status": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "keine_depression|fehlt|aktuell|remittiert"
  }
}
```

**Arztbrief zur Analyse:**
{doctors_letter}
