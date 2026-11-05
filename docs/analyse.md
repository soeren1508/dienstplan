# Analyse der echten Wochen (generiert)

Zeitraum: KW 24–45. Erzeugt mit `python -m planner.analyse`.
Urlaub/Krank sind herausgerechnet. Format: häufigste Einteilung (Anteil) · zweithäufigste.

## 1. Muster pro Person und Wochentag

| Person | Par. | Mo | Di | Mi | Do | Fr |
|---|---|---|---|---|---|---|
| Kristin | gerade | FD Assistenz Ulf (42%) · FD Behandlung | SD Assistenz Ulf (66%) · FD Anmeldung | FD Assistenz Ulf (33%) · SD Assistenz Ulf | FD Anmeldung (50%) · FD Springer | SD Anmeldung (33%) · FD Assistenz Wilke OP |
| Kristin | ungerade | FD Assistenz Ulf (80%) · SD Anmeldung | FD Assistenz Ulf (80%) · Frei | FD Assistenz Ulf (80%) · SD Assistenz Ulf | FD Anmeldung (40%) · FD Springer | FD Assistenz Wilke OP (33%) · FD Anmeldung |
| Deborah | gerade | FD Assistenz Ulf (33%) · FD Anmeldung | FD Assistenz Ulf (87%) · FD Behandlung | FD Assistenz Ulf (50%) · FD Anmeldung | FD Behandlung (28%) · FD Anmeldung | – (85%) · FD Anmeldung |
| Deborah | ungerade | SD Assistenz Ulf (28%) · SD Anmeldung | FD Assistenz Ulf (28%) · SD Behandlung | SD Anmeldung (62%) · SD Assistenz Ulf | SD Anmeldung (33%) · SD Behandlung | SD Behandlung (57%) · SD Anmeldung |
| Imke | gerade | SD Anmeldung (50%) · SD Springer | FD Behandlung (44%) · SD Behandlung | FD Assistenz Wilke OP (55%) · FD Behandlung | SD Anmeldung (37%) · FD Anmeldung | FD Assistenz Wilke OP (62%) · FD Anmeldung |
| Imke | ungerade | FD Anmeldung (33%) · FD Assistenz Ulf | FD Anmeldung (28%) · SD Anmeldung | FD Assistenz Wilke OP (42%) · FD Assistenz Ulf | FD Anmeldung (28%) · FD Springer | FD Anmeldung (75%) · FD Springer |
| Nadine | gerade | FD Anmeldung (33%) · FD Assistenz Lisa OP | FD Anmeldung (55%) · FD Springer | FD Anmeldung (55%) · SD Anmeldung | SD Assistenz Lisa OP (33%) · SD Anmeldung | FD Anmeldung (77%) · FD Behandlung |
| Nadine | ungerade | FD Anmeldung (30%) · FD Assistenz Lisa | FD Anmeldung (50%) · FD Behandlung | FD Anmeldung (40%) · SD Anmeldung | SD Assistenz Lisa OP (30%) · FD Anmeldung | SD Anmeldung (40%) · FD Anmeldung |
| Nicolas | gerade | SD Anmeldung (40%) · FD Springer | SD Anmeldung (50%) · FD Anmeldung | SD Assistenz Ulf (20%) · GANZ Behandlung | FD Assistenz Lisa OP (30%) · FD Springer | SD Anmeldung (55%) · SD Springer |
| Nicolas | ungerade | FD Anmeldung (37%) · FD Springer | SD Anmeldung (55%) · FD Anmeldung | FD Anmeldung (44%) · SD Anmeldung | FD Assistenz Lisa OP (22%) · Frei | FD Anmeldung (33%) · FD Springer |
| Alyssa | gerade | – (50%) · SD Assistenz Lisa OP | – (57%) · FD Behandlung | – (57%) · FD Behandlung | – (50%) · FD Behandlung | – (50%) · FD Behandlung |
| Alyssa | ungerade | – (50%) · FD Behandlung | – (50%) · FD Behandlung | – (50%) · FD Behandlung | – (55%) · Schule | – (55%) · SD Behandlung |
| Pauline | gerade | SD Behandlung (33%) · FD Behandlung | FD Behandlung (66%) · SD Behandlung | Schule (77%) · FD Behandlung | SD Behandlung (37%) · FD Behandlung | FD Behandlung (50%) · FD Assistenz Wilke |
| Pauline | ungerade | SD Assistenz Florian (40%) · FD Behandlung | SD Behandlung (40%) · FD Behandlung | Schule (60%) · FD Behandlung | SD Behandlung (50%) · Fortbildung | FD Behandlung (55%) · SD Assistenz Florian |
| Nina | gerade | SD Behandlung (30%) · SD Assistenz Ulf | FD Behandlung (30%) · – | – (30%) · FD Behandlung | FD Behandlung (30%) · – | – (100%) |
| Nina | ungerade | SD Assistenz Ulf (55%) · – | FD Anmeldung (33%) · – | – (22%) · FD Behandlung | FD Behandlung (22%) · – | – (90%) · FD Behandlung |
| Emilia | gerade | – (100%) | – (100%) | – (100%) | – (100%) | – (100%) |
| Emilia | ungerade | – (100%) | – (100%) | – (100%) | – (100%) | – (100%) |
| Molly | gerade | FD Behandlung (45%) · FD Assistenz Lisa | FD Behandlung (40%) · – | – (40%) · SD Behandlung | FD Behandlung (30%) · – | – (40%) · SD Behandlung |
| Molly | ungerade | FD Behandlung (20%) · FD Assistenz Wilke | FD Behandlung (27%) · – | – (36%) · SD Behandlung | FD Behandlung (18%) · – | – (36%) · Schule |
| Matthias | gerade | – (36%) · FD Behandlung | SD Behandlung (45%) · – | – (36%) · FD Behandlung | – (36%) · SD Behandlung | – (36%) · FD Behandlung |
| Matthias | ungerade | – (33%) · FD Assistenz Ulf | – (36%) · SD Assistenz Ulf | – (36%) · FD Assistenz Wilke | – (36%) · FD Behandlung | – (36%) · SD Assistenz Lisa |

