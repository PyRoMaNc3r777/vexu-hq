// VEXU HQ service worker
// HTML + JSON: NETWORK-FIRST (online vezi mereu ultimul deploy/date), fallback la cache offline.
// CSS (style.css?v=hash): NETWORK-FIRST, ca designul nou să nu rămână blocat în cache. Imagini/fonturi/icon-uri: CACHE-FIRST. Mărește VERSION când schimbi imagini cu același nume.
const VERSION = 'v8-2026-10-25';
const CACHE = 'vexu-hq-' + VERSION;
const BASE = '/vexu-hq/';
const CORE = ['', 'index.html', 'style.css', 'events.js', 'feed.js', 'blog.html', 'shorts.html', 'virtual-events.json', 'shorts.json', 'shorts-views.json', 'calendar.html', 'recap.html', 'data.json', 'extra.json', 'posts.json',
  'posts-index.json', 'posts-search.json', 'calendar-events.json', 'player-history.json', 'history.json',
  'manifest.webmanifest', 'icon.png', 'icon-192.png', 'icon-512.png', 'fonts/geist-latin.woff2', 'fonts/geist-latin-ext.woff2', 'fonts/geist-mono-latin.woff2', 'fonts/geist-mono-latin-ext.woff2'].map(p => BASE + p);

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(CORE.map(u =>
    fetch(u, {cache: 'no-store'}).then(r => r.ok ? c.put(key(new URL(u, location.origin)), r) : null).catch(() => null)
  ))).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('vexu-hq-') && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

// cheie de cache fără query (?<timestamp>) și cu / → index.html
function key(u) {
  let p = u.pathname;
  if (p.endsWith('/')) p += 'index.html';
  return u.origin + p;
}

async function networkFirst(req, u) {
  const c = await caches.open(CACHE);
  try {
    const r = await fetch(req, {cache: 'no-cache'});
    if (r && r.ok) c.put(key(u), r.clone()).catch(() => {});
    return r;
  } catch (err) {
    const hit = await c.match(key(u));
    if (hit) return hit;
    if (req.mode === 'navigate') {
      const home = await c.match(key(new URL(BASE, location.origin)));
      if (home) return home;
    }
    throw err;
  }
}

async function cacheFirst(req, u) {
  const c = await caches.open(CACHE);
  const hit = await c.match(key(u));
  if (hit) return hit;
  const r = await fetch(req);
  if (r && r.ok) c.put(key(u), r.clone()).catch(() => {});
  return r;
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const u = new URL(req.url);
  if (u.origin !== location.origin || !u.pathname.startsWith(BASE)) return; // Roblox/roproxy etc. merg direct la rețea
  const p = u.pathname;
  if (req.mode === 'navigate' || p.endsWith('/') || /\.(html|json|webmanifest|css|js)$/.test(p)) {
    e.respondWith(networkFirst(req, u));
  } else if (/\.(png|jpe?g|webp|gif|svg|ico|woff2?)$/.test(p)) {
    e.respondWith(cacheFirst(req, u));
  }
});
