// Service Worker — Dienstplan 2026
const CACHE = "dienstplan-v1";
const SHELL = ["/", "/static/icon.svg"];

// Install: Cache-Shell
self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

// Activate: Alten Cache löschen
self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Fetch: API immer frisch vom Netz, UI-Shell aus Cache
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  // API-Requests immer live (nie cachen)
  if (url.pathname.startsWith("/api/")) {
    e.respondWith(fetch(e.request));
    return;
  }
  // Alles andere: Network-first, Cache als Fallback
  e.respondWith(
    fetch(e.request)
      .then(resp => {
        const clone = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
        return resp;
      })
      .catch(() => caches.match(e.request))
  );
});
