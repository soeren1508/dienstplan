"""
einstellungen.py — wer wird vom neuen Planer verplant, wer nicht.

Abgestimmt mit der Praxis am 01.11.2026 (siehe docs/regeln.md).
Änderungen an Personen gehören HIERHER, nicht in den Planer-Code.
"""

from config import TFAS, TFAS_MANUAL, AZUBIS

# Werden automatisch verplant (FD/SD, Anmeldung, Assistenz, Springer, Behandlung)
AUTOMATISCH = [p for p in TFAS + TFAS_MANUAL + AZUBIS if p not in ("Alyssa", "Kristin")]

# Werden NICHT verplant – ihre Zellen bleiben, wie sie sind (Eingabe für den Planer)
NICHT_AUTOMATISCH = {
    "Hanne":     "läuft zurzeit mit Florian mit, nur manuell",
    "Nicolette": "Empfang mit festen Arbeitszeiten (keine FD-Anmeldung)",
    "Alyssa":    "langzeitkrank, fällt länger aus",
    "Kristin":   "krankgeschrieben (voraussichtlich bis ca. Anfang Dezember), bleibt als Krank im Plan",
}

# Längere Ausfälle: der Planer trägt in alle NICHT manuell geplanten Zellen
# "Krank" ein (manuelle Einträge bleiben). Wert = letzter Tag oder None (offen).
LANGZEIT_KRANK = {
    "Kristin": None,   # voraussichtlich bis ca. Anfang Dezember
    "Alyssa":  None,
}

# Rollen, die jemand (noch) nicht übernehmen darf. Schlüssel wie in regeln._rolle_key():
#   "Anmeldung", "Assistenz Ulf", "Assistenz Lisa", "Assistenz Wilke", "Assistenz Florian", "Springer"
KANN_NICHT = {
    "Emilia":  {"Anmeldung", "Assistenz Ulf"},   # neu: OP + Behandlung ja, Ulf + Empfang noch nicht
    "Pauline": {"Anmeldung", "Assistenz Ulf"},   # Behandlung, OP, Lisa ja
}

# Emilia: jede Woche 1 Tag frei, im Wechsel Freitag / anderer Tag.
# ❓ Noch mit Emilia abzustimmen: welcher andere Tag, und in welcher KW-Parität Freitag.
# Stand 05.11.: KW 45 (ungerade) hat sie Fr frei → ungerade KW = Freitag.
EMILIA_FREI = {"gerade": None, "ungerade": 4}   # None = Tag noch offen (❓)

# Feste freie Tage (di: 0=Mo … 4=Fr), getrennt nach gerader/ungerader KW
FREIE_TAGE = {
    "Nina":   {"gerade": {4}, "ungerade": {4}},                 # nie freitags
    "Emilia": {k: ({v} if v is not None else set()) for k, v in EMILIA_FREI.items()},
    # Deborah (gerade KW Fr frei) steht unten bei DEBORAH_*
}
NIE_AM_TAG = {p: t["gerade"] & t["ungerade"] for p, t in FREIE_TAGE.items()}   # Kompatibilität


# ---------------------------------------------------------------------------
# Schule (Berufsschule)
# ---------------------------------------------------------------------------
# Pauline: Mittwoch ganztägig.
# Molly + Matthias: Do + Fr. An jedem der beiden Tage kommt EINER nach der
# Schule ab 15:30 in den SD, der andere hat ganztägig Schule; am anderen Tag
# umgekehrt. Aus dem Plan KW 37–41 abgeleitet: Wechsel alle 2 Wochen
#   KW 37–38: Do Molly ab 15:30, Fr Matthias ab 15:30
#   KW 39–40: Do Matthias ab 15:30, Fr Molly ab 15:30
#   KW 41–42: wie 37–38 …  (❓ von den Azubis noch zu bestätigen)
SCHULE_FEST = {"Pauline": {2: "ganz"}}
SCHULE_DO_FR = ("Molly", "Matthias")
SCHULE_ANKER_KW = 37          # Block 0 = Molly kommt Do ab 15:30
SCHULE_BLOCK_WOCHEN = 2
SCHULFERIEN_KW = {43, 44, 52, 53}   # Hamburg: Herbstferien, Weihnachten


def schule(person: str, kw: int, di: int) -> str | None:
    """None = keine Schule, "ganz" = ganztägig Schule, "ab 15:30" = danach SD."""
    if kw in SCHULFERIEN_KW:
        return None
    if di in SCHULE_FEST.get(person, {}):
        return SCHULE_FEST[person][di]
    if person in SCHULE_DO_FR and di in (3, 4):
        block = (kw - SCHULE_ANKER_KW) // SCHULE_BLOCK_WOCHEN
        molly_do = block % 2 == 0
        kommt_do = "Molly" if molly_do else "Matthias"
        kommt = kommt_do if di == 3 else ("Matthias" if molly_do else "Molly")
        return "ab 15:30" if person == kommt else "ganz"
    return None

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
