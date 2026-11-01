# Regelwerk – Entwurf zur Abstimmung

Grundlage: die echten Wochen KW 24–45 (`docs/analyse.md`). Jede Regel bekommt eine ID,
die später 1:1 in `planner/regeln.py` umgesetzt wird.
**Pflicht** = muss immer erfüllt sein. **Wunsch** = möglichst, mit Gewicht.

Status: ✅ bestätigt · ❓ Frage offen · ✏️ Entwurf

## A. Feste Vorgaben (Eingaben, werden nie verplant)
- ✅ Manuelle Einträge haben immer Vorrang.
- ✅ Urlaub, Krank, Feiertag aus der Urlaubsplanung bleiben stehen.
- ✏️ Schultage: Alyssa Do, Pauline Mi, Molly Do, Matthias Di (außer in Ferien-KWs).
- ✏️ Ärzte arbeiten nach festem Muster (`ARZT_PATTERNS`) + Samstagsrotation → Eingabe, nicht verplant.

## B. Pflichtregeln (Entwurf)
| ID | Regel | Beobachtung in den echten Wochen |
|---|---|---|
| `anmeldung_fd_sd` | Anmeldung in FD und SD je genau 1× besetzt | 32× fehlt eine Anmeldung ❓ |
| `assistenz_ulf` | Ulf da → Assistenz in FD und SD | SD fehlt 35×, FD 17× ❓ |
| `assistenz_lisa_op` | Lisa „OP Ganztag“ → OP-Assistenz FD und SD | fehlt 35× ❓ |
| `assistenz_wilke_op` | Wilke „FD OP“ → OP-Assistenz | fehlt 11× |
| `gesperrt_unveraendert` | manuelle Einträge bleiben | ✅ |

## C. Wünsche (Entwurf)
| ID | Wunsch | Beobachtung |
|---|---|---|
| `balance_fd_sd` | FD/SD etwa gleich stark | oft FD=4–5, SD=0 ❓ |
| `stamm_anmeldung` | Anmeldung bevorzugt: FD Nadine/Nicolas/Imke, SD Nicolas/Nadine/Deborah/Imke | aus Analyse |
| `stamm_ulf` | Assistenz Ulf bevorzugt Kristin/Deborah | aus Analyse |
| `stamm_wilke_op` | Assistenz Wilke-OP bevorzugt Imke | 13 von 18 |
| `deborah_paritaet` | Deborah gerade KW FD, ungerade KW SD; Fr gerade frei | weitgehend ✓ |
| `fairness_samstag` | Samstage fair verteilt | ❓ |

## D. Offene Fragen an die Praxis
1. **Anmeldung:** Übernimmt Nicolette (Empfang 08:30–17:00, seit 01.09.) die FD-Anmeldung?
   Braucht es dann noch eine TFA in „FD: Anmeldung“?
2. **Ulf:** Ulf arbeitet 09–17 Uhr. Braucht er wirklich eine *SD*-Assistenz, oder reicht eine
   Assistenz ganztags/FD?
3. **Neue Rollen:** In der Praxis gibt es „Assistenz Lisa“ (ohne OP), „Assistenz Florian“,
   „Assistenz Wilke“ (ohne OP) und „Springer“. Wann ist welche Rolle nötig? Pflicht oder nach Bedarf?
4. **Lisa OP:** Die OP-Assistenz fehlt oft, weil stattdessen „Assistenz Lisa“ eingetragen ist.
   Ist das dasselbe?
5. **Azubis:** Molly und Matthias machen viel Assistenz (Ulf, Lisa, Wilke). Dürfen sie allein
   eine Pflichtrolle besetzen, oder nur zusätzlich (Tandem)?
6. **Nina / Nicolette / Hanne:** Sollen sie automatisch verplant werden oder weiter nur manuell?
7. **Alyssa:** Ist in vielen Wochen leer („–“). Hat sich ihr Umfang geändert?
8. **Mindestbesetzung:** Wie viele TFAs braucht es mindestens pro Schicht (FD / SD)?
9. **Arbeitszeit:** Gibt es Soll-Tage/Stunden pro Person und Woche, die eingehalten werden müssen?
10. **Samstag:** Bleibt die feste Rotationsliste (`SA_TFA`), oder soll der Planer sie fair verteilen?
