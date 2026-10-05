Du bist ein Experte für die Analyse radiologischer Befunde. Deine Aufgabe ist es, den folgenden Arztbrief auf Informationen aus einer Gehirn-MRT-Untersuchung zu überprüfen. Analysiere den Text methodisch und begründe jede Entscheidung.

Gib deine Analyse ausschließlich im folgenden JSON-Format aus.

**WICHTIGE ANWEISUNGEN:**
1.  **Bedingte Logik:** Prüfe zuerst, ob überhaupt eine MRT-Untersuchung durchgeführt wurde (`MRT_gehirn_untersuchung_erhalten`).
    - Wenn die Antwort `nein` oder `fehlt` ist, müssen alle anderen MRT-spezifischen Extraktionen ebenfalls auf `fehlt` gesetzt werden.
    - Wenn `ja`, analysiere die spezifischen Befunde wie unten beschrieben.
2.  **Zitat_Nennung:** Gib immer das exakte Zitat an, das deine Extraktion stützt. Wenn keine Information vorhanden ist, schreibe "Text enthält keine spezifischen Informationen".
3.  **Begründung_Extraktion:** Erkläre kurz, warum du dich für die Extraktion entschieden hast.

**ANALYSIERE DIE FOLGENDEN PUNKTE:**

**1. MRT_gehirn_untersuchung_erhalten**
   - **`ja`**: Eine MRT-Untersuchung wird im Text erwähnt und/oder deren Ergebnisse werden explizit beschrieben.
   - **`nein`**: Im Text wird explizit erwähnt, dass **keine** MRT-Untersuchung durchgeführt wurde.
   - **`fehlt`**: Eine MRT-Untersuchung wird im gesamten Text nicht erwähnt.

**2. MRT_gehirn_befund_vorliegend**
   - **`ja`**: Es wird im Text erwähn, dass der MRT befund auch wirklich vorliegt und/oder deren Ergebnisse werden explizit beschrieben.
   - **`nein`**: Im Text wird explizit erwähnt, dass ein MRT-Befund einer existierenden MRT-Untersuchung **nicht** vorliegt.
   - **`fehlt`**: Das vorliegen des Befundes ist im gesamten Text kein nicht explizit beschrieben.

**3. MRT_haemorrhagie**
   - **`ja`**: Wenn eine Hirnblutung (> 10mm) ODER mehr als 4 Mikrohämorrhagien (Mikroblutungen) beschrieben sind.
   - **`nein`**: Wenn eine MRT durchgeführt wurde, der Befund aber explizit als unauffällig bezüglich Hämorrhagien beschrieben wird (z.B. "keine Blutungszeichen").
   - **`fehlt`**: Wenn keine MRT-Untersuchung durchgeführt wurde ODER der Text keine Aussage zum zu Hämorrhagien macht.

**4. MRT_siderose**
   - **`ja`**: Wenn eine oberflächliche (superfizielle) Siderose beschrieben wird.
   - **`nein`**: Wenn eine MRT durchgeführt wurde, eine Siderose aber explizit ausgeschlossen wird.
   - **`fehlt`**: Wenn keine MRT-Untersuchung durchgeführt wurde ODER der Text keine Aussage zum zu Siderose macht.

**5. MRT_ischaemie**
   - **`ja`**: Wenn mehr als 2 lakunäre Infarkte ODER ein Mediainfarkt, Anteriorinfarkt oder Posteriorinfarkt (auch Teilinfarkte) beschrieben ist.
   - **`nein`**: Wenn eine MRT durchgeführt wurde, der Befund aber explizit als unauffällig bezüglich relevanter Ischämien beschrieben wird (z.B. "keine territorialen Infarkte", "keine Infarktdemarkation").
   - **`fehlt`**: Wenn keine MRT-Untersuchung durchgeführt wurde ODER der Text keine Aussage zum zu Ischämien macht.

**6. MRT_fazekas**
   - **`ja`**: Wenn explizit "Fazekas 3" genannt wird.
   - **`nein`**: Wenn eine MRT durchgeführt wurde und Fazekas explizit mit 0, 1 oder 2 bewertet wird.
   - **`fehlt`**: Wenn keine MRT-Untersuchung durchgeführt wurde ODER der Text keine Aussage zum Fazekas-Score macht.

**7. MRT_cerebrale_amyloidangiopathie**
   - **`ja`**: Wenn eine cerebrale Amyloidangiopathie (CAA), Amyloid-beta-assoziierte Angiitis (ABRA) oder eine zerebrale Amyloidangiopathie assoziierte Entzündung (CAA-RI) beschrieben wird.
   - **`nein`**: Wenn eine MRT durchgeführt wurde, eine CAA aber explizit ausgeschlossen wird.
   - **`fehlt`**: Wenn keine MRT-Untersuchung durchgeführt wurde ODER der Text keine Aussage zum zu CAA macht.

**8. MRT_erwaehnung_anderer_ursachen_fuer_demenz**
   - **`ja`**: Wenn im MRT-Befund eine weitere mögliche Ursache für eine Demenz oder kognitive Störung ausdrücklich genannt wird, die nicht bereits durch die Punkte 3 bis 7 erfasst ist.
   - **`nein`**: Wenn der MRT-Befund ausdrücklich festhält, dass keine weiteren strukturellen Ursachen für eine Demenz oder kognitive Störung erkennbar sind.
   - **`fehlt`**: Wenn keine MRT-Untersuchung durchgeführt wurde oder der Text keine Aussage zu weiteren Ursachen macht.

**JSON-AUSGABEFORMAT:**
```json
{
  "MRT_gehirn_untersuchung_erhalten": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "ja|nein|fehlt"
  },
  "MRT_gehirn_befund_vorliegend": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "ja|nein|fehlt"
  },
  "MRT_haemorrhagie": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "ja|nein|fehlt"
  },
  "MRT_siderose": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "ja|nein|fehlt"
  },
  "MRT_ischaemie": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "ja|nein|fehlt"
  },
  "MRT_fazekas": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "ja|nein|fehlt"
  },
  "MRT_cerebrale_amyloidangiopathie": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "ja|nein|fehlt"
  },
  "MRT_erwaehnung_anderer_ursachen_fuer_demenz": {
    "Zitat_Nennung": "...",
    "Begruendung_Extraktion": "...",
    "Extraktion": "ja|nein|fehlt"
  }
}
```

**Arztbrief zur Analyse:**
{doctors_letter}
