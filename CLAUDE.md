# Dienstplan 2026 – Tierarztpraxis Hamburg

Flask-PWA zur Dienstplanung (FD/SD, Urlaub, Krank, Überstunden). Deployt auf Render (Free, Frankfurt).

## Aufbau
- `app.py` – Flask-API, Auth (`EDIT_PIN` als Render-Env-Var), Auto-Save nach GitHub
- `scheduler.py` – `generate_week(kw, vacations, auffl, krank=None)`, automatische Planung
- `config.py` – Personen, Gruppen, Muster, Feiertage, Rotationen
- `vacations.py` – liest `Urlaubsplanung 2026.xlsx` ("U" = Urlaub, "K" = Krank)
- `rules.py` – alte Regelprüfung; live genutzt wird `_validate_plan()` in `app.py`
- `templates/index.html` – komplette Oberfläche (HTML+CSS+JS in einer Datei)
- `static/sw.js` – Service Worker, cached nur statische Dateien, nie HTML/API

## Daten und Persistenz
- `overrides.json`, `vacation_overrides.json`, `overtime_rotation.json`, `dismissed_issues.json`
  werden von der App per GitHub-Contents-API auf `main` committet (Env: `GITHUB_TOKEN`).
- Auto-Save-Commits tragen `[skip render] [skip ci]`. `[skip deploy]` kennt Render NICHT.
- Manuelle Overrides haben immer Vorrang vor der Auto-Planung und dürfen nie überschrieben werden.
- Vor `git push` immer `git pull --rebase origin main` (die App committet laufend).

## Personen (Stand Okt 2026)
- Ärzte: Ulf, Wilke, Florian, Lisa (auto); Hanne (nur manuell)
- TFAs: Kristin, Deborah, Imke, Nadine, Nicolas, Alyssa (auto); Nina (manuell, Juli-Muster); Emilia (neu Nov 2026, nur manuell)
- Azubis (Anzeige): Molly, Matthias, Pauline (Pauline wird intern wie TFA geplant, `TFAS_DISPLAY_ALS_AZUBI`)
- Nicolette (Empfang) ist seit Nov 2026 ausgeschieden und entfernt; Ronja ebenso.

## Bedienung / Wünsche des Nutzers
- Zelle antippen: Schnellauswahl mit FD ▾ / SD ▾ (aufklappbar), Mitteldienst, Urlaub, Krank, „📆 Zeitraum…“.
- Abwesenheit (Krank/Urlaub/Frei/WB) auch für Zeiträume (Von/Bis, Schnellwahl Woche/2 Wochen).
- Regelprobleme sind ausgeblendet: `SHOW_RULE_ISSUES = false` in `index.html`.
- 🔄-Button lädt die neueste Version (löscht Service Worker und Caches).

## Mobil (iPhone) – gelernte Stolpersteine
- Kopfzeile mit Tagen ist eine eigene, per JS horizontal synchronisierte Tabelle (`#frozen-head-wrap`)
  außerhalb von `.table-wrap`, weil `overflow-x:auto` sonst `position:sticky` am Seitenrand verhindert.
- Die echte `<thead>` in `#table-wrap` ist mit `visibility: collapse` versteckt (liefert Spaltenbreiten).
- Kein `transform` auf `.topbar` – `.topbar-actions` (fixed) würde sonst an der Kopfzeile kleben.
- Nach Änderungen an `index.html` lokal den Flask-Server komplett neu starten (Template-Cache).
- Schärfe: kein `transform`/`filter` mit Bruchteil-Pixeln auf Text (Kopfzeile wird per `scrollLeft`
  synchronisiert, Hover-Effekte nur bei `@media (hover: hover)`), Systemschrift `-apple-system`.
- Mobil: genau 3 Tage pro Bildschirmbreite (`--daycol`), Wischen rastet tageweise ein (scroll-snap).
- Erste Spalte der eingefrorenen Kopfzeile braucht `z-index: 20` (Tages-Zellen haben 10).
- Ansicht-Modus: beim Öffnen springt die Tabelle so, dass direkt nach den Namen der heutige Tag
  beginnt (`positioniereHeute()`, einmal pro Wochenwechsel). Heute = nur blauer Rahmen, kein Hintergrund.

## Farben (Stand 06.11.2026, vom Nutzer so gewünscht)
- EINE klare Farbe pro Dienst, für Ärzte, TFAs und Azubis gleich:
  Frühdienst klares Blau (#8ec5ff), Spätdienst klares Orange (#ffb870), ganztags Grün.
  Anmeldung hat dieselbe Dienstfarbe, nur fett.
- Azubis mit „Schule ab 15:30“ / „Schule 15:30 bei …“ (Schule + danach Dienst) = Spätdienst-Farbe;
  nur „Schule“ ohne Uhrzeit ist grau.
- Keine Farben pro Arzt und keine Seitenbalken (vom Nutzer abgelehnt: zu unruhig).
- Abwesend gedämpft grau, Krank rosa mit roter Schrift. Logik: `cellClass()`/`schichtVon()` in index.html.

## Deployment
- Render-Dienst „dienstplan“, Auto-Deploy „On Commit“ muss aktiv sein (Settings → Build & Deploy).
- Bei Deploy-Fehlern zuerst https://status.render.com prüfen.
- Crewmeister-Anbindung wurde geprüft und verworfen (API nur lesend, Modul nicht gebucht).

## Planungs-Agent (neu, in Arbeit)
- Übergabe-Dokument: `docs/planer.md` – zuerst lesen, nicht den ganzen Code.
- Regelwerk-Entwurf mit offenen Fragen: `docs/regeln.md`; Muster der echten Wochen: `docs/analyse.md` (generiert).
- Code in `planner/`, Oberfläche in `static/vorschlag.js` (index.html dafür nicht lesen).
- Vorschläge nur sichtbar mit Env `VORSCHLAG_AKTIV=1` (live aktuell aus).
