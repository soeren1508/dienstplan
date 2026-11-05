# Planungs-Agent – Übergabe für neue Sitzungen

**Diese Datei zuerst lesen.** Sie ersetzt das erneute Durchlesen des ganzen Codes.
Stand: 05.11.2026 (Planer v1)

## Ziel
Ein Planer erstellt für eine KW einen **Vorschlag**. In der App kann man den Vorschlag
ganz, teilweise oder gar nicht übernehmen. Nichts wird ohne Klick gespeichert.
Manuelle Einträge und Urlaub/Krank/Feiertag werden nie überschrieben.

## Vorgehen (Phasen)
| # | Phase | Stand |
|---|---|---|
| 0 | Framework: Prüfstand, Analyse, Regel-Bausteine, API, Oberfläche hinter Schalter | ✅ fertig |
| 1 | Regelwerk mit dem Nutzer abstimmen → `docs/regeln.md` | ⏳ großteils ✅ (01.11.), Rest: Abschnitt D in regeln.md |
| 2 | Regeln aus `docs/regeln.md` in `planner/regeln.py` + `planner/einstellungen.py` umsetzen | ⏳ Pflichtregeln + Personen ✅, Wünsche-Gewichte offen |
| 3 | Neuer Planer `planner/loeser.py` (exakte Optimierung per DP, ohne Zusatzpakete), Standard in der App | ✅ 05.11. erste Version |
| 4 | Live schalten: Render-Env `VORSCHLAG_AKTIV=1`, später optional wöchentlicher Auto-Vorschlag | offen |

## Dateien (nur diese sind für den Planer relevant)
| Datei | Inhalt |
|---|---|
| `planner/einstellungen.py` | **Personen** (wer automatisch), feste Regeln, bevorzugte Besetzung |
| `planner/zellen.py` | Zellwert → Schicht/Rolle/Arzt/abwesend (`parse()`); Rolle = zuerst genanntes Stichwort |
| `planner/woche.py` | `Woche`-Objekt; `lade_ist_wochen()` holt echte Wochen über app.py |
| `planner/regeln.py` | Regelbausteine (`@regel`), `bewertung()` |
| `planner/planer.py` | Planer-Schnittstelle, `PLANER`-Register, `vorschlag()`, Schutz fester Zellen |
| `planner/loeser.py` | **der neue Planer**: plant eine Woche Mo–Fr, Tag für Tag, Strafpunkte oben in der Datei |
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
Achtung: Lokal immer mit `env -u GITHUB_TOKEN` starten (`planner/woche.py` macht das selbst),
sonst lädt app.py Live-Daten von GitHub und speichert Änderungen direkt auf `main`.
Achtung: „Übernehmen“ in der lokalen App schreibt in `overrides.json` → vor Commit prüfen
(`git diff overrides.json`), ggf. `git checkout overrides.json`.

## Messwerte (Prüfstand, KW 24–45)
| Planer | Treffer | Schicht | Pflichtverstöße Vorschlag | Pflichtverstöße Ist-Plan |
|---|---|---|---|---|
| baseline (alter scheduler.py), Stand 01.11. vormittags | 42 % | 57 % | 60 | 135 |
| baseline nach Regelwerk-Abstimmung (01.11.) | 41 % | 58 % | 68 | 85 (Einzelfälle über 22 Wochen) |
| **loeser** (05.11.), KW 36–45 | 42 % | 71 % | **1** | 23 |

Prüfstand ab 05.11.: verglichen werden nur Personen aus `einstellungen.AUTOMATISCH`; wer in einer
Woche gar nicht im Plan stand (z.B. Emilia vor Nov.), bleibt leer. „Treffer“ = exakt Nicolas' Wahl –
niedrig ist normal, weil es oft mehrere gleich gute Einteilungen gibt. Maßgeblich sind die Pflichtverstöße.

„Ist-Plan 135“ (alter Stand) lag v.a. an Prüffehlern (Nina/Azubis nicht gezählt, „Assistenz Lisa“ ≠ OP).
Nach Korrektur + neuen Regeln (01.11.): siehe `docs/analyse.md` Abschnitt 3 – nur noch Einzelfälle.

## Entscheidungen
- Der Plan wird von einem deterministischen Planer berechnet, nicht von einer KI.
- Vorschläge werden nicht gespeichert, sondern bei Bedarf berechnet. Gespeichert wird nur,
  was übernommen wird (als normale Overrides).
- Fest (nie änderbar): manuelle Overrides + Urlaub/Krank/Feiertag (`planer.feste_zellen`).
- Prüfstand: Planer sieht nur Abwesenheiten + Ärzte/Empfang; TFA/Azubi-Zellen werden
  geleert (kein Abschreiben). Referenzwochen KW 24–45 (von Hand fertig geplant).
- Bestehende Wochen werden nicht verändert; Auto-Vorschläge erst ab einer KW, die der Nutzer nennt.
- Alter `scheduler.py` bleibt unverändert Basis der Live-App, bis der neue Planer besser ist.
- **Geplant wird nur auf Knopfdruck und nur die angezeigte Woche** („🤖 Woche planen“). Kein automatisches
  Vorausplanen. Übernommene Zellen werden normale manuelle Einträge und sind danach fest.
- OR-Tools verworfen: Installation zu schwer für Render Free (512 MB, zieht pandas/numpy).
- FD/SD-Ausgleich zuerst über die TFA-Gruppe (so zählt die FD/SD-Zeile der App), dann über alle.
- Langzeit-Kranke (`einstellungen.LANGZEIT_KRANK`) werden in nicht-manuellen Zellen als „Krank“ eingetragen.
