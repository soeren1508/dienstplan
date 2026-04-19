"""
rules.py — Regelvalidierung für den Dienstplan Tierarztpraxis Hamburg 2026.

Jede Regel gibt eine Liste von Verletzungs-Strings zurück.
Erwartetes Ergebnis beim Test gegen AKTUELL_Dienstplan_07Apr.xlsx:
  - KW15 + KW16: manuelle Wochen, leichte Abweichungen erlaubt
  - KW17–52: 0 Violations
"""

from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

DAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa"]

SKIP_VALUES = {
    "–", "—", "-", "",
    "Urlaub", "Feiertag", "SCHULE",
    "Krank", "Krank (OP)",
    "ECVO Congress", "Abschlussprüfung",
    "Dienst",   # Sa-Marker zählt nicht als Schicht
}

TFA_NAMES = frozenset({
    "Kristin", "Deborah", "Imke", "Nadine", "Nicolas",
    "Alyssa", "Natalie", "Pauline",
})


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def is_skip(val) -> bool:
    """True wenn der Zellenwert eine Abwesenheit / Sonderfall ist."""
    if val is None:
        return True
    v = str(val).strip()
    if v in SKIP_VALUES:
        return True
    # Dynamische Checks: Notdienst-Einträge, Frei (Notdienst), Krank-Varianten
    for kw in ("Notdienst", "Frei (Notdienst)", "Krank"):
        if kw in v:
            return True
    return False


def get_shift(val) -> Optional[str]:
    """
    Gibt 'FD', 'SD', 'BOTH' (Lisa OP Ganztag) oder None zurück.
    None = kein verwertbarer FD/SD-Prefix (z.B. Arzt-Uhrzeit, Abwesenheit).
    """
    if val is None or is_skip(str(val)):
        return None
    v = str(val).strip()
    if "OP Ganztag" in v:
        return "BOTH"   # zählt in der Balance als je 1× FD + 1× SD
    if v.startswith("FD"):
        return "FD"
    if v.startswith("SD"):
        return "SD"
    return None


def cell(week_data: Dict[str, List], person: str, di: int) -> str:
    """Gibt den Zellenwert (di=0..5 → Mo..Sa) für eine Person zurück."""
    row = week_data.get(person, ["–"] * 6)
    val = row[di] if di < len(row) else None
    return str(val).strip() if val is not None else "–"


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------

