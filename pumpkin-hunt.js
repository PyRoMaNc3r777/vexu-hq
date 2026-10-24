/* VEXU HQ · Vânătoarea de dovleci 🎃 (Halloween 2026)
   100% local: progres în localStorage, fără conturi, fără server, fără servicii externe.
   OPRIRE: pune ON = false (sau se oprește singură după END, adică după 2 nov 2026, ora României). */
(function () {
  var ON = true;
  var END = Date.parse('2026-11-03T00:00:00+02:00');
  if (!ON || Date.now() >= END) return;

  var KEY = 'vexu-dovleci-2026';
  var src = (document.currentScript && document.currentScript.src) || '';
  var BASE = src ? src.replace(/[^\/]*$/, '') : '/vexu-hq/';
  var path = location.pathname.replace(BASE.replace(/^https?:\/\/[^\/]+/, ''), '/');
  var page = path.split('/').pop() || 'index.html';
  var dir = path.split('/').slice(-2, -1)[0] || '';

  // Cei N dovleci: id, unde stă pe pagină, indiciu + link pentru panou.
  var P = [
    {id: 'dash', is: function () { return dir === '' && (page === 'index.html' || page === ''); }, sel: ['.sub'], how: 'append',
     hint: '⚡ Dashboard', href: 'index.html'},
    {id: 'blog', is: function () { return dir === '' && page === 'blog.html'; }, sel: ['.ftitle'], how: 'append',
     hint: '📰 Blog', href: 'blog.html'},
    {id: 'cal', is: function () { return dir === '' && page === 'calendar.html'; }, sel: ['.w > p'], how: 'append',
     hint: '📅 Calendar Halloween', href: 'calendar.html'},
    {id: 'joc', is: function () { return dir === 'joc'; }, sel: ['.cta b'], how: 'append',
     hint: '🎮 orice pagină de joc', href: 'joc/steal-an-egg.html'},
    {id: 'sae', is: function () { return dir === 'posts' && page.indexOf('halloween-dimension-e-live-in-steal-an-egg') === 0; }, sel: ['.art-m .dt'], how: 'after',
     hint: '🥚 postarea „Halloween Dimension e LIVE” (Steal An Egg)', href: 'posts/halloween-dimension-e-live-in-steal-an-egg-3-biomuri-echo-phantom-express-part-2-pe-24-oct.html'},
    {id: 'mm2', is: function () { return dir === 'posts' && page.indexOf('murder-mystery-2-halloween-2026') === 0; }, sel: ['.txt > p:last-of-type', '.txt'], how: 'append',
     hint: '🔪 postarea Murder Mystery 2 Halloween', href: 'posts/murder-mystery-2-halloween-2026-a-inceput-aseara-la-22-00-tine-pana-pe-16-noiembrie.html'},
    {id: 'hollow', is: function () { return dir === 'posts' && page.indexOf('the-hollow-eventul-de-halloween') === 0; }, sel: ['.art-m', '.w > nav'], how: 'append',
     hint: '🌑 postarea despre The Hollow', href: 'posts/the-hollow-eventul-de-halloween-al-roblox-vine-pe-22-octombrie.html'}
  ];
  var N = P.length;

  function load() { try { var a = JSON.parse(localStorage.getItem(KEY) || '[]'); return Array.isArray(a) ? a : []; } catch (e) { return []; } }
  function save(a) { try { localStorage.setItem(KEY, JSON.stringify(a)); } catch (e) {} }
  var found = load().filter(function (id) { return P.some(function (p) { return p.id === id; }); });

  var css = '.ph-pk{display:inline-block;vertical-align:middle;margin:0 2px;padding:0;min-width:28px;min-height:28px;border:0;background:none;font-size:15px;line-height:1;cursor:pointer;opacity:.7;-webkit-tap-highlight-color:transparent}' +
    '.ph-pk:hover,.ph-pk:focus-visible{opacity:1}.ph-pk:focus-visible{outline:2px solid #ff8a1f;outline-offset:2px;border-radius:6px}.ph-pk.got{animation:php .4s ease-out forwards;pointer-events:none}' +
    '@keyframes php{to{transform:scale(1.8);opacity:0}}' +
    '.ph-bd{position:fixed;left:12px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:19;padding:0 12px;min-height:32px;border-radius:6px;border:1px solid #2a2c35;background:#121317;color:#a2a5b0;font:500 12px/1 "Geist Mono",ui-monospace,monospace;cursor:pointer;transition:background-color .12s,color .12s}' +
    '.ph-bd:hover{background:#17181d;color:#ecedf0}.ph-bd:focus-visible{outline:2px solid #ff8a1f;outline-offset:2px}.ph-bd.all{border-color:#ff8a1f;color:#ff8a1f}' +
    /* telefon: insigna stă discret la finalul paginii (în flux), nu plutește peste conținut */
    '@media(max-width:600px){.ph-bd{position:relative;left:auto;bottom:auto;display:block;width:max-content;margin:8px 16px calc(72px + env(safe-area-inset-bottom))}.ph-pn{bottom:calc(16px + env(safe-area-inset-bottom))}}' +
    '.ph-ts{position:fixed;left:50%;top:calc(12px + env(safe-area-inset-top));z-index:40;transform:translate(-50%,-12px);opacity:0;padding:10px 16px;border-radius:8px;border:1px solid #2a2c35;border-left:3px solid #ff8a1f;background:#17181d;color:#ecedf0;font:500 14px/1.3 "Geist",system-ui,sans-serif;pointer-events:none;transition:opacity .2s,transform .2s;max-width:calc(100vw - 32px)}' +
    '.ph-ts.on{opacity:1;transform:translate(-50%,0)}' +
    '.ph-pn{position:fixed;left:12px;bottom:calc(56px + env(safe-area-inset-bottom));z-index:39;width:min(320px,calc(100vw - 24px));max-height:70vh;overflow:auto;padding:16px;border-radius:8px;border:1px solid #2a2c35;background:#121317;color:#a2a5b0;font:14px/1.5 "Geist",system-ui,sans-serif}' +
    '.ph-pn h3{margin:0 0 8px;font-size:15px;color:#ecedf0;letter-spacing:-.01em}.ph-pn ul{margin:8px 0;padding:0;list-style:none}.ph-pn li{margin:4px 0}.ph-pn a{color:#ff8a1f}' +
    '.ph-pn .x{float:right;border:0;background:none;color:#a2a5b0;font-size:18px;cursor:pointer;padding:0 4px;min-width:32px;min-height:32px}.ph-pn .rs{margin-top:8px;border:1px solid #2a2c35;background:none;color:#a2a5b0;border-radius:6px;padding:0 12px;min-height:32px;cursor:pointer;font-size:12px}' +
    '.ph-pn .ctax{display:flex;flex-direction:column;gap:8px;margin-top:12px}.ph-pn .ctax a{display:block;text-align:center;padding:10px;border-radius:6px;border:1px solid #2a2c35;color:#ecedf0;text-decoration:none;font-weight:600;background:#17181d}.ph-pn .ctax a.yt{border-color:#ff8a1f}' +
    '@media(prefers-reduced-motion:reduce){.ph-pk.got{animation:none!important}.ph-ts{transition:none}}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }

  var toast = el('div', 'ph-ts'); toast.setAttribute('role', 'status'); toast.setAttribute('aria-live', 'polite');
  var tt;
  function say(t) { toast.textContent = t; toast.classList.add('on'); clearTimeout(tt); tt = setTimeout(function () { toast.classList.remove('on'); }, 2800); }

  var badge = el('button', 'ph-bd'); badge.type = 'button';
  var panel = null;
  function upd() {
    badge.textContent = '🎃 ' + found.length + '/' + N;
    badge.classList.toggle('all', found.length >= N);
    badge.setAttribute('aria-label', 'Vânătoarea de dovleci: ' + found.length + ' din ' + N + ' găsiți');
  }
  function closePanel() { if (panel) { panel.remove(); panel = null; } }
  function openPanel(final) {
    closePanel();
    var done = found.length >= N;
    var h = '<button class="x" type="button" aria-label="Închide">✕</button>';
    if (done) {
      h += '<h3>🎉 Felicitări, vânătorule!</h3><p>Ai găsit toți cei ' + N + ' dovleci ascunși prin VEXU HQ! 🎃👑 Ești oficial cel mai tare vânător de dovleci de Halloween.</p>' +
        '<p><b>Follow = Au ce bile! 💥</b></p><div class="ctax"><a href="https://www.tiktok.com/@vexu_online" target="_blank" rel="noopener">🎵 TikTok @vexu_online</a>' +
        '<a class="yt" href="https://www.youtube.com/@VexuOnline" target="_blank" rel="noopener">▶️ YouTube VEXU Online</a></div>';
    } else {
      h += '<h3>🎃 Vânătoarea de dovleci</h3><p>Am ascuns ' + N + ' dovleci mici prin site. Apasă pe ei când îi vezi! Progresul rămâne doar pe dispozitivul tău.</p><p>Unde să cauți:</p>';
    }
    h += '<ul>' + P.map(function (p) {
      var ok = found.indexOf(p.id) >= 0;
      return '<li>' + (ok ? '✅ ' : '❔ ') + '<a href="' + BASE + p.href + '">' + p.hint + '</a></li>';
    }).join('') + '</ul><button class="rs" type="button">↺ Reîncepe vânătoarea</button>';
    panel = el('div', 'ph-pn', h); panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-label', 'Vânătoarea de dovleci');
    panel.querySelector('.x').onclick = closePanel;
    panel.querySelector('.rs').onclick = function () { found = []; save(found); upd(); closePanel(); placeAll(); say('Vânătoarea a reînceput! 🎃'); };
    document.body.appendChild(panel);
  }
  badge.onclick = function () { if (panel) closePanel(); else openPanel(); };

  function grab(p, b) {
    if (found.indexOf(p.id) < 0) { found.push(p.id); save(found); }
    b.classList.add('got'); setTimeout(function () { b.remove(); }, 520);
    upd();
    if (found.length >= N) { say('Ai găsit ' + N + '/' + N + ' dovleci! 🎉'); setTimeout(function () { openPanel(true); }, 700); }
    else say('Ai găsit ' + found.length + '/' + N + ' dovleci! 🎃');
  }
  function place(p) {
    if (found.indexOf(p.id) >= 0 || !p.is() || document.querySelector('.ph-pk[data-id="' + p.id + '"]')) return;
    var t = null;
    for (var i = 0; i < p.sel.length && !t; i++) t = document.querySelector(p.sel[i]);
    if (!t) return;
    var b = el('button', 'ph-pk', '🎃'); b.type = 'button'; b.dataset.id = p.id;
    b.setAttribute('aria-label', 'Dovleac ascuns! Apasă ca să-l prinzi'); b.title = 'Un dovleac ascuns!';
    b.onclick = function (ev) { ev.preventDefault(); ev.stopPropagation(); grab(p, b); };
    if (p.how === 'after') t.insertAdjacentElement('afterend', b); else t.appendChild(b);
  }
  function placeAll() { P.forEach(place); }

  function init() {
    document.body.appendChild(toast); document.body.appendChild(badge); upd(); placeAll();
    // unele pagini își construiesc conținutul din JS: mai încercăm o dată după încărcare
    setTimeout(placeAll, 1500);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
