# Regelwerk

Grundlage: die von Nicolas manuell geplanten Wochen (KW 24–46, Schwerpunkt KW 36–46)
und die Abstimmung mit der Praxis am 01.11.2026.
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
| Nicolette | Empfang mit festen Zeiten, steht im Plan wie bisher. Ist **keine** FD-Anmeldung, wird nicht verplant. | ✅ |
| Hanne | wird nicht automatisch verplant (läuft mit Florian mit) | ✅ |
| Nina | wird ganz normal verplant; **freitags nie** | ✅ |
| Deborah | gerade KW Frühdienst, ungerade KW Spätdienst; gerade KW freitags frei | ✅ |
| Alyssa | langzeitkrank (vorerst bis 11.11., voraussichtlich länger) → nicht verplanen | ✅ |
| Kristin | krankgeschrieben, bleibt als „Krank“ im Plan → nicht verplanen | ✅ |
| Emilia | neue TFA (Nov 2026), steht im Plan, wird vorerst nur manuell von Nicolas geplant | ✅ |
| Molly, Matthias, Pauline | werden verplant, auch allein in Assistenz-Rollen (so in der Praxis) | ✏️ |
| Ärzte | festes Muster + Samstagsrotation; Eingabe, nicht verplant | ✏️ |

## B. Pflichtregeln
| ID | Regel | Verstöße in den echten Wochen |
|---|---|---|
| `anmeldung_fd_sd` | TFA-Anmeldung in FD und SD je genau 1× (Nicolette zählt nicht) | einzelne Ausnahmen |
| `assistenz_ulf` | Ulf da → **je eine Assistenz vormittags (FD) und nachmittags (SD)** ✅ | wenige Lücken |
| `assistenz_lisa_op` | Lisa operiert → Assistenz FD und SD; „Assistenz Lisa“ = „Assistenz Lisa OP“ ✅ | einzelne |
| `assistenz_wilke_op` | Wilke „FD OP“ → eine Assistenz; „Assistenz Wilke“ zählt ✏️ | einzelne |
| `nina_kein_freitag` | Nina freitags nie eingeplant ✅ | 1× |
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

Weitere Wünsche (Gewichtung folgt): FD/SD ausgeglichen (`balance_fd_sd`), Rollen fair verteilt.

## D. Offene Fragen
1. ❓ **Mindestbesetzung:** Wie viele Personen braucht es mindestens pro Schicht (FD / SD)?
2. ❓ **Arbeitszeit:** Gibt es Soll-Tage pro Woche je Person (z.B. Teilzeit Nina, Azubis)?
3. ❓ **Samstag:** Feste Rotationsliste weiterführen oder fair verteilen lassen?
4. ❓ **Assistenz Florian / Springer:** Nach Bedarf oder fest an bestimmten Tagen?
5. ✏️ **Azubis allein:** Dürfen Molly/Matthias eine Pflicht-Assistenz allein besetzen? (Daten: ja)
6. ❓ **Wilke-OP-Freitag:** Mehrmals ohne Assistenz geplant (KW 36, 39, 42) – Ausnahme oder Lücke?
