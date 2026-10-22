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
    {id: 'sae', is: function () { return dir === 'posts' && page.indexOf('halloween-dimension-e-live-in-steal-an-egg') === 0; }, sel: ['.hero .dt'], how: 'after',
     hint: '🥚 postarea „Halloween Dimension e LIVE” (Steal An Egg)', href: 'posts/halloween-dimension-e-live-in-steal-an-egg-3-biomuri-echo-phantom-express-part-2-pe-24-oct.html'},
    {id: 'mm2', is: function () { return dir === 'posts' && page.indexOf('murder-mystery-2-halloween-2026') === 0; }, sel: ['.txt > p:last-of-type', '.txt'], how: 'append',
     hint: '🔪 postarea Murder Mystery 2 Halloween', href: 'posts/murder-mystery-2-halloween-2026-a-inceput-aseara-la-22-00-tine-pana-pe-16-noiembrie.html'},
    {id: 'hollow', is: function () { return dir === 'posts' && page.indexOf('the-hollow-eventul-de-halloween') === 0; }, sel: ['.w > nav'], how: 'append',
     hint: '🌑 postarea despre The Hollow', href: 'posts/the-hollow-eventul-de-halloween-al-roblox-vine-pe-22-octombrie.html'}
  ];
  var N = P.length;

  function load() { try { var a = JSON.parse(localStorage.getItem(KEY) || '[]'); return Array.isArray(a) ? a : []; } catch (e) { return []; } }
  function save(a) { try { localStorage.setItem(KEY, JSON.stringify(a)); } catch (e) {} }
  var found = load().filter(function (id) { return P.some(function (p) { return p.id === id; }); });

  var css = '.ph-pk{display:inline-block;vertical-align:middle;margin:0 4px;padding:2px;min-width:30px;min-height:30px;border:0;background:none;font-size:17px;line-height:1;cursor:pointer;opacity:.85;filter:drop-shadow(0 0 6px #ff7a00aa);animation:phw 3.2s ease-in-out infinite;-webkit-tap-highlight-color:transparent}' +
    '.ph-pk:hover,.ph-pk:focus-visible{opacity:1;transform:scale(1.25)}.ph-pk.got{animation:php .5s ease-out forwards;pointer-events:none}' +
    '@keyframes phw{0%,86%,100%{transform:rotate(0)}90%{transform:rotate(-14deg)}95%{transform:rotate(12deg)}}@keyframes php{to{transform:scale(2.2);opacity:0}}' +
    '.ph-bd{position:fixed;left:12px;bottom:calc(20px + env(safe-area-inset-bottom));z-index:19;padding:5px 10px;border-radius:999px;border:1px solid #ff7a0099;background:#1a0b05e0;color:#ffb066;font:700 12px/1.2 system-ui,sans-serif;cursor:pointer;box-shadow:0 0 10px #ff7a0044;opacity:.88}' +
    '.ph-bd:hover{opacity:1}.ph-bd.all{border-color:#ff2bd6;color:#ffd1f5}' +
    /* telefon: insigna nu mai plutește peste carduri; stă discret la finalul paginii (în flux), sub CTA, departe de butonul 🎃 „Înapoi sus” */
    '@media(max-width:600px){.ph-bd{position:relative;left:auto;bottom:auto;display:block;width:max-content;margin:4px auto calc(72px + env(safe-area-inset-bottom));padding:4px 9px;font-size:11px;opacity:.8}.ph-pn{bottom:calc(16px + env(safe-area-inset-bottom))}}' +
    '.ph-ts{position:fixed;left:50%;top:calc(12px + env(safe-area-inset-top));z-index:40;transform:translate(-50%,-20px);opacity:0;padding:9px 16px;border-radius:12px;border:1px solid #ff7a00;background:#1a0b05f2;color:#ffd9b0;font:700 14px/1.3 system-ui,sans-serif;box-shadow:0 0 18px #ff7a0066;pointer-events:none;transition:opacity .25s,transform .25s;max-width:calc(100vw - 32px);text-align:center}' +
    '.ph-ts.on{opacity:1;transform:translate(-50%,0)}' +
    '.ph-pn{position:fixed;left:12px;bottom:calc(58px + env(safe-area-inset-bottom));z-index:39;width:min(320px,calc(100vw - 24px));max-height:70vh;overflow:auto;padding:12px 14px;border-radius:14px;border:1px solid #ff7a00;background:#120818f5;color:#e9e2ff;font:14px/1.45 system-ui,sans-serif;box-shadow:0 0 24px #ff7a0055}' +
    '.ph-pn h3{margin:0 0 6px;font-size:15px;color:#ffb066}.ph-pn ul{margin:6px 0;padding:0;list-style:none}.ph-pn li{margin:3px 0}.ph-pn a{color:#00f0ff}' +
    '.ph-pn .x{float:right;border:0;background:none;color:#ffb066;font-size:18px;cursor:pointer;padding:0 4px}.ph-pn .rs{margin-top:6px;border:1px solid #ff7a0088;background:none;color:#ffb066;border-radius:8px;padding:4px 10px;cursor:pointer;font-size:12px}' +
    '.ph-pn .ctax{display:flex;flex-direction:column;gap:6px;margin-top:8px}.ph-pn .ctax a{display:block;text-align:center;padding:8px;border-radius:10px;border:1px solid #ff2bd6;color:#fff;text-decoration:none;font-weight:700;background:#ff2bd622}.ph-pn .ctax a.yt{border-color:#ff3b3b;background:#ff3b3b22}' +
    '@media(prefers-reduced-motion:reduce){.ph-pk,.ph-pk.got{animation:none!important}.ph-ts{transition:none}}';
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
