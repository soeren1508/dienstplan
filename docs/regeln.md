# Regelwerk

Grundlage: die von Nicolas manuell geplanten Wochen (KW 24–46, Schwerpunkt KW 36–46)
und die Abstimmung mit der Praxis am 01.11. und 05.11.2026.
Umsetzung: Personen/Vorlieben in `planner/einstellungen.py`, Prüfregeln in `planner/regeln.py`.

Status: ✅ bestätigt · ❓ offen · ✏️ aus den Daten abgeleitet, noch nicht ausdrücklich bestätigt

## Grundsätze
- ✅ Die bestehenden Wochen werden **nicht** verändert. Das Regelwerk gilt nur für künftige Vorschläge.
- ✅ Ab welcher KW automatisch vorgeschlagen wird, gibt die Praxis vor (**nicht** die kommende Woche).
- ✅ Manuelle Einträge haben immer Vorrang; Urlaub/Krank/Feiertag werden nie überschrieben.
- ✅ Schreibweise der Zellen wie bei Nicolas: `FD: Anmeldung`, `SD: Assistenz Ulf`,
  `FD: Assistenz Lisa` (auch bei OP), `FD: Assistenz Wilke`, `FD: Springer`, `FD: Behandlung`.

## A. Personen
| Person | Regel | Status |
|---|---|---|
| Nicolette | ausgeschieden (Nov 2026), aus dem Plan entfernt | ✅ |
| Hanne | wird nicht automatisch verplant (läuft mit Florian mit) | ✅ |
| Nina | wird ganz normal verplant; **freitags nie** | ✅ |
| Deborah | gerade KW Frühdienst, ungerade KW Spätdienst; gerade KW freitags frei | ✅ |
| Alyssa | langzeitkrank, fällt länger aus → nicht verplanen | ✅ |
| Kristin | krankgeschrieben (voraussichtlich bis ca. Anfang Dezember), bleibt als „Krank“ im Plan | ✅ |
| Emilia | wird normal verplant (Behandlung, OP, Assistenz Lisa/Wilke/Florian); **noch nicht** Anmeldung, **noch nicht** bei Ulf | ✅ 05.11. |
| Emilia | jede Woche 1 Tag frei: **ungerade KW Freitag** ✅ (KW 45 = Fr 06.11.), gerade KW fester anderer Tag ❓ | ⏳ |
| Pauline | **nie** Anmeldung, **nie** bei Ulf; Behandlung, OP und Lisa ja | ✅ 05.11. |
| Molly, Matthias, Pauline | werden verplant, auch allein in Assistenz-Rollen (so in der Praxis) | ✏️ |
| Ärzte | festes Muster + Samstagsrotation; Eingabe, nicht verplant | ✏️ |

## B. Pflichtregeln
| ID | Regel | Verstöße in den echten Wochen |
|---|---|---|
| `anmeldung_fd_sd` | TFA-Anmeldung in FD und SD je genau 1× | einzelne Ausnahmen |
| `assistenz_ulf` | Ulf da → **je eine Assistenz vormittags (FD) und nachmittags (SD)** ✅ | wenige Lücken |
| `assistenz_lisa_op` | Lisa operiert → Assistenz FD und SD; „Assistenz Lisa“ = „Assistenz Lisa OP“ ✅ | einzelne |
| `assistenz_wilke_op` | Wilke „FD OP“ → eine Assistenz; „Assistenz Wilke“ zählt ✅ (OP-Ärzte haben immer einen Helfer) | einzelne |
| `nina_kein_freitag` | Nina freitags nie eingeplant ✅ | 1× |
| `rollen_verbote` | Emilia und Pauline: keine Anmeldung, nicht bei Ulf ✅ | 1× (Pauline bei Ulf) |
| `deborah_wechsel` | Deborahs Schichtwechsel (s.o.) ✅ | 5× in 22 Wochen |
| `gesperrt_unveraendert` | manuelle Einträge bleiben exakt erhalten ✅ | 0 |

## C. Bevorzugte Besetzung (Wunsch, aus Nicolas’ Planung KW 36–46) ✏️
Reihenfolge = erste Wahl zuerst. Steht in `planner/einstellungen.py` und ist dort leicht änderbar.

