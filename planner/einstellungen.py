"""
einstellungen.py — wer wird vom neuen Planer verplant, wer nicht.

Abgestimmt mit der Praxis am 01.11.2026 (siehe docs/regeln.md).
Änderungen an Personen gehören HIERHER, nicht in den Planer-Code.
"""

from config import TFAS, TFAS_MANUAL, AZUBIS

# Werden automatisch verplant (FD/SD, Anmeldung, Assistenz, Springer, Behandlung)
AUTOMATISCH = [p for p in TFAS + TFAS_MANUAL + AZUBIS if p not in ("Alyssa", "Kristin", "Emilia")]

# Werden NICHT verplant – ihre Zellen bleiben, wie sie sind (Eingabe für den Planer)
NICHT_AUTOMATISCH = {
    "Hanne":     "läuft zurzeit mit Florian mit, nur manuell",
    "Nicolette": "Empfang mit festen Arbeitszeiten (keine FD-Anmeldung)",
    "Alyssa":    "langzeitkrank (vorerst bis 11.11., voraussichtlich länger)",
    "Kristin":   "krankgeschrieben, bleibt als Krank im Plan stehen",
    "Emilia":    "neue TFA (Nov 2026), plant Nicolas vorerst manuell",
}

# Feste Abwesenheiten je Wochentag (di: 0=Mo … 4=Fr)
NIE_AM_TAG = {
    "Nina": {4},   # Nina arbeitet freitags nicht
}

# Deborah: gerade KW → FD, ungerade KW → SD; gerade KW Freitag frei
DEBORAH_SCHICHT = {True: "FD", False: "SD"}   # key: KW gerade?
DEBORAH_FREI_FR_GERADE = True

# Schreibweise der Zellen = so wie Nicolas manuell plant
SCHREIBWEISE = {
    "anmeldung":  "{s}: Anmeldung",
    "assistenz":  "{s}: Assistenz {arzt}",       # auch bei OP: "Assistenz Lisa", "Assistenz Wilke"
    "springer":   "{s}: Springer",
    "behandlung": "{s}: Behandlung",
}

# ---------------------------------------------------------------------------
# Bevorzugte Besetzung (Wunsch, keine Pflicht) — abgeleitet aus den von
# Nicolas manuell geplanten Wochen KW 36–46. Reihenfolge = Priorität.
# Deborah wird nur in ihrer Paritätsschicht eingesetzt (s.o.).
# ---------------------------------------------------------------------------
ULF_ASSISTENZ = {
    # di: {"FD": [...], "SD": [...]}
    0: {"FD": ["Matthias", "Deborah", "Molly"],          "SD": ["Nina", "Deborah", "Matthias"]},
    1: {"FD": ["Deborah", "Matthias", "Molly", "Nadine"], "SD": ["Molly", "Deborah", "Imke", "Matthias"]},
    2: {"FD": ["Deborah", "Nadine", "Molly"],            "SD": ["Molly", "Matthias", "Nina", "Nicolas", "Deborah"]},
    3: {"FD": ["Imke", "Nadine"],                        "SD": ["Deborah", "Nadine"]},
    4: {"FD": ["Imke", "Nadine"],                        "SD": ["Deborah", "Nadine"]},
}
ANMELDUNG = {
    "FD": ["Nadine", "Nicolas", "Imke", "Deborah", "Nina"],
    "SD": ["Nicolas", "Nadine", "Imke", "Deborah", "Nina"],
}
ASSISTENZ_LISA  = {"FD": ["Molly", "Nicolas", "Nina", "Nadine"], "SD": ["Nadine", "Molly", "Pauline"]}
ASSISTENZ_WILKE = {"FD": ["Imke", "Matthias", "Molly"],          "SD": ["Pauline", "Molly"]}
# Nina montags im SD bei Ulf: Nicolas schreibt "SD: Assistenz Ulf ab 15 Uhr"