## 2. Wer übernimmt welche Rolle (Anzahl Tage)

- **FD Anmeldung** (105): Nadine 38, Nicolas 24, Imke 21, Deborah 9, Kristin 7, Nina 6
- **FD Assistenz Florian** (12): Nina 3, Matthias 3, Nicolas 2, Pauline 2, Molly 1, Imke 1
- **FD Assistenz Lisa** (26): Molly 11, Nadine 4, Nina 4, Pauline 3, Kristin 1, Alyssa 1, Matthias 1, Imke 1
- **FD Assistenz Lisa OP** (19): Nicolas 7, Nadine 4, Molly 3, Imke 2, Alyssa 1, Pauline 1, Deborah 1
- **FD Assistenz Ulf** (58): Kristin 18, Deborah 17, Matthias 8, Molly 6, Nadine 4, Imke 3, Alyssa 2
- **FD Assistenz Wilke** (16): Matthias 7, Molly 3, Pauline 3, Imke 2, Nadine 1
- **FD Assistenz Wilke OP** (18): Imke 13, Kristin 3, Nadine 2
- **FD Springer** (31): Nicolas 14, Nadine 6, Kristin 5, Imke 4, Molly 1, Deborah 1
- **None Springer** (1): Nicolas 1
- **SD Anmeldung** (73): Nicolas 26, Nadine 14, Deborah 13, Imke 12, Kristin 4, Nina 4
- **SD Assistenz Florian** (9): Pauline 6, Matthias 2, Nina 1
- **SD Assistenz Lisa** (17): Molly 8, Matthias 4, Pauline 3, Nadine 1, Deborah 1
- **SD Assistenz Lisa OP** (14): Nadine 8, Pauline 2, Nicolas 1, Alyssa 1, Kristin 1, Imke 1
- **SD Assistenz Ulf** (44): Nina 9, Kristin 8, Deborah 8, Matthias 6, Molly 5, Nadine 2, Nicolas 2, Imke 2, Alyssa 1, Pauline 1
- **SD Assistenz Wilke** (12): Pauline 5, Molly 3, Alyssa 1, Imke 1, Matthias 1, Nina 1
- **SD Springer** (12): Alyssa 4, Nina 3, Nicolas 1, Imke 1, Nadine 1, Kristin 1, Matthias 1

## 3. Verstöße der echten Wochen gegen die aktuellen Regeln

Viele Verstöße = Regel passt nicht zur Praxis und muss überarbeitet werden.

- `anmeldung_fd_sd` (pflicht): 37× — SD: Anmeldung fehlt 19×; FD: Anmeldung fehlt 10×; FD: Anmeldung doppelt 7×; SD: Anmeldung doppelt 1×
- `assistenz_ulf` (pflicht): 18× — Ulf da → SD: Assistenz fehlt 15×; Ulf da → FD: Assistenz fehlt 3×
- `assistenz_lisa_op` (pflicht): 16× — Lisa OP → SD: Assistenz fehlt 11×; Lisa OP → FD: Assistenz fehlt 5×
- `assistenz_wilke_op` (pflicht): 8× — Wilke OP → Assistenz fehlt 8×
- `freie_tage` (pflicht): 1× — Nina eingeplant, hat an dem Tag frei 1×
- `deborah_wechsel` (pflicht): 5× — Deborah FD statt SD 4×; Deborah gerade KW Fr eingeplant 1×
- `rollen_verbote` (pflicht): 1× — Pauline: Assistenz Ulf nicht erlaubt 1×
- `jeder_arzt_helfer` (wunsch): 169× — Lisa FD ohne Assistenz 39×; Florian FD ohne Assistenz 29×; Lisa SD ohne Assistenz 28×; Wilke SD ohne Assistenz 26×
- `balance_fd_sd` (wunsch): 19× — FD=6, SD=0 5×; FD=5, SD=0 5×; FD=5, SD=1 4×; FD=4, SD=0 4×
- `gesperrt_unveraendert` (pflicht): 0× — ok
