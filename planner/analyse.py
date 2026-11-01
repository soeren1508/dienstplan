"""
analyse.py — liest Muster aus den echten Wochen (Grundlage für docs/regeln.md).

    python -m planner.analyse              # schreibt docs/analyse.md
    python -m planner.analyse --kw 36-45   # anderer Zeitraum

Erzeugt:
  1. Person × Wochentag × (gerade/ungerade KW): häufigste Einteilung + Anteil
  2. Wer übernimmt welche Pflichtrolle wie oft (Anmeldung, Assistenz …)
  3. Wie oft verletzen die echten Wochen die aktuellen Regeln
Die Datei ist generiert — nicht von Hand bearbeiten, sondern neu erzeugen.
"""

from __future__ import annotations

import argparse
import collections
from pathlib import Path

from .pruefstand import PERSONEN, REFERENZ, _bereich
from .regeln import REGELN, TAGE, pruefe_alle
from .woche import lade_ist_wochen
from .zellen import parse

ZIEL = Path(__file__).resolve().parent.parent / "docs" / "analyse.md"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--kw", default=f"{REFERENZ.start}-{REFERENZ.stop - 1}")
    a = ap.parse_args(argv)
    kws = list(_bereich(a.kw))
    wochen = lade_ist_wochen(kws)

    muster = collections.defaultdict(collections.Counter)   # (p, di, parität) -> Counter
    rollen = collections.defaultdict(collections.Counter)   # rolle -> Counter(person)
    for w in wochen.values():
        par = "g" if w.gerade else "u"
        for p in PERSONEN:
            for di in range(5):
                if w.feiertag(di):
                    continue
                z = parse(w.plan[p][di])
                if z.abwesend in ("Urlaub", "Krank"):
                    continue   # zufällige Abwesenheit sagt nichts über das Muster
                muster[(p, di, par)][z.schluessel] += 1
                if z.arbeitet and z.rolle in ("Anmeldung", "Assistenz", "Springer"):
                    rollen[f"{z.schicht} {z.rolle}" + (f" {z.arzt}" if z.arzt else "")
                           + (" OP" if z.op else "")][p] += 1

    zeilen = [
        "# Analyse der echten Wochen (generiert)",
        "",
        f"Zeitraum: KW {kws[0]}–{kws[-1]}. Erzeugt mit `python -m planner.analyse`.",
        "Urlaub/Krank sind herausgerechnet. Format: häufigste Einteilung (Anteil) · zweithäufigste.",
        "",
        "## 1. Muster pro Person und Wochentag",
        "",
        "| Person | Par. | " + " | ".join(TAGE[:5]) + " |",
        "|---|---|" + "---|" * 5,
    ]
    for p in PERSONEN:
        for par, label in (("g", "gerade"), ("u", "ungerade")):
            zellen = []
            for di in range(5):
                c = muster[(p, di, par)]
                n = sum(c.values())
                if not n:
                    zellen.append("")
                    continue
                top = c.most_common(2)
                s = f"{top[0][0]} ({100 * top[0][1] // n}%)"
                if len(top) > 1:
                    s += f" · {top[1][0]}"
                zellen.append(s)
            zeilen.append(f"| {p} | {label} | " + " | ".join(zellen) + " |")

    zeilen += ["", "## 2. Wer übernimmt welche Rolle (Anzahl Tage)", ""]
    for rolle in sorted(rollen):
        c = rollen[rolle]
        zeilen.append(f"- **{rolle}** ({sum(c.values())}): "
                      + ", ".join(f"{p} {n}" for p, n in c.most_common()))

    zeilen += ["", "## 3. Verstöße der echten Wochen gegen die aktuellen Regeln", "",
               "Viele Verstöße = Regel passt nicht zur Praxis und muss überarbeitet werden.", ""]
    vs = collections.Counter()
    for w in wochen.values():
        for v in pruefe_alle(w):
            vs[(v.regel, v.text)] += 1
    for r in REGELN:
        treffer = [(t, n) for (rid, t), n in vs.most_common() if rid == r.id]
        gesamt = sum(n for _, n in treffer)
        zeilen.append(f"- `{r.id}` ({r.art}): {gesamt}× — "
                      + ("; ".join(f"{t} {n}×" for t, n in treffer[:4]) or "ok"))

    ZIEL.parent.mkdir(exist_ok=True)
    ZIEL.write_text("\n".join(zeilen) + "\n", encoding="utf-8")
    print(f"geschrieben: {ZIEL.relative_to(ZIEL.parent.parent)} ({len(zeilen)} Zeilen)")


if __name__ == "__main__":
    main()
