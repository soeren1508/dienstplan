"""
scheduler.py — Generiert den Dienstplan wochenweise.
"""

from datetime import date, timedelta
from typing import Dict, List, Optional

from config import (
    ARZT_PATTERNS, FEIERTAGE_HH_2026, SCHULTAGE, SCHUL_AUSFALL,
    SA_ARZT, SA_TFA, NOTDIENSTE, ECVO_TAGE, SPEZIAL,
    PERSONAL_EXIT, PRUEFUNGSTAGE, VACATION_OVERRIDES,
    ALL_PERSONS, ARZTE, TFAS, DAYS,
)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def kw_to_monday(kw: int, year: int = 2026) -> date:
    return date.fromisocalendar(year, kw, 1)

def week_dates(kw: int) -> List[date]:
    mo = kw_to_monday(kw)
    return [mo + timedelta(days=i) for i in range(6)]

def is_vacation(person, di, vacations, dates):
    return dates[di] in vacations.get(person, set())

def is_feiertag(di, dates):
    return dates[di] in FEIERTAGE_HH_2026

def is_schule(person, di, kw_num):
    if di not in SCHULTAGE.get(person, []):
        return False
    return kw_num not in SCHUL_AUSFALL.get(person, set())

def person_absent(person, di, vacations, dates, kw_num):
    if kw_num >= PERSONAL_EXIT.get(person, 999):
        return True   # ausgetretene Person → immer abwesend
    return (is_vacation(person, di, vacations, dates)
            or is_feiertag(di, dates)
            or is_schule(person, di, kw_num))

def pick_min(pool, auffl):
    avail = [p for p in pool if p in auffl]
    return min(avail, key=lambda p: auffl[p]) if avail else None

def auffl_add(person, val, auffl):
    auffl[person] = auffl.get(person, 0) + 1
    v = val.strip()
    return v if v.endswith("+ Auffüllen") else v + " + Auffüllen"


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------

