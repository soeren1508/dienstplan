"""
loeser.py — der neue Wochenplaner (exakte Optimierung, ohne Zusatzpakete).

Plant EINE Woche, Mo–Fr, Tag für Tag. Samstag bleibt unberührt (Rotation).

Wer wird geplant?  Nur Personen aus einstellungen.AUTOMATISCH, und nur Zellen,
                   die NICHT fest sind. Fest = manueller Eintrag (hat immer
                   Vorrang), Urlaub/Krank/Feiertag. Feste Zellen anderer
                   Personen zählen aber mit (z.B. eine manuell eingetragene
                   "FD: Anmeldung" von Nina → keine zweite nötig).

Was wird optimiert? (Strafpunkte, kleiner = besser)
    Anmeldung FD/SD fehlt ............ 1000   doppelt ........ 500
    Ulf-Assistenz FD/SD fehlt ......... 800
    OP-Arzt ohne Assistenz ............ 700
    übriger Arzt je Schicht ohne Hilfe  100
    FD/SD-Ungleichgewicht ............. 10 je Person Unterschied
    bevorzugte Besetzung .............. Bonus nach Reihenfolge in einstellungen.py
Harte Regeln: Deborah-Schicht, Rollenverbote (Emilia/Pauline), Schule ab 15:30
nur SD (keine Anmeldung), max. eine Anmeldung und eine Assistenz je Arzt und Schicht.
"""

from __future__ import annotations

from config import ALL_PERSONS
from . import einstellungen as E
from .planer import Planer, feste_zellen
from .regeln import PLANBAR, arzt_schichten, lisa_op, _rolle_key
from .woche import Woche
from .zellen import parse

SCHICHTEN = ("FD", "SD")

from config import TFAS, TFAS_MANUAL, TFAS_DISPLAY_ALS_AZUBI  # noqa: E402
# "T" = Gruppe TFAs wie in der App-Anzeige (FD/SD-Zeile), "A" = Azubis
_TFA_ANZEIGE = {p for p in TFAS + TFAS_MANUAL if p not in TFAS_DISPLAY_ALS_AZUBI}


def _gruppe(p: str) -> str:
    return "T" if p in _TFA_ANZEIGE else "A"

AERZTE_HILFE = ("Ulf", "Lisa", "Wilke", "Florian")

STRAFE = {
    "anmeldung_fehlt": 1000, "anmeldung_doppelt": 500,
    "ulf_fehlt": 800, "op_fehlt": 700, "arzt_fehlt": 100,
    "balance": 10, "balance_alle": 4, "praeferenz": 3,
}


def _wert(schicht: str, rolle: str, notiz: str = "") -> str:
    v = f"{schicht}: {rolle}"
    return f"{v} || {notiz}" if notiz else v


