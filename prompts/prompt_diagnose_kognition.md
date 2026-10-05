Du bist ein Experte für die Analyse medizinischer Dokumente. Deine Aufgabe ist es, den folgenden Arztbrief sorgfältig zu prüfen und spezifische Informationen zur kognitiven Störung, deren Ätiologie, zu Biomarkern und zum kognitiven Status zu extrahieren. Analysiere den Text Schritt für Schritt und begründe jede deiner Entscheidungen.

Gib deine Analyse ausschließlich im folgenden JSON-Format aus. Fülle für jede der Kategorien alle Felder aus.

**WICHTIGE ANWEISUNGEN:**
1.  **Zitat_Nennung:** Gib immer das exakte Zitat aus dem Text an, das deine Extraktion stützt. Wenn keine Information vorhanden ist, schreibe "Text enthält keine Informationen".
2.  **Begruendung_Extraktion:** Erkläre kurz und präzise, warum du dich basierend auf dem Zitat und den unten stehenden Regeln für eine bestimmte Extraktion entschieden hast.
3.  **Extraktion:** Wähle eine der vorgegebenen Optionen. Für die Ätiologie kann eine Liste von Optionen gewählt werden.

**ANALYSIERE DIE FOLGENDEN PUNKTE:**

**1. Kognitive Störung - Präsenz:**
   - **`ja`**: Wenn im Text eine Demenz oder eine kognitive Störung erwähnt wird (unabhängig vom Schweregrad).
   - **`nein`**: Wenn im Text explizit erwähnt oder diagnostiziert wird, dass **keine** Demenz oder kognitive Störung vorliegt.
   - **`fehlt`**: Wenn das Thema Demenz oder kognitive Störung im gesamten Text nicht erwähnt wird.

**2. Kognitive Störung - Schweregrad:**
   - **Anweisung:** Werte diesen Punkt nur aus, wenn bei "1. Kognitive Störung - Präsenz" die Antwort `ja` war. Wenn bei "1. Kognitive Störung - Präsenz" die Antwort `nein` war, sollte hier `keine_kognitive_stoerung` ausgewählt werden. 
   - **`keine_kognitive_stoerung`**: Wenn von "Kognitive Störung - Präsenz" mit `nein` beantwortet wurde.
   - **`leicht`**: Wenn von "leichter Demenz", "leichter kognitiver Störung", "MCI" oder "aMCI" (mild cognitive impairment) die Rede ist.
   - **`mittel`**: Wenn von "mittelgradiger Demenz" oder "mittelschwerer Demenz" die Rede ist.
   - **`schwer`**: Wenn von "schwerer Demenz" oder "fortgeschrittener Demenz" die Rede ist.
   - **`fehlt`**: Wenn ein Schweregrad einer Demenz oder einer kognitive Störung im gesamten Text nicht erwähnt wird. 

**3. Kognitive Störung Ätiologie:**
   - **Anweisung:** Wähle eine oder mehrere der folgenden Ursachen aus, wenn im Text Hinweise darauf gegeben werden. Wenn bei "1. Kognitive Störung - Präsenz" die Antwort `nein` oder `fehlt` war, oder wenn keine Ätiologie genannt wird, gib eine leere Liste `[]` zurück.
   - **Gültige Optionen:** "Alzheimer-Krankheit", "Lewy-Koerperchen Demenz", "Frontotemporale Demenz (FTD)", "Parkinson-Krankheit", "vaskulaere Demenz", "cerebrale Mikroangiopathie", "Multi-Infarkt Demenz", "Progressive supranukleaere Blickparese (PSP)", "Normaldruckhydrocephalus (NPH)", "Kortikobasale Degeneration (CBD)", "Huntington-Krankheit", "Creutzfeld-Jacob Krankheit (CJD)", "Primaer Progressive Aphasie (PPA)", "Wernicke Encephalopathie", "Encephalitis", "Tumor", "Chorea Huntington"
   - **Achtung:** Du sollst nicht eigenständig eine Differentialdiagnose erstellen. Außerdem geht es um wahrscheinliche Ätiologien. Mögliche, aber vom Behandler als weniger wahrscheinliche Differentialdiagnosen beschriebene Ätiologien sollst du ignorieren.
  

**4. Pathologische Amyloid-Biomarker:**
   - **`ja`**: Wenn eine der folgenden Bedingungen erfüllt ist:
     - Amyloid Aß42 (oder Beta-Amyloid (1-42)) ist < 630 pg/ml.
     - Der Aß42/40-Quotient (oder Amyloidquotient) ist < 0,096.
     - Einer dieser Marker wird im Brief explizit als "pathologisch" bewertet.
     - Eine PET-Untersuchung weist Amyloid nach.
   - **`nein`**: Wenn die Marker explizit als normwertig beschrieben werden.
   - **`fehlt`**: Wenn keine Angaben zu diesen Markern gemacht werden.

**5. Mini-Mental-Status-Test (MMSE) Ergebnis:**
   - **`<punktzahl>`**: Gib die reine Punktzahl des MMSE-Tests (auch MMST) an. Wenn "26/30" steht, gib `26` an.
   - **`-1`**: Wenn kein MMSE-Test erwähnt wird.
   - **Hinweis**: Falls mehrere MMSE-Ergebnisse vorliegen, verwende das aktuellste Ergebnis.

**JSON-AUSGABEFORMAT:**
```json
{
  "kognitive_stoerung_praesenz": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "ja|nein|fehlt"
  },
  "kognitive_stoerung_schweregrad": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "leicht|mittel|schwer|fehlt|keine_kognitive_stoerung"
  },
  "kognitive_stoerung_aetiologie": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": []
  },
  "pathologische_amyloid_biomarker": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "ja|nein|fehlt"
  },
  "mini_mental_status_test_ergebnis": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": -1
  }
}
```

**Arztbrief zur Analyse:**
{doctors_letter}
