"""
planner — neues Planungs-Framework (Vorschläge statt direkter Auto-Planung).

Getrennt vom Live-Betrieb: Nichts hier schreibt selbst in overrides.json.
Erst wenn ein Vorschlag in der App übernommen wird, entstehen Overrides.

Module:
    zellen.py     Zellwerte verstehen ("FD: Assistenz Ulf || 08:30-17:00" → Schicht/Rolle)
    woche.py      Wochen-Kontext (Daten, Abwesenheiten, Gruppen) und Ist-Plan laden
    regeln.py     Regelwerk: Pflichtregeln + Wünsche, jede Regel einzeln prüfbar
    planer.py     Planer-Schnittstelle + Baseline (alter scheduler.py)
    pruefstand.py CLI: Planer gegen echte, von Hand fertig geplante Wochen messen
    analyse.py    CLI: Muster aus den echten Wochen auslesen (für das Regelwerk)
    api.py        Flask-Endpunkte für Vorschläge (Feature-Flag VORSCHLAG_AKTIV)

Siehe docs/planer.md (Übergabe-Dokument für neue Sitzungen).
"""
