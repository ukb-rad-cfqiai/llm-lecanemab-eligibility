Du bist ein Experte für die Analyse medizinischer Dokumente mit Fokus auf systemische Erkrankungen und Medikation. Deine Aufgabe ist es, den folgenden Arztbrief sorgfältig zu prüfen und für jede der unten genannten Kategorien die spezifischen Erkrankungen oder Medikationen zu identifizieren.

Gib deine Analyse ausschließlich im folgenden JSON-Format aus.

**WICHTIGE ANWEISUNGEN:**
1.  **Extraktion als Liste:** Wähle für jede Kategorie **eine oder mehrere** der unter "Gültige Optionen" aufgeführten Optionen. Gib das Ergebnis als eine Liste von Zeichenketten (Strings) aus. Die Schreibweise, inklusive Abkürzungen in Klammern, muss exakt übernommen werden.
2.  **Keine Information:** Wenn für eine Kategorie keine relevante Information im Text gefunden wird, gib eine **leere Liste** `[]` zurück.
3.  **Zitat_Nennung:** Gib immer das exakte Zitat (oder die exakten Zitate) aus dem Text an, das/die deine Extraktion(en) stützt. Wenn keine Information vorhanden ist, schreibe "Text enthält keine Informationen".
4.  **Begründung_Extraktion:** Erkläre kurz und präzise, warum du dich basierend auf dem Zitat für die entsprechenden Optionen entschieden hast. Wenn mehrere Einträge gefunden werden, sollte die Begründung alle Funde abdecken.

**ANALYSIERE DIE FOLGENDEN PUNKTE:**

**1. immunologische_erkrankung** Identifiziere die spezifische(n) Autoimmunerkrankung(en). **Achtung:** Hashimoto-Thyreoiditis zählt hier nicht dazu.
    *   **Gültige Optionen:** "Morbus Bechterew (M. Bechterew)", "Morbus Crohn (M. Crohn)", "Colitis ulcerosa (CU)", "Psoriasis-Arthritis (PsA)", "Rheumatoide Arthritis (RA)", "SAPHO-Syndrom", "Systemischer Lupus erythematodes (SLE)", "Multiple Sklerose (MS)", "Sjoegren-Syndrom", "Sklerodermie", "Vaskulitis", "Autoimmunhepatitis (AIH)", "Chronische Polyarthritis (cP)", "Dermatomyositis", "Mischkollagenose"
    *   **Sonderregel:** Falls du andere immunologische Erkrankungen findest, die nicht explizit in den Optionen gelistet sind, füge den **exakten Namen der immunologischen Erkrankungen** zur Extraktionsliste hinzu.
    *   **Achtung:** Du sollst nicht eigenständig eine Differentialdiagnose erstellen. Es geht um explizite Nennungen von immunologische Erkrankungen durch den Behandler. Mögliche, aber als weniger wahrscheinliche Differentialdiagnosen, beschrieben durch den Behandler, sollst du ignorieren.
   
**2. gerinnungsstoerung** Identifiziere die spezifische(n) Gerinnungsstörung(en).
    *   **Gültige Optionen:** "Thrombophilie", "Haemophilie A", "Haemophilie B", "Von-Willebrand-Syndrom (VWS)", "Thrombozytopenie (leicht)", "Thrombozytopenie (schwer)", "Thrombozythaemie (leicht)", "Thrombozythaemie (schwer)", "Faktor-V-Leiden-Mutation (FVL)", "Protein-C-Mangel", "Antiphospholipid-Syndrom (APS)", "Disseminierte intravasale Gerinnung (DIC)"
    *   **Sonderregel:** Falls du andere Gerinnungsstörungen findest, die nicht explizit in den Optionen gelistet sind, füge den **exakten Namen der Gerinnungsstörung** zur Extraktionsliste hinzu.
    *   **Achtung:** Du sollst nicht eigenständig eine Differentialdiagnose erstellen. Es geht um explizite Nennungen von immunologische Erkrankungen durch den Behandler. Mögliche, aber als weniger wahrscheinliche Differentialdiagnosen, beschrieben durch den Behandler, sollst du ignorieren.
   
**3. immunosuppression** Identifiziere die spezifische(n) immunmodulierende(n) Medikation(en).
    *   **Gültige Optionen:** "Methotrexat (MTX)", "Cortison", "Prednisolon", "Methylpredisolon", "Prednison", "Dexamethason", "Azathioprin (AZA)", "Cyclosporin (CSA)", "Tacrolimus", "Mycophenolatmofetil (MMF)", "Infliximab", "Adalimumab", "Etanercept", "Rituximab", "Cyclophosphamid (CTX)", "Orale Glukokortikoide", "Systemische Glukokortikoide"
    *   **Sonderregel:** Falls du andere Medikamente findest, die auf "-mab" enden und nicht explizit in den Optionen gelistet sind (z.B. "Denosumab"), füge den **exakten Namen des Medikaments** zur Extraktionsliste hinzu.
    
**4. antikoagulation** Identifiziere das/die spezifische(n) Medikament(e) zur Antikoagulation.
    *   **Gültige Optionen:** "Marcumar (Phenprocoumon)", "Eliquis (Apixaban)", "Xarelto (Rivaroxaban)", "Lixiana (Edoxaban)", "Pradaxa (Dabigatran)", "Heparin", "Clexane (Enoxaparin)", "Warfarin"
 
**JSON-AUSGABEFORMAT:**
```json
{
  "immunologische_erkrankung": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": []
  },
  "gerinnungsstoerung": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": []
  },
  "immunosuppression": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": []
  },
  "antikoagulation": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": []
  }
}
```
**Arztbrief zur Analyse:**
{doctors_letter}
