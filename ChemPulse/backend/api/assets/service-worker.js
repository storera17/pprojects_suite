self.addEventListener("install", (event) => {
  event.waitUntil(caches.open("chempulse-mobile-v1").then((cache) => cache.addAll(["/mobile", "/mobile/app.js", "/mobile/manifest.webmanifest"])));
});
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/api/")) return;
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