def generate_week(kw_num, vacations, auffl):
    dates = week_dates(kw_num)
    is_even = kw_num % 2 == 0
    plan = {p: ["–"] * 6 for p in ALL_PERSONS}

    def s(p, di, v): plan[p][di] = v
    def g(p, di): return plan[p][di]
    def free(p, di): return plan[p][di] == "–"
    def pa(p, di): return person_absent(p, di, vacations, dates, kw_num)

    # ── 1) Feiertage + Urlaub ───────────────────────────────────────────────
    for p in ALL_PERSONS:
        for di in range(6):
            if is_feiertag(di, dates):
                s(p, di, "Feiertag")
            elif is_vacation(p, di, vacations, dates):
                s(p, di, "Urlaub")

    # ── 1b) Urlaub-Korrekturen (fehlende Tage in Urlaubsdatei) ─────────────
    for (person, kw, di) in VACATION_OVERRIDES:
        if kw_num == kw and g(person, di) == "–":
            s(person, di, "Urlaub")

    # ── 2) Personal-Exits ───────────────────────────────────────────────────
    for person, exit_kw in PERSONAL_EXIT.items():
        if kw_num >= exit_kw:
            for di in range(6):
                if g(person, di) != "Feiertag":
                    s(person, di, "–")

    # ── 3) Prüfungstage ─────────────────────────────────────────────────────
    for (person, kw, di) in PRUEFUNGSTAGE:
        if kw_num == kw and (free(person, di) or plan[person][di] == "Urlaub"):
            s(person, di, "Abschlussprüfung")

    # ── 4) Notdienst ────────────────────────────────────────────────────────
    for (arzt, tfa, kw, di) in NOTDIENSTE:
        if kw_num != kw:
            continue
        for person in (arzt, tfa):
            s(person, di, "Notdienst (20–8 Uhr)")
            if di > 0 and g(person, di - 1) == "–":
                s(person, di - 1, "Frei (Notdienst)")
            if di < 4 and g(person, di + 1) == "–":
                s(person, di + 1, "Frei (Notdienst)")

    # ── 5) ECVO Congress + Spezial ──────────────────────────────────────────
    for (person, kw, di) in ECVO_TAGE:
        if kw_num == kw:
            s(person, di, "ECVO Congress")
    for (person, kw, di, val) in SPEZIAL:
        if kw_num == kw:
            s(person, di, val)

    # ── 6) Arzt-Basismuster ─────────────────────────────────────────────────
    for arzt, pattern in ARZT_PATTERNS.items():
        for di in range(5):
            if free(arzt, di):
                s(arzt, di, "–" if pa(arzt, di) else pattern[di])

    # ── 7) Schultage ────────────────────────────────────────────────────────
    for person in TFAS:
        for di in range(5):
            if (free(person, di)
                    and is_schule(person, di, kw_num)
                    and kw_num < PERSONAL_EXIT.get(person, 999)):
                s(person, di, "SCHULE")

    # ── 8) Deborah Fr = "–" in geraden KWs (ab KW17) ───────────────────────
    if is_even and kw_num >= 17 and free("Deborah", 4):
        s("Deborah", 4, "FREI_SCHUTZ")   # Schutz-Marker gegen fill_remaining

    # ── 9) Lisa OP Ganztag → Pflicht-Assistenz ──────────────────────────────
    for di in [0, 3]:
        if g("Lisa", di) != "OP Ganztag":
            continue
        if di == 0:  # Mo
            # Even Mo: Imke=FD:Anmeldung, Kristin=Assistenz Ulf (via step 11) → beide überspringen
            fd_chain = ("Nicolas", "Pauline") if is_even else ("Nicolas", "Imke", "Kristin", "Pauline")
            # SD Mo: nur Nadine/Alyssa/Pauline (Imke+Kristin machen Anmeldung/Assistenz Ulf)
            sd_chain = ("Nadine", "Alyssa", "Pauline")
        else:  # Do
            # Even Do: Imke=Anmeldung/SD → Deborah als Fallback
            # Odd Do: Imke korrekt als Fallback (KW27/39)
            # Kristin nie SD:Assistenz Lisa OP Do (sie macht Anmeldung via step 12c)
            fd_chain = ("Nicolas", "Deborah", "Pauline") if is_even else ("Nicolas", "Imke", "Deborah", "Pauline")
            sd_chain = ("Nadine", "Alyssa", "Imke", "Pauline")
        for fb in fd_chain:
            if free(fb, di) and not pa(fb, di):
                s(fb, di, "FD: Assistenz Lisa OP")
                break
        for fb in sd_chain:
            if free(fb, di) and not pa(fb, di):
                s(fb, di, "SD: Assistenz Lisa OP")
                break

    # ── 10) Wilke FD OP → Imke FD: Assistenz Wilke OP (Mi + Fr) ────────────
    for di in [2, 4]:
        if g("Wilke", di) != "FD OP":
            continue
        # Fr in ungeraden KWs: nur wenn Imke absent → Kristin als Fallback
        if di == 4 and not is_even and not pa("Imke", di):
            continue
        if free("Imke", di) and not pa("Imke", di):
            s("Imke", di, "FD: Assistenz Wilke OP")
        else:
            # Fr: Kristin als primärer Fallback, Mi: Nadine als primärer Fallback
            fb_order = ("Kristin", "Nadine") if di == 4 else ("Nadine", "Kristin")
            for fb in fb_order:
                if free(fb, di) and not pa(fb, di):
                    s(fb, di, "FD: Assistenz Wilke OP")
                    break

    # ── 11) Ulf-Assistenz ───────────────────────────────────────────────────
    # Vorab: Wenn Deborah in gerader KW Anmeldung übernimmt (Nadine ganze Woche weg),
    # bleibt sie für Ulf-Assistenz nur auf Mo verfügbar.
    nadine_ganz_weg = all(pa("Nadine", di) for di in range(5))
    deborah_deckt_anmeldung_mo = is_even and nadine_ganz_weg

    def ulf_da(di):
        return g("Ulf", di) not in ("–", "Feiertag", "Urlaub", "Krank")

    for di in [0, 1, 2]:   # Mo, Di, Mi
        if not ulf_da(di):
            continue

        # Prioritäten je nach Parität und Deborah-Status
        # Deborah ist nur in ihrem Paritäts-Shift (gerade→FD, ungerade→SD) erlaubt.
        # Pauline übernimmt SD-Assistenz Ulf (Mo) damit Deborah/Kristin für Anmeldung frei bleiben.
        if is_even:
            if di == 0:  # Mo gerade
                if deborah_deckt_anmeldung_mo:
                    fd_prio = ["Kristin", "Deborah", "Natalie"]
                    sd_prio = ["Pauline", "Natalie", "Kristin"]   # Pauline: kein Anmeldungs-Verbot für Assistenz
                else:
                    fd_prio = ["Deborah", "Kristin", "Natalie"]
                    sd_prio = ["Pauline", "Natalie", "Kristin"]   # Pauline entlastet Kristin/Deborah
            elif di == 1:  # Di gerade
                if not pa("Natalie", 1) and free("Natalie", 1):
                    fd_prio = ["Natalie", "Deborah", "Kristin"]
                    sd_prio = ["Kristin", "Imke", "Deborah", "Natalie"]
                else:
                    fd_prio = ["Deborah", "Kristin", "Natalie"]
                    sd_prio = ["Kristin", "Natalie", "Deborah"]
            else:  # Mi gerade
                if kw_num >= 27:
                    fd_prio = ["Deborah", "Kristin", "Natalie"]
                else:
                    fd_prio = ["Kristin", "Deborah", "Natalie"]
                sd_prio = ["Natalie", "Kristin", "Nicolas", "Deborah"]  # Nicolas als Fallback vor Deborah
        else:
            # Ungerade KW
            if di == 0:  # Mo: Natalie FD, Kristin SD; Pauline hält SD:Assistenz Ulf → Deborah für Anmeldung frei
                fd_prio = ["Natalie", "Kristin", "Deborah"]
                sd_prio = ["Pauline", "Kristin", "Natalie"]   # Pauline erst → Deborah frei für SD:Anmeldung
            elif di == 1:  # Di ungerade: Imke+Nicolas als Fallbacks für FD (wenn Natalie+Kristin fehlen)
                fd_prio = ["Natalie", "Kristin", "Imke", "Nicolas", "Deborah"]
                sd_prio = ["Kristin", "Deborah", "Natalie"]
            else:  # Mi ungerade
                fd_prio = ["Natalie", "Kristin", "Deborah"]
                sd_prio = ["Natalie", "Kristin", "Deborah", "Imke"]

        # FD-Slot — Deborah nur in geraden KWs (Paritätspflicht)
        for fp in fd_prio:
            if fp == "Deborah" and not is_even:
                continue   # ungerade KW → Deborah niemals FD
            if free(fp, di) and not pa(fp, di):
                s(fp, di, "FD: Assistenz Ulf")
                break

        # SD-Slot — Deborah nur in ungeraden KWs (Paritätspflicht)
        for sp in sd_prio:
            if sp == "Deborah" and is_even:
                continue   # gerade KW → Deborah niemals SD
            if free(sp, di) and not pa(sp, di):
                s(sp, di, "SD: Assistenz Ulf")
                break

        # Gerade Di: Imke SD:Assistenz Ulf wenn Kristin abwesend UND Deborah FD genommen hat
        if is_even and di == 1 and pa("Kristin", 1) and g("Deborah", 1) == "FD: Assistenz Ulf":
            if free("Imke", 1) and not pa("Imke", 1):
                s("Imke", 1, "SD: Assistenz Ulf")

        # In gerader KW Mo: Natalie + Auffüllen hinzufügen, falls sie SD: Assistenz Ulf bekommen hat
        # ODER (wenn Deborah nicht Anmeldung deckt) als Extra-SD einsetzen, falls kein SD-Slot belegt
        if is_even and di == 0:
            natalie_val = g("Natalie", 0)
            if "SD: Assistenz Ulf" in natalie_val and "+ Auffüllen" not in natalie_val:
                # Natalie hat den SD-Slot via sd_prio bekommen → Auffüllen dranhängen
                s("Natalie", 0, auffl_add("Natalie", natalie_val, auffl))
            elif not deborah_deckt_anmeldung_mo and free("Natalie", 0) and not pa("Natalie", 0):
                # Nur zuweisen wenn der SD-Assistenz-Ulf-Slot noch nicht belegt ist
                sd_ulf_belegt = any(
                    "SD: Assistenz Ulf" in plan[p][0]
                    for p in ("Kristin", "Deborah", "Imke", "Nadine", "Nicolas", "Alyssa", "Pauline")
                )
                if not sd_ulf_belegt:
                    s("Natalie", 0, auffl_add("Natalie", "SD: Assistenz Ulf", auffl))

    # Auffüllen für Ulf-Assistenz Di: Parität bestimmt wer es bekommt
    # Gerade KW → Kristin, Ungerade KW → Deborah
    if ulf_da(1):
        auffl_person_di = "Kristin" if is_even else "Deborah"
        if ("Assistenz Ulf" in g(auffl_person_di, 1)
                and "+ Auffüllen" not in g(auffl_person_di, 1)):
            s(auffl_person_di, 1, auffl_add(auffl_person_di, g(auffl_person_di, 1), auffl))

    # ── 12) Fr-Vorplanung: Alyssa SD-Lock + Kristin-Shift ──────────────────────
    # Alyssa Fr = SD-Lock (bis KW25): früh setzen damit Fill-Balance stimmt
    if kw_num <= 25 and free("Alyssa", 4) and not pa("Alyssa", 4):
        s("Alyssa", 4, "SD: Behandlung (ab 15:30)")
    # Kristin Fr: Shift gegenläufig zu Imke (Wilke-OP-Tage); Anmeldung wenn noch offen
    if free("Kristin", 4) and not pa("Kristin", 4):
        from rules import get_shift as _gs
        imke_fr_shift = _gs(g("Imke", 4))   # FD wenn Imke Wilke-OP hat, sonst None
        kr_shift = "SD" if imke_fr_shift == "FD" else "FD"
        if kr_shift == "FD":
            s("Kristin", 4, "FD: Anmeldung + Bestellungen")
        else:  # SD — auch SD braucht Anmeldung
            s("Kristin", 4, "SD: Anmeldung + Bestellungen")
    elif "Assistenz Wilke OP" in g("Kristin", 4) and "+ Bestellungen" not in g("Kristin", 4):
        s("Kristin", 4, g("Kristin", 4) + " + Bestellungen")

    # ── 12b) Nicolas Fr Vorplanung: SD:Anmeldung (gerade) / FD:Behandlung (ungerade) ──
    # Wenn Nadine absent (Urlaub etc.), übernimmt Nicolas FD:Anmeldung → kein Pre-Set
    if free("Nicolas", 4) and not pa("Nicolas", 4) and not pa("Nadine", 4):
        s("Nicolas", 4, "SD: Anmeldung" if is_even else "FD: Behandlung")

    # ── 12c) Kristin Do Vorplanung: FD:Anmeldung (gerade) / SD:Anmeldung (ungerade) ──
    if free("Kristin", 3) and not pa("Kristin", 3):
        kr_do = "FD: Anmeldung" if is_even else "SD: Anmeldung"
        s("Kristin", 3, kr_do)

    # ── 12d) Nadine Di Vorplanung in geraden KWs = immer FD:Anmeldung ─────────
    if is_even and free("Nadine", 1) and not pa("Nadine", 1):
        s("Nadine", 1, "FD: Anmeldung")

    # ── 13) Samstags-Rotation ────────────────────────────────────────────────
    sa_arzt = SA_ARZT.get(kw_num)
    sa_tfa  = SA_TFA.get(kw_num)
    for arzt in ARZTE:
        if free(arzt, 5) and arzt == sa_arzt:
            s(arzt, 5, "Dienst")
    if sa_tfa and free(sa_tfa, 5) and not is_vacation(sa_tfa, 5, vacations, dates):
        s(sa_tfa, 5, "Dienst")

    # ── 14) Füll-Logik ───────────────────────────────────────────────────────
    _fill_remaining(plan, kw_num, is_even, vacations, dates, auffl,
                    deborah_deckt_anmeldung_mo)

    # ── 14b) Lisa OP Do Auffüllen (nach fill_remaining, ohne Nicolas) ────────
    if g("Lisa", 3) == "OP Ganztag":
        cands = [p for p in ("Nadine", "Pauline", "Imke")
                 if (g(p, 3) not in ("–", "Urlaub", "Feiertag", "FREI_SCHUTZ", "SCHULE",
                                      "Abschlussprüfung")
                     and "Notdienst" not in g(p, 3)
                     and "Frei" not in g(p, 3)
                     and "Anmeldung" not in g(p, 3)
                     and "Bestellungen" not in g(p, 3)
                     and "+ Auffüllen" not in g(p, 3)
                     and not pa(p, 3))]
        winner = pick_min(cands, auffl)
        if winner:
            s(winner, 3, auffl_add(winner, g(winner, 3), auffl))

    # ── 15) Schutz-Marker entfernen ──────────────────────────────────────────
    for p in ALL_PERSONS:
        for di in range(6):
            if plan[p][di] == "FREI_SCHUTZ":
                plan[p][di] = "–"

    # ── 15b) Post-Fix: verbleibende Anmeldungs- und Assistenz-Ulf-Lücken schließen ─
    # Sicherheitsnetz: läuft nach allen anderen Schritten und konvertiert
    # Behandlung → Anmeldung/Assistenz Ulf wo nötig.
    for di in range(5):
        if is_feiertag(di, dates):
            continue

        def _fd_anm():
            return any("FD" in plan[p][di] and "Anmeldung" in plan[p][di] for p in TFAS)
        def _sd_anm():
            return any("SD" in plan[p][di] and "Anmeldung" in plan[p][di] for p in TFAS)
        def _fd_ulf():
            return any("FD" in plan[p][di] and "Assistenz Ulf" in plan[p][di] for p in TFAS)
        def _sd_ulf():
            return any("SD" in plan[p][di] and "Assistenz Ulf" in plan[p][di] for p in TFAS)

        # FD:Anmeldung fehlt → ersten FD:Behandlung (nicht Pauline) umwandeln
        if not _fd_anm():
            for p in TFAS:
                if p == "Pauline":
                    continue
                v = plan[p][di]
                if v.startswith("FD") and "Behandlung" in v and "Assistenz" not in v:
                    plan[p][di] = "FD: Anmeldung"
                    break

        # SD:Anmeldung fehlt → ersten SD:Behandlung (nicht Pauline) umwandeln
        if not _sd_anm():
            for p in TFAS:
                if p == "Pauline":
                    continue
                v = plan[p][di]
                if v.startswith("SD") and "Behandlung" in v and "Assistenz" not in v:
                    plan[p][di] = "SD: Anmeldung"
                    break

        # Ulf anwesend: FD:Assistenz Ulf fehlt → ersten FD:Behandlung umwandeln
        if ulf_da(di) and not _fd_ulf():
            for p in TFAS:
                v = plan[p][di]
                if v.startswith("FD") and "Behandlung" in v and "Assistenz" not in v:
                    plan[p][di] = "FD: Assistenz Ulf"
                    break

        # Ulf anwesend: SD:Assistenz Ulf fehlt → ersten SD:Behandlung umwandeln
        if ulf_da(di) and not _sd_ulf():
            for p in TFAS:
                v = plan[p][di]
                if v.startswith("SD") and "Behandlung" in v and "Assistenz" not in v:
                    plan[p][di] = "SD: Assistenz Ulf"
                    break

    return plan


