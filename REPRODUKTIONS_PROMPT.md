# Dienstplan-App — Vollständiger Reproduktions-Prompt

> Diesen Prompt an Claude übergeben, um die App von Grund auf neu zu erstellen.
> Alle Konstanten, Regeln, Features und Konfigurationen sind vollständig enthalten.
> **Stand: April 2026**

---

## 1. Was gebaut werden soll

Eine **Progressive Web App (PWA)** für den Wochendienstplan einer Tierarztpraxis in Hamburg.  
Backend: **Flask/Python** auf [Render.com](https://render.com) (Free Tier).  
Persistenz: **GitHub Contents API** (kein Datenbank-Bedarf).

**Ziele:**
- Alle Mitarbeiter können den Plan lesen (kein Login nötig)
- Praxisleitung kann Dienste per PIN-geschütztem Bearbeitungsmodus ändern
- Änderungen überleben Server-Neustarts (GitHub als Storage)
- Native-App-Gefühl auf iPhone (PWA, kein Zoom, Bottom Sheets)

---

## 2. Mitarbeiter

### Ärzte
| Name | Mo | Di | Mi | Do | Fr | Sa |
|------|----|----|----|----|----|----|
| Ulf | 09–17 | 09–17 | 09–17 | – | – | – |
| Wilke | FD (09–16) | SD (12–19) | FD OP | SD (12–19) | FD OP | Rotation |
| Florian | SD (13–19) | FD (09–14) | SD (12–19) | FD (09–16) | FD (09–16) | Rotation |
| Lisa | OP Ganztag | FD (09–16) | 09–12 Uhr | OP Ganztag | SD (12–19) | Rotation |

### TFAs
`Kristin, Deborah, Imke, Nadine, Nicolas, Alyssa, Natalie, Pauline`

**Azubis mit Schultagen:**
- Alyssa → Do (Schulfrei-KWs: 16)
- Natalie → Di (Schulfrei-KWs: 16, 20)
- Pauline → Mi (Schulfrei-KWs: 16, 29, 30, 33, 34, 43, 52)

**Personalveränderungen 2026:**
- Natalie + Alyssa: ab KW26 nicht mehr da (alle Felder `–`)
- Molly: KW19–27 als Minijob
- Matthias + Molly: ab KW31 als Azubi-Tandem

---

## 3. Planungszeitraum & Feiertage

**KW 15–52** (Vollplan), aktiv dargestellt: **KW 17–23** (Standard-Range im Frontend).  
Wochentage: Mo–Sa (Index 0–5). So = kein Dienst.

**Feiertage Hamburg 2026:**
```python
date(2026, 4, 6),   # Ostermontag       KW15 Mo
date(2026, 5, 1),   # Tag der Arbeit    KW18 Fr
date(2026, 5, 14),  # Christi Himmelfahrt KW20 Do
date(2026, 5, 25),  # Pfingstmontag     KW22 Mo
date(2026, 10, 3),  # Tag d. Dt. Einheit KW40 Sa
date(2026, 12, 25), # 1. Weihnachtstag  KW52 Fr
date(2026, 12, 26), # 2. Weihnachtstag  KW52 Sa
```

---

## 4. Samstags-Rotation (direkt aus Excel, Ground Truth)

```python
SA_ARZT = {
  15:"Wilke", 16:"Lisa",    17:"Florian", 18:"Florian",
  19:"Wilke", 20:"Lisa",    21:"Florian", 22:"Wilke",
  23:"Lisa",  24:"Lisa",    25:"Wilke",   26:"Florian",
  27:"Lisa",  28:"Wilke",   29:"Florian", 30:"Lisa",
  31:"Wilke", 32:"Florian", 33:"Lisa",    34:"Wilke",
  35:"Florian",36:"Lisa",   37:"Wilke",   38:"Florian",
  39:"Wilke", 40:None,
  41:"Florian",42:"Lisa",   43:"Wilke",   44:"Florian",
  45:"Lisa",  46:"Wilke",   47:"Florian", 48:"Lisa",
  49:"Wilke", 50:"Florian", 51:"Lisa",    52:None,
}
SA_TFA = {
  15:"Imke",   16:"Nadine",  17:"Kristin", 18:"Alyssa",
  19:"Kristin",20:"Imke",    21:"Nicolas", 22:"Nicolas",
  23:"Kristin",24:"Imke",    25:"Alyssa",  26:None,
  27:"Nadine", 28:None,      29:"Nicolas", 30:None,
  31:"Kristin",32:"Imke",    33:"Nadine",  34:"Nicolas",
  35:None,     36:None,      37:"Kristin", 38:"Nadine",
  39:"Imke",   40:None,
  41:"Nicolas",42:None,      43:None,      44:"Kristin",
  45:"Imke",   46:"Nadine",  47:"Nicolas", 48:None,
  49:None,     50:"Kristin", 51:"Imke",    52:None,
}
```

---

## 5. Dienst-Typen (Zellwerte)

### TFA-Dienste
- `FD: Anmeldung`, `SD: Anmeldung`
- `FD: Behandlung`, `SD: Behandlung`
- `FD: Springer`, `SD: Springer` ← **neu, teal Farbe**
- `FD: Assistenz Ulf`, `SD: Assistenz Ulf`
- `FD: Assistenz Lisa OP`, `SD: Assistenz Lisa OP`
- `FD: Assistenz Wilke OP`
- `SD: Behandlung (ab 15:30)` (Alyssa Fr, Pauline Do)
- `Dienst` (Samstag)
- `Urlaub`, `Krank`, `Frei`, `Frei (ÜS-Abbau)` ← ÜS-Abbau-Freitag
- `SCHULE`, `Abschlussprüfung`
- `–` (kein Dienst)

**Hinweis-Separator:** `"FD: Behandlung || Freitext"` → Zelle zeigt Dienst + 📝-Notiz.  
Der `_strip_note(val)`-Helper trennt den Note-Teil vor Validierungen ab.

**Auffüllen:** Suffix `+ Auffüllen` an beliebigen Dienst anhängbar (rotierendes System).

---

## 6. Planungsregeln (`_validate_plan`)

1. **Anmeldung** – je 1 FD + 1 SD pro Tag (wenn ≥1 TFA im jeweiligen Shift aktiv)
2. **Assistenz Ulf** (Mo–Mi) – wenn Ulf da: 1 FD + 1 SD Assistenz Ulf
3. **Assistenz Lisa OP** (Mo + Do) – wenn Lisa OP Ganztag: 1 FD + 1 SD Assistenz Lisa OP
4. **Assistenz Wilke OP** (Mi + Fr) – wenn Wilke FD OP: 1 TFA FD Assistenz Wilke OP
5. **FD/SD-Parität** – Warnung wenn Differenz ≥ 4 (TFAs only)

**Feste Rollenmuster:**
| Person | Regel |
|--------|-------|
| Deborah | gerade KW → FD:Beh, ungerade → SD:Beh; Fr gerade KW frei |
| Kristin | Do: FD-Anm (gerade) / SD-Anm (ungerade); Fr: gegenläufig zu Imke + Bestellungen |
| Nicolas | Fr: SD-Anm (gerade) / FD:Beh (ungerade) |
| Nadine | Di: FD-Anm (gerade) |
| Alyssa | Fr: SD:Beh (ab 15:30) |
| Pauline | Do: SD:Beh (ab 15:30) |

---

## 7. Überstunden-Abbau-Logik (`_check_overtime`)

Wird ausgelöst wenn:
- Mindestens 1 Arzt abwesend (Urlaub/Krank) an einem Tag
- ≥ 4 TFAs aktiv an diesem Tag

**Simulation:** Kopie des Plans → TFA auf `Frei (ÜS-Abbau)` → `_validate_plan()` → nur vorschlagen wenn keine neuen Regelverstöße entstehen.

**Assistenz-Ausschluss:** Wer Ulf/Lisa/Wilke assistiert, darf nicht vorgeschlagen werden.

**Anmeldungs-Swap:** Wenn der Kandidat Anmeldung hat, wird geprüft ob eine Behandlungs-Person im gleichen Shift die Anmeldung übernehmen kann → dann Swap anbieten.

**Faire Rotation:** `overtime_rotation.json` zählt wie oft jede Person vorgeschlagen wurde → wer am wenigsten dran war, wird zuerst vorgeschlagen.

---

## 8. Technische Architektur

```
dienstplan/
├── app.py                   ← Flask-App, API-Routen, GitHub-Persistenz, Auth
├── scheduler.py             ← Planungs-Algorithmus (generate_week)
├── config.py                ← Alle Konstanten (Personal, Feiertage, Rotation, Overrides)
├── vacations.py             ← Excel-Urlaubsplanung laden
├── rules.py                 ← Hilfsfunktionen (get_shift, is_skip)
├── requirements.txt
├── render.yaml
├── overrides.json           ← Zell-Overrides (GitHub-persistiert)
├── vacation_overrides.json  ← Urlaubs-Overrides (GitHub-persistiert)
├── overtime_rotation.json   ← ÜS-Vorschlagszähler (GitHub-persistiert)
├── Urlaubsplanung 2026.xlsx
├── static/
│   ├── logo.png
│   └── sw.js                ← Service Worker (PWA, HTML nie gecacht)
└── templates/
    └── index.html           ← Single-Page-App (HTML + CSS + JS, ~2600 Zeilen)
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
        value: soeren1508/dienstplan
      - key: SECRET_KEY
        generateValue: true
```

---

## 9. API-Endpunkte

| Methode | URL | Auth | Beschreibung |
|---------|-----|------|-------------|
| GET | `/` | – | HTML-Seite |
| GET | `/manifest.json` | – | PWA-Manifest |
| GET | `/api/me` | – | Auth-Status |
| POST | `/api/auth` | – | Login mit PIN |
| DELETE | `/api/auth` | – | Logout |
| GET | `/api/plan/<kw>` | – | Plan + Overrides für KW |
| GET | `/api/validate/<kw>` | – | Regelvalidierung |
| GET | `/api/validate/<kw>/suggestions` | – | Lösungsvorschläge |
| POST | `/api/override` | ✓ | Einzelzelle überschreiben |
| POST | `/api/overrides/clear/<kw>` | ✓ | KW-Overrides löschen |
| POST | `/api/regenerate` | ✓ | Plan neu berechnen |
| POST | `/api/absence` | ✓ | Abwesenheit eintragen |
| POST | `/api/swap` | ✓ | Dienste tauschen |
| POST | `/api/vacation-day` | ✓ | Urlaubstag hinzufügen/entfernen |
| GET | `/api/overtime/<kw>` | – | ÜS-Abbau-Vorschläge laden |
| POST | `/api/overtime/apply` | ✓ | ÜS-Abbau eintragen (+ opt. Swap) |

**`/api/overtime/apply` Body:**
```json
{ "kw": 21, "di": 2, "person": "Kristin",
  "swap": { "person": "Nadine", "value": "FD: Anmeldung" } }
```
`swap` kann `null` sein (kein Anmeldungs-Tausch nötig).

---

## 10. Auth & Session (wichtig!)

```python
# SECRET_KEY deterministisch ableiten → überlebt Render-Neustarts
_key_base = os.environ.get("SECRET_KEY") or ("dienstplan-2026-" + EDIT_PIN)
app.secret_key = hashlib.sha256(_key_base.encode()).hexdigest()

app.config.update(
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8),
    SESSION_COOKIE_SAMESITE    = "Lax",
    SESSION_COOKIE_HTTPONLY    = True,
)
```

**Warum deterministisch?** Render triggert nach jedem GitHub-Push (= nach jeder Änderung) einen Auto-Deploy. Mit `secrets.token_hex(32)` wäre die Session nach der ersten Änderung sofort ungültig → 403 bei der nächsten Aktion.

```python
# Login:
session["authenticated"] = True
session.permanent = True   # 8h Lifetime
```

---

## 11. Frontend (index.html) – Struktur & Features

### 11.1 Viewport & Touch
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0,
  maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
```
- `user-scalable=no` → kein versehentliches Zoomen
- `-webkit-tap-highlight-color: transparent`
- `overscroll-behavior: none` → kein iOS-Bounce
- Alle Inputs: `font-size: 16px` auf Mobile → verhindert iOS-Auto-Zoom

### 11.2 Topbar (2-Zeilen-Layout auf Mobile)

**Desktop:** Alle Buttons in einer Zeile (via `display: contents`).

**Mobile (≤640px):**
- **Zeile 1:** 🐾 Logo · KW-Nav · 📅 Kalender · Woche/Tag-Toggle · 🔒 Bearbeiten
- **Zeile 2** (`topbar-actions`): 🤒 Abwesenheit · ⇄ Tausch · 🏖 Urlaub · ⏱ ÜS-Abbau · ↩ Reset · ⟳ Neu (edit-only)

```html
<div class="topbar">
  <div class="topbar-row1">  <!-- display:contents auf Desktop -->
    <!-- Logo, KW-Nav, Kalender, View-Toggle, Lock -->
  </div>
  <div class="topbar-actions">  <!-- display:contents Desktop / flex Mobile -->
    <!-- Action-Buttons mit .btn-icon + .btn-lbl -->
  </div>
</div>
```

### 11.3 Farbcodierung der Zellen

```
.c-anmeldung       #e0e7ff / #3730a3   Indigo   – FD/SD Anmeldung
.c-fd-beh          #bfdbfe / #1e3a8a   Blau     – FD: Behandlung
.c-sd-beh          #fed7aa / #9a3412   Orange   – SD: Behandlung
.c-springer        #f0fdfa / #134e4a   Teal     – FD/SD: Springer ← neu
.c-assistenz-ulf   #a5f3fc / #0e7490   Cyan     – Assistenz Ulf
.c-assistenz-lisa  #c4b5fd / #5b21b6   Lila     – Assistenz Lisa
.c-assistenz-wilke #86efac / #166534   Mint     – Assistenz Wilke
.c-urlaub          #e2e8f0 / #64748b   Grau
.c-krank           #fee2e2 / #991b1b   Rot
.c-feiertag        #fef9c3 / #854d0e   Gelb
.c-schule          #ede9fe / #5b21b6   Violett
.c-dienst          #d1fae5 / #065f46   Grün     – Samstag
.c-frei            #f8fafc / #94a3b8   Hellgrau
.c-pruefung        #fce7f3 / #9d174d   Pink
.c-op              #cffafe / #164e63   Cyan     – OP / Sonderzeiten
.c-springer        #f0fdfa / #134e4a   Teal     – FD/SD Springer
```

### 11.4 Quick-Picks (Edit-Popup)

```javascript
const QUICK_PICKS = [
  { label: "FD: Behandlung",        cls: "qp-fd" },
  { label: "SD: Behandlung",        cls: "qp-sd" },
  { label: "FD: Springer",          cls: "qp-springer" },  // neu
  { label: "SD: Springer",          cls: "qp-springer" },  // neu
  { label: "FD: Anmeldung",         cls: "qp-fd" },
  { label: "SD: Anmeldung",         cls: "qp-sd" },
  { label: "FD: Assistenz Lisa OP", cls: "qp-fd" },
  { label: "SD: Assistenz Lisa OP", cls: "qp-sd" },
  { label: "FD: Assistenz Ulf",     cls: "qp-fd" },
  { label: "SD: Assistenz Ulf",     cls: "qp-sd" },
  { label: "Urlaub",                cls: "qp-urlaub" },
  { label: "–",                     cls: "" },
];
```

### 11.5 Edit-Popup (Zelle bearbeiten)

- Freitext-Input + Quick-Pick-Buttons
- **📝 Hinweis-Feld** (Textarea): Freitext-Notiz pro Zelle
- Wert wird als `"FD: Behandlung || Notiztext"` gespeichert
- Zelle zeigt Dienst + `<span class="cell-note">📝 Notiz</span>`
- `_strip_note(val)` trennt Note vor Validierungen

**Mobile:** Edit-Popup wird zum Bottom Sheet (von unten, volle Breite, Zieh-Indikator, `env(safe-area-inset-bottom)`)

### 11.6 Modals (alle Bottom Sheets auf Mobile)

| Modal | Trigger | Funktion |
|-------|---------|----------|
| 🔒 PIN | Schloss-Button | Bearbeitungsmodus freischalten |
| 🤒 Abwesenheit | Topbar-Button | Person + Tag + Grund (Krank/Urlaub/Frei) |
| ⇄ Tausch | Topbar-Button | Person A + Person B + Tag, mit Vorschau + Regelcheck |
| 🏖 Urlaub (Picker) | Topbar-Button | Action-Sheet: Urlaub anpassen ODER ÜS-Frei |
| 🏖 Urlaub anpassen | Picker → Option 1 | Von-Bis-Datum, hinzufügen/entfernen |
| ⏱ Frei (ÜS-Abbau) | Picker → Option 2 | Person + Datum → Frei (ÜS-Abbau) eintragen |
| ⏱ ÜS-Abbau | Topbar-Button (edit) | Automatische Vorschläge anzeigen |
| 📅 Kalender | 📅-Button | Mini-Kalender zur KW-Navigation (CSS Grid, kein Table) |

**Vac-Picker (Action Sheet):** Tippen auf 🏖 öffnet zuerst Auswahlsheet:
```
┌─────────────────────────────────┐
│  Was möchtest du tun?           │
│  🏖 Urlaub anpassen             │
│  ⏱ Frei (Überstunden-Abbau)     │
│  Abbrechen                      │
└─────────────────────────────────┘
```

### 11.7 ÜS-Abbau-Feature

- **Automatisch** (⏱-Button in Topbar, nur im Bearbeitungsmodus):
  - Zeigt rotes Badge mit Anzahl der Vorschläge
  - Modal mit Liste: Tag · Arzt abwesend · TFA-Anzahl · Vorgeschlagene Person · Rotationsstand
  - „Eintragen"-Button → setzt `Frei (ÜS-Abbau)`, optional mit Anmeldungs-Swap

- **Manuell** (🏖 → ⏱ Frei (ÜS-Abbau)):
  - Person + Datum wählen
  - Konvertiert Datum → KW + Wochentag-Index
  - Ruft `/api/overtime/apply` auf

### 11.8 Kalender

CSS-Grid-basiert (kein `<table>`), verhindert Overflow-Probleme:
```css
.cal-grid {
  display: grid;
  grid-template-columns: 20px repeat(7, 1fr);
  width: 100%;
  box-sizing: border-box;
}
```
Panel: `width: 230px; overflow: hidden; position: fixed;`

### 11.9 Weitere Features

- **Sticky Personenspalte:** `td.person-name { position: sticky; left: 0; z-index: 4; }`
- **FD/SD-Balance-Zeile** im Tabellenkopf (grün/gelb/rot)
- **Toast-Nachrichten** (oben mittig, 4 Sekunden, ✓/✗ Prefix)
- **Tagesansicht** (Card-Layout, per Wischgeste navigierbar)
- **Person-Filter** (Dropdown, versteckt auf Mobile)
- **Legende** (aufklappbar, alle Farben erklärt)
- **Heute-Badge** im Kalender (roter ausgefüllter Kreis)

---

## 12. GitHub-Persistenz

**Problem:** Render.com Free Tier löscht Dateien bei Neustart.  
**Lösung:** Drei JSON-Dateien werden bei jeder Änderung via GitHub Contents API gespeichert und beim Start geladen.

```python
def _github_push(filename, content, message):
    # GET aktuellen SHA → PUT mit neuem Inhalt
    ...

def _sync_from_github():
    # Lädt overrides.json, vacation_overrides.json, overtime_rotation.json
    ...
```

**Gespeicherte Dateien:**
- `overrides.json` – Zell-Overrides
- `vacation_overrides.json` – Urlaubs-Korrekturen
- `overtime_rotation.json` – ÜS-Vorschlagszähler

**Benötigte Env-Vars auf Render.com:**
| Variable | Wert |
|----------|------|
| `EDIT_PIN` | z.B. `7391` |
| `GITHUB_TOKEN` | GitHub Personal Access Token (Scope: `repo`) |
| `GITHUB_REPO` | `soeren1508/dienstplan` |
| `SECRET_KEY` | Von Render auto-generiert (oder selbst gesetzt) |

---

## 13. overrides.json – Format

```json
{
  "17": {
    "Nicolas": { "4": "FD: Behandlung" },
    "Nadine":  { "2": "FD: Behandlung || Bitte früh kommen" }
  }
}
```

`"__reset__"` als Wert → Override löschen (generierten Wert wiederherstellen).  
Hinweis-Separator: `" || "` (Leerzeichen-Pipe-Leerzeichen).

---

## 14. vacation_overrides.json – Format

```json
{
  "Kristin": { "add": ["2026-05-04"], "remove": [] }
}
```

---

## 15. overtime_rotation.json – Format

```json
{ "Kristin": 2, "Nadine": 1, "Imke": 0, "Nicolas": 3 }
```

Zählt wie oft jede Person für ÜS-Abbau vorgeschlagen wurde. Wer am seltensten dran war, kommt zuerst.

---

## 16. config.py – Wichtige Konstanten

```python
SCHULTAGE = { "Alyssa": [3], "Natalie": [1], "Pauline": [2], "Molly": [3], "Matthias": [1] }

PERSONAL_EXIT  = { "Natalie": 26, "Alyssa": 26 }
PERSONAL_ENTRY = {
    "Molly_mini":  {"kw_start": 19, "kw_end": 27, "mode": "minijob"},
    "Matthias":    {"kw_start": 31, "mode": "tandem"},
    "Molly_azubi": {"kw_start": 31, "mode": "tandem"},
}

VACATION_OVERRIDES = [   # Urlaubstage die in Excel fehlen
    ("Natalie", 23, 0), ("Natalie", 23, 5), ("Alyssa", 23, 5),
    ("Florian", 24, 5), ("Kristin", 25, 5), ("Nicolas", 27, 5),
    ("Imke", 28, 5), ("Nicolas", 28, 5), ("Wilke", 30, 5),
    ("Deborah", 30, 5), ("Pauline", 31, 5), ("Nadine", 34, 5),
    ("Imke", 37, 5), ("Kristin", 21, 4),
]

PRUEFUNGSTAGE = [
    ("Natalie", 23, 1), ("Natalie", 23, 2),
    ("Alyssa",  23, 1), ("Alyssa",  23, 2),
]

NOTDIENSTE = [
    ("Florian", "Kristin", 36, 2),   # KW36 Mi
    ("Wilke",   "Imke",    49, 3),   # KW49 Do
]

ECVO_TAGE = [
    ("Florian", 22, 2), ("Florian", 22, 3), ("Florian", 22, 4),
]

SPEZIAL = [
    ("Florian", 52, 3, "FD (09–16)"),   # Heiligabend
    ("Ulf",     15, 3, "09:00–17:00"),  # KW15 Do
]
```

---

## 17. Bekannte Sonderfälle

- **KW22 Mo**: Pfingstmontag → Feiertag
- **KW18 Fr**: Tag der Arbeit → Feiertag
- **KW20 Do**: Christi Himmelfahrt → Feiertag
- **Florian KW22 Mi–Fr**: ECVO Congress
- **Natalie + Alyssa KW23 Di+Mi**: Abschlussprüfung
- **Natalie KW23 Mo+Sa**: Urlaub (fehlt in Excel → in VACATION_OVERRIDES)
- **Diverse Sa-Urlaube**: In VACATION_OVERRIDES hartkodiert

---

## 18. PWA / Service Worker (sw.js)

```javascript
const CACHE_NAME = "dienstplan-v3";
const STATIC_ASSETS = ["/static/logo.png"];

// HTML: NIEMALS cachen (immer fresh vom Server)
// Statische Assets: Cache-First
```

---

## 19. Deployment

```bash
# 1. Lokaler Test
cd dienstplan
pip install flask flask-cors openpyxl
python app.py  # → http://localhost:5050

# 2. GitHub Push
git add -A && git commit -m "Update" && git push

# 3. Render.com
# New Web Service → GitHub-Repo verbinden
# Env-Vars eintragen: EDIT_PIN, GITHUB_TOKEN, GITHUB_REPO
# Deploy (~ 3 min)
```

**Render Free Tier:** Server schläft nach 15 min → Kaltstart ~30–60 Sek.  
**Auto-Deploy:** Jeder GitHub-Push löst Render-Redeploy aus. Deshalb deterministischer `SECRET_KEY`!

---

## 20. Häufige Fehler & Lösungen

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| `NameError: _generate_all` | Funktion vor Definition aufgerufen | `_sync_from_github()` + `_generate_all()` NACH deren Definition aufrufen |
| `403 Nicht autorisiert` nach erster Änderung | `secrets.token_hex(32)` als secret_key → nach Auto-Deploy ungültig | Deterministischen Key verwenden (aus PIN ableiten) |
| Git push rejected (remote ahead) | GitHub-API pusht overrides.json → remote ist weiter | `git stash && git pull --rebase && git stash pop && git push` |
| Kalender zu breit / overflow | `<table>` in `position:fixed` = unzuverlässig | CSS Grid: `grid-template-columns: 20px repeat(7, 1fr)` |
| iOS Zoom bei Input | `font-size < 16px` auf Input | Alle Inputs im Mobile-CSS: `font-size: 16px !important` |
| Session verliert sich auf Handy | `session.permanent = False` | `session.permanent = True` + `PERMANENT_SESSION_LIFETIME = 8h` |

---

*Stand: April 2026 · Tierarztpraxis Hamburg · Repo: soeren1508/dienstplan*
