"""
api.py — Flask-Endpunkte für Planungs-Vorschläge.

Feature-Flag: Umgebungsvariable VORSCHLAG_AKTIV=1 (Standard: aus).
Ist das Flag aus, antworten alle Endpunkte außer /status mit 404 und die
Oberfläche zeigt den Knopf nicht an → im Live-Betrieb ändert sich nichts.

    GET  /api/vorschlag/status            {aktiv, planer}
    GET  /api/vorschlag/<kw>              Vorschlag berechnen (nichts wird gespeichert)
    POST /api/vorschlag/<kw>/uebernehmen  {zellen: [{person, di, neu}]} → Overrides

Ablehnen = einfach schließen; es wird nichts gespeichert.
Gesperrte Zellen (bereits manuell eingetragen) werden nie überschrieben.
"""

from __future__ import annotations

import os

from flask import Blueprint, abort, jsonify, request

from config import ALL_PERSONS
from .planer import STANDARD, vorschlag
from .regeln import REGELN, TAGE, bewertung
from .woche import Woche


def aktiv() -> bool:
    return os.environ.get("VORSCHLAG_AKTIV", "") in ("1", "true", "ja")


def register(app, *, require_auth, load_overrides, save_overrides, plan_for_kw,
             get_vac, get_krank):
    bp = Blueprint("vorschlag", __name__)
    regel_text = {r.id: r.text for r in REGELN}

    def _woche(kw: int) -> Woche:
        from scheduler import week_dates
        ov = load_overrides()
        gesperrt = {p: {int(di): v for di, v in d.items()}
                    for p, d in ov.get(str(kw), {}).items() if p in ALL_PERSONS}
        return Woche(kw, week_dates(kw), plan_for_kw(kw, ov), gesperrt,
                     get_vac(), get_krank())

    def _kurz(b):
        return {
            "pflicht": b["pflicht"],
            "strafpunkte": b["strafpunkte"],
            "meldungen": [
                {"regel": v.regel, "tag": TAGE[v.di], "text": v.text, "person": v.person,
                 "beschreibung": regel_text.get(v.regel, "")}
                for v in b["verstoesse"]
            ],
        }

    @bp.route("/api/vorschlag/status")
    def status():
        return jsonify({"aktiv": aktiv(), "planer": STANDARD})

    @bp.route("/api/vorschlag/<int:kw>")
    @require_auth
    def berechnen(kw):
        if not aktiv():
            abort(404)
        w = _woche(kw)
        planer = request.args.get("planer", STANDARD)
        r = vorschlag(w, planer)
        return jsonify({
            "kw": kw,
            "planer": planer,
            "aenderungen": r["aenderungen"],
            "vorher": _kurz(bewertung(w)),
            "nachher": _kurz(bewertung(w.kopie_mit(r["plan"]))),
        })

    @bp.route("/api/vorschlag/<int:kw>/uebernehmen", methods=["POST"])
    @require_auth
    def uebernehmen(kw):
        if not aktiv():
            abort(404)
        zellen = (request.get_json() or {}).get("zellen", [])
        ov = load_overrides()
        kw_ov = ov.setdefault(str(kw), {})
        uebernommen, uebersprungen = 0, 0
        for z in zellen:
            p, di, neu = z.get("person"), str(z.get("di")), z.get("neu")
            if p not in ALL_PERSONS or di not in {str(i) for i in range(6)} or not isinstance(neu, str):
                uebersprungen += 1
                continue
            if di in kw_ov.get(p, {}):
                uebersprungen += 1   # manueller Eintrag hat Vorrang
                continue
            kw_ov.setdefault(p, {})[di] = neu
            uebernommen += 1
        if not kw_ov:
            ov.pop(str(kw), None)
        if uebernommen:
            save_overrides(ov)
        return jsonify({"ok": True, "uebernommen": uebernommen, "uebersprungen": uebersprungen})

    app.register_blueprint(bp)
