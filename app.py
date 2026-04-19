"""
app.py — Dienstplan Web-App (Flask)

Aufruf:
    cd dienstplan
    python app.py
    → http://localhost:5050          (Ansicht für alle)
    → http://<LAN-IP>:5050          (andere Geräte im Netzwerk)

PIN ändern: Umgebungsvariable EDIT_PIN setzen, oder direkt hier:
    EDIT_PIN = "1234"
"""

import hashlib
import json
import os
import secrets
import socket
import sys
from datetime import date
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, render_template, session, Response
from flask_cors import CORS

DIENSTPLAN_DIR = Path(__file__).resolve().parent
REPO_DIR       = DIENSTPLAN_DIR.parent
sys.path.insert(0, str(DIENSTPLAN_DIR))

from scheduler import generate_week
from vacations import load_vacations
from config    import ALL_PERSONS, ARZTE, TFAS, DAYS

# Excel-Datei: erst im selben Verzeichnis suchen (Deployment), dann im Repo-Root (lokal)
_urlaub_candidates = [
    DIENSTPLAN_DIR / "Urlaubsplanung 2026.xlsx",
    REPO_DIR / "Urlaubsplanung 2026.xlsx",
]
URLAUB_PATH = next((p for p in _urlaub_candidates if p.exists()), _urlaub_candidates[-1])
if not URLAUB_PATH.exists():
    print(f"WARNUNG: Urlaubsplanung nicht gefunden. Gesucht: {_urlaub_candidates}")

OVERRIDES_PATH     = DIENSTPLAN_DIR / "overrides.json"
VAC_OVERRIDES_PATH = DIENSTPLAN_DIR / "vacation_overrides.json"

# PIN für den Bearbeitungsmodus (Umgebungsvariable EDIT_PIN, Fallback "1234")
EDIT_PIN = os.environ.get("EDIT_PIN", "1234")

app = Flask(__name__)
CORS(app)  # Erlaubt Netlify-Frontend → Render-Backend

# SECRET_KEY: stabil aus Env-Var (wichtig für Render.com, sonst verliert jeder Restart Sessions)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)


# ---------------------------------------------------------------------------
# Auth-Hilfsfunktionen
# ---------------------------------------------------------------------------

