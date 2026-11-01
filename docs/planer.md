# Planungs-Agent – Übergabe für neue Sitzungen

**Diese Datei zuerst lesen.** Sie ersetzt das erneute Durchlesen des ganzen Codes.
Stand: 01.11.2026

## Ziel
Ein Planer erstellt für eine KW einen **Vorschlag**. In der App kann man den Vorschlag
ganz, teilweise oder gar nicht übernehmen. Nichts wird ohne Klick gespeichert.
Manuelle Einträge und Urlaub/Krank/Feiertag werden nie überschrieben.

## Vorgehen (Phasen)
| # | Phase | Stand |
|---|---|---|
| 0 | Framework: Prüfstand, Analyse, Regel-Bausteine, API, Oberfläche hinter Schalter | ✅ fertig |
| 1 | Regelwerk mit dem Nutzer abstimmen → `docs/regeln.md` | ⏳ offen: Fragen in regeln.md beantworten |
| 2 | Regeln aus `docs/regeln.md` in `planner/regeln.py` umsetzen; Ist-Wochen sollen kaum Pflichtverstöße haben | offen |
| 3 | Neuer Planer (Constraint-Solver, z.B. OR-Tools CP-SAT) in `planner/planer.py` registrieren, am Prüfstand messen | offen |
| 4 | Live schalten: Render-Env `VORSCHLAG_AKTIV=1`, später optional wöchentlicher Auto-Vorschlag | offen |

## Dateien (nur diese sind für den Planer relevant)
| Datei | Inhalt |
|---|---|
| `planner/zellen.py` | Zellwert → Schicht/Rolle/Arzt/abwesend (`parse()`) |
| `planner/woche.py` | `Woche`-Objekt; `lade_ist_wochen()` holt echte Wochen über app.py |
| `planner/regeln.py` | Regelbausteine (`@regel`), `bewertung()` |
| `planner/planer.py` | Planer-Schnittstelle, `PLANER`-Register, `vorschlag()`, Schutz fester Zellen |
| `planner/pruefstand.py` | misst Planer gegen echte Wochen |
| `planner/analyse.py` | erzeugt `docs/analyse.md` (Muster der echten Wochen) |
| `planner/api.py` | Endpunkte `/api/vorschlag/...`, Feature-Flag |
| `static/vorschlag.js` | komplette Vorschlags-Oberfläche (Knopf 🤖, Panel, Markierung) |

**`templates/index.html` muss für die Vorschlagsfunktion nicht gelesen werden.**
Sie enthält nur ein `<script src="/static/vorschlag.js?v=N">` am Ende. Nach Änderungen
an `vorschlag.js` dort `v=` hochzählen (Cache). vorschlag.js nutzt aus index.html nur:
`currentKw`, `loadKw()`, `showToast()`, `renderView()`, `.topbar-actions`,
`td.cell[data-person][data-di]`.

In `app.py` steht nur ein kleiner Block am Ende (`_vorschlag_api.register(...)`).

## Befehle
```bash
python -m planner.pruefstand                      # Baseline, KW 24–45, eine Zeile pro KW
python -m planner.pruefstand --planer <name> --kw 36-45
python -m planner.pruefstand --details 44         # Abweichungen einer KW
python -m planner.analyse                         # docs/analyse.md neu erzeugen
VORSCHLAG_AKTIV=1 python app.py                   # App lokal mit Vorschlags-Knopf (PIN 1234)
```
Lokale Abhängigkeiten: `pip install --ignore-installed blinker -r requirements.txt`.
Achtung: „Übernehmen“ in der lokalen App schreibt in `overrides.json` → vor Commit prüfen
(`git diff overrides.json`), ggf. `git checkout overrides.json`.

## Messwerte (Prüfstand, KW 24–45)
| Planer | Treffer | Schicht | Pflichtverstöße Vorschlag | Pflichtverstöße Ist-Plan |
|---|---|---|---|---|
| baseline (alter scheduler.py) | 42 % | 57 % | 60 | 135 |

„Ist-Plan 135“ heißt: Die alten Regeln passen nicht mehr zur Praxis → Phase 1/2.

## Entscheidungen
- Der Plan wird von einem deterministischen Planer berechnet, nicht von einer KI.
- Vorschläge werden nicht gespeichert, sondern bei Bedarf berechnet. Gespeichert wird nur,
  was übernommen wird (als normale Overrides).
- Fest (nie änderbar): manuelle Overrides + Urlaub/Krank/Feiertag (`planer.feste_zellen`).
- Prüfstand: Planer sieht nur Abwesenheiten + Ärzte/Empfang; TFA/Azubi-Zellen werden
  geleert (kein Abschreiben). Referenzwochen KW 24–45 (von Hand fertig geplant).
- Alter `scheduler.py` bleibt unverändert Basis der Live-App, bis der neue Planer besser ist.