# ---------------------------------------------------------------------------
# Füll-Logik
# ---------------------------------------------------------------------------

def _fill_remaining(plan, kw_num, is_even, vacations, dates, auffl,
                     deborah_deckt_anmeldung_mo):
    from rules import get_shift, is_skip

    def can_fill(p, di):
        """Gibt True zurück, wenn die Zelle befüllt werden kann (nicht geschützt, nicht absent)."""
        return (plan[p][di] == "–"                       # nur echte Leerstellen
                and not person_absent(p, di, vacations, dates, kw_num)
                and kw_num < PERSONAL_EXIT.get(p, 999))

    def anm_covered(di):
        fd_a = sd_a = False
        for p in plan:
            v = str(plan[p][di])
            if "Anmeldung" in v:
                if v.startswith("FD"):   fd_a = True
                elif v.startswith("SD"): sd_a = True
        return fd_a, sd_a

    def balance(di):
        fd = sd = 0
        for p in ("Kristin", "Deborah", "Imke", "Nadine", "Nicolas",
                  "Alyssa", "Natalie", "Pauline"):
            v = plan[p][di]
            if is_skip(v): continue
            sh = get_shift(v)
            if sh == "FD":    fd += 1
            elif sh == "SD":  sd += 1
            elif sh == "BOTH": fd += 1; sd += 1
        return fd, sd

    # Paritätssensitive Verarbeitungsreihenfolge
    if is_even:
        # Gerade KW: Nadine=FD:Anmeldung, Nicolas=SD:Anmeldung (aus Excel-Muster)
        FILL_ORDER = ("Nadine", "Nicolas", "Alyssa", "Imke", "Deborah",
                      "Natalie", "Kristin", "Pauline")
        FD_ANM_PRIO = ("Nadine", "Nicolas", "Alyssa", "Imke", "Kristin")
        SD_ANM_PRIO = ("Nicolas", "Nadine", "Alyssa", "Imke", "Kristin")
    else:
        # Ungerade KW: Imke vor Nadine → Imke nimmt SD:Anmeldung zuerst
        FILL_ORDER = ("Alyssa", "Nicolas", "Imke", "Nadine", "Deborah",
                      "Natalie", "Kristin", "Pauline")
        # Erweitert: Nicolas, Natalie, Imke, Nadine können FD:Anmeldung übernehmen
        FD_ANM_PRIO = ("Alyssa", "Nicolas", "Natalie", "Imke", "Nadine", "Kristin")
        SD_ANM_PRIO = ("Imke", "Nadine", "Alyssa", "Nicolas", "Kristin")

    for di in range(5):
        if is_feiertag(di, dates):
            continue
        for person in FILL_ORDER:
            if not can_fill(person, di):
                continue

            # Deborah: Paritätspflicht (gerade→FD, ungerade→SD).
            # Übernimmt Anmeldung ihrer Schicht wenn noch keine vorhanden → sonst Behandlung.
            if person == "Deborah":
                shift = "FD" if is_even else "SD"
                fd_anm_now, sd_anm_now = anm_covered(di)
                anm_now = fd_anm_now if shift == "FD" else sd_anm_now
                plan[person][di] = f"{shift}: Anmeldung" if not anm_now else f"{shift}: Behandlung"
                continue

            # Imke: Mo in geraden KWs — Anmeldungs-Verteilung
            if person == "Imke" and is_even and di == 0:
                fd_anm_now, sd_anm_now = anm_covered(di)
                fd_now, sd_now = balance(di)
                shift = "FD" if fd_now <= sd_now else "SD"
                if not fd_anm_now and not sd_anm_now and deborah_deckt_anmeldung_mo:
                    # Deborah übernimmt FD:Anmeldung → Imke deckt SD:Anmeldung ab
                    plan[person][di] = "SD: Anmeldung"
                elif not fd_anm_now:
                    plan[person][di] = "FD: Anmeldung"
                elif not sd_anm_now:
                    plan[person][di] = "SD: Anmeldung"
                else:
                    plan[person][di] = f"{shift}: Behandlung"
                continue

            # Nadine Mi in ungeraden KWs: bevorzugt FD:Anmeldung, dann SD:Anmeldung
            if person == "Nadine" and di == 2 and not is_even:
                fd_anm_now, sd_anm_now = anm_covered(di)
                fd_now, sd_now = balance(di)
                shift = "FD" if fd_now <= sd_now else "SD"
                if not fd_anm_now:
                    plan[person][di] = "FD: Anmeldung"
                elif not sd_anm_now:
                    plan[person][di] = "SD: Anmeldung"
                else:
                    plan[person][di] = f"{shift}: Behandlung"
                continue

            # Nadine Fr: bevorzugt FD:Anmeldung (beide Paritäten)
            if person == "Nadine" and di == 4:
                fd_anm_now, sd_anm_now = anm_covered(di)
                fd_now, sd_now = balance(di)
                shift = "FD" if fd_now <= sd_now else "SD"
                if not fd_anm_now:
                    plan[person][di] = "FD: Anmeldung"
                elif not sd_anm_now:
                    plan[person][di] = "SD: Anmeldung"
                else:
                    plan[person][di] = f"{shift}: Behandlung"
                continue

            # Nadine Do: bevorzugt SD:Anmeldung (wenn fehlt) → Deborah/andere decken FD:Anmeldung ab
            if person == "Nadine" and di == 3:
                fd_anm_now, sd_anm_now = anm_covered(di)
                fd_now, sd_now = balance(di)
                shift = "FD" if fd_now <= sd_now else "SD"
                if not sd_anm_now and not fd_anm_now:
                    plan[person][di] = "SD: Anmeldung"   # SD:Anmeldung Priorität → FD wird durch Deborah gedeckt
                elif not fd_anm_now:
                    plan[person][di] = "FD: Anmeldung"
                elif not sd_anm_now:
                    plan[person][di] = "SD: Anmeldung"
                else:
                    plan[person][di] = f"{shift}: Behandlung"
                continue

            # Pauline Do: immer SD ab 15:30
            if person == "Pauline" and di == 3:
                plan[person][di] = "SD: Behandlung (ab 15:30)"
                continue

            # Alyssa Fr: immer SD ab 15:30 (kein Anmeldungs-Override)
            if person == "Alyssa" and di == 4:
                plan[person][di] = "SD: Behandlung (ab 15:30)"
                continue

            fd_now, sd_now = balance(di)
            fd_anm, sd_anm = anm_covered(di)
            shift = "FD" if fd_now <= sd_now else "SD"

            if shift == "FD" and not fd_anm and person in FD_ANM_PRIO:
                plan[person][di] = "FD: Anmeldung"
            elif shift == "SD" and not sd_anm and person in SD_ANM_PRIO:
                plan[person][di] = "SD: Anmeldung"
            else:
                plan[person][di] = f"{shift}: Behandlung"
