"""
pruefstand.py — misst einen Planer an den echten, von Hand fertig geplanten Wochen.

    python -m planner.pruefstand                    # Baseline, KW 24–45
    python -m planner.pruefstand --planer neu --kw 30-40
    python -m planner.pruefstand --details 38       # Abweichungen einer KW

Kennzahlen pro KW (nur TFAs + Azubis, Mo–Fr, nicht gesperrte Zellen):
    Treffer   Zelle stimmt in Schicht+Rolle(+Arzt) mit dem Ist-Plan überein
    Schicht   nur FD/SD stimmt
    Pflicht   Anzahl verletzter Pflichtregeln im Vorschlag
    Ist-Pfl.  Pflichtverstöße im echten Plan (zeigt, wo Regeln noch nicht stimmen)

Ausgabe bewusst kurz (eine Zeile pro KW), damit sie wenig Kontext kostet.
"""

from __future__ import annotations

import argparse

from config import TFAS, TFAS_MANUAL, AZUBIS
from .planer import PLANER, STANDARD, nur_eingaben, vorschlag
from .regeln import bewertung, TAGE
from .woche import lade_ist_wochen
from .zellen import parse

PERSONEN = TFAS + TFAS_MANUAL + AZUBIS
# Referenzwochen: von Hand fertig geplant (siehe docs/planer.md)
REFERENZ = range(24, 46)


def _bereich(s: str):
    a, _, b = s.partition("-")
    return range(int(a), int(b or a) + 1)


def messe(w, planer):
    eingabe = nur_eingaben(w, PERSONEN)
    vs = vorschlag(eingabe, planer)["plan"]
    n = treffer = schicht = 0
    abw = []
    for p in PERSONEN:
        for di in range(5):
            if w.feiertag(di) or di in eingabe.gesperrt.get(p, {}):
                continue
            ist, neu = parse(w.plan[p][di]), parse(vs[p][di])
            if ist.leer and neu.leer:
                continue
            n += 1
            if ist.schluessel == neu.schluessel:
                treffer += 1
            else:
                abw.append((p, di, w.plan[p][di], vs[p][di]))
            if ist.schicht == neu.schicht:
                schicht += 1
    return {
        "n": n, "treffer": treffer, "schicht": schicht,
        "pflicht": bewertung(eingabe.kopie_mit(vs))["pflicht"],
        "ist_pflicht": bewertung(w)["pflicht"],
        "abweichungen": abw,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--planer", default=STANDARD, choices=sorted(PLANER))
    ap.add_argument("--kw", default=f"{REFERENZ.start}-{REFERENZ.stop - 1}")
    ap.add_argument("--details", type=int, help="Abweichungen dieser KW auflisten")
    a = ap.parse_args(argv)

    kws = [a.details] if a.details else list(_bereich(a.kw))
    wochen = lade_ist_wochen(kws)
    print(f"Planer: {a.planer}  |  KW {kws[0]}–{kws[-1]}")
    print(f"{'KW':>3} {'Zellen':>6} {'Treffer':>8} {'Schicht':>8} {'Pflicht':>7} {'Ist-Pfl.':>8}")
    summe = {"n": 0, "treffer": 0, "schicht": 0, "pflicht": 0, "ist_pflicht": 0}
    for kw in kws:
        r = messe(wochen[kw], a.planer)
        for k in summe:
            summe[k] += r[k]
        q = lambda x: f"{100 * x / r['n']:.0f}%" if r["n"] else "–"
        print(f"{kw:>3} {r['n']:>6} {q(r['treffer']):>8} {q(r['schicht']):>8} {r['pflicht']:>7} {r['ist_pflicht']:>8}")
        if a.details:
            for p, di, ist, neu in r["abweichungen"]:
                print(f"    {TAGE[di]} {p:<9} ist: {ist:<38} vorschlag: {neu}")
    if len(kws) > 1 and summe["n"]:
        print(f"SUM {summe['n']:>6} {100 * summe['treffer'] / summe['n']:>7.0f}% "
              f"{100 * summe['schicht'] / summe['n']:>7.0f}% {summe['pflicht']:>7} {summe['ist_pflicht']:>8}")


if __name__ == "__main__":
    main()
