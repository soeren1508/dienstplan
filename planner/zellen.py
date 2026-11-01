"""
zellen.py — Zellwerte des Dienstplans in eine Struktur übersetzen.

Ein Zellwert ist Freitext, z.B.:
    "FD: Assistenz Ulf || 08:30-17:00 Uhr"   → Schicht FD, Rolle Assistenz, Arzt Ulf
    "SD: Behandlung (ab 15:30) + Auffüllen"  → Schicht SD, Rolle Behandlung, Auffüllen
    "Urlaub" / "Krank" / "Schule"            → abwesend
Alles nach " || " ist eine Notiz (Uhrzeit o.ä.) und zählt nicht zur Rolle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

LEER = {"–", "-", "", "FREI_SCHUTZ"}

# Schlüsselwörter → Abwesenheitsgrund (Reihenfolge = Priorität beim Erkennen)
ABWESEND = [
    ("Feiertag", "Feiertag"),
    ("Urlaub", "Urlaub"),
    ("Krank", "Krank"),
    ("Frei", "Frei"),
    ("Notdienst", "Notdienst"),
    ("SCHULE", "Schule"),
    ("Schule", "Schule"),
    ("Abschlussprüfung", "Prüfung"),
    ("Weiterbildung", "Fortbildung"),
    ("Fortbildung", "Fortbildung"),
    ("Strahlenkurs", "Fortbildung"),
    ("ECVO", "Fortbildung"),
]

ARZT_NAMEN = ("Ulf", "Wilke", "Florian", "Lisa", "Hanne")


@dataclass(frozen=True)
class Zelle:
    roh: str
    leer: bool = False
    abwesend: str | None = None   # Grund, falls abwesend
    schicht: str | None = None    # "FD" | "SD" | "GANZ" | None
    rolle: str | None = None      # Anmeldung | Behandlung | Assistenz | Springer | Dienst | Arzt | Empfang | Sonstiges
    arzt: str | None = None       # bei Assistenz: welcher Arzt
    op: bool = False              # Assistenz bei OP
    auffuellen: bool = False
    notiz: str = ""

    @property
    def arbeitet(self) -> bool:
        return not self.leer and self.abwesend is None

    @property
    def schluessel(self) -> str:
        """Vergleichswert für den Prüfstand: Schicht + Rolle (+ Arzt/OP)."""
        if self.leer:
            return "–"
        if self.abwesend:
            return self.abwesend
        teile = [self.schicht or "?", self.rolle or "?"]
        if self.arzt:
            teile.append(self.arzt + (" OP" if self.op else ""))
        return " ".join(teile)


def _schicht(text: str) -> str | None:
    t = text.strip()
    if t.startswith("FD"):
        return "FD"
    if t.startswith("SD"):
        return "SD"
    if "Ganztag" in t or "Tagdienst" in t:
        return "GANZ"
    # reine Uhrzeiten wie "09:00–17:00" → ganztägig
    if re.match(r"^\d{1,2}[:.]?\d{0,2}\s*[–-]", t):
        return "GANZ"
    return None


def parse(wert) -> Zelle:
    roh = "–" if wert is None else str(wert)
    haupt, _, notiz = roh.partition(" || ")
    h = haupt.strip()

    if h in LEER:
        return Zelle(roh=roh, leer=True, notiz=notiz)

    hat_schicht = h.startswith(("FD", "SD"))
    if not hat_schicht:   # "SD: Assistenz Lisa ab 15:30 wegen Schule" ist KEINE Abwesenheit
        for wort, grund in ABWESEND:
            if wort in h:
                # "Schule ab 15:30" / "Schule 15:30 bei Lisa" → arbeitet ab Nachmittag
                if grund == "Schule" and re.search(r"\d{1,2}:\d{2}", h):
                    arzt = next((a for a in ARZT_NAMEN if a in h), None)
                    return Zelle(roh=roh, schicht="SD", rolle="Assistenz" if arzt else "Behandlung",
                                 arzt=arzt, notiz=notiz or h)
                return Zelle(roh=roh, abwesend=grund, notiz=notiz)

    schicht = _schicht(h)
    if "Mitteldienst" in h:
        schicht = "GANZ"
    # Rolle = das ZUERST genannte Schlüsselwort (Praxis-Schreibweise, z.B.
    # "SD: Assistenz Ulf + dann Anmeldung zum lernen" → Assistenz,
    #  "SD: Springer Anmeldung zum lernen" → Springer)
    rolle, arzt, op = "Sonstiges", None, False
    kandidaten = [(h.find(k), r) for k, r in (
        ("Anmeldung", "Anmeldung"), ("Assistenz", "Assistenz"), ("Springer", "Springer"),
        ("Behandlung", "Behandlung"), ("Einarbeitung", "Behandlung"), ("Mitteldienst", "Behandlung"),
    ) if k in h]
    if kandidaten:
        rolle = min(kandidaten)[1]
        if rolle == "Anmeldung" and not hat_schicht and "Mitteldienst" not in h:
            rolle = "Empfang"   # Nicolette: "Anmeldung (08:30–17:00 Uhr)"
        if rolle == "Assistenz":
            rest = h[h.find("Assistenz"):]
            arzt = next((a for a in ARZT_NAMEN if a in rest), None)
            op = "OP" in rest
    elif h == "Dienst":
        rolle = "Dienst"
    elif "OP" in h or re.search(r"\d", h):
        rolle = "Arzt"   # Arzt-Muster wie "FD OP", "SD (12–19)", "09:00–17:00"

    return Zelle(
        roh=roh, schicht=schicht, rolle=rolle, arzt=arzt, op=op,
        auffuellen="Auffüllen" in roh, notiz=notiz,
    )