class LoeserPlaner(Planer):
    name = "loeser"
    beschreibung = "Optimierer (dynamische Programmierung), Regeln aus regeln.md"

    def plane(self, w: Woche) -> dict[str, list[str]]:
        plan = {p: list(w.plan.get(p, ["–"] * 6)) for p in ALL_PERSONS}
        fest = feste_zellen(w)
        for di in range(5):
            if w.feiertag(di):
                continue
            self._plane_tag(w, plan, fest, di)
        return plan

    # ── Verfügbarkeit ────────────────────────────────────────────────────
    def _status(self, w: Woche, p: str, di: int, fest) -> str:
        """'fest' | 'frei' | 'schule' | 'ab1530' | 'da'"""
        if (p, di) in fest:
            return "fest"
        d = w.dates[di]
        if d in w.urlaub.get(p, set()) or d in w.krank.get(p, set()):
            return "fest"
        par = "gerade" if w.gerade else "ungerade"
        if di in E.FREIE_TAGE.get(p, {}).get(par, set()):
            return "frei"
        if p == "Deborah" and w.gerade and di == 4 and E.DEBORAH_FREI_FR_GERADE:
            return "frei"
        s = E.schule(p, w.kw, di)
        if s == "ganz":
            return "schule"
        if s == "ab 15:30":
            return "ab1530"
        return "da"

    # ── ein Tag ──────────────────────────────────────────────────────────
    def _plane_tag(self, w: Woche, plan, fest, di: int):
        """Exakte Optimierung per dynamischer Programmierung.

        1. "Plätze" sammeln, die besetzt werden sollen und noch nicht durch feste
           Zellen besetzt sind: Anmeldung FD/SD, Assistenz je Arzt und Schicht.
        2. DP über die Plätze: jeder Platz bekommt eine freie Person oder bleibt
           leer (Strafpunkte). Zustand = (Platz, benutzte Personen, Anzahl FD).
        3. Wer übrig bleibt → Behandlung, so auf FD/SD verteilt, dass es
           möglichst ausgeglichen ist.
        """
        from functools import lru_cache

        arzt_sch = {a: arzt_schichten(plan.get(a, ["–"] * 6)[di]) for a in AERZTE_HILFE}
        op = {"Lisa": lisa_op(w, di),
              "Wilke": "FD OP" in str(plan.get("Wilke", ["–"] * 6)[di])}

        # Feste Zellen auswerten, freie/Schul-Tage eintragen
        leute, basis = [], {}
        for p in PLANBAR:
            bis = E.LANGZEIT_KRANK.get(p, "–")
            if bis != "–" and (p, di) not in fest and (bis is None or w.dates[di] <= bis):
                plan[p][di] = "Krank"
                continue
            st = self._status(w, p, di, fest) if p in E.AUTOMATISCH else "fest"
            if st in ("da", "ab1530"):
                leute.append((p, st))
                continue
            if st == "frei":
                plan[p][di] = "–"
            elif st == "schule":
                plan[p][di] = "Schule"
            z = parse(plan[p][di])
            if z.arbeitet and z.schicht in SCHICHTEN:
                basis[(z.schicht, _rolle_key(z))] = basis.get((z.schicht, _rolle_key(z)), 0) + 1
                g = _gruppe(p)
                basis[(g, z.schicht)] = basis.get((g, z.schicht), 0) + 1
        if not leute:
            return

        # Plätze
        plaetze = []   # (schicht, rolle, strafe_wenn_leer)
        for s in SCHICHTEN:
            if not basis.get((s, "Anmeldung")):
                plaetze.append((s, "Anmeldung", STRAFE["anmeldung_fehlt"]))
            for a in AERZTE_HILFE:
                if s in arzt_sch[a] and not basis.get((s, f"Assistenz {a}")):
                    gew = (STRAFE["ulf_fehlt"] if a == "Ulf"
                           else STRAFE["op_fehlt"] if op.get(a) else STRAFE["arzt_fehlt"])
                    plaetze.append((s, f"Assistenz {a}", gew))

        def darf(i, platz):
            p, st = leute[i]
            s, r, _ = platz
            if st == "ab1530" and (s != "SD" or r == "Anmeldung"):
                return False
            if p == "Deborah" and s != E.DEBORAH_SCHICHT[w.gerade]:
                return False
            return r not in E.KANN_NICHT.get(p, set())

        def bonus(i, platz):
            liste = self._vorliebe(di, platz[0], platz[1])
            p = leute[i][0]
            return STRAFE["praeferenz"] * (len(liste) - liste.index(p)) if p in liste else 0

        def rest_strafe(maske, z):
            """Übrige Personen → Behandlung; FD/SD so verteilen, dass zuerst die
            TFAs (wie die FD/SD-Zeile der App zählt), dann alle ausgeglichen sind.
            z = (fdT, sdT, fdA, sdA) aus den besetzten Plätzen."""
            n = {("T", "FD"): z[0], ("T", "SD"): z[1], ("A", "FD"): z[2], ("A", "SD"): z[3]}
            for k_ in n:
                n[k_] += basis.get(k_, 0)
            flex = {"T": [], "A": []}
            for i, (p, st) in enumerate(leute):
                if maske >> i & 1:
                    continue
                g = _gruppe(p)
                if st == "ab1530":
                    n[(g, "SD")] += 1
                elif p == "Deborah":
                    n[(g, E.DEBORAH_SCHICHT[w.gerade])] += 1
                else:
                    flex[g].append(i)
            best = None
            for kt in range(len(flex["T"]) + 1):
                for ka in range(len(flex["A"]) + 1):
                    tfd = n[("T", "FD")] + kt
                    tsd = n[("T", "SD")] + len(flex["T"]) - kt
                    afd = n[("A", "FD")] + ka
                    asd = n[("A", "SD")] + len(flex["A"]) - ka
                    c = (STRAFE["balance"] * abs(tfd - tsd)
                         + STRAFE["balance_alle"] * abs(tfd + afd - tsd - asd))
                    if best is None or c < best[0]:
                        best = (c, set(flex["T"][:kt]) | set(flex["A"][:ka]))
            return best

        @lru_cache(maxsize=None)
        def dp(j, maske, z):
            if j == len(plaetze):
                return rest_strafe(maske, z)[0], ()
            platz = plaetze[j]
            best = dp(j + 1, maske, z)
            best = (best[0] + platz[2], (None,) + best[1])
            for i in range(len(leute)):
                if maske >> i & 1 or not darf(i, platz):
                    continue
                pos = (0 if _gruppe(leute[i][0]) == "T" else 2) + (0 if platz[0] == "FD" else 1)
                z2 = tuple(v + (1 if k_ == pos else 0) for k_, v in enumerate(z))
                c, wahl = dp(j + 1, maske | 1 << i, z2)
                c -= bonus(i, platz)
                if c < best[0]:
                    best = (c, (i,) + wahl)
            return best

        _, wahl = dp(0, 0, (0, 0, 0, 0))
        maske, z = 0, [0, 0, 0, 0]
        for platz, i in zip(plaetze, wahl):
            if i is None:
                continue
            p, st = leute[i]
            plan[p][di] = _wert(platz[0], platz[1], "ab 15:30 (Schule)" if st == "ab1530" else "")
            maske |= 1 << i
            z[(0 if _gruppe(p) == "T" else 2) + (0 if platz[0] == "FD" else 1)] += 1
        _, ins_fd = rest_strafe(maske, tuple(z))
        for i, (p, st) in enumerate(leute):
            if maske >> i & 1:
                continue
            if st == "ab1530":
                plan[p][di] = _wert("SD", "Behandlung", "ab 15:30 (Schule)")
            elif p == "Deborah":
                plan[p][di] = _wert(E.DEBORAH_SCHICHT[w.gerade], "Behandlung")
            else:
                plan[p][di] = _wert("FD" if i in ins_fd else "SD", "Behandlung")

    @staticmethod
    def _vorliebe(di, s, r) -> list[str]:
        if r == "Anmeldung":
            return E.ANMELDUNG.get(s, [])
        if r == "Assistenz Ulf":
            return E.ULF_ASSISTENZ.get(di, {}).get(s, [])
        if r == "Assistenz Lisa":
            return E.ASSISTENZ_LISA.get(s, [])
        if r == "Assistenz Wilke":
            return E.ASSISTENZ_WILKE.get(s, [])
        return []
