"""
planer.py — Planer-Schnittstelle.

Ein Planer bekommt eine Woche (mit gesperrten Zellen) und liefert einen
vollständigen Plan {person: [6 Werte]}. Gesperrte Zellen MÜSSEN unverändert
bleiben — `vorschlag()` erzwingt das zusätzlich.

Planer registrieren sich in PLANER, damit Prüfstand und App per Name wählen:
    python -m planner.pruefstand --planer baseline
"""

from __future__ import annotations

from config import ALL_PERSONS
from .woche import Woche, basis_plan
from .zellen import parse


class Planer:
    name = "?"
    beschreibung = ""

    def plane(self, w: Woche) -> dict[str, list[str]]:
        raise NotImplementedError


class BaselinePlaner(Planer):
    """Der bisherige scheduler.py — Messlatte, die der neue Planer schlagen muss."""
    name = "baseline"
    beschreibung = "alter scheduler.py (Wenn-dann-Kette)"

    def plane(self, w: Woche):
        return basis_plan(w.kw)


PLANER: dict[str, Planer] = {p.name: p for p in (BaselinePlaner(),)}
STANDARD = "baseline"   # wird unten auf "loeser" gesetzt


def vorschlag(w: Woche, planer: str | None = None) -> dict:
    """Vorschlag berechnen: gesperrte Zellen erzwingen, Änderungen auflisten.

    Rückgabe:
        plan        kompletter Vorschlagsplan
        aenderungen [{person, di, alt, neu}]  nur Zellen, die sich ändern würden
    """
    roh = PLANER[planer or STANDARD].plane(w)
    plan = {p: list(roh.get(p, w.plan.get(p, ["–"] * 6))) for p in ALL_PERSONS}
    fest = feste_zellen(w)
    for p, di in fest:
        plan[p][di] = w.plan[p][di]
    aenderungen = [
        {"person": p, "di": di, "alt": w.plan[p][di], "neu": plan[p][di]}
        for p in ALL_PERSONS for di in range(6)
        if (p, di) not in fest and plan[p][di] != w.plan[p][di]
    ]
    return {"plan": plan, "aenderungen": aenderungen}


FEST_GRUENDE = ("Urlaub", "Krank", "Feiertag")


def feste_zellen(w: Woche) -> set[tuple[str, int]]:
    """Zellen, die ein Vorschlag nie ändern darf: manuelle Einträge sowie
    Urlaub/Krank/Feiertag aus der Urlaubsplanung."""
    fest = {(p, di) for p, tage in w.gesperrt.items() for di in tage}
    for p in ALL_PERSONS:
        for di in range(6):
            if parse(w.plan.get(p, ["–"] * 6)[di]).abwesend in FEST_GRUENDE:
                fest.add((p, di))
    return fest


def nur_eingaben(w: Woche, personen) -> Woche:
    """Für den Prüfstand: Was der Planer vorab wissen darf.

    - Abwesenheiten bleiben stehen und gesperrt (echte Eingaben).
    - Ärzte, Empfang usw. bleiben wie geplant (Eingabe für die TFA-Planung).
    - Alle übrigen Zellen der zu planenden `personen` werden geleert, damit
      ein Planer die Lösung nicht einfach aus dem Ist-Plan abschreiben kann.
    """
    eing, plan = {}, {p: list(r) for p, r in w.plan.items()}
    for p, tage in w.gesperrt.items():
        keep = {di: v for di, v in tage.items() if parse(v).abwesend}
        if keep:
            eing[p] = keep
    for p in personen:
        if all(parse(v).leer for v in plan[p][:5]):
            # Person war in der Woche gar nicht eingeplant (z.B. noch nicht
            # eingestellt) → bleibt leer und gesperrt, wird nicht verplant
            eing[p] = {di: plan[p][di] for di in range(6)}
            continue
        for di in range(6):
            if not parse(plan[p][di]).abwesend:
                plan[p][di] = "–"
    return Woche(w.kw, w.dates, plan, eing, w.urlaub, w.krank)


# Neuer Planer (am Dateiende importiert, um Zirkelbezug zu vermeiden)
from .loeser import LoeserPlaner  # noqa: E402
PLANER[LoeserPlaner.name] = LoeserPlaner()
STANDARD = LoeserPlaner.name
