// Service Worker — Dienstplan 2026
// Version hochzählen → Browser löscht alten Cache automatisch
const CACHE = "dienstplan-v3";

// Nur wirklich statische Dateien cachen (kein HTML!)
const STATIC = ["/static/logo.png", "/static/icon.svg"];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(STATIC))
      .then(() => self.skipWaiting())   // sofort aktivieren
  );
});

self.addEventListener("activate", e => {
  // Alle alten Cache-Versionen löschen
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);

  // HTML-Seite und API: IMMER frisch vom Server (nie aus Cache)
  if (url.pathname === "/" || url.pathname.startsWith("/api/")) {
    e.respondWith(fetch(e.request));
    return;
  }

  // Statische Dateien (Logo, Icons): Cache-first
  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(resp => {
        const clone = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
        return resp;
      });
    })
  );
});