def _pin_hash(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()

def _is_authenticated() -> bool:
    return session.get("authenticated") is True

def require_auth(f):
    """Decorator: gibt 403 zurück wenn nicht eingeloggt."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not _is_authenticated():
            return jsonify({"ok": False, "error": "Nicht autorisiert"}), 403
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Plan-Cache
# ---------------------------------------------------------------------------
_plan_cache: dict[int, dict] = {}


# ---------------------------------------------------------------------------
# Urlaubs-Overrides (manuelle Ergänzungen / Streichungen über die App)
# ---------------------------------------------------------------------------

def _load_vac_overrides() -> dict:
    if VAC_OVERRIDES_PATH.exists():
        with open(VAC_OVERRIDES_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_vac_overrides(data: dict):
    with open(VAC_OVERRIDES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _get_all_vac():
    """Excel-Urlaub + manuelle Korrekturen zusammenführen."""
    all_vac = load_vacations(URLAUB_PATH)
    for person, changes in _load_vac_overrides().items():
        if person not in all_vac:
            all_vac[person] = set()
        for iso in changes.get("add", []):
            all_vac[person].add(date.fromisoformat(iso))
        for iso in changes.get("remove", []):
            all_vac[person].discard(date.fromisoformat(iso))
    return all_vac


def _generate_all():
    global _plan_cache
    all_vac = _get_all_vac()
    auffl   = {p: 0 for p in ALL_PERSONS}
    plans   = {}
    for kw in range(17, 24):
        plans[kw] = generate_week(kw, all_vac, auffl)
    _plan_cache = plans


def _iso_kw(d) -> int:
    """ISO-Kalenderwoche für ein date-Objekt."""
    return d.isocalendar()[1]


def _load_overrides() -> dict:
    if OVERRIDES_PATH.exists():
        with open(OVERRIDES_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_overrides(data: dict):
    with open(OVERRIDES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _plan_for_kw(kw: int, overrides: dict) -> dict:
    base  = _plan_cache.get(kw, {})
    kw_ov = overrides.get(str(kw), {})
    result = {}
    for person in ALL_PERSONS:
        row = list(base.get(person, ["–"] * 6))
        for di_str, val in kw_ov.get(person, {}).items():
            row[int(di_str)] = val
        result[person] = row
    return result


# ---------------------------------------------------------------------------
# Routen — Öffentlich (View)
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/manifest.json")
def manifest():
    data = {
        "name": "Dienstplan 2026",
        "short_name": "Dienstplan",
        "description": "Tierarztpraxis Hamburg – Dienstplan 2026",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f5f6fa",
        "theme_color": "#1e293b",
        "orientation": "portrait-primary",
        "icons": [
            {"src": "/static/logo.png", "sizes": "any", "type": "image/png", "purpose": "any maskable"},
        ],
        "categories": ["productivity", "medical"],
    }
    return Response(
        __import__("json").dumps(data, ensure_ascii=False),
        mimetype="application/manifest+json"
    )


@app.route("/api/me")
def api_me():
    """Gibt Auth-Status zurück (wird beim Seitenlade abgefragt)."""
    return jsonify({"authenticated": _is_authenticated()})


@app.route("/api/plan/<int:kw>")
def api_plan(kw):
    if not _plan_cache:
        _generate_all()
    overrides    = _load_overrides()
    plan         = _plan_for_kw(kw, overrides)
    kw_ov        = overrides.get(str(kw), {})
    from scheduler import week_dates
    dates        = week_dates(kw)
    date_labels  = [d.strftime("%-d.%-m.") for d in dates]
    return jsonify({
        "kw":        kw,
        "dates":     date_labels,
        "plan":      plan,
        "days":      DAYS,
        "persons":   ALL_PERSONS,
        "arzte":     ARZTE,
        "tfas":      TFAS,
        "overrides": kw_ov,
    })


@app.route("/api/validate/<int:kw>")
def api_validate(kw):
    if not _plan_cache:
        _generate_all()
    overrides = _load_overrides()
    plan      = _plan_for_kw(kw, overrides)
    issues    = _validate_plan(plan, kw)
    return jsonify(issues)


@app.route("/api/validate/<int:kw>/suggestions")
def api_suggestions(kw):
    if not _plan_cache:
        _generate_all()
    overrides   = _load_overrides()
    plan        = _plan_for_kw(kw, overrides)
    issues      = _validate_plan(plan, kw)
    suggestions = _suggest_fixes(plan, issues, kw)
    return jsonify(suggestions)


# ---------------------------------------------------------------------------
# Routen — Auth
# ---------------------------------------------------------------------------

@app.route("/api/auth", methods=["POST"])
def api_auth():
    data = request.get_json() or {}
    pin  = str(data.get("pin", ""))
    if pin == EDIT_PIN:
        session["authenticated"] = True
        session.permanent = False   # Läuft mit Browser-Session ab
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Falscher PIN"}), 401


@app.route("/api/auth", methods=["DELETE"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Routen — Geschützt (Edit)
# ---------------------------------------------------------------------------

@app.route("/api/override", methods=["POST"])
@require_auth
def api_override():
    data   = request.get_json()
    kw     = str(data["kw"])
    person = data["person"]
    di     = str(data["di"])
    value  = data["value"]

    overrides = _load_overrides()
    if value == "__reset__":
        overrides.get(kw, {}).get(person, {}).pop(di, None)
        if not overrides.get(kw, {}).get(person):
            overrides.get(kw, {}).pop(person, None)
        if not overrides.get(kw):
            overrides.pop(kw, None)
    else:
        overrides.setdefault(kw, {}).setdefault(person, {})[di] = value

    _save_overrides(overrides)
    return jsonify({"ok": True})


@app.route("/api/regenerate", methods=["POST"])
@require_auth
def api_regenerate():
    _generate_all()
    return jsonify({"ok": True})


@app.route("/api/overrides/clear/<int:kw>", methods=["POST"])
@require_auth
def api_clear_kw(kw):
    overrides = _load_overrides()
    overrides.pop(str(kw), None)
    _save_overrides(overrides)
    return jsonify({"ok": True})


@app.route("/api/absence", methods=["POST"])
@require_auth
def api_absence():
    """
    Trägt eine Abwesenheit (Krank / Frei / Urlaub) als Override ein und
    gibt sofort die Validierungs-Issues für den betroffenen Tag zurück.

    Body: { kw, person, di, grund }
    Antwort: { ok, issues_day: [...], issues_cell: {...} }
    """
    if not _plan_cache:
        _generate_all()
    data   = request.get_json()
    kw     = int(data["kw"])
    person = data["person"]
    di     = int(data["di"])
    grund  = data.get("grund", "Krank")   # "Krank", "Urlaub", "Frei"

    if person not in ALL_PERSONS:
        return jsonify({"ok": False, "error": f"Unbekannte Person: {person}"}), 400
    if di < 0 or di > 5:
        return jsonify({"ok": False, "error": "Ungültiger Tag"}), 400

    overrides = _load_overrides()
    overrides.setdefault(str(kw), {}).setdefault(person, {})[str(di)] = grund
    _save_overrides(overrides)

    plan        = _plan_for_kw(kw, overrides)
    issues      = _validate_plan(plan, kw)
    suggestions = _suggest_fixes(plan, issues, kw)

    return jsonify({
        "ok":          True,
        "issues_day":  issues["day"].get(str(di), []),
        "issues_cell": {
            p: issues["cell"][p].get(str(di), [])
            for p in ALL_PERSONS
            if issues["cell"][p].get(str(di))
        },
        "suggestions":   suggestions,
        "total_issues":  sum(len(v) for v in issues["day"].values()),
    })


@app.route("/api/swap", methods=["POST"])
@require_auth
def api_swap():
    """
    Tauscht die Dienste von zwei Personen an einem Tag.
    Body: { kw, di, person_a, person_b }
    """
    if not _plan_cache:
        _generate_all()
    data     = request.get_json()
    kw       = int(data["kw"])
    di       = int(data["di"])
    person_a = data["person_a"]
    person_b = data["person_b"]

    if person_a not in ALL_PERSONS or person_b not in ALL_PERSONS:
        return jsonify({"ok": False, "error": "Unbekannte Person"}), 400
    if person_a == person_b:
        return jsonify({"ok": False, "error": "Gleiche Person gewählt"}), 400

    overrides = _load_overrides()
    plan      = _plan_for_kw(kw, overrides)

    val_a = str(plan[person_a][di]).replace(" + Auffüllen", "").strip()
    val_b = str(plan[person_b][di]).replace(" + Auffüllen", "").strip()

    # Overrides setzen
    overrides.setdefault(str(kw), {}).setdefault(person_a, {})[str(di)] = val_b
    overrides.setdefault(str(kw), {}).setdefault(person_b, {})[str(di)] = val_a
    _save_overrides(overrides)

    plan_new    = _plan_for_kw(kw, overrides)
    issues      = _validate_plan(plan_new, kw)
    suggestions = _suggest_fixes(plan_new, issues, kw)

    return jsonify({
        "ok":   True,
        "swap": {
            "person_a": person_a, "before_a": val_a, "after_a": val_b,
            "person_b": person_b, "before_b": val_b, "after_b": val_a,
        },
        "issues":       issues,
        "suggestions":  suggestions,
        "total_issues": sum(len(v) for v in issues["day"].values()),
    })


@app.route("/api/vacation-day", methods=["POST"])
@require_auth
def api_vacation_day():
    """
    Fügt einen Urlaubstag hinzu oder entfernt ihn — triggert komplette Neuplanung.
    Body: { person, date: "2026-05-11", action: "add"|"remove" }
    """
    data    = request.get_json()
    person  = data["person"]
    iso     = data["date"]
    action  = data["action"]   # "add" | "remove"

    if person not in ALL_PERSONS:
        return jsonify({"ok": False, "error": "Unbekannte Person"}), 400

    vac_ov     = _load_vac_overrides()
    person_ov  = vac_ov.setdefault(person, {"add": [], "remove": []})

    if action == "add":
        if iso not in person_ov["add"]:
            person_ov["add"].append(iso)
        if iso in person_ov.get("remove", []):
            person_ov["remove"].remove(iso)
    elif action == "remove":
        if iso not in person_ov.get("remove", []):
            person_ov.setdefault("remove", []).append(iso)
        if iso in person_ov.get("add", []):
            person_ov["add"].remove(iso)
    else:
        return jsonify({"ok": False, "error": "action muss 'add' oder 'remove' sein"}), 400

    _save_vac_overrides(vac_ov)
    _generate_all()   # Neuplanung mit aktualisierten Urlaubs-Daten

    kw        = _iso_kw(date.fromisoformat(iso))
    overrides = _load_overrides()
    plan      = _plan_for_kw(kw, overrides)
    issues    = _validate_plan(plan, kw)
    suggestions = _suggest_fixes(plan, issues, kw)

    from scheduler import week_dates
    dates      = week_dates(kw)
    date_labels = [d.strftime("%-d.%-m.") for d in dates]

    return jsonify({
        "ok":           True,
        "kw":           kw,
        "dates":        date_labels,
        "plan":         plan,
        "issues":       issues,
        "suggestions":  suggestions,
        "total_issues": sum(len(v) for v in issues["day"].values()),
    })


@app.route("/api/apply-suggestions", methods=["POST"])
@require_auth
def api_apply_suggestions():
    """
    Wendet einen oder mehrere Vorschläge als Overrides an.
    Body: { kw, overrides: [{person, di, value}, ...] }
    """
    if not _plan_cache:
        _generate_all()
    data        = request.get_json()
    kw          = int(data["kw"])
    new_overrides_list = data["overrides"]

    overrides = _load_overrides()
    for ov in new_overrides_list:
        overrides.setdefault(str(kw), {}).setdefault(ov["person"], {})[str(ov["di"])] = ov["value"]
    _save_overrides(overrides)

    plan        = _plan_for_kw(kw, overrides)
    issues      = _validate_plan(plan, kw)
    suggestions = _suggest_fixes(plan, issues, kw)

    return jsonify({
        "ok":           True,
        "issues":       issues,
        "suggestions":  suggestions,
        "total_issues": sum(len(v) for v in issues["day"].values()),
    })


# ---------------------------------------------------------------------------
# Lösungsvorschläge für Regelverstoße
# ---------------------------------------------------------------------------

def _suggest_fixes(plan: dict, issues: dict, kw: int) -> list:
    """
    Analysiert Regel-Verstöße und gibt konkrete Override-Vorschläge zurück.
    Format je Vorschlag:
      { day: int, msg: str, description: str,
        overrides: [{person, di, value}, ...] }
    """
    def _is_free(val):
        s = str(val) if val else "–"
        return s in ("–", "Urlaub", "Feiertag", "SCHULE", "FREI_SCHUTZ",
                     "Abschlussprüfung", "Krank", "Frei") or "Frei" in s

    suggestions = []

    for di_str, msgs in issues["day"].items():
        di  = int(di_str)
        row = {p: str(plan[p][di]) for p in ALL_PERSONS}

        def tfa_in_shift(shift):
            return [p for p in TFAS if shift in row[p] and not _is_free(row[p])]

        for msg in msgs:
            # ── Anmeldung fehlt ──────────────────────────────────────────────
            if "FD: Anmeldung fehlt" in msg:
                cands = [p for p in tfa_in_shift("FD") if "Anmeldung" not in row[p]]
                for c in cands[:3]:
                    old = row[c].replace(" + Auffüllen", "")
                    suggestions.append({
                        "day": di, "msg": msg,
                        "description": f"{DAYS[di]}: {c}  {old} → FD: Anmeldung",
                        "overrides": [{"person": c, "di": di, "value": "FD: Anmeldung"}],
                    })

            elif "SD: Anmeldung fehlt" in msg:
                cands = [p for p in tfa_in_shift("SD") if "Anmeldung" not in row[p]]
                for c in cands[:3]:
                    old = row[c].replace(" + Auffüllen", "")
                    suggestions.append({
                        "day": di, "msg": msg,
                        "description": f"{DAYS[di]}: {c}  {old} → SD: Anmeldung",
                        "overrides": [{"person": c, "di": di, "value": "SD: Anmeldung"}],
                    })

            # ── Ulf-Assistenz fehlt ──────────────────────────────────────────
            elif "FD: Assistenz" in msg and "Ulf" in msg:
                cands = [p for p in tfa_in_shift("FD") if "Assistenz" not in row[p]]
                for c in cands[:3]:
                    old = row[c].replace(" + Auffüllen", "")
                    suggestions.append({
                        "day": di, "msg": msg,
                        "description": f"{DAYS[di]}: {c}  {old} → FD: Assistenz Ulf",
                        "overrides": [{"person": c, "di": di, "value": "FD: Assistenz Ulf"}],
                    })

            elif "SD: Assistenz" in msg and "Ulf" in msg:
                cands = [p for p in tfa_in_shift("SD") if "Assistenz" not in row[p]]
                for c in cands[:3]:
                    old = row[c].replace(" + Auffüllen", "")
                    suggestions.append({
                        "day": di, "msg": msg,
                        "description": f"{DAYS[di]}: {c}  {old} → SD: Assistenz Ulf",
                        "overrides": [{"person": c, "di": di, "value": "SD: Assistenz Ulf"}],
                    })

            # ── Lisa-OP-Assistenz fehlt ──────────────────────────────────────
            elif "Lisa OP → FD" in msg:
                cands = [p for p in tfa_in_shift("FD") if "Assistenz" not in row[p]]
                for c in cands[:3]:
                    old = row[c].replace(" + Auffüllen", "")
                    suggestions.append({
                        "day": di, "msg": msg,
                        "description": f"{DAYS[di]}: {c}  {old} → FD: Assistenz Lisa OP",
                        "overrides": [{"person": c, "di": di, "value": "FD: Assistenz Lisa OP"}],
                    })

            elif "Lisa OP → SD" in msg:
                cands = [p for p in tfa_in_shift("SD") if "Assistenz" not in row[p]]
                for c in cands[:3]:
                    old = row[c].replace(" + Auffüllen", "")
                    suggestions.append({
                        "day": di, "msg": msg,
                        "description": f"{DAYS[di]}: {c}  {old} → SD: Assistenz Lisa OP",
                        "overrides": [{"person": c, "di": di, "value": "SD: Assistenz Lisa OP"}],
                    })

            # ── Wilke-OP-Assistenz fehlt ─────────────────────────────────────
            elif "Wilke FD OP" in msg:
                cands = [p for p in TFAS if not _is_free(row[p]) and "Assistenz" not in row[p]]
                for c in cands[:3]:
                    old = row[c].replace(" + Auffüllen", "")
                    suggestions.append({
                        "day": di, "msg": msg,
                        "description": f"{DAYS[di]}: {c}  {old} → Assistenz Wilke OP",
                        "overrides": [{"person": c, "di": di, "value": "Assistenz Wilke OP"}],
                    })

    return suggestions


# ---------------------------------------------------------------------------
# Regel-Validierung
# ---------------------------------------------------------------------------

def _validate_plan(plan: dict, kw: int) -> dict:
    from scheduler import week_dates
    from config    import FEIERTAGE_HH_2026

    dates  = week_dates(kw)
    issues = {"day": {}, "cell": {p: {} for p in ALL_PERSONS}}

    def v(val):    return str(val) if val else "–"
    def shift(val):
        s = v(val)
        return "FD" if s.startswith("FD") else ("SD" if s.startswith("SD") else None)
    def working(val):
        s = v(val)
        return s not in ("–", "Urlaub", "Feiertag", "SCHULE", "FREI_SCHUTZ",
                         "Abschlussprüfung") and "Frei" not in s
    def add_day(di, msg):
        issues["day"].setdefault(str(di), []).append(msg)
    def add_cell(p, di, msg):
        issues["cell"][p].setdefault(str(di), []).append(msg)

    for di in range(5):
        if dates[di] in FEIERTAGE_HH_2026:
            continue
        row          = {p: v(plan[p][di]) for p in ALL_PERSONS}
        active_tfas  = [p for p in TFAS if working(row[p])]

        # Anmeldung
        fd_anm = [p for p in TFAS if "FD" in row[p] and "Anmeldung" in row[p]]
        sd_anm = [p for p in TFAS if "SD" in row[p] and "Anmeldung" in row[p]]
        if len(active_tfas) >= 2:
            # Nur flaggen wenn mind. 2 TFAs mit generischer Behandlung im gleichen Shift da
            # sind, die Anmeldung hätten übernehmen können (einzelne Person = Ausnahme OK)
            fd_beh_persons = [
                p for p in TFAS
                if "FD" in row[p] and "Behandlung" in row[p] and "Assistenz" not in row[p]
                and working(row[p])
            ]
            sd_beh_persons = [
                p for p in TFAS
                if "SD" in row[p] and "Behandlung" in row[p] and "Assistenz" not in row[p]
                and working(row[p])
            ]
            if not fd_anm and len(fd_beh_persons) >= 2: add_day(di, "FD: Anmeldung fehlt")
            if not sd_anm and len(sd_beh_persons) >= 2: add_day(di, "SD: Anmeldung fehlt")
        for p in fd_anm[1:]: add_cell(p, di, "FD: Anmeldung doppelt besetzt")
        for p in sd_anm[1:]: add_cell(p, di, "SD: Anmeldung doppelt besetzt")
        if len(fd_anm) > 1: add_day(di, f"FD: Anmeldung mehrfach ({', '.join(fd_anm)})")
        if len(sd_anm) > 1: add_day(di, f"SD: Anmeldung mehrfach ({', '.join(sd_anm)})")

        # Ulf-Assistenz
        ulf_present = row.get("Ulf", "–") not in ("–", "Urlaub", "Feiertag")
        fd_ulf = [p for p in TFAS if "FD" in row[p] and "Assistenz Ulf" in row[p]]
        sd_ulf = [p for p in TFAS if "SD" in row[p] and "Assistenz Ulf" in row[p]]
        if ulf_present:
            if not fd_ulf: add_day(di, "Ulf anwesend → FD: Assistenz fehlt")
            if not sd_ulf: add_day(di, "Ulf anwesend → SD: Assistenz fehlt")
            for p in fd_ulf[1:]: add_cell(p, di, "FD: Assistenz Ulf doppelt")
            for p in sd_ulf[1:]: add_cell(p, di, "SD: Assistenz Ulf doppelt")
        else:
            for p in fd_ulf + sd_ulf: add_cell(p, di, "Ulf Assistenz obwohl Ulf abwesend")

        # Lisa OP
        if "OP Ganztag" in row.get("Lisa", "–"):
            fd_l = [p for p in TFAS if "FD" in row[p] and "Assistenz Lisa OP" in row[p]]
            sd_l = [p for p in TFAS if "SD" in row[p] and "Assistenz Lisa OP" in row[p]]
            if not fd_l: add_day(di, "Lisa OP → FD: Assistenz fehlt")
            if not sd_l: add_day(di, "Lisa OP → SD: Assistenz fehlt")
            for p in fd_l[1:]: add_cell(p, di, "FD: Assistenz Lisa OP doppelt")
            for p in sd_l[1:]: add_cell(p, di, "SD: Assistenz Lisa OP doppelt")

        # Wilke OP
        if "FD OP" in row.get("Wilke", "–"):
            fw = [p for p in TFAS if "Assistenz Wilke OP" in row[p]]
            # Fr in ungeraden KWs: Imke übernimmt keinen Wilke-OP-Slot (Struktur-Ausnahme)
            wilke_fr_ungerade_ausnahme = (
                di == 4 and kw % 2 != 0
                and working(row.get("Imke", "–"))
            )
            if not fw and not wilke_fr_ungerade_ausnahme:
                add_day(di, "Wilke FD OP → Assistenz fehlt")
            for p in fw[1:]: add_cell(p, di, "Assistenz Wilke OP doppelt")

        # FD/SD-Balance
        fd_n = sum(1 for p in TFAS if shift(row[p]) == "FD")
        sd_n = sum(1 for p in TFAS if shift(row[p]) == "SD")
        if active_tfas and abs(fd_n - sd_n) >= 4:
            add_day(di, f"FD/SD-Ungleichgewicht: FD={fd_n}, SD={sd_n}")

    return issues


# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------

def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unbekannt"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print("Generiere Plan KW 17–23 …")
    _generate_all()
    ip = _get_local_ip()
    print(f"""
╔══════════════════════════════════════════════════════╗
  Dienstplan-App gestartet

  Auf diesem Computer:   http://localhost:{port}
  Im Praxis-Netzwerk:    http://{ip}:{port}

  Mitarbeiter können den Plan NUR ansehen.
  Bearbeitungs-PIN: {EDIT_PIN}
  (änderbar mit: export EDIT_PIN=neupin)
╚══════════════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
