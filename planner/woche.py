"""
woche.py — Wochen-Kontext für Planer und Regeln.

Eine `Woche` bündelt alles, was ein Planer wissen muss:
    kw, dates            Kalenderwoche und die 6 Tage (Mo–Sa)
    plan                 {person: [6 Zellwerte]}  (Ist-Plan oder Vorschlag)
    gesperrt             {person: {di: wert}}     manuelle Einträge, die nie
                                                  überschrieben werden dürfen
    urlaub, krank        {person: set[date]}      aus Urlaubsplanung + Korrekturen

`lade_ist_wochen()` holt die echten Wochen (Basis + manuelle Overrides)
über app.py, damit Prüfstand/Analyse exakt das sehen, was die App zeigt.
"""

from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass, field
from datetime import date

from config import FEIERTAGE_HH_2026, ALL_PERSONS


@dataclass
class Woche:
    kw: int
    dates: list[date]
    plan: dict[str, list[str]]
    gesperrt: dict[str, dict[int, str]] = field(default_factory=dict)
    urlaub: dict[str, set] = field(default_factory=dict)
    krank: dict[str, set] = field(default_factory=dict)

    @property
    def gerade(self) -> bool:
        return self.kw % 2 == 0

    def feiertag(self, di: int) -> bool:
        return self.dates[di] in FEIERTAGE_HH_2026

    def kopie_mit(self, plan: dict[str, list[str]]) -> "Woche":
        return Woche(self.kw, self.dates, plan, self.gesperrt, self.urlaub, self.krank)


def _app():
    """app.py lazy importieren (Startausgaben unterdrücken)."""
    with contextlib.redirect_stdout(io.StringIO()):
        import app  # noqa: WPS433
    return app


def lade_ist_wochen(kws) -> dict[int, Woche]:
    """Echte Wochen so, wie die App sie zeigt (Basis-Plan + Overrides)."""
    from scheduler import week_dates

    app = _app()
    overrides = app._load_overrides()
    urlaub, krank = app._get_all_vac(), app._get_all_krank()
    wochen = {}
    for kw in kws:
        kw_ov = overrides.get(str(kw), {})
        gesperrt = {p: {int(di): v for di, v in d.items()} for p, d in kw_ov.items()
                    if p in ALL_PERSONS}
        wochen[kw] = Woche(
            kw=kw, dates=week_dates(kw), plan=app._plan_for_kw(kw, overrides),
            gesperrt=gesperrt, urlaub=urlaub, krank=krank,
        )
    return wochen


def basis_plan(kw: int) -> dict[str, list[str]]:
    """Plan des alten scheduler.py (ohne manuelle Overrides)."""
    app = _app()
    base = app._plan_cache.get(kw, {})
    return {p: list(base.get(p, ["–"] * 6)) for p in ALL_PERSONS}
