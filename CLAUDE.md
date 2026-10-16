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
- TFAs: Kristin, Deborah, Imke, Nadine, Nicolas, Alyssa (auto); Nina (manuell, Juli-Muster)
- Azubis (Anzeige): Molly, Matthias, Pauline (Pauline wird intern wie TFA geplant, `TFAS_DISPLAY_ALS_AZUBI`)
- Empfang: Nicolette (Default-Muster ab 01.09.)
- Ronja ist ausgeschieden und entfernt.

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

## Deployment
- Render-Dienst „dienstplan“, Auto-Deploy „On Commit“ muss aktiv sein (Settings → Build & Deploy).
- Bei Deploy-Fehlern zuerst https://status.render.com prüfen.
- Crewmeister-Anbindung wurde geprüft und verworfen (API nur lesend, Modul nicht gebucht).
