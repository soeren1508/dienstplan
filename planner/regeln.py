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

from config import TFAS
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


def tfa_zellen(w: Woche, di: int, personen=TFAS):
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
       "Hat Lisa 'OP Ganztag', gibt es in FD und SD je eine OP-Assistenz.")
def _lisa_op(w: Woche):
    v = []
    for di in werktage(w):
        if "OP Ganztag" not in str(w.plan.get("Lisa", ["–"] * 6)[di]):
            continue
        for sch in ("FD", "SD"):
            if not _besetzung(w, di, sch, "Assistenz", arzt="Lisa", op=True):
                v.append(Verstoss("assistenz_lisa_op", di, f"Lisa OP → {sch}: Assistenz fehlt"))
    return v


@regel("assistenz_wilke_op", "pflicht",
       "Hat Wilke 'FD OP', gibt es eine OP-Assistenz (Ausnahme: Fr in ungeraden KWs, wenn Imke arbeitet).")
def _wilke_op(w: Woche):
    v = []
    for di in werktage(w):
        if "FD OP" not in str(w.plan.get("Wilke", ["–"] * 6)[di]):
            continue
        hat = [p for p, z in tfa_zellen(w, di).items()
               if z.arbeitet and z.rolle == "Assistenz" and z.arzt == "Wilke" and z.op]
        ausnahme = di == 4 and not w.gerade and parse(w.plan["Imke"][di]).arbeitet
        if not hat and not ausnahme:
            v.append(Verstoss("assistenz_wilke_op", di, "Wilke OP → Assistenz fehlt"))
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
