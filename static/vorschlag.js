// vorschlag.js — Oberfläche für Planungs-Vorschläge (planner/api.py)
//
// Eigenständig: index.html bindet diese Datei nur per <script> ein.
// Für Änderungen an der Vorschlags-Oberfläche muss index.html NICHT gelesen
// oder geändert werden. Genutzte Globals aus index.html (stabil halten):
//   currentKw, isEditMode, loadKw(kw), showToast(msg, type), renderView()
//   Tabellenzellen: td.cell[data-person][data-di]
//
// Ist VORSCHLAG_AKTIV auf dem Server aus, macht diese Datei gar nichts.
// Nach Änderungen: ?v= im <script>-Tag in index.html hochzählen (Cache).
(() => {
  "use strict";
  const TAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa"];
  let daten = null;          // letzte Antwort von /api/vorschlag/<kw>
  let auswahl = new Set();   // "person|di"

  const css = `
    #vs-overlay{position:fixed;inset:0;background:rgba(15,23,42,.45);display:none;z-index:900;
      align-items:flex-end;justify-content:center}
    #vs-overlay.offen{display:flex}
    #vs-panel{background:#fff;color:#0f172a;width:100%;max-width:640px;max-height:85vh;overflow:auto;
      border-radius:14px 14px 0 0;padding:16px;box-sizing:border-box;font-size:14px}
    @media (min-width:700px){#vs-overlay{align-items:center}#vs-panel{border-radius:14px}}
    #vs-panel h3{margin:0 0 4px;font-size:17px}
    #vs-panel .vs-sub{color:#64748b;margin-bottom:12px}
    #vs-panel .vs-tag{font-weight:600;margin:12px 0 4px}
    #vs-panel label{display:flex;gap:8px;align-items:flex-start;padding:6px 0;border-bottom:1px solid #e2e8f0}
    #vs-panel .vs-alt{color:#94a3b8;text-decoration:line-through}
    #vs-panel .vs-neu{color:#047857;font-weight:600}
    #vs-panel .vs-knoepfe{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px;position:sticky;bottom:-16px;
      background:#fff;padding:10px 0}
    #vs-panel button{padding:10px 14px;border-radius:8px;border:1px solid #cbd5e1;background:#f8fafc;font-size:14px}
    #vs-panel button.vs-primaer{background:#047857;border-color:#047857;color:#fff}
    #vs-panel .vs-meldung{font-size:12px;color:#b45309}
    td.cell.vs-markiert{outline:2px dashed #047857;outline-offset:-2px}
    @media (prefers-color-scheme: dark){
      #vs-panel{background:#1e293b;color:#e2e8f0}
      #vs-panel label{border-color:#334155}
      #vs-panel button{background:#334155;border-color:#475569;color:#e2e8f0}
      #vs-panel .vs-knoepfe{background:#1e293b}
    }`;

  async function start() {
    let status;
    try {
      const r = await fetch("/api/vorschlag/status");
      status = r.ok ? await r.json() : null;
    } catch { status = null; }
    if (!status || !status.aktiv) return;   // Feature aus → nichts anzeigen

    document.head.insertAdjacentHTML("beforeend", `<style>${css}</style>`);
    document.body.insertAdjacentHTML("beforeend",
      `<div id="vs-overlay"><div id="vs-panel"></div></div>`);
    const leiste = document.querySelector(".topbar-actions");
    if (leiste) {
      leiste.insertAdjacentHTML("afterbegin",
        `<button class="btn btn-ghost edit-only" id="btn-vorschlag" title="Diese Woche planen">
           <span class="btn-icon">🤖</span><span class="btn-lbl">Woche planen</span></button>`);
      document.getElementById("btn-vorschlag").addEventListener("click", oeffnen);
    }
    document.getElementById("vs-overlay").addEventListener("click", e => {
      if (e.target.id === "vs-overlay") schliessen();
    });

    // Markierungen nach jedem Neuzeichnen der Tabelle wieder anbringen
    if (typeof window.renderView === "function") {
      const orig = window.renderView;
      window.renderView = function (...a) { const r = orig.apply(this, a); markieren(); return r; };
    }
  }

  async function oeffnen() {
    const panel = document.getElementById("vs-panel");
    panel.innerHTML = `<h3>Woche planen · KW ${currentKw}</h3><div class="vs-sub">wird berechnet … Nur diese Woche, manuelle Einträge bleiben unverändert.</div>`;
    document.getElementById("vs-overlay").classList.add("offen");
    try {
      const r = await fetch(`/api/vorschlag/${currentKw}`, { credentials: "same-origin" });
      if (!r.ok) throw new Error((r.status === 401 || r.status === 403) ? "Bitte zuerst PIN eingeben" : `Fehler ${r.status}`);
      daten = await r.json();
    } catch (e) {
      panel.innerHTML = `<h3>Woche planen · KW ${currentKw}</h3><div class="vs-sub">${e.message}</div>
        <div class="vs-knoepfe"><button data-a="zu">Schließen</button></div>`;
      panel.querySelector("[data-a=zu]").onclick = schliessen;
      return;
    }
    auswahl = new Set(daten.aenderungen.map(a => `${a.person}|${a.di}`));
    zeichnen();
    markieren();
  }

  function zeichnen() {
    const panel = document.getElementById("vs-panel");
    const a = daten.aenderungen;
    const v = daten.vorher.pflicht, n = daten.nachher.pflicht;
    let html = `<h3>Woche planen · KW ${daten.kw}</h3>
      <div class="vs-sub">${a.length} Änderung${a.length !== 1 ? "en" : ""} ·
        Pflichtregel-Verstöße: ${v} → ${n} · Planer: ${daten.planer}<br>
        Manuelle Einträge bleiben unverändert.</div>`;
    if (!a.length) html += `<div>Keine Änderungen vorgeschlagen.</div>`;
    TAGE.forEach((tag, di) => {
      const amTag = a.filter(x => x.di === di);
      if (!amTag.length) return;
      html += `<div class="vs-tag">${tag}</div>`;
      for (const x of amTag) {
        const k = `${x.person}|${x.di}`;
        html += `<label><input type="checkbox" data-k="${esc(k)}" ${auswahl.has(k) ? "checked" : ""}>
          <span><b>${esc(x.person)}</b><br><span class="vs-alt">${esc(x.alt)}</span> → <span class="vs-neu">${esc(x.neu)}</span></span></label>`;
      }
    });
    if (daten.nachher.meldungen.length) {
      html += `<div class="vs-tag">Offene Regelhinweise im Vorschlag</div>` +
        daten.nachher.meldungen.slice(0, 20).map(m =>
          `<div class="vs-meldung">${m.tag}: ${esc(m.text)}</div>`).join("");
    }
    html += `<div class="vs-knoepfe">
        <button class="vs-primaer" data-a="alle" ${a.length ? "" : "disabled"}>Alle übernehmen</button>
        <button data-a="auswahl" ${a.length ? "" : "disabled"}>Auswahl übernehmen</button>
        <button data-a="ab">Ablehnen</button></div>`;
    panel.innerHTML = html;
    panel.querySelectorAll("input[data-k]").forEach(cb => cb.onchange = () => {
      cb.checked ? auswahl.add(cb.dataset.k) : auswahl.delete(cb.dataset.k);
      markieren();
    });
    panel.querySelector("[data-a=alle]").onclick = () => uebernehmen(a);
    panel.querySelector("[data-a=auswahl]").onclick =
      () => uebernehmen(a.filter(x => auswahl.has(`${x.person}|${x.di}`)));
    panel.querySelector("[data-a=ab]").onclick = () => { schliessen(); showToast("Vorschlag verworfen", "ok"); };
  }

  async function uebernehmen(liste) {
    if (!liste.length) { showToast("Nichts ausgewählt", "err"); return; }
    try {
      const kw = daten.kw;   // schliessen() setzt daten = null
      const r = await fetch(`/api/vorschlag/${kw}/uebernehmen`, {
        method: "POST", credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ zellen: liste.map(x => ({ person: x.person, di: x.di, neu: x.neu })) }),
      });
      if (!r.ok) throw new Error(`Fehler ${r.status}`);
      const res = await r.json();
      schliessen();
      await loadKw(kw);
      showToast(`${res.uebernommen} Zelle${res.uebernommen !== 1 ? "n" : ""} übernommen`, "ok");
    } catch (e) {
      showToast("Übernehmen fehlgeschlagen: " + e.message, "err");
    }
  }

  function schliessen() {
    document.getElementById("vs-overlay").classList.remove("offen");
    daten = null;
    markieren();
  }

  function markieren() {
    document.querySelectorAll("td.cell.vs-markiert").forEach(td => td.classList.remove("vs-markiert"));
    if (!daten || daten.kw !== currentKw) return;
    for (const x of daten.aenderungen) {
      if (!auswahl.has(`${x.person}|${x.di}`)) continue;
      const td = document.querySelector(`td.cell[data-person="${CSS.escape(x.person)}"][data-di="${x.di}"]`);
      if (td) td.classList.add("vs-markiert");
    }
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