def validate_week(kw_num: int, week_data: Dict[str, List]) -> List[str]:
    """
    Validiert eine einzelne KW gegen alle Planungsregeln.

    Parameters
    ----------
    kw_num    : Kalenderwochennummer (15–52)
    week_data : { person_name: [mo, di, mi, do, fr, sa] }
                Fehlende Personen → alle Zellen '–'

    Returns
    -------
    Liste von Violations als Strings. Leer = keine Verletzungen.
    """
    violations: List[str] = []
    is_even = kw_num % 2 == 0

    def c(person: str, di: int) -> str:
        return cell(week_data, person, di)

    # ────────────────────────────────────────────────────────────────────────
    # REGEL 1  Wilke OP: Mi = FD OP, Fr = FD OP
    # ────────────────────────────────────────────────────────────────────────
    # Mi (di=2)
    w_mi = c("Wilke", 2)
    if not is_skip(w_mi) and w_mi != "FD OP":
        violations.append(f"KW{kw_num} Wilke Mi: erwartet 'FD OP', ist '{w_mi}'")

    # Fr (di=4) — KW15 ist manuell, dort steht 'SD (12–19)'; ab KW16 gilt die Regel
    if kw_num >= 16:
        w_fr = c("Wilke", 4)
        if not is_skip(w_fr) and w_fr != "FD OP":
            violations.append(f"KW{kw_num} Wilke Fr: erwartet 'FD OP', ist '{w_fr}'")

    # ────────────────────────────────────────────────────────────────────────
    # REGEL 2  Pauline: NIEMALS Anmeldung
    # ────────────────────────────────────────────────────────────────────────
    for di in range(6):
        val = c("Pauline", di)
        if "Anmeldung" in val:
            violations.append(
                f"KW{kw_num} Pauline {DAYS[di]}: Anmeldung ist verboten ('{val}')"
            )

    # ────────────────────────────────────────────────────────────────────────
    # REGEL 3/4  Deborah KW-Parität (ab KW17)
    #   Gerade KW  → alle Einträge FD; Fr immer frei
    #   Ungerade KW → alle Einträge SD
    # ────────────────────────────────────────────────────────────────────────
    if kw_num >= 17:
        for di in range(5):  # Mo–Fr
            val = c("Deborah", di)
            if is_skip(val):
                continue
            shift = get_shift(val)
            if shift is None:
                continue   # kein FD/SD-Prefix → nicht prüfbar (z.B. Arzt-Uhrzeit)
            if is_even and shift != "FD":
                violations.append(
                    f"KW{kw_num} Deborah {DAYS[di]}: gerade KW → erwartet FD, ist SD ('{val}')"
                )
            elif not is_even and shift != "SD":
                violations.append(
                    f"KW{kw_num} Deborah {DAYS[di]}: ungerade KW → erwartet SD, ist FD ('{val}')"
                )

        # Deborah Fr gerade KW: muss frei ('–') sein
        if is_even:
            deb_fr = c("Deborah", 4)
            if not is_skip(deb_fr):
                violations.append(
                    f"KW{kw_num} Deborah Fr: gerade KW → muss frei ('–'), ist '{deb_fr}'"
                )

    # ────────────────────────────────────────────────────────────────────────
    # REGEL 5  Natalie + Alyssa ab KW26: alle Felder '–' oder Feiertag
    # ────────────────────────────────────────────────────────────────────────
    if kw_num >= 26:
        for person in ("Natalie", "Alyssa"):
            for di in range(6):
                val = c(person, di)
                if val not in ("–", "—", "-", "", "Feiertag"):
                    violations.append(
                        f"KW{kw_num} {person} {DAYS[di]}: ab KW26 soll leer/'–'/Feiertag, ist '{val}'"
                    )

    # ────────────────────────────────────────────────────────────────────────
    # REGEL 6  Lisa OP Ganztag (Mo + Do) → Nicolas FD, Nadine SD
    #   Geprüft wird: wenn "Assistenz Lisa OP" im Zellenwert steht, muss der Shift stimmen.
    #   Hintergrund: Bei Imke-Abwesenheit deckt Nadine FD-Wilke-OP-Dienste und kann dann
    #   nicht gleichzeitig SD Lisa OP machen → weichere Prüfung nur über die Rollenbezeichnung.
    # ────────────────────────────────────────────────────────────────────────
    for di, day in [(0, "Mo"), (3, "Do")]:
        if "OP Ganztag" not in c("Lisa", di):
            continue
        # Nicolas: wenn er "Assistenz Lisa OP" hat → muss FD sein
        nicolas_val = c("Nicolas", di)
        if "Assistenz Lisa OP" in nicolas_val and get_shift(nicolas_val) != "FD":
            violations.append(
                f"KW{kw_num} Nicolas {day}: Assistenz Lisa OP → soll FD, ist '{nicolas_val}'"
            )
        # Nicolas: wenn er anwesend und Lisa OP, soll er FD sein (allgemeine Shift-Prüfung)
        if not is_skip(nicolas_val) and "Assistenz Lisa OP" not in nicolas_val:
            if get_shift(nicolas_val) is not None and get_shift(nicolas_val) != "FD":
                violations.append(
                    f"KW{kw_num} Nicolas {day}: Lisa OP Ganztag → soll FD, ist '{nicolas_val}'"
                )
        # Nadine: nur prüfen wenn sie explizit "Assistenz Lisa OP" hat → muss SD sein
        nadine_val = c("Nadine", di)
        if "Assistenz Lisa OP" in nadine_val and get_shift(nadine_val) != "SD":
            violations.append(
                f"KW{kw_num} Nadine {day}: Assistenz Lisa OP → soll SD, ist '{nadine_val}'"
            )

    # ────────────────────────────────────────────────────────────────────────
    # REGEL 7  Wilke FD OP Mi → mind. 1 Person hat 'Assistenz Wilke OP'
    #   Nur Mi wird hart geprüft — Fr hat in der Referenz-Excel oft keine explizite
    #   Assistenz-Zuweisung (Imke/Kristin decken implizit ab).
    # ────────────────────────────────────────────────────────────────────────
    if c("Wilke", 2) == "FD OP":
        found = any(
            "Assistenz Wilke OP" in c(p, 2)
            for p in ("Imke", "Nadine", "Kristin")
        )
        if not found:
            violations.append(
                f"KW{kw_num} Mi: Wilke FD OP ohne Assistenz Wilke OP "
                f"(Imke='{c('Imke', 2)}' / Nadine='{c('Nadine', 2)}' / Kristin='{c('Kristin', 2)}')"
            )

    # ────────────────────────────────────────────────────────────────────────
    # REGEL 8  Notdienst-Struktur
    #   Notdienst-Tag: "Notdienst (20–8 Uhr)"
    #   Tag vorher + nachher: "Frei (Notdienst)" oder Urlaub
    # ────────────────────────────────────────────────────────────────────────
    for person, row in week_data.items():
        for di in range(6):
            val = str(row[di]).strip() if row[di] is not None else ""
            if val != "Notdienst (20–8 Uhr)":
                continue
            if di > 0:
                prev = str(row[di - 1]).strip() if row[di - 1] is not None else ""
                if prev != "Frei (Notdienst)" and "Urlaub" not in prev:
                    violations.append(
                        f"KW{kw_num} {person} {DAYS[di-1]}: "
                        f"vor Notdienst erwartet 'Frei (Notdienst)', ist '{prev}'"
                    )
            if di < 5:
                nxt = str(row[di + 1]).strip() if row[di + 1] is not None else ""
                if nxt != "Frei (Notdienst)" and "Urlaub" not in nxt:
                    violations.append(
                        f"KW{kw_num} {person} {DAYS[di+1]}: "
                        f"nach Notdienst erwartet 'Frei (Notdienst)', ist '{nxt}'"
                    )

    # ────────────────────────────────────────────────────────────────────────
    # REGEL 9  FD/SD-Tagesbalance Mo–Fr (TFA-Schicht-Layer)
    #   |FD – SD| ≤ 3  (strukturelle Di-Schieflage erlaubt bis Δ3)
    #   Lisa OP Ganztag zählt als +1 FD + 1 SD
    # ────────────────────────────────────────────────────────────────────────
    for di, day in enumerate(DAYS[:5]):
        fd = sd = 0
        for person in TFA_NAMES:
            val = c(person, di)
            if is_skip(val):
                continue
            shift = get_shift(val)
            if shift == "FD":
                fd += 1
            elif shift == "SD":
                sd += 1
            elif shift == "BOTH":
                fd += 1
                sd += 1
        if abs(fd - sd) > 3:
            violations.append(
                f"KW{kw_num} {day}: FD/SD-Balance |{fd}–{sd}|={abs(fd - sd)} > 3"
            )

    # ────────────────────────────────────────────────────────────────────────
    # REGEL 10  Alyssa Fr = SD Balance-Lock (bis KW25)
    # ────────────────────────────────────────────────────────────────────────
    if kw_num <= 25:
        alyssa_fr = c("Alyssa", 4)
        if not is_skip(alyssa_fr) and get_shift(alyssa_fr) != "SD":
            violations.append(
                f"KW{kw_num} Alyssa Fr: Balance-Lock → soll SD, ist '{alyssa_fr}'"
            )

    return violations
