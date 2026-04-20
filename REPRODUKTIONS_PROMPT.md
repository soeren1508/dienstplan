# Dienstplan-App — Vollständiger Reproduktions-Prompt

> Diesen Prompt an Claude übergeben, um die App von Grund auf neu zu erstellen.
> Alle Konstanten, Regeln und Konfigurationen sind vollständig enthalten.

---

## 1. Was gebaut werden soll

Eine **Progressive Web App (PWA)** für den Wochendienstplan einer Tierarztpraxis in Hamburg.
Die App läuft als **Flask/Python-Backend** auf [Render.com](https://render.com) (kostenlos).

**Zweck:**  
- Alle Mitarbeiter können den Plan im Browser lesen (kein Login)  
- Die Praxisleitung kann Dienste bearbeiten, tauschen und Abwesenheiten eintragen (PIN-geschützt)  
- Änderungen bleiben dauerhaft erhalten (GitHub-API als Persistenz-Backend)  
- Die App funktioniert auf iPhone-Homescreen wie eine native App (PWA)

---

## 2. Mitarbeiter

### Ärzte (4 Personen)
| Name | Wochenmuster |
|------|-------------|
| Ulf | Mo–Mi: `09:00–17:00`, Do+Fr: frei |
| Wilke | Mo: `FD (09–16)`, Di: `SD (12–19)`, Mi: `FD OP`, Do: `SD (12–19)`, Fr: `FD OP` |
| Florian | Mo: `SD (13–19)`, Di: `FD (09–14)`, Mi: `SD (12–19)`, Do: `FD (09–16)`, Fr: `FD (09–16)` |
| Lisa | Mo: `OP Ganztag`, Di: `FD (09–16)`, Mi: `09–12 Uhr`, Do: `OP Ganztag`, Fr: `SD (12–19)` |

### TFAs – Tiermedizinische Fachangestellte (8 Personen)
`Kristin, Deborah, Imke, Nadine, Nicolas, Alyssa, Natalie, Pauline`

**Schüler (Ausbildung):**
- Alyssa: Donnerstags Schule
- Natalie: Dienstags Schule
- Pauline: Mittwochs Schule

**Schulfrei-KWs** (kein Schultag trotz Ausbildungstag):
- Natalie: KW16, KW20
- Pauline: KW16, 29, 30, 33, 34, 43, 52
- Alyssa: KW16

**Personalveränderungen 2026:**
- Natalie und Alyssa verlassen die Praxis ab KW26 (ab dann immer `–`)
- Molly startet als Minijob KW19–27
- Matthias + Molly starten als Azubis ab KW31

---

## 3. Planungszeitraum

**KW 17–23** (April–Juni 2026), Wochentage Mo–Sa (Index 0–5).

Tage-Index: `0=Mo, 1=Di, 2=Mi, 3=Do, 4=Fr, 5=Sa`

---

## 4. Feiertage Hamburg 2026

```python
{
    date(2026, 4, 6),   # Ostermontag    (KW15 Mo)
    date(2026, 5, 1),   # Tag der Arbeit (KW18 Fr)
    date(2026, 5, 14),  # Christi Himmelfahrt (KW20 Do)
    date(2026, 5, 25),  # Pfingstmontag  (KW22 Mo)
}
```

---

## 5. Samstags-Rotation

Samstage werden direkt aus einer Excel-Datei (`Urlaubsplanung 2026.xlsx`) entnommen.
Für KW17–23:

| KW | Arzt Sa | TFA Sa |
|----|---------|--------|
| 17 | Florian | Kristin |
| 18 | Florian | Alyssa |
| 19 | Wilke   | Kristin |
| 20 | Lisa    | Imke |
| 21 | Florian | Nicolas |
| 22 | Wilke   | Nicolas |
| 23 | Lisa    | Kristin |

---

## 6. Dienst-Typen (Werte in Zellen)

### TFAs
- `FD: Anmeldung` — Frühdienst Empfang
- `FD: Behandlung` — Frühdienst Behandlung
- `FD: Assistenz Ulf` — Frühdienst Assistenz bei Dr. Ulf
- `FD: Assistenz Lisa OP` — OP-Assistenz bei Dr. Lisa (Frühdienst)
- `FD: Assistenz Wilke OP` — OP-Assistenz bei Dr. Wilke
- `FD: Anmeldung + Bestellungen` — Anmeldung + Bestellwesen
- `SD: Anmeldung` — Spätdienst Empfang
- `SD: Behandlung` — Spätdienst Behandlung
- `SD: Assistenz Ulf` — Spätdienst Assistenz bei Dr. Ulf
- `SD: Assistenz Lisa OP` — OP-Assistenz bei Dr. Lisa (Spätdienst)
- `SD: Behandlung (ab 15:30)` — Spätdienst ab 15:30 (Alyssa Fr, Pauline Do)
- `SD: Behandlung + Bestellungen` — Spätdienst + Bestellwesen
- `Dienst` — Samstagsdienst
- `Urlaub`, `Krank`, `Frei` — Abwesenheiten
- `SCHULE` — Berufsschultag
- `Abschlussprüfung` — Prüfungstage (KW23: Natalie, Alyssa Di+Mi)
- `–` — kein Dienst

Zusatz `+ Auffüllen` kann an jeden Dienst angehängt werden (Auffüllaufgabe).

---

## 7. Planungsregeln

### 7.1 Pflicht-Besetzungen

**Anmeldung:**  
Jeden Werktag muss genau eine Person FD: Anmeldung und genau eine Person SD: Anmeldung haben (wenn mindestens 1 TFA im jeweiligen Shift aktiv ist).

**Ulf-Assistenz (Mo–Mi):**  
Wenn Ulf anwesend: je 1 TFA FD: Assistenz Ulf + 1 TFA SD: Assistenz Ulf (pro Tag).

**Lisa OP (Mo + Do):**  
Wenn Lisa `OP Ganztag`: je 1 TFA FD: Assistenz Lisa OP + 1 TFA SD: Assistenz Lisa OP.

**Wilke FD OP (Mi + Fr):**  
Wenn Wilke `FD OP`: 1 TFA FD: Assistenz Wilke OP (primär Imke; in ungeraden KWs Fr ist Imke ausgenommen sofern anwesend).

### 7.2 Parität FD/SD

Das System versucht, FD- und SD-Dienste fair aufzuteilen. Warnung wenn Differenz ≥ 4.

### 7.3 Feste Rollenmuster

| Person | Tag | Gerade KW | Ungerade KW |
|--------|-----|-----------|-------------|
| Deborah | Mo–Fr | FD: Behandlung | SD: Behandlung |
| Deborah | Fr | frei (FREI_SCHUTZ) | normal |
| Kristin | Do | FD: Anmeldung | SD: Anmeldung |
| Kristin | Fr | gegenläufig zu Imke (FD wenn Imke SD, und umgekehrt) + Bestellungen |
| Nicolas | Fr | SD: Anmeldung | FD: Behandlung |
| Nadine  | Di | FD: Anmeldung | frei zu vergeben |
| Alyssa  | Fr | SD: Behandlung (ab 15:30) | SD: Behandlung (ab 15:30) |
| Pauline | Do | SD: Behandlung (ab 15:30) | SD: Behandlung (ab 15:30) |

### 7.4 Auffüllen

Die Person mit dem bisher niedrigsten Auffüll-Zähler bekommt Auffüll-Aufgaben zugeteilt (rotierendes System über alle KWs).

---

## 8. Technische Architektur

```
dienstplan/
├── app.py              ← Flask-App, API-Routen, GitHub-Persistenz
├── scheduler.py        ← Planungs-Algorithmus
├── config.py           ← Alle Konstanten (Personal, Feiertage, Rotation)
├── vacations.py        ← Urlaubsplanung aus Excel laden
├── rules.py            ← Hilfsfunktionen (get_shift, is_skip)
├── requirements.txt    ← flask, flask-cors, openpyxl, gunicorn
├── render.yaml         ← Render.com-Konfiguration
├── overrides.json      ← Manuelle Änderungen (wird über GitHub-API gespeichert)
├── vacation_overrides.json ← Manuelle Urlaubsänderungen
├── Urlaubsplanung 2026.xlsx ← Quelldatei für Urlaub + Samstags-Rotation
├── static/
│   ├── logo.png        ← App-Icon
│   ├── icon.svg        ← Icon-Variante
│   └── sw.js           ← Service Worker (PWA)
└── templates/
    └── index.html      ← Komplette Single-Page-App (HTML + CSS + JS)
```

### requirements.txt
```
flask
flask-cors
openpyxl
gunicorn
```

### render.yaml
```yaml
services:
  - type: web
    name: dienstplan
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
    envVars:
      - key: EDIT_PIN
        sync: false
      - key: GITHUB_TOKEN
        sync: false
      - key: GITHUB_REPO
        value: DEIN_GITHUB_USERNAME/dienstplan
      - key: SECRET_KEY
        generateValue: true
```

---

## 9. API-Endpunkte (Flask)

| Methode | URL | Beschreibung |
|---------|-----|-------------|
| GET | `/` | Haupt-HTML-Seite |
| GET | `/manifest.json` | PWA-Manifest |
| GET | `/api/me` | Auth-Status |
| POST | `/api/auth` | Login mit PIN |
| DELETE | `/api/auth` | Logout |
| GET | `/api/plan/<kw>` | Plan + Overrides für KW laden |
| GET | `/api/validate/<kw>` | Regelvalidierung |
| GET | `/api/validate/<kw>/suggestions` | Lösungsvorschläge |
| POST | `/api/override` | Einzelne Zelle überschreiben |
| POST | `/api/overrides/clear/<kw>` | Alle Overrides für KW löschen |
| POST | `/api/regenerate` | Plan neu berechnen |
| POST | `/api/absence` | Abwesenheit eintragen |
| POST | `/api/swap` | Zwei Dienste tauschen |
| POST | `/api/vacation-day` | Urlaubstag hinzufügen/entfernen |
| POST | `/api/apply-suggestions` | Vorschlag direkt übernehmen |

---

## 10. Frontend (index.html)

### 10.1 Ansichten
- **Wochenansicht**: Tabelle, Personen als Zeilen, Mo–Sa als Spalten
- **Tagesansicht**: Eine Spalte pro Person für den gewählten Tag (mobil-optimiert)
- **Kalender**: Mini-Kalender zum KW-Wechsel

### 10.2 Farbcodierung der Zellen
```
FD: Anmeldung          → helles Blau    #dbeafe / #1d4ed8
FD: Behandlung         → Blau
FD: Assistenz Ulf      → Lila           #ede9fe / #6d28d9
FD: Assistenz Lisa OP  → Cyan           #cffafe / #0e7490
FD: Assistenz Wilke OP → Cyan-grün
SD: Anmeldung          → Orange         #ffedd5 / #c2410c
SD: Behandlung         → Orange
SD: Assistenz Ulf      → Rosa           #fce7f3 / #9d174d
SD: Assistenz Lisa OP  → Gelb-Grün      #d9f99d / #3f6212
Dienst (Sa)            → Grün           #d1fae5 / #065f46
Urlaub                 → Grau           #f1f5f9 / #475569
SCHULE                 → Indigo         #e0e7ff / #3730a3
Krank/Frei             → Rot-Grau
–                      → Weiß / leer
```

### 10.3 Edit-Modus
- Rechts oben: Schloss-Button → PIN-Eingabe → Bearbeitungsmodus
- Im Bearbeitungsmodus: Zelle anklicken → Popup mit Freitext + Quick-Pick-Buttons
- Quick-Pick-Buttons: alle gängigen FD/SD-Rollen als Schnellauswahl

### 10.4 Spezial-Dialoge
**🤒 Abwesenheit:**
- Person + Datum + Grund (Krank/Urlaub/Frei) wählen
- Sofortige Anzeige welche Rollen unbesetzt werden

**⇄ Tausch:**
- Person A + Person B + Tag wählen
- Vorschau zeigt was getauscht wird
- Regelprüfung vor Bestätigung

**🏖 Urlaub:**
- Person + Von-Bis-Datum + Aktion (hinzufügen/entfernen)
- Löst komplette Neuplanung aus

### 10.5 Validierung & Badges
- Rote/gelbe Warndreiecke bei Regelverstoßen
- Tages-Warnung-Leiste über dem Plan
- Lösungsvorschläge als klickbare Buttons

### 10.6 FD/SD-Balance-Zeile
Im Tabellenkopf: Für jeden Tag ein farbcodiertes "FD x / SD y"-Badge  
(grün ≤ 1 Differenz, gelb 2–3, rot ≥ 4). Nur TFAs zählen, keine Ärzte.

### 10.7 Toast-Nachrichten
Nach jeder Änderung erscheint oben mittig ein grüner Toast:  
`✓ [Person] [Tag]: gespeichert`  
Bei Fehler: roter Toast mit `✗ Fehlermeldung`

### 10.8 PWA / Service Worker
- HTML wird **nie** gecacht (immer frisch vom Server)
- Nur logo.png + icon.svg im Cache (Version: `dienstplan-v3`)
- `manifest.json` mit Icons für iOS Home-Screen

---

## 11. GitHub-Persistenz

**Problem:** Render.com (Free Tier) löscht Dateien bei jedem Neustart.  
**Lösung:** `overrides.json` und `vacation_overrides.json` werden bei jeder Änderung über die **GitHub Contents API** gespeichert. Beim Start wird die aktuellste Version von GitHub geladen.

### Benötigte Umgebungsvariablen auf Render.com:
- `EDIT_PIN` — PIN für Bearbeitungsmodus (z.B. `7391`)
- `GITHUB_TOKEN` — GitHub Personal Access Token (Scope: `repo`)
- `GITHUB_REPO` — GitHub-Repository (z.B. `soeren1508/dienstplan`)
- `SECRET_KEY` — Flask Session Key (automatisch generiert von Render)

### Token erstellen:
GitHub → Settings → Developer settings → Personal access tokens (classic) → Generate new token  
→ Scope: `repo` anklicken → Token kopieren → Als `GITHUB_TOKEN` auf Render eintragen

---

## 12. overrides.json — Format

Struktur: `{ "<kw>": { "<person>": { "<di>": "<wert>" } } }`

Beispiel:
```json
{
  "17": {
    "Nicolas": { "4": "FD: Behandlung" },
    "Nadine":  { "2": "FD: Behandlung", "3": "SD: Assistenz Lisa OP + Auffüllen" }
  },
  "18": {
    "Nicolas": { "3": "SD: Behandlung" }
  }
}
```

Sonderwert `"__reset__"` → löscht einen Override (stellt generierten Wert wieder her).

---

## 13. vacation_overrides.json — Format

```json
{
  "Kristin": {
    "add":    ["2026-05-04", "2026-05-05"],
    "remove": []
  }
}
```

---

## 14. Urlaubsplanung 2026.xlsx — Aufbau

Die Excel-Datei enthält:
- Urlaubsdaten pro Person (Nachname → Vorname via Mapping)
- Samstags-Arzt- und TFA-Rotation (direkt ausgelesen)

Nachname → Vorname-Mapping:
```
Krohn → Ulf, Gädeken → Wilke, Jäger → Lisa, Grosser → Florian
Bünger → Nicolas, Herzog → Kristin, Wildenhain → Deborah
Leonhard → Imke, Engel → Nadine, Andic → Alyssa
Bormann → Pauline, Lepak → Natalie
```

---

## 15. Bekannte Sonderfälle

- **KW22 Mo** ist Pfingstmontag → Feiertag, kein Dienst für alle
- **KW18 Fr** ist Tag der Arbeit → Feiertag
- **KW20 Do** ist Christi Himmelfahrt → Feiertag
- **Florian KW22 Mi–Fr**: ECVO Congress (kein Dienst)
- **Natalie + Alyssa KW23 Di+Mi**: Abschlussprüfung
- **Natalie KW23 Mo+Sa**: Urlaub (fehlt in Excel → hartkodiert)
- **Deborah KW30 Sa**: Urlaub (fehlt in Excel → hartkodiert)
- Weitere fehlende Urlaubstage: in `VACATION_OVERRIDES` in `config.py`

---

## 16. Manuell korrigierte Zellen (KW17–23)

Diese Abweichungen vom generierten Plan wurden manuell eingetragen
und liegen in `overrides.json`:

| KW | Person | Di | Wert |
|----|--------|-----|------|
| 17 | Nicolas | 4 (Fr) | FD: Behandlung |
| 17 | Nadine | 2 (Mi) | FD: Behandlung |
| 17 | Nadine | 3 (Do) | SD: Assistenz Lisa OP + Auffüllen |
| 18 | Nicolas | 3 (Do) | SD: Behandlung |
| 18 | Natalie | 3 (Do) | FD: Behandlung |
| 19 | Deborah | 0 (Mo) | SD: Anmeldung |
| 19 | Deborah | 4 (Fr) | SD: Anmeldung |
| 19 | Nadine | 1 (Di) | FD: Anmeldung |
| 19 | Alyssa | 1 (Di) | FD: Behandlung |
| 19 | Alyssa | 4 (Fr) | SD: Behandlung |
| 19 | Pauline | 3 (Do) | SD: Behandlung (ab 15:30) + Auffüllen |
| 20 | Deborah | 0 (Mo) | FD: Anmeldung |
| 20 | Deborah | 2 (Mi) | FD: Anmeldung |
| 20 | Imke | 0 (Mo) | SD: Anmeldung |
| 20 | Imke | 1 (Di) | SD: Behandlung |
| 20 | Alyssa | 2 (Mi) | SD: Behandlung |
| 20 | Alyssa | 4 (Fr) | SD: Anmeldung |
| 21 | Nicolas | 4 (Fr) | SD: Anmeldung |
| 21 | Nadine | 2 (Mi) | FD: Behandlung |
| 21 | Nadine | 3 (Do) | SD: Assistenz Lisa OP + Auffüllen |
| 21 | Nadine | 4 (Fr) | FD: Behandlung |
| 22 | Kristin | 2 (Mi) | FD: Assistenz Ulf |
| 22 | Kristin | 3 (Do) | SD: Behandlung |
| 22 | Natalie | 3 (Do) | FD: Anmeldung |
| 22 | Pauline | 3 (Do) | SD: Behandlung (ab 15:30) + Auffüllen |
| 23 | Nicolas | 4 (Fr) | SD: Behandlung |
| 23 | Nadine | 0 (Mo) | SD: Anmeldung |
| 23 | Nadine | 4 (Fr) | FD: Behandlung |
| 23 | Pauline | 0 (Mo) | SD: Assistenz Lisa OP |
| 23 | Pauline | 3 (Do) | FD: Behandlung |

---

## 17. Deployment-Ablauf

1. GitHub-Repository erstellen (Private!)
2. Code pushen: `git push origin main`
3. Render.com: New Web Service → GitHub-Repo verbinden
4. Umgebungsvariablen eintragen: `EDIT_PIN`, `GITHUB_TOKEN`, `GITHUB_REPO`
5. Deploy starten (~3 Minuten)
6. URL an Team schicken

**Kostenlos-Tarif Hinweis:** Render.com fährt die App nach 15 min Inaktivität herunter.  
Beim nächsten Aufruf: ~30–60 Sekunden Wartezeit (Kaltstart).

---

## 18. Lokaler Start (macOS)

```bash
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Gemeinsame\ Dokumente/Flo/Praxis/Claude/dienstplan
pip install flask flask-cors openpyxl
python app.py
# → http://localhost:5050
```

---

*Erstellt: April 2026 | Tierarztpraxis Hamburg | Planungszeitraum KW17–23*
