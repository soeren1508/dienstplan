"""
config.py — Alle Konstanten für den Dienstplan Tierarztpraxis Hamburg 2026.
"""

from datetime import date

# ---------------------------------------------------------------------------
# Schultage (di=0=Mo … di=4=Fr)
# Platzhalter – leicht änderbar
# ---------------------------------------------------------------------------
SCHULTAGE = {
    "Alyssa":   [3],   # Do
    "Natalie":  [1],   # Di
    "Pauline":  [2],   # Mi
    "Molly":    [3],   # Do (Platzhalter)
    "Matthias": [1],   # Di (Platzhalter)
}

# KWs, in denen kein Schultag stattfindet (Schulferien, Prüfungsblöcke etc.)
# Abgeleitet aus AKTUELL_Dienstplan_07Apr.xlsx
SCHUL_AUSFALL: dict[str, set[int]] = {
    "Natalie": {16, 20},                     # KW16=Osterferien, KW20=Pfingstferien
    "Pauline": {16, 29, 30, 33, 34, 43, 52}, # Osterferien, Sommerferien, Herbstferien, Weihnachten
    "Alyssa":  {16},                          # Osterferien (KW15: Halbtagsschule+OP)
}

# ---------------------------------------------------------------------------
# Feiertage Hamburg 2026 (relevant für KW15–52)
# ---------------------------------------------------------------------------
FEIERTAGE_HH_2026: set[date] = {
    date(2026, 4, 6),   # Ostermontag      → KW15 Mo
    date(2026, 5, 1),   # Tag der Arbeit   → KW18 Fr
    date(2026, 5, 14),  # Christi Himmelfahrt → KW20 Do
    date(2026, 5, 25),  # Pfingstmontag    → KW22 Mo
    date(2026, 10, 3),  # Tag d. Dt. Einheit → KW40 Sa
    date(2026, 12, 25), # 1. Weihnachtstag → KW52 Fr
    date(2026, 12, 26), # 2. Weihnachtstag → KW52 Sa
}

# ---------------------------------------------------------------------------
# Arzt-Basismuster (wenn anwesend, kein Urlaub/Feiertag)
# Index: 0=Mo, 1=Di, 2=Mi, 3=Do, 4=Fr, 5=Sa
# Sa = "–" als Platzhalter, wird von Sa-Rotation überschrieben
# ---------------------------------------------------------------------------
ARZT_PATTERNS = {
    "Ulf":     ["09:00–17:00", "09:00–17:00", "09:00–17:00", "–", "–",        "–"],
    "Wilke":   ["FD (09–16)",  "SD (12–19)",  "FD OP",       "SD (12–19)", "FD OP",       "–"],
    "Florian": ["SD (13–19)",  "FD (09–14)",  "SD (12–19)",  "FD (09–16)", "FD (09–16)",  "–"],
    "Lisa":    ["OP Ganztag",  "FD (09–16)",  "09–12 Uhr",   "OP Ganztag", "SD (12–19)",  "–"],
}

# ---------------------------------------------------------------------------
# Personalzeitlinie
# ---------------------------------------------------------------------------
PERSONAL_EXIT = {
    "Natalie": 26,   # ab KW26 ← alle Felder '–'
    "Alyssa":  26,
}

PERSONAL_ENTRY = {
    "Molly_mini":  {"kw_start": 19, "kw_end": 27, "mode": "minijob"},
    "Matthias":    {"kw_start": 31, "mode": "tandem"},
    "Molly_azubi": {"kw_start": 31, "mode": "tandem"},
}

# ---------------------------------------------------------------------------
# Urlaub-Korrekturen (Person, kw, di) — Tage die in der Urlaubsplanung fehlen
# ---------------------------------------------------------------------------
VACATION_OVERRIDES: list[tuple] = [
    ("Natalie", 23, 0),   # KW23 Mo: fehlt in Urlaubsdatei, Ref zeigt Urlaub
    ("Natalie", 23, 5),   # KW23 Sa
    ("Alyssa",  23, 5),   # KW23 Sa
    ("Florian", 24, 5),   # KW24 Sa
    ("Kristin", 25, 5),   # KW25 Sa
    ("Nicolas", 27, 5),   # KW27 Sa
    ("Imke",    28, 5),   # KW28 Sa
    ("Nicolas", 28, 5),   # KW28 Sa
    ("Wilke",   30, 5),   # KW30 Sa
    ("Deborah", 30, 5),   # KW30 Sa
    ("Pauline", 31, 5),   # KW31 Sa
    ("Nadine",  34, 5),   # KW34 Sa
    ("Imke",    37, 5),   # KW37 Sa
    ("Kristin", 21, 4),   # KW21 Fr: fehlt in Urlaubsdatei, Ref zeigt Urlaub
]

# ---------------------------------------------------------------------------
# Prüfungstage (Person, kw, di)  — di=0..4
# ---------------------------------------------------------------------------
PRUEFUNGSTAGE: list[tuple] = [
    ("Natalie", 23, 1),   # KW23 Di
    ("Natalie", 23, 2),   # KW23 Mi
    ("Alyssa",  23, 1),
    ("Alyssa",  23, 2),
]

