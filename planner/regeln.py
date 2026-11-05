"""
regeln.py — das Regelwerk.

Jede Regel ist ein eigener, kleiner Baustein:
    id        stabiler Schlüssel (für Doku, Prüfstand, Ausnahmen)
    art       "pflicht" (muss erfüllt sein) oder "wunsch" (möglichst erfüllen)
    gewicht   Strafpunkte pro Verstoß (für Wünsche; Pflicht zählt separat)
    text      Beschreibung in Alltagssprache
    pruefe    Funktion(Woche) -> Liste von Verstößen

Neue Regel = neue Funktion mit @regel(...). Der Planer (später) und der
Prüfstand lesen nur REGELN — es gibt keine zweite, versteckte Regelquelle.

STAND: Startbestand = die Prüfungen aus app._validate_plan(), unverändert
übernommen. Das neue Regelwerk wird in docs/regeln.md mit dem Nutzer
abgestimmt und dann hier umgesetzt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from config import TFAS, TFAS_MANUAL, AZUBIS

# Alle, die Pflichtrollen (Anmeldung, Assistenz) besetzen können.
# Hanne (Ärztin, läuft mit Florian mit) und Nicolette (Empfang, feste Zeiten) nicht.
PLANBAR = TFAS + TFAS_MANUAL + AZUBIS
from .woche import Woche
from .zellen import parse

TAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa"]


@dataclass(frozen=True)
class Verstoss:
    regel: str
    di: int
    text: str
    person: str | None = None


@dataclass(frozen=True)
class Regel:
    id: str
    art: str
    gewicht: int
    text: str
    pruefe: Callable[[Woche], list[Verstoss]]


REGELN: list[Regel] = []


def regel(id: str, art: str, text: str, gewicht: int = 10):
    assert art in ("pflicht", "wunsch")

    def deko(fn):
        REGELN.append(Regel(id, art, gewicht, text, fn))
        return fn
    return deko


# ── Hilfen ────────────────────────────────────────────────────────────────

def werktage(w: Woche):
    """Mo–Fr ohne Feiertage."""
    return [di for di in range(5) if not w.feiertag(di)]


def tfa_zellen(w: Woche, di: int, personen=PLANBAR):
    return {p: parse(w.plan[p][di]) for p in personen if p in w.plan}


def _besetzung(w, di, schicht, rolle, arzt=None, op=None):
    out = []
    for p, z in tfa_zellen(w, di).items():
        if not z.arbeitet or z.schicht != schicht or z.rolle != rolle:
            continue
        if arzt and z.arzt != arzt:
            continue
        if op is not None and z.op != op:
            continue
        out.append(p)
    return out


def lisa_op(w, di) -> bool:
    """Lisa operiert ganztags ("OP Ganztag", "OP (Ganztag)", "OP 09:00-17:00 Uhr")."""
    z = str(w.plan.get("Lisa", ["–"] * 6)[di]).split(" || ")[0]
    return z.startswith("OP")


def _arzt_da(w, arzt, di):
    return arzt in w.plan and parse(w.plan[arzt][di]).arbeitet


# ── Startbestand (aus app._validate_plan) ───────────────────────────────────

@regel("anmeldung_fd_sd", "pflicht",
       "Sobald in einer Schicht TFAs arbeiten, ist die Anmeldung in FD und SD je genau einmal besetzt.")
def _anmeldung(w: Woche):
    v = []
    for di in werktage(w):
        zellen = tfa_zellen(w, di)
        for sch in ("FD", "SD"):
            aktiv = [p for p, z in zellen.items() if z.arbeitet and z.schicht == sch]
            anm = _besetzung(w, di, sch, "Anmeldung")
            if aktiv and not anm:
                v.append(Verstoss("anmeldung_fd_sd", di, f"{sch}: Anmeldung fehlt"))
            for p in anm[1:]:
                v.append(Verstoss("anmeldung_fd_sd", di, f"{sch}: Anmeldung doppelt", p))
    return v


@regel("assistenz_ulf", "pflicht",
       "Ist Ulf da, hat er in FD und SD je eine Assistenz.")
def _ulf(w: Woche):
    v = []
    for di in werktage(w):
        if not _arzt_da(w, "Ulf", di):
            continue
        for sch in ("FD", "SD"):
            if not _besetzung(w, di, sch, "Assistenz", arzt="Ulf"):
                v.append(Verstoss("assistenz_ulf", di, f"Ulf da → {sch}: Assistenz fehlt"))
    return v


@regel("assistenz_lisa_op", "pflicht",
       "Operiert Lisa ganztags, hat sie in FD und SD je eine Assistenz ('Assistenz Lisa' = 'Assistenz Lisa OP').")
def _lisa_op(w: Woche):
    v = []
    for di in werktage(w):
        if not lisa_op(w, di):
            continue
        for sch in ("FD", "SD"):
            # "Assistenz Lisa" und "Assistenz Lisa OP" gelten gleich (Praxis-Schreibweise)
            if not _besetzung(w, di, sch, "Assistenz", arzt="Lisa"):
                v.append(Verstoss("assistenz_lisa_op", di, f"Lisa OP → {sch}: Assistenz fehlt"))
    return v


@regel("assistenz_wilke_op", "pflicht",
       "Hat Wilke 'FD OP', hat er eine Assistenz ('Assistenz Wilke' = 'Assistenz Wilke OP').")
def _wilke_op(w: Woche):
    v = []
    for di in werktage(w):
        if "FD OP" not in str(w.plan.get("Wilke", ["–"] * 6)[di]):
            continue
        hat = [p for p, z in tfa_zellen(w, di).items()
               if z.arbeitet and z.rolle == "Assistenz" and z.arzt == "Wilke"]
        if not hat:
            v.append(Verstoss("assistenz_wilke_op", di, "Wilke OP → Assistenz fehlt"))
    return v


@regel("freie_tage", "pflicht", "Feste freie Tage: Nina nie freitags; Emilia ungerade KW freitags (gerade KW: Tag offen).")
def _freie_tage(w: Woche):
    from .einstellungen import FREIE_TAGE
    v = []
    par = "gerade" if w.gerade else "ungerade"
    for p, tage in FREIE_TAGE.items():
        for di in tage[par]:
            if p in w.plan and parse(w.plan[p][di]).arbeitet:
                v.append(Verstoss("freie_tage", di, f"{p} eingeplant, hat an dem Tag frei", p))
    return v


@regel("deborah_wechsel", "pflicht",
       "Deborah: gerade KW Frühdienst, ungerade KW Spätdienst; gerade KW freitags frei.")
def _deborah(w: Woche):
    from .einstellungen import DEBORAH_SCHICHT, DEBORAH_FREI_FR_GERADE
    soll = DEBORAH_SCHICHT[w.gerade]
    v = []
    for di in werktage(w):
        z = parse(w.plan.get("Deborah", ["–"] * 6)[di])
        if not z.arbeitet:
            continue
        if di == 4 and w.gerade and DEBORAH_FREI_FR_GERADE:
            v.append(Verstoss("deborah_wechsel", di, "Deborah gerade KW Fr eingeplant", "Deborah"))
        elif z.schicht in ("FD", "SD") and z.schicht != soll:
            v.append(Verstoss("deborah_wechsel", di, f"Deborah {z.schicht} statt {soll}", "Deborah"))
    return v


def _rolle_key(z) -> str | None:
    if z.rolle == "Anmeldung":
        return "Anmeldung"
    if z.rolle == "Assistenz" and z.arzt:
        return f"Assistenz {z.arzt}"
    return z.rolle


@regel("rollen_verbote", "pflicht",
       "Niemand bekommt eine Rolle, die er/sie noch nicht übernehmen darf (z.B. Emilia/Pauline nicht Anmeldung, nicht bei Ulf).")
def _verbote(w: Woche):
    from .einstellungen import KANN_NICHT
    v = []
    for p, verboten in KANN_NICHT.items():
        for di in werktage(w):
            z = parse(w.plan.get(p, ["–"] * 6)[di])
            if z.arbeitet and _rolle_key(z) in verboten:
                v.append(Verstoss("rollen_verbote", di, f"{p}: {_rolle_key(z)} nicht erlaubt", p))
    return v


def arzt_schichten(wert) -> set[str]:
    """In welchen Schichten arbeitet ein Arzt laut Zelle? FD, SD oder beide."""
    import re
    z = parse(wert)
    if not z.arbeitet:
        return set()
    h = str(wert).split(" || ")[0]
    if h.startswith("FD"):   # auch "FD OP" (Wilke) = nur Frühdienst
        return {"FD"}
    if h.startswith("SD"):
        return {"SD"}
    m = re.search(r"(\d{1,2})(?::\d{2})?\s*[–-]\s*(\d{1,2})", h)
    if m:
        von, bis = int(m.group(1)), int(m.group(2))
        if bis <= 14:
            return {"FD"}
        if von >= 12:
            return {"SD"}
    return {"FD", "SD"}   # ganztags, OP, unklar


@regel("jeder_arzt_helfer", "wunsch",
       "Wenn genug Personal da ist, hat jeder anwesende Arzt in jeder Schicht, in der er arbeitet, eine Assistenz.",
       gewicht=20)
def _arzt_helfer(w: Woche):
    v = []
    for arzt in ("Wilke", "Florian", "Lisa"):   # Ulf: eigene Pflichtregel; Hanne läuft mit Florian
        for di in werktage(w):
            for sch in sorted(arzt_schichten(w.plan.get(arzt, ["–"] * 6)[di])):
                hat = [p for p, z in tfa_zellen(w, di).items()
                       if z.arbeitet and z.rolle == "Assistenz" and z.arzt == arzt
                       and z.schicht in (sch, "GANZ")]
                if not hat:
                    v.append(Verstoss("jeder_arzt_helfer", di, f"{arzt} {sch} ohne Assistenz"))
    return v


@regel("balance_fd_sd", "wunsch",
       "FD und SD sind ungefähr gleich stark besetzt (Differenz < 4).", gewicht=5)
def _balance(w: Woche):
    v = []
    for di in werktage(w):
        z = tfa_zellen(w, di)
        fd = sum(1 for x in z.values() if x.arbeitet and x.schicht == "FD")
        sd = sum(1 for x in z.values() if x.arbeitet and x.schicht == "SD")
        if (fd or sd) and abs(fd - sd) >= 4:
            v.append(Verstoss("balance_fd_sd", di, f"FD={fd}, SD={sd}"))
    return v


@regel("gesperrt_unveraendert", "pflicht",
       "Manuelle Einträge (Overrides) bleiben exakt erhalten.")
def _gesperrt(w: Woche):
    v = []
    for p, tage in w.gesperrt.items():
        for di, wert in tage.items():
            if w.plan.get(p, [None] * 6)[di] != wert:
                v.append(Verstoss("gesperrt_unveraendert", di, f"{p}: manueller Eintrag verändert", p))
    return v


# ── Auswertung ──────────────────────────────────────────────────────────────

def pruefe_alle(w: Woche) -> list[Verstoss]:
    out = []
    for r in REGELN:
        out.extend(r.pruefe(w))
    return out


def bewertung(w: Woche) -> dict:
    """Kennzahlen: Pflicht-Verstöße und Strafpunkte der Wünsche."""
    art = {r.id: r for r in REGELN}
    vs = pruefe_alle(w)
    pflicht = [x for x in vs if art[x.regel].art == "pflicht"]
    straf = sum(art[x.regel].gewicht for x in vs if art[x.regel].art == "wunsch")
    return {"pflicht": len(pflicht), "strafpunkte": straf, "verstoesse": vs}