**Assistenz Ulf** (Ulf arbeitet Mo–Mi, manchmal Do)
| Tag | Vormittag (FD) | Nachmittag (SD) |
|---|---|---|
| Mo | Matthias, Deborah, Molly | **Nina („ab 15 Uhr“)**, Deborah, Matthias |
| Di | Deborah, Matthias, Molly, Nadine | Molly, Deborah, Imke, Matthias |
| Mi | Deborah, Nadine, Molly | Molly, Matthias, Nina, Nicolas, Deborah |
| Do | Imke, Nadine | Deborah, Nadine |

**Anmeldung:** FD Nadine › Nicolas › Imke › Deborah › Nina; SD Nicolas › Nadine › Imke › Deborah › Nina
**Assistenz Lisa:** FD Molly › Nicolas › Nina › Nadine; SD Nadine › Molly › Pauline
**Assistenz Wilke:** FD Imke › Matthias › Molly; SD Pauline › Molly

**`jeder_arzt_helfer`** ✅ (Wunsch, hohes Gewicht): Wenn genug Leute da sind, bekommt **jeder Arzt in jeder
Schicht, in der er arbeitet, eine Assistenz** (Wilke, Florian, Lisa; Ulf ist ohnehin Pflicht; Hanne läuft mit Florian).
Schicht des Arztes aus seiner Zelle: „FD …“/„09–12“ = FD, „SD …“ = SD, „09:00–17:00“/„OP Ganztag“ = beide.
In KW 36–46 war das 69× nicht möglich – deshalb Wunsch, nicht Pflicht.

Reihenfolge der Wichtigkeit beim Verteilen: 1. Anmeldung FD+SD → 2. Ulf FD+SD → 3. OP-Ärzte →
4. übrige Ärzte je Schicht → 5. Behandlung/Springer, FD/SD ausgeglichen (`balance_fd_sd`).

## D. Schule der Azubis (aus dem Plan KW 32–47)
- Pauline: **Mittwoch** Schule (ganztägig) ✅.
- Molly + Matthias: seit KW 37 **Donnerstag und Freitag** Schule. An beiden Tagen kommt **einer von beiden
  nach der Schule ab 15:30 in den SD**, der andere hat dort ganztägig Schule – am anderen Tag umgekehrt:

  | KW | Do: kommt ab 15:30 | Fr: kommt ab 15:30 |
  |---|---|---|
  | 37 | Molly | Matthias |
  | 38 | Molly | Matthias |
  | 39 | Matthias | Molly |
  | 40 | Matthias | (Molly krank) |
  | 41 | Molly | Matthias |
  | 42 | Fortbildung | beide (13:30/14:30) |
  | 43–44 | Herbstferien → normal im Dienst | |
  | 45 | Fortbildung | beide Schule |

  ✏️ **Fortgesetzte Logik (Annahme):** Wechsel alle 2 Wochen, ab KW 37 gezählt, Ferien-KWs ohne Schule:
  KW 45–46 Do Molly / Fr Matthias ab 15:30 · KW 47–48 Do Matthias / Fr Molly · KW 49–50 wie 45–46 …
  Umgesetzt in `planner/einstellungen.py` → `schule()`; Anker/Rhythmus dort änderbar.
  ❓ Von Molly/Matthias bestätigen lassen (die Datenbasis sind nur KW 37–41).
  ❓ In `config.py` stehen noch alte Platzhalter (Molly Do, Matthias **Di**) → wird nach Klärung korrigiert.

## E. Offene Fragen
1. ✅ **Mindestbesetzung:** keine feste Zahl – alle Verfügbaren werden auf FD/SD aufgeteilt.
2. ❓ **Arbeitszeit:** Gibt es Soll-Tage pro Woche je Person (z.B. Teilzeit Nina, Azubis)?
3. ❓ **Samstag:** Feste Rotationsliste weiterführen oder fair verteilen lassen?
4. ✅ **Assistenz Florian:** jeder Arzt bekommt je Schicht einen Helfer, wenn möglich (`jeder_arzt_helfer`). Springer = wer übrig bleibt.
5. ✏️ **Azubis allein:** Dürfen Molly/Matthias eine Pflicht-Assistenz allein besetzen? (Daten: ja)
6. ✅ **OP-Ärzte** haben immer einen Helfer (Pflicht) – auch Wilke freitags.