# ---------------------------------------------------------------------------
# Notdienste (aus Referenz-Excel, nicht aus Prompt-Config)
# Format: (Arzt, TFA, kw, di)
# Abgeleitet aus AKTUELL_Dienstplan_07Apr.xlsx:
#   KW36 Mi (02.09.): Florian + Kristin
#   KW49 Do (03.12.): Wilke + Imke
# ---------------------------------------------------------------------------
NOTDIENSTE: list[tuple] = [
    ("Florian", "Kristin", 36, 2),   # KW36 Mi
    ("Wilke",   "Imke",    49, 3),   # KW49 Do
]

# ---------------------------------------------------------------------------
# Samstags-Arzt-Rotation (direkt aus Excel abgeleitet – Ground Truth)
# None = Feiertag oder kein Dienst
# ---------------------------------------------------------------------------
SA_ARZT: dict[int, str | None] = {
    15: "Wilke",   16: "Lisa",    17: "Florian", 18: "Florian",
    19: "Wilke",   20: "Lisa",    21: "Florian", 22: "Wilke",
    23: "Lisa",    24: "Lisa",    25: "Wilke",   26: "Florian",
    27: "Lisa",    28: "Wilke",   29: "Florian", 30: "Lisa",
    31: "Wilke",   32: "Florian", 33: "Lisa",    34: "Wilke",
    35: "Florian", 36: "Lisa",    37: "Wilke",   38: "Florian",
    39: "Wilke",   40: None,
    41: "Florian", 42: "Lisa",    43: "Wilke",   44: "Florian",
    45: "Lisa",    46: "Wilke",   47: "Florian", 48: "Lisa",
    49: "Wilke",   50: "Florian", 51: "Lisa",    52: None,
}

# Samstags-TFA-Rotation (direkt aus Excel abgeleitet – Ground Truth)
# None = keine TFA (Urlaub-Engpass oder Sommer)
SA_TFA: dict[int, str | None] = {
    15: "Imke",    16: "Nadine",  17: "Kristin", 18: "Alyssa",
    19: "Kristin", 20: "Imke",    21: "Nicolas", 22: "Nicolas",
    23: "Kristin", 24: "Imke",    25: "Alyssa",  26: None,
    27: "Nadine",  28: None,      29: "Nicolas", 30: None,
    31: "Kristin", 32: "Imke",    33: "Nadine",  34: "Nicolas",
    35: None,      36: None,      37: "Kristin", 38: "Nadine",
    39: "Imke",    40: None,
    41: "Nicolas", 42: None,      43: None,      44: "Kristin",
    45: "Imke",    46: "Nadine",  47: "Nicolas", 48: None,
    49: None,      50: "Kristin", 51: "Imke",    52: None,
}

# ---------------------------------------------------------------------------
# ECVO Congress (Florian)
# ---------------------------------------------------------------------------
ECVO_TAGE: list[tuple] = [
    ("Florian", 22, 2),   # KW22 Mi
    ("Florian", 22, 3),   # KW22 Do
    ("Florian", 22, 4),   # KW22 Fr
]

# ---------------------------------------------------------------------------
# Spezial-Assignments
# ---------------------------------------------------------------------------
SPEZIAL: list[tuple] = [
    # (Person, kw, di, wert)
    ("Florian", 52, 3, "FD (09–16)"),   # Heiligabend 24.12. KW52 Do → Florian Dienst
    ("Ulf",     15, 3, "09:00–17:00"),  # KW15 Do → Ulf arbeitet (abweichend vom Basismuster)
]

# ---------------------------------------------------------------------------
# Urlaubsplanung 2026: Nachname → Vorname-Mapping (für parse_vacations)
# ---------------------------------------------------------------------------
NACHNAME_ZU_VORNAME: dict[str, str] = {
    "Krohn":      "Ulf",
    "Gädeken":    "Wilke",
    "Jäger":      "Lisa",
    "Grosser":    "Florian",
    "Bünger":     "Nicolas",
    "Herzog":     "Kristin",
    "Wildenhain": "Deborah",
    "Leonhard":   "Imke",
    "Engel":      "Nadine",
    "Andic":      "Alyssa",
    "Bormann":    "Pauline",
    "Lepak":      "Natalie",
}

# ---------------------------------------------------------------------------
# Vollständige Personenliste (Planungs-Reihenfolge)
# ---------------------------------------------------------------------------
ALL_PERSONS = [
    "Ulf", "Wilke", "Florian", "Lisa",
    "Kristin", "Deborah", "Imke", "Nadine", "Nicolas",
    "Alyssa", "Natalie", "Pauline",
]
ARZTE = ["Ulf", "Wilke", "Florian", "Lisa"]
TFAS  = ["Kristin", "Deborah", "Imke", "Nadine", "Nicolas", "Alyssa", "Natalie", "Pauline"]

# ---------------------------------------------------------------------------
# Tage-Mapping
# ---------------------------------------------------------------------------
DAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa"]
