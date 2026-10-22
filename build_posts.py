#!/usr/bin/env python3
"""Generează posts/<slug>.html, posts-index.json, posts-search.json, calendar-events.json, blog.html, calendar.html din posts.json.

Utilizare:
  python3 build_posts.py              # rebuild complet
  python3 build_posts.py --append batch.json   # adaugă postări din fișier (array JSON) apoi rebuild

Fiecare post: titlu, text, eticheta (sau listă), img, surse[], date (YYYY-MM-DD).
Opțional: published (ISO +03/+02), featured, section ("shorts"), slug (fixează URL-ul), old_slugs[], events[],
          confirmat/zvon (blocuri separate), joc (numele jocului; "Roblox (platformă)" pentru știri de platformă).
Dacă lipsește joc → se detectează automat (joc_detect.py) și se scrie în posts.json ("" = ambiguu / fără joc).
Pagini per joc: joc/<slug-joc>.html. Evenimente de calendar fără postare: calendar-extra.json.
Dacă lipsește published → se completează automat cu ora curentă Europe/Bucharest.
Dacă lipsește date → se ia din published (sau azi).
"""
import json, re, unicodedata, html, os, sys, argparse
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from joc_detect import detect as detect_joc, canon as canon_joc

D = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(D, 'posts.json')
TZ = ZoneInfo('Europe/Bucharest')
PAGE = 12

def now_ro():
    return datetime.now(TZ)

def slug(t):
    a = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', a).strip('-')

LUNI = ['ianuarie','februarie','martie','aprilie','mai','iunie','iulie','august','septembrie','octombrie','noiembrie','decembrie']
def ro_date(d):
    y, m, dd = map(int, d.split('-')[:3])
    return f'{dd} {LUNI[m-1]} {y}'

def labels_of(p):
    e = p.get('eticheta', 'CONFIRMAT')
    return e if isinstance(e, list) else [e]

def excerpt_of(p, n=140):
    t = p.get('text') or p.get('confirmat') or ''
    flat = ' '.join(t.replace('\n- ', ' • ').split())
    return flat if len(flat) < n else flat[: n - 1].rsplit(' ', 1)[0] + '…'

def search_text(p):
    """Text pentru căutarea din blog (posts-search.json): titlu + text + confirmat + zvon, fără diacritice/URL-uri, lowercase."""
    z = p.get('zvon') or []
    raw = ' '.join([p.get('titlu', ''), p.get('text', ''), p.get('confirmat', ''), ' '.join(z if isinstance(z, list) else [z])])
    raw = URL.sub(' ', raw)
    raw = ''.join(c for c in unicodedata.normalize('NFD', raw) if unicodedata.category(c) != 'Mn').lower()
    return ' '.join(raw.split())

def pub_key(p):
    return p.get('published') or (p.get('date', '1970-01-01') + 'T12:00:00+03:00')

def ensure_meta(posts):
    changed = False
    now = now_ro()
    for p in posts:
        if 'published' not in p:
            p['published'] = now.isoformat(timespec='seconds')
            changed = True
        if 'date' not in p:
            p['date'] = p['published'][:10]
            changed = True
        if 'joc' not in p:
            p['joc'] = detect_joc(p)
            changed = True
    return changed

def joc_of(p):
    return (p.get('joc') or '').strip()

def joc_slug(j):
    return slug(j)

CSS = """@media(min-width:768px){.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.grid .p{margin:0}a.p.feat{display:grid;grid-template-columns:1.3fr 1fr}.feat img{height:100%;min-height:320px}.feat h2{font-size:1.7em}.hero{max-width:1100px;margin:14px auto}.hero .b{max-width:760px;margin:auto;padding:24px}.hero .txt{font-size:1.15em}}@media(min-width:1200px){.grid{grid-template-columns:repeat(3,1fr)}.hero{display:grid;grid-template-columns:1fr 1fr}.hero .hi{padding:16px}.hero img{border-radius:12px}}
*{box-sizing:border-box}body{margin:0;background:#07040f;color:#eee;font-family:system-ui,sans-serif;background-image:radial-gradient(circle at 20% 0,#3b0a5c 0,transparent 50%),radial-gradient(circle at 100% 100%,#002f3d 0,transparent 50%);min-height:100vh}
.w{max-width:1400px;margin:auto;padding:16px}h1{font-size:2em;margin:8px 0;text-align:center;background:linear-gradient(90deg,#ff2bd6,#00f0ff);-webkit-background-clip:text;color:transparent}
nav{text-align:center;margin:8px 0;display:flex;flex-wrap:wrap;gap:8px;justify-content:center;align-items:center}nav a,.btn{color:#00f0ff;margin:0 4px;font-weight:700;text-decoration:none}.btn{display:inline-block;margin:14px 0;padding:10px 16px;border:1px solid #00f0ff;border-radius:12px;box-shadow:0 0 12px #00f0ff55;background:#000a;cursor:pointer;font:inherit}
.p{background:#120a22cc;border:1px solid #ff2bd655;border-radius:16px;margin:14px 0;overflow:hidden;box-shadow:0 0 18px #ff2bd622}a.p{display:block;color:inherit;text-decoration:none}a.p:hover{border-color:#ff2bd6;box-shadow:0 0 24px #ff2bd666}
.p img{width:100%;height:190px;object-fit:cover;display:block}.hero img{height:auto;max-height:420px}.b{padding:14px}h2{margin:6px 0;font-size:1.15em}.l{display:inline-block;padding:3px 9px;border-radius:20px;font-size:.72em;font-weight:800}
.dt{color:#9a8fb5;font-size:.8em;margin-left:6px}.txt{font-size:1.05em;line-height:1.55;margin:10px 0}.more{color:#ff7be6;font-weight:700;font-size:.85em;margin-top:8px}
.CONFIRMAT{background:#39ff8822;color:#39ff88;border:1px solid #39ff88}.VEXU-LIVE{background:#ff2bd622;color:#ff2bd6;border:1px solid #ff2bd6;box-shadow:0 0 10px #ff2bd6aa;text-shadow:0 0 6px #ff2bd6}.txt ul{margin:8px 0;padding-left:22px}.txt li{margin:4px 0}.txt a{color:#00f0ff;word-break:break-all}.TREND-SHORTS{background:#00f0ff22;color:#00f0ff;border:1px solid #00f0ff;box-shadow:0 0 10px #00f0ffaa;text-shadow:0 0 6px #00f0ff}.sec{margin:28px 0 6px;font-size:1.5em;color:#00f0ff;text-shadow:0 0 10px #00f0ff}.bx{border-radius:12px;padding:12px 14px;margin:12px 0}.bx h3{margin:0 0 6px;font-size:1em}.bxC{background:#39ff8814;border:1px solid #39ff88;box-shadow:0 0 12px #39ff8833}.bxC h3{color:#39ff88}.bxZ{background:#ffd40014;border:1px solid #ffd400;box-shadow:0 0 12px #ffd40033}.bxZ h3{color:#ffd400}.ZVON{background:#ffd40022;color:#ffd400;border:1px solid #ffd400}.s a{color:#ff7be6;font-size:.8em;word-break:break-all;display:block;margin-top:4px}
.fx{position:fixed;inset:0;pointer-events:none;overflow:hidden;z-index:0}.fx span{position:absolute;bottom:-60px;font-size:22px;opacity:0;filter:drop-shadow(0 0 8px #ff7a00);animation:fl 18s linear infinite}.fx span:nth-child(1){left:6%;animation-delay:0s}.fx span:nth-child(2){left:22%;animation-delay:6s;font-size:16px}.fx span:nth-child(3){left:41%;animation-delay:11s}.fx span:nth-child(4){left:63%;animation-delay:3s;font-size:18px}.fx span:nth-child(5){left:80%;animation-delay:9s}.fx span:nth-child(6){left:93%;animation-delay:14s;font-size:15px}@keyframes fl{0%{transform:translateY(0) rotate(0);opacity:0}10%{opacity:.55}50%{transform:translate(18px,-55vh) rotate(12deg)}90%{opacity:.4}100%{transform:translate(-12px,-110vh) rotate(-10deg);opacity:0}}.w{position:relative;z-index:1}@media(prefers-reduced-motion:reduce){.fx{display:none}*{animation:none!important}}a.p{transition:transform .2s,border-color .2s,box-shadow .2s}a.p:hover{transform:translateY(-3px)}a.p:active{transform:scale(.98)}
.filters{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:12px 0 6px}.chip{border:1px solid #ff2bd655;background:#120a22cc;color:#eee;border-radius:999px;padding:7px 12px;font-size:.85em;font-weight:700;cursor:pointer}.chip.on{border-color:#00f0ff;color:#00f0ff;box-shadow:0 0 12px #00f0ff55}.chip .n{opacity:.7;margin-left:4px}.srch{display:flex;max-width:560px;margin:12px auto 0;position:relative}.srch input{flex:1;width:100%;font:inherit;font-size:16px;color:#eee;background:#120a22cc;border:1px solid #ff2bd655;border-radius:999px;padding:10px 42px 10px 16px;outline:none;-webkit-appearance:none;appearance:none}.srch input:focus{border-color:#00f0ff;box-shadow:0 0 14px #00f0ff55}.srch input::placeholder{color:#9a8fb5}.srch input::-webkit-search-cancel-button{display:none}.srch button{position:absolute;right:6px;top:50%;transform:translateY(-50%);border:0;background:none;color:#ff7be6;font-size:1.05em;padding:6px 10px;cursor:pointer;visibility:hidden}.qinfo{text-align:center;color:#9a8fb5;font-size:.82em;min-height:1em;margin:4px 0 0}.dayh{margin:22px 0 8px;font-size:1.25em;color:#ff7be6;text-shadow:0 0 10px #ff2bd655}.dayh:first-child{margin-top:8px}#moreWrap{text-align:center;margin:18px 0}#featSlot .p{margin-top:8px}.empty{text-align:center;color:#9a8fb5;padding:24px}.shorts-entry{text-align:center;margin:10px 0 4px}.shorts-entry button{border:1px solid #00f0ff;background:#00f0ff18;color:#00f0ff;border-radius:12px;padding:10px 14px;font-weight:800;cursor:pointer;box-shadow:0 0 12px #00f0ff44}
.cal .row{display:grid;grid-template-columns:72px 1fr;gap:12px;align-items:start;margin:14px 0}.cal .ico{width:72px;height:72px;border-radius:14px;object-fit:cover;border:1px solid #ff2bd655;background:#000a}.cal .card{background:#120a22cc;border:1px solid #ff2bd655;border-radius:16px;padding:14px;box-shadow:0 0 18px #ff2bd622}.cal .st{font-weight:800;margin:6px 0;color:#ffd400}.cal .st.live{color:#39ff88;text-shadow:0 0 10px #39ff88}.cal .st.done{color:#9a8fb5}.cal .cd{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}.cal .cd div{background:#000a;border:1px solid #00f0ff66;border-radius:10px;padding:8px 6px;min-width:58px;text-align:center}.cal .cd b{display:block;font-size:1.3em;color:#ff2bd6}.cal .cd span{font-size:.65em;color:#aaa}.cal .meta{color:#9a8fb5;font-size:.85em}.cal a.golink{color:#00f0ff;font-weight:700;text-decoration:none}.note{font-size:.8em;color:#ffd400;margin-top:6px}@media(max-width:520px){.cal .row{grid-template-columns:56px 1fr}.cal .ico{width:56px;height:56px}}
.rp{position:fixed;top:0;left:0;height:3px;width:100%;transform-origin:0 50%;transform:scaleX(0);background:linear-gradient(90deg,#ff7a00,#ff2bd6,#00f0ff);box-shadow:0 0 10px #ff2bd6,0 0 18px #ff7a0088;z-index:50;pointer-events:none}.acts{display:flex;flex-wrap:wrap;gap:10px;align-items:center}.acts .btn{margin:14px 0}.shr{border-color:#ff7a00;color:#ffb066;box-shadow:0 0 12px #ff7a0055}.shr.ok{border-color:#39ff88;color:#39ff88;box-shadow:0 0 14px #39ff8877}.rel{margin:10px 0 24px}.rel h2{color:#ff7be6;text-shadow:0 0 10px #ff2bd655;font-size:1.25em;margin:8px 0}.rel .grid{display:grid;grid-template-columns:1fr;gap:12px}.rel a.p{margin:0;display:grid;grid-template-columns:110px 1fr}.rel a.p img{height:100%;min-height:86px}.rel .b{padding:10px 12px}.rel .dt{display:block;margin:4px 0 0}.rel h3{margin:6px 0 0;font-size:.95em;line-height:1.3}@media(min-width:768px){.rel .grid{grid-template-columns:repeat(3,1fr)}.rel a.p{display:block}.rel a.p img{height:150px}}
.jl{display:inline-block;margin:8px 0 2px;padding:4px 11px;border-radius:999px;border:1px solid #ff7a00;color:#ffb066;background:#ff7a0018;font-weight:800;font-size:.85em;text-decoration:none;box-shadow:0 0 10px #ff7a0044}.jl:hover{background:#ff7a0033}.jg{display:block;color:#ffb066;font-size:.78em;font-weight:700;margin-top:6px}
.ftitle{text-align:center;color:#9a8fb5;font-size:.78em;font-weight:800;letter-spacing:.06em;text-transform:uppercase;margin:12px 0 0}#gfilters{margin-top:6px}#gfilters .chip.on{border-color:#ff7a00;color:#ffb066;box-shadow:0 0 12px #ff7a0055}.gpage{text-align:center;margin:6px 0 0;min-height:1em}.gpage a{color:#ffb066;font-weight:800;text-decoration:none}
@media(max-width:767px){#gfilters{flex-wrap:nowrap;justify-content:flex-start;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding:2px 16px 8px;margin-left:-16px;margin-right:-16px}#gfilters::-webkit-scrollbar{display:none}#gfilters .chip{flex:0 0 auto;white-space:nowrap}}
.cta{text-align:center;margin:26px 0 10px;padding:16px;border-radius:16px;border:1px solid #ff2bd6;background:#120a22cc;box-shadow:0 0 18px #ff2bd644}.cta b{display:block;font-size:1.2em;margin-bottom:8px;color:#ff7be6;text-shadow:0 0 10px #ff2bd655}.cta a{display:inline-block;margin:6px;padding:10px 16px;border-radius:12px;font-weight:800;text-decoration:none;border:1px solid #00f0ff;color:#00f0ff;background:#000a;box-shadow:0 0 12px #00f0ff55}.cta a.yt{border-color:#ff3b3b;color:#ff7070;box-shadow:0 0 12px #ff3b3b55}
.gcount{text-align:center;color:#9a8fb5;margin:4px 0 0}"""

CSS_FX = 'h1{background-image:linear-gradient(90deg,#ff2bd6,#00f0ff,#ff7a00,#ff2bd6);background-size:300% auto;-webkit-background-clip:text;background-clip:text;animation:shm 8s linear infinite}h1 .em{color:#fff;-webkit-text-fill-color:#fff;filter:drop-shadow(0 0 8px #ff7a00aa)}@keyframes shm{to{background-position:300% center}}.moon{position:fixed;top:-46px;right:-46px;width:150px;height:150px;border-radius:50%;background:radial-gradient(circle at 38% 38%,#fff8de,#ffd27a 42%,#ff8a1f 70%,#ff7a0000 72%);box-shadow:0 0 70px 24px #ff7a0033;opacity:.28;pointer-events:none;z-index:0;animation:mn 6s ease-in-out infinite}@keyframes mn{50%{opacity:.45}}@media(min-width:768px){.moon{top:-30px;right:-30px;width:220px;height:220px}}@media(prefers-reduced-motion:reduce){h1,.moon{animation:none}}'
EMO = re.compile('([\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF][\uFE0F\u200D\U0001F000-\U0001FAFF\u2600-\u27BF]*)')
def emo_h1(body):
    # emoji din <h1> primesc span.em ca să nu fie colorate de gradient (altfel apar ca pătrate)
    return re.sub(r'(<h1[^>]*>)(.*?)(</h1>)', lambda m: m.group(1) + EMO.sub(r'<span class="em">\1</span>', m.group(2)) + m.group(3), body, flags=re.S)

# PWA: manifest + service worker (sw.js), căi absolute sub /vexu-hq/
PWA_HEAD = ('<link rel="manifest" href="/vexu-hq/manifest.webmanifest"><meta name="theme-color" content="#07040f">'
            '<link rel="apple-touch-icon" href="/vexu-hq/icon-192.png"><meta name="apple-mobile-web-app-capable" content="yes">'
            '<meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="VEXU HQ">')
PWA_JS = "<script>if('serviceWorker' in navigator)addEventListener('load',()=>navigator.serviceWorker.register('/vexu-hq/sw.js',{scope:'/vexu-hq/'}).catch(()=>{}))</script>"

CSS_TOP = '.totop{position:fixed;right:14px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:20;width:46px;height:46px;border-radius:50%;border:1px solid #ff7a00;background:#1a0b05e6;color:#ffb066;font-size:20px;line-height:44px;text-align:center;cursor:pointer;box-shadow:0 0 16px #ff7a0066,inset 0 0 10px #ff7a0033;opacity:0;transform:translateY(20px) scale(.8);pointer-events:none;transition:opacity .25s,transform .25s}.totop.on{opacity:1;transform:none;pointer-events:auto;animation:tg 2.6s ease-in-out infinite}.totop:active{transform:scale(.9)}@keyframes tg{50%{box-shadow:0 0 26px #ff7a00aa,0 0 40px #ff2bd644,inset 0 0 10px #ff7a0033}}.spd{position:fixed;top:0;left:18px;z-index:0;pointer-events:none;width:2px;height:70px;background:linear-gradient(#fff0,#ffffff55);transform-origin:top center;animation:sw 5s ease-in-out infinite,dr 9s ease-in-out infinite}.spd:after{content:"🕷️";position:absolute;bottom:-18px;left:-10px;font-size:20px;filter:drop-shadow(0 0 6px #ff2bd6)}@keyframes sw{0%,100%{transform:rotate(6deg)}50%{transform:rotate(-6deg)}}@keyframes dr{0%,100%{height:60px}50%{height:120px}}.fog{position:fixed;left:0;right:0;bottom:0;height:32vh;max-height:260px;z-index:0;pointer-events:none;overflow:hidden;opacity:.9;-webkit-mask-image:linear-gradient(transparent,#000 75%);mask-image:linear-gradient(transparent,#000 75%)}.fog i{position:absolute;left:0;bottom:-10%;width:200%;height:110%;background-repeat:repeat-x;background-size:50% 100%;background-image:radial-gradient(ellipse 30% 55% at 18% 80%,#c8b4ff40,transparent 70%),radial-gradient(ellipse 34% 45% at 58% 90%,#ffffff2b,transparent 70%),radial-gradient(ellipse 26% 50% at 88% 78%,#c8b4ff38,transparent 70%);animation:fgx 46s linear infinite;will-change:transform}.fog i+i{bottom:-25%;opacity:.8;background-image:radial-gradient(ellipse 32% 50% at 30% 85%,#ff7a002e,transparent 70%),radial-gradient(ellipse 28% 45% at 75% 92%,#ff2bd626,transparent 70%);animation-duration:70s;animation-direction:reverse}@keyframes fgx{to{transform:translateX(-50%)}}@media(max-width:600px){.fog{height:24vh}.spd{left:8px;animation:sw 5s ease-in-out infinite,drm 9s ease-in-out infinite}.spd:after{font-size:17px;bottom:-15px;left:-8px}}@keyframes drm{0%,100%{height:12px}50%{height:30px}}@media(prefers-reduced-motion:reduce){.totop.on{animation:none}.spd{animation:none}.fog i{animation:none}}'
TOP_HTML = '<div class="fog" aria-hidden="true"><i></i><i></i></div><div class="spd" aria-hidden="true"></div><button class="totop" id="totop" type="button" aria-label="Înapoi sus" title="Înapoi sus">🎃</button>'
# Vânătoarea de dovleci (Halloween 2026): oprire din pumpkin-hunt.js (ON / END) sau golește HUNT_JS.
HUNT_JS = '<script src="/vexu-hq/pumpkin-hunt.js" defer></script>'
TOP_JS = "<script>(function(){var b=document.getElementById('totop');if(!b)return;function u(){b.classList.toggle('on',scrollY>600)}addEventListener('scroll',u,{passive:true});u();b.onclick=function(){scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'})}})()</script>"
def page(title, body, extra_js=''):
    body = emo_h1(body)
    return (f'<!doctype html><html lang="ro"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)}</title><link rel="icon" type="image/png" href="/vexu-hq/icon.png">{PWA_HEAD}<style>\n{CSS}\n{CSS_FX}{CSS_TOP}\n</style></head><body>'
            f'<div class="moon" aria-hidden="true"></div>'
            f'<div class="fx" aria-hidden="true"><span>🎃</span><span>🦇</span><span>👻</span><span>🦇</span><span>🎃</span><span>🕸️</span></div>'
            f'<div class="w">{body}</div>{TOP_HTML}{extra_js}{TOP_JS}{HUNT_JS}{PWA_JS}</body></html>\n')

e = html.escape
def cls(l): return re.sub(r'[^A-Za-z0-9]+', '-', l).strip('-')
def chips(p):
    return ' '.join(f'<span class="l {cls(l)}">{e(l)}</span>' for l in labels_of(p))
URL = re.compile(r'https?://[^\s()<>]+[^\s()<>.,;:!?]')
def link(t): return URL.sub(lambda m: f'<a href="{m.group(0)}" target="_blank" rel="noopener">{m.group(0)}</a>', e(t))
def rich(t):
    out, ul = [], False
    for ln in t.split('\n'):
        if ln.startswith('- '):
            if not ul: out.append('<ul>'); ul = True
            out.append(f'<li>{link(ln[2:])}</li>')
        else:
            if ul: out.append('</ul>'); ul = False
            out.append(f'<p style="margin:6px 0">{link(ln)}</p>')
    if ul: out.append('</ul>')
    return ''.join(out)

NAV_BLOG = ('<nav><a href="index.html">⚡ Dashboard</a><a href="blog.html">📰 Blog</a>'
            '<a href="calendar.html">📅 Calendar Halloween</a><a href="recap.html">📊 Rezumatul săptămânii</a></nav>')
NAV_POST = ('<nav><a href="../blog.html">← Blog</a><a href="../calendar.html">📅 Calendar</a>'
            '<a href="../recap.html">📊 Rezumat</a><a href="../index.html">⚡ Dashboard</a></nav>')

NAV_JOC = ('<nav><a href="../blog.html">← Blog</a><a href="../calendar.html">📅 Calendar</a>'
           '<a href="../recap.html">📊 Rezumat</a><a href="../index.html">⚡ Dashboard</a></nav>')
CTA = ('<div class="cta"><b>Follow = Au ce bile! 💥</b>'
       '<a href="https://www.tiktok.com/@vexu_online" target="_blank" rel="noopener">🎵 TikTok @vexu_online</a>'
       '<a class="yt" href="https://www.youtube.com/@VexuOnline" target="_blank" rel="noopener">▶️ YouTube VEXU Online</a></div>')

BLOG_JS = r"""
<script>
const TZ='Europe/Bucharest', PAGE=12;
const es=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const cls=l=>l.replace(/[^A-Za-z0-9]+/g,'-');
const fid=l=>l.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
const norm=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
function dayKey(iso){
  const d=new Date(iso.includes('T')?iso:iso+'T12:00:00+03:00');
  return new Intl.DateTimeFormat('en-CA',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit'}).format(d); // YYYY-MM-DD
}
function todayKey(){return new Intl.DateTimeFormat('en-CA',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date())}
function yesterdayKey(){const t=new Date(); const p=new Intl.DateTimeFormat('en-CA',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(t).reduce((a,x)=>(a[x.type]=x.value,a),{});
  const utc=Date.UTC(+p.year,+p.month-1,+p.day)-864e5; return new Intl.DateTimeFormat('en-CA',{timeZone:'UTC',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(utc));}
function dayLabel(key){
  const t=todayKey(), y=yesterdayKey();
  if(key===t) return 'Azi';
  if(key===y) return 'Ieri';
  const [Y,M,D]=key.split('-').map(Number);
  return new Intl.DateTimeFormat('ro-RO',{timeZone:'UTC',weekday:'long',day:'numeric',month:'long'}).format(new Date(Date.UTC(Y,M-1,D,12)));
}
// hash: #f=<eticheta>&g=<joc>&q=<căutare>
function parseHash(){const h=(location.hash||'').replace(/^#/,''); const o={f:'toate',g:'toate',q:''};
  h.split('&').forEach(kv=>{const i=kv.indexOf('='); if(i<0)return; const k=kv.slice(0,i); let v=kv.slice(i+1); try{v=decodeURIComponent(v.replace(/\+/g,' '))}catch(e){}
    if(k==='f'&&/^[\w-]+$/.test(v)) o.f=v; if(k==='g'&&/^[\w-]+$/.test(v)) o.g=v; if(k==='q') o.q=v;}); return o}
function setHash(){const parts=[]; if(filter!=='toate') parts.push('f='+filter); if(game!=='toate') parts.push('g='+game); if(q.trim()) parts.push('q='+encodeURIComponent(q.trim()));
  const h=parts.length?'#'+parts.join('&'):''; if((location.hash||'')!==h) history.replaceState(null,'',h||location.pathname+location.search)}
let ALL=[], FILTERS=[{id:'toate',label:'Toate'}], GAMES=[{id:'toate',label:'Toate'}], shown=0, filter='toate', game='toate', q='', SEARCH=null, sLoading=false;
// lista de etichete derivată din date (posts-index.json ← posts.json), ordonată după numărul de postări
function buildFilters(){const m=new Map(); ALL.forEach(p=>(p.labels||[]).forEach(l=>{const id=fid(l); if(!id)return; const x=m.get(id)||{id,label:l,n:0}; x.n++; m.set(id,x)}));
  FILTERS=[{id:'toate',label:'Toate'}].concat([...m.values()].sort((a,b)=>b.n-a.n||a.label.localeCompare(b.label,'ro')))}
// jocuri (câmpul joc din posts.json), ordonate după numărul de postări
function buildGames(){const m=new Map(); ALL.forEach(p=>{if(!p.joc||!p.jocSlug)return; const x=m.get(p.jocSlug)||{id:p.jocSlug,label:p.joc,n:0}; x.n++; m.set(p.jocSlug,x)});
  GAMES=[{id:'toate',label:'Toate'}].concat([...m.values()].sort((a,b)=>b.n-a.n||a.label.localeCompare(b.label,'ro')))}
function validFilter(){if(!FILTERS.some(f=>f.id===filter)) filter='toate'; if(!GAMES.some(g=>g.id===game)) game='toate'}
function gmatch(p,g){return g==='toate'||p.jocSlug===g}
function terms(){return norm(q).split(/\s+/).filter(Boolean)}
function hay(p){if(p._h===undefined||(SEARCH&&!p._full)){p._full=!!SEARCH; p._h=norm(p.title+' '+(p.excerpt||'')+' '+(p.labels||[]).join(' ')+' '+(p.joc||'')+' '+((SEARCH&&SEARCH[p.slug])||''))} return p._h}
function qmatch(p,t){return !t.length||t.every(w=>hay(p).includes(w))}
function fmatch(p,f){return f==='toate'||(p.labels||[]).some(l=>fid(l)===f)}
function loadSearch(){if(SEARCH||sLoading)return; sLoading=true;
  fetch('posts-search.json?'+Date.now()).then(r=>r.json()).then(d=>{SEARCH=d; if(q.trim()) paint()}).catch(()=>{sLoading=false})}
function chipsHtml(labels,date){return labels.map(l=>`<span class="l ${cls(l)}">${es(l)}</span>`).join(' ')+`<span class="dt">📅 ${es(date)}</span>`}
function cardHtml(p, feat){
  return `<a class="p${feat?' feat':''}" href="posts/${es(p.slug)}.html"><img src="${es(p.img)}" alt="" loading="lazy"><div class="b">${chipsHtml(p.labels,p.dateRo)}<h2>${es(p.title)}</h2><div>${es(p.excerpt)}</div>${p.joc?`<span class="jg">🎮 ${es(p.joc)}</span>`:''}<div class="more">Citește tot →</div></div></a>`;
}
function renderFilters(t){
  const base=ALL.filter(p=>qmatch(p,t));
  document.getElementById('filters').innerHTML=FILTERS.map(f=>`<button type="button" class="chip${filter===f.id?' on':''}" data-f="${es(f.id)}" aria-pressed="${filter===f.id}">${es(f.label)}<span class="n">(${base.filter(p=>gmatch(p,game)&&fmatch(p,f.id)).length})</span></button>`).join('');
  document.querySelectorAll('#filters .chip').forEach(b=>b.onclick=()=>{filter=b.dataset.f; setHash(); shown=0; paint()});
  const gb=base.filter(p=>fmatch(p,filter));
  const gf=document.getElementById('gfilters');
  gf.innerHTML=GAMES.map(g=>`<button type="button" class="chip${game===g.id?' on':''}" data-g="${es(g.id)}" aria-pressed="${game===g.id}">${g.id==='toate'?'🎮 ':''}${es(g.label)}<span class="n">(${gb.filter(p=>gmatch(p,g.id)).length})</span></button>`).join('');
  gf.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{game=b.dataset.g; setHash(); shown=0; paint()});
  const on=gf.querySelector('.chip.on'); if(on&&game!=='toate'&&gf.scrollWidth>gf.clientWidth) gf.scrollLeft=on.offsetLeft-gf.clientWidth/2+on.offsetWidth/2;
  const cur=GAMES.find(g=>g.id===game);
  document.getElementById('gpage').innerHTML=game!=='toate'&&cur?`<a href="joc/${es(cur.id)}.html">🎮 Pagina jocului ${es(cur.label)} →</a>`:'';
}
function paint(){
  const t=terms();
  renderFilters(t);
  const ok=p=>fmatch(p,filter)&&gmatch(p,game)&&qmatch(p,t);
  // un singur post evidențiat sus; celelalte marcate featured rămân în feed (cronologic), nu dispar
  const feat=ALL.find(p=>p.featured && ok(p));
  const rest=ALL.filter(p=>p!==feat && ok(p)).sort((a,b)=>(Date.parse(b.published)||0)-(Date.parse(a.published)||0));
  document.getElementById('featSlot').innerHTML=feat?cardHtml(feat,true):'';
  const slice=rest.slice(0, Math.max(shown, PAGE));
  shown=slice.length;
  let html='', last='', open=false;
  for(const p of slice){
    const k=dayKey(p.published||p.date);
    if(k!==last){ if(open) html+='</div>'; html+=`<h2 class="dayh">${es(dayLabel(k))}</h2><div class="grid">`; open=true; last=k; }
    html+=cardHtml(p,false);
  }
  if(open) html+='</div>';
  if(!feat && !slice.length) html=t.length?`<div class="empty">Nicio știre găsită pentru „${es(q.trim())}”${filter!=='toate'?' pe filtrele astea':''}.</div>`:'<div class="empty">Nicio postare pe filtrele astea.</div>';
  document.getElementById('feed').innerHTML=html;
  const n=rest.length+(feat?1:0);
  document.getElementById('qinfo').textContent=t.length?(n===1?'1 rezultat':`${n} rezultate`)+(SEARCH?'':' (se încarcă textul complet…)'):'';
  document.getElementById('qx').style.visibility=q?'visible':'hidden';
  const more=document.getElementById('moreBtn');
  const left=rest.length-shown;
  more.style.display=left>0?'inline-block':'none';
  more.textContent=left>0?`Vezi mai multe (${left})`:'';
}
const qi=document.getElementById('q');
qi.addEventListener('focus',loadSearch);
qi.addEventListener('input',()=>{q=qi.value; loadSearch(); shown=0; setHash(); if(ALL.length) paint()});
qi.addEventListener('keydown',e=>{if(e.key==='Escape'){qi.value=q=''; setHash(); shown=0; paint()}});
document.getElementById('qform').onsubmit=e=>{e.preventDefault(); qi.blur()};
document.getElementById('qx').onclick=()=>{qi.value=q=''; setHash(); shown=0; paint(); qi.focus()};
document.getElementById('moreBtn').onclick=()=>{shown+=PAGE; paint()};
document.getElementById('shortsBtn').onclick=()=>{filter=FILTERS.some(f=>f.id==='trend-shorts')?'trend-shorts':'toate'; setHash(); shown=0; paint(); document.getElementById('filters').scrollIntoView({behavior:'smooth'})};
({f:filter,g:game,q}=parseHash()); qi.value=q; if(q) loadSearch();
fetch('posts-index.json?'+Date.now()).then(r=>r.json()).then(data=>{
  ALL=data.posts||data; buildFilters(); buildGames(); validFilter(); paint();
}).catch(err=>{document.getElementById('feed').innerHTML='<div class="empty">Nu pot încărca indexul.</div>'});
window.addEventListener('hashchange',()=>{({f:filter,g:game,q}=parseHash()); qi.value=q; if(q) loadSearch(); validFilter(); shown=0; paint()});
</script>
"""

CAL_JS = r"""
<script>
const TZ='Europe/Bucharest';
const es=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function cdHtml(ms){let s=Math.max(0,Math.floor(ms/1000));return [[Math.floor(s/86400),'zile'],[Math.floor(s%86400/3600),'ore'],[Math.floor(s%3600/60),'min'],[s%60,'sec']].map(([v,l])=>`<div><b>${String(v).padStart(2,'0')}</b><span>${l}</span></div>`).join('')}
function fmt(iso, o){ if(!iso) return ''; const d=new Date(iso); return new Intl.DateTimeFormat('ro-RO',Object.assign({timeZone:TZ},o)).format(d)}
function relevant(ev, now){
  if(ev.coming_soon) return new Date('2099-01-01');
  if(ev.announced && ev.start) return now;
  if(ev.start){ const s=new Date(ev.start); if(ev.end){ const e=new Date(ev.end); if(now<e) return s>now?s:e; return e;} return s; }
  if(ev.end && ev.end_only) return new Date(ev.end);
  if(ev.start_date){ const s=new Date(ev.start_date+'T12:00:00+03:00'); if(ev.end_date){ const e=new Date(ev.end_date+'T23:59:59+02:00'); return now<e? (now<s?s:e): e;} return s; }
  if(ev.end_date) return new Date(ev.end_date+'T12:00:00+02:00');
  return new Date('2099-01-01');
}
function status(ev, now){
  if(ev.coming_soon) return {kind:'soon', text:'Coming Soon — dată neanunțată', target:null};
  if(ev.announced && ev.start) return {kind:'live', text:'Anunțat oficial pe '+fmt(ev.start,{weekday:'long',day:'numeric',month:'long'})+' — disponibil acum', target:null};
  if(ev.date_only && ev.start_date){
    const day=ev.start_date;
    const today=new Intl.DateTimeFormat('en-CA',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
    if(today<day) return {kind:'soon', text:'Începe pe '+fmt(day+'T12:00:00+03:00',{weekday:'long',day:'numeric',month:'long'})+' (doar data confirmată)'};
    if(today===day) return {kind:'live', text:'LIVE azi (oră neconfirmată)'};
    return {kind:'done', text:'Terminat / trecut'};
  }
  if(ev.end_only && ev.end){
    const e=new Date(ev.end);
    if(now<e) return {kind:'soon', text:'Se termină în…', target:e};
    return {kind:'done', text:'Terminat'};
  }
  if(ev.no_end && ev.start_date){
    const s=new Date(ev.start_date+'T12:00:00+03:00');
    if(now<s) return {kind:'soon', text:'Începe în…', target:s};
    return {kind:'live', text:'LIVE — '+ (ev.end_note||'fără dată de final anunțată'), target:null};
  }
  if(ev.start_date && ev.end_date && !ev.start){
    const s=new Date(ev.start_date+'T00:00:00+03:00');
    const e=new Date(ev.end_date+'T23:59:59+02:00');
    if(now<s) return {kind:'soon', text:'Începe în…', target:s};
    if(now<=e) return {kind:'live', text:'LIVE — se termină în…', target:e};
    return {kind:'done', text:'Terminat'};
  }
  const s=ev.start?new Date(ev.start):null;
  const e=ev.end?new Date(ev.end):null;
  if(s && now<s) return {kind:'soon', text:'Începe în…', target:s};
  if(s && (!e || now<e)) {
    if(ev.end_time_unknown && ev.end_date){
      return {kind:'live', text:'LIVE — final anunțat: '+fmt(ev.end_date+'T12:00:00+02:00',{day:'numeric',month:'long'}), target:null};
    }
    if(e) return {kind:'live', text:'LIVE — se termină în…', target:e};
    return {kind:'live', text:'LIVE', target:null};
  }
  if(ev.end_time_unknown && ev.end_date && s && now>=s){
    const endD=ev.end_date;
    const today=new Intl.DateTimeFormat('en-CA',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
    if(today<=endD) return {kind:'live', text:'LIVE — final: '+fmt(endD+'T12:00:00+02:00',{day:'numeric',month:'long'})+' (oră neanunțată)', target:null};
  }
  return {kind:'done', text:'Terminat'};
}
function windowText(ev){
  if(ev.coming_soon) return 'Dată: Coming Soon (neanunțată oficial)';
  if(ev.announced && ev.start) return 'Anunț oficial: '+fmt(ev.start,{weekday:'short',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'});
  const bits=[];
  if(ev.start) bits.push('Start: '+fmt(ev.start,{weekday:'short',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'}));
  else if(ev.start_date) bits.push('Start: '+fmt(ev.start_date+'T12:00:00+03:00',{weekday:'short',day:'numeric',month:'short'})+(ev.date_only?' (doar data)':''));
  if(ev.end) bits.push('Final: '+fmt(ev.end,{weekday:'short',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'}));
  else if(ev.end_date) bits.push('Final: '+fmt(ev.end_date+'T12:00:00+02:00',{weekday:'short',day:'numeric',month:'short'})+(ev.end_time_unknown?' (oră neanunțată)':''));
  else if(ev.no_end) bits.push(ev.end_note||'fără dată de final anunțată');
  if(ev.end_only && ev.end) return 'Se termină: '+fmt(ev.end,{weekday:'short',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'});
  return bits.join(' · ');
}
let EVENTS=[];
function paint(){
  const now=new Date();
  const sorted=[...EVENTS].sort((a,b)=>relevant(a,now)-relevant(b,now));
  document.getElementById('cal').innerHTML=sorted.map(ev=>{
    const st=status(ev,now);
    const cd=st.target?`<div class="cd">${cdHtml(st.target-now)}</div>`:'';
    const note=ev.zvon_note?`<div class="note">⚠️ ${es(ev.zvon_note)}</div>`:'';
    return `<div class="row"><img class="ico" src="${es(ev.img)}" alt="" loading="lazy"><div class="card">
      <div><span class="l CONFIRMAT">CONFIRMAT</span> <b>${es(ev.game||'')}</b> — ${es(ev.name)}</div>
      <div class="st ${st.kind==='live'?'live':st.kind==='done'?'done':''}">${es(st.text)}</div>
      ${cd}
      <div class="meta">${es(windowText(ev))}</div>
      ${note}
      <div style="margin-top:8px">${ev.slug?`<a class="golink" href="posts/${es(ev.slug)}.html">Vezi postarea →</a>`:ev.link?`<a class="golink" href="${es(ev.link)}" target="_blank" rel="noopener">Pagina oficială a eventului →</a>`:''}</div>
    </div></div>`;
  }).join('');
}
fetch('calendar-events.json?'+Date.now()).then(r=>r.json()).then(d=>{EVENTS=d.events||d; paint(); setInterval(paint,1000)}).catch(()=>{document.getElementById('cal').innerHTML='<div class="empty">Nu pot încărca calendarul.</div>'});
</script>
"""

POST_JS = r"""<script>(()=>{const b=document.querySelector('.rp');if(b){let r=0;const u=()=>{r=0;const h=document.documentElement,m=h.scrollHeight-innerHeight;b.style.transform='scaleX('+(m>0?Math.min(1,scrollY/m):1)+')'};addEventListener('scroll',()=>{if(!r){r=1;requestAnimationFrame(u)}},{passive:true});addEventListener('resize',u);u()}
const s=document.getElementById('shr');if(s)s.onclick=async()=>{const d={title:document.title,url:location.href.split('#')[0]};try{if(navigator.share){await navigator.share(d);return}await navigator.clipboard.writeText(d.url);s.textContent='✅ Link copiat!';s.classList.add('ok');setTimeout(()=>{s.textContent='🔗 Distribuie';s.classList.remove('ok')},2200)}catch(e){}}})()</script>"""

def related(posts, i, n=3):
    """Postări apropiate în timp care au o etichetă comună (stabil între build-uri); completează cu cele mai apropiate în timp."""
    p = posts[i]; me = set(labels_of(p)); t = pub_key(p)
    def dist(j):
        a, b = sorted([t, pub_key(posts[j])])
        try:
            return abs((datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds())
        except Exception:
            return 1e12
    others = [j for j in range(len(posts)) if j != i and (posts[j].get('slug') or slug(posts[j]['titlu'])) != (p.get('slug') or slug(p['titlu']))]
    same = sorted([j for j in others if me & set(labels_of(posts[j]))], key=dist)
    rest = sorted([j for j in others if j not in same], key=dist)
    return (same + rest)[:n]

def related_html(posts, i):
    cards = ''
    for j in related(posts, i):
        q = posts[j]; qs = q.get('slug') or slug(q['titlu'])
        cards += (f'<a class="p" href="{e(qs)}.html"><img src="../{e(q["img"])}" alt="" loading="lazy"><div class="b">{chips(q)}'
                  f'<span class="dt">📅 {ro_date(q["date"])}</span><h3>{e(q["titlu"])}</h3></div></a>')
    return f'<section class="rel"><h2>👀 Mai citește</h2><div class="grid">{cards}</div></section>' if cards else ''

def build_post_pages(posts):
    os.makedirs(os.path.join(D, 'posts'), exist_ok=True)
    index_items = []
    cal_events = []
    search = {}
    order = sorted(range(len(posts)), key=lambda i: (bool(posts[i].get('featured')), pub_key(posts[i]), -i), reverse=True)
    for i in order:
        p = posts[i]
        s = p.get('slug') or slug(p['titlu'])
        lab = f'{chips(p)}<span class="dt">📅 {ro_date(p["date"])}</span>'
        src = ''.join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(u)}</a>' for u in p.get('surse', []))
        def sl(us):
            return '<div class="s">Sursă:' + ''.join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(u)}</a>' for u in us) + '</div>'
        if 'confirmat' in p or 'zvon' in p:
            txt = rich(p['text']) if p.get('text') else ''
            if 'confirmat' in p:
                txt += f'<div class="bx bxC"><h3>✅ CONFIRMAT</h3><div>{link(p["confirmat"])}</div>{sl(p.get("confirmat_surse", []))}</div>'
            if 'zvon' in p:
                txt += '<div class="bx bxZ"><h3>⚠️ ZVON</h3><ul>' + ''.join(f'<li>{link(z)}</li>' for z in p['zvon']) + f'</ul>{sl(p.get("zvon_surse", []))}</div>'
        else:
            txt = rich(p['text'])
        for o in p.get('old_slugs', []):
            open(os.path.join(D, 'posts', o + '.html'), 'w', encoding='utf-8').write(
                f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={s}.html">'
                f'<link rel="canonical" href="{s}.html"><a href="{s}.html">Mutat aici →</a>\n')
        body = (NAV_POST +
                f'<div class="p hero"><div class="hi"><img src="../{e(p["img"])}" alt=""></div><div class="b">{lab}'
                + (f'<a class="jl" href="../joc/{e(joc_slug(joc_of(p)))}.html">🎮 {e(joc_of(p))}</a>' if joc_of(p) else '') +
                f'<h1 style="text-align:left;font-size:1.6em">{e(p["titlu"])}</h1>'
                f'<div class="txt">{txt}</div><div class="s">Surse:{src}</div></div></div>'
                f'<div class="acts"><a class="btn" href="../blog.html">← Înapoi la blog</a>'
                f'<button type="button" class="btn shr" id="shr">🔗 Distribuie</button></div>'
                + related_html(posts, i))
        body = '<div class="rp" aria-hidden="true"></div>' + body
        open(os.path.join(D, 'posts', s + '.html'), 'w', encoding='utf-8').write(page(p['titlu'] + ' · VEXU HQ', body, POST_JS))
        print('posts/' + s + '.html')
        item = {
            'slug': s,
            'title': p['titlu'],
            'labels': labels_of(p),
            'date': p['date'],
            'dateRo': ro_date(p['date']),
            'published': pub_key(p),
            'img': p['img'],
            'excerpt': excerpt_of(p),
            'featured': bool(p.get('featured')),
            'section': p.get('section'),
            'joc': joc_of(p) or None,
            'jocSlug': joc_slug(joc_of(p)) if joc_of(p) else None,
        }
        index_items.append(item)
        search[s] = search_text(p)
        for ev in p.get('events', []):
            ce = dict(ev)
            ce['slug'] = s
            ce['img'] = p['img']
            ce['post_title'] = p['titlu']
            cal_events.append(ce)
    # evenimente fără postare (calendar-extra.json); se sar automat când o postare are events[] cu același joc+nume sau același link (în surse/events)
    xp = os.path.join(D, 'calendar-extra.json')
    if os.path.exists(xp):
        ex = json.load(open(xp, encoding='utf-8'))
        ex = ex.get('events', []) if isinstance(ex, dict) else ex
        links = {u for p in posts if p.get('events') for u in p.get('surse', [])} | {ev.get('link') for ev in cal_events if ev.get('link')}
        keys = {((ev.get('game') or '').lower(), (ev.get('name') or '').lower()) for ev in cal_events}
        for ev in ex:
            if ev.get('link') in links or ((ev.get('game') or '').lower(), (ev.get('name') or '').lower()) in keys:
                print('calendar-extra: sărit (există deja într-o postare):', ev.get('game'), ev.get('name'))
                continue
            ce = dict(ev); ce.setdefault('img', 'generic-neon.png'); ce['standalone'] = True
            cal_events.append(ce)
    feat = [x for x in index_items if x['featured']]
    rest = sorted([x for x in index_items if not x['featured']], key=lambda x: x['published'], reverse=True)
    index_items = feat + rest

    open(os.path.join(D, 'posts-index.json'), 'w', encoding='utf-8').write(
        json.dumps({'generated': now_ro().isoformat(timespec='seconds'), 'posts': index_items}, ensure_ascii=False, indent=1) + '\n')
    open(os.path.join(D, 'posts-search.json'), 'w', encoding='utf-8').write(
        json.dumps(search, ensure_ascii=False, separators=(',', ':')) + '\n')
    open(os.path.join(D, 'calendar-events.json'), 'w', encoding='utf-8').write(
        json.dumps({'generated': now_ro().isoformat(timespec='seconds'), 'events': cal_events}, ensure_ascii=False, indent=1) + '\n')
    return index_items

def build_game_pages(posts):
    """joc/<slug>.html: toate postările unui joc, cele mai noi primele. Doar jocuri cu ≥1 postare; paginile rămase fără postări se șterg."""
    jd = os.path.join(D, 'joc')
    os.makedirs(jd, exist_ok=True)
    groups = {}
    for p in posts:
        j = joc_of(p)
        if j:
            groups.setdefault(joc_slug(j), (j, []))[1].append(p)
    made = set()
    for js, (j, ps) in sorted(groups.items()):
        ps = sorted(ps, key=pub_key, reverse=True)
        cards = ''
        for q in ps:
            qs = q.get('slug') or slug(q['titlu'])
            cards += (f'<a class="p" href="../posts/{e(qs)}.html"><img src="../{e(q["img"])}" alt="" loading="lazy"><div class="b">{chips(q)}'
                      f'<span class="dt">📅 {ro_date(q["date"])}</span><h2>{e(q["titlu"])}</h2><div>{e(excerpt_of(q))}</div>'
                      f'<div class="more">Citește tot →</div></div></a>')
        n = len(ps)
        body = (f'<h1>🎮 {e(j)}</h1>{NAV_JOC}'
                f'<p class="gcount">{n} {"postare" if n == 1 else "postări"} · cele mai noi primele · '
                f'<a href="../blog.html#g={e(js)}" style="color:#00f0ff">vezi în blog cu filtre</a></p>'
                f'<div class="grid">{cards}</div>{CTA}'
                f'<div style="text-align:center"><a class="btn" href="../blog.html">← Toate știrile</a></div>')
        open(os.path.join(jd, js + '.html'), 'w', encoding='utf-8').write(page(f'{j} · VEXU HQ', body))
        made.add(js + '.html')
    for f in os.listdir(jd):
        if f.endswith('.html') and f not in made:
            os.remove(os.path.join(jd, f))
    print(f'joc/: {len(made)} pagini de joc')
    return groups

def build_blog():
    noscript = '<noscript><p style="text-align:center;color:#9a8fb5">Activează JavaScript pentru feed-ul grupat pe zile. Postările individuale rămân în <code>posts/</code>.</p></noscript>'
    body = (f'<h1>📰 VEXU HQ · Știri</h1>{NAV_BLOG}'
            f'<div class="shorts-entry"><button type="button" id="shortsBtn">🔥 Ce merge în Shorts</button></div>'
            f'<form class="srch" id="qform" role="search"><input type="search" id="q" placeholder="Caută în știri…" aria-label="Caută în știri" autocomplete="off" enterkeyhint="search"><button type="button" id="qx" aria-label="Șterge căutarea">✕</button></form>'
            f'<div class="qinfo" id="qinfo" aria-live="polite"></div>'
            f'<div class="filters" id="filters"></div>'
            f'<div class="ftitle">Jocuri</div><div class="filters" id="gfilters" role="toolbar" aria-label="Filtru după joc"></div>'
            f'<div class="gpage" id="gpage"></div>'
            f'<div id="featSlot"></div><div id="feed"></div>'
            f'<div id="moreWrap"><button type="button" class="btn" id="moreBtn" style="display:none">Vezi mai multe</button></div>'
            f'{noscript}{CTA}')
    open(os.path.join(D, 'blog.html'), 'w', encoding='utf-8').write(page('VEXU HQ · Știri', body, BLOG_JS))

def build_calendar():
    body = (f'<h1>📅 Calendar Halloween</h1>{NAV_BLOG}'
            f'<p style="text-align:center;color:#9a8fb5">Doar ferestre CONFIRMAT din blog · ora României · countdown live</p>'
            f'<div class="cal" id="cal">Se încarcă…</div>')
    open(os.path.join(D, 'calendar.html'), 'w', encoding='utf-8').write(page('Calendar Halloween · VEXU HQ', body, CAL_JS))

# ───────────── Rezumatul săptămânii (recap.html) ─────────────
# Generat la build din posts.json (știrile din ultimele 7 zile, ora României), iar în browser se recalculează
# din posts-index.json + player-history.json + data.json (ultimele date scrise de GitHub Action), deci e mereu la zi.
# Doar date reale: zilele fără măsurători apar „fără date”, nimic nu se completează.
RECAP_DAYS = 7
RECAP_MAX_CONF = 10
RECAP_MAX_OTHER = 6

def recap_skip(p):
    """Fără conținut Steal An Egg PART 2 în rezumat (regulă VEXU)."""
    if (p.get('jocSlug') or '') != 'steal-an-egg':
        return False
    blob = (p.get('title', '') + ' ' + p.get('slug', '') + ' ' + (p.get('excerpt') or '')).lower()
    return bool(re.search(r'part[\s-]*(2|ii)\b', blob))

def recap_pick(items, keys):
    wk = [x for x in items if x['published'][:10] and datetime.fromisoformat(x['published']).astimezone(TZ).date().isoformat() in keys and not recap_skip(x)]
    wk.sort(key=lambda x: x['published'], reverse=True)
    conf = [x for x in wk if 'CONFIRMAT' in x['labels']][:RECAP_MAX_CONF]
    other = [x for x in wk if 'CONFIRMAT' not in x['labels'] and 'ZVON' in x['labels']][:RECAP_MAX_OTHER]
    return wk, conf, other

def recap_row(x):
    lab = ' '.join(f'<span class="l {cls(l)}">{e(l)}</span>' for l in x['labels'])
    d = datetime.fromisoformat(x['published']).astimezone(TZ)
    return (f'<a class="rn" href="posts/{e(x["slug"])}.html">{lab}<b>{e(x["title"])}</b>'
            f'<i>{"🎮 " + e(x["joc"]) + " · " if x.get("joc") else ""}{d.day} {LUNI[d.month-1][:3]}, {d:%H:%M}</i></a>')

RECAP_CSS = ('.rc{background:#120a22cc;border:1px solid #ff2bd655;border-radius:16px;padding:14px;margin:14px 0;box-shadow:0 0 18px #ff2bd622}'
 '.rc h2{margin:0 0 10px;color:#ff7be6;font-size:1.15em}.rsub{text-align:center;color:#9a8fb5;font-size:.9em;margin:4px 0 10px}'
 '.rn{display:block;padding:10px 0;border-top:1px solid #ffffff12;color:inherit;text-decoration:none}.rn:first-of-type{border-top:0}.rn b{display:block;margin:5px 0 3px;line-height:1.35}'
 '.rn i{font-style:normal;color:#9a8fb5;font-size:.8em}.rn:hover b{color:#00f0ff}.rnum{display:flex;flex-wrap:wrap;gap:8px}.rnum div{flex:1 1 90px;background:#000a;border:1px solid #00f0ff55;border-radius:12px;padding:8px;text-align:center}'
 '.rnum b{display:block;font-size:1.4em;color:#00f0ff}.rnum span{font-size:.75em;color:#9a8fb5}#rchart svg{width:100%;height:auto;display:block}#rchart text{fill:#bdb3d6;font:12px system-ui,sans-serif}'
 '.rmeta{color:#9a8fb5;font-size:.82em;margin-top:8px;line-height:1.45}.rcard{display:flex;flex-direction:column;align-items:center;gap:10px}'
 '.rcard img{width:min(100%,300px);aspect-ratio:9/16;border-radius:14px;border:1px solid #ff2bd666;box-shadow:0 0 24px #ff2bd644;background:#07040f}'
 '.rcard .btn{margin:4px 0;font-weight:800}@media(min-width:900px){.rgrid{display:grid;grid-template-columns:1.2fr 1fr;gap:16px;align-items:start}.rgrid .rc{margin:0 0 16px}}')

RECAP_JS = r"""<script>
(()=>{const TZ='Europe/Bucharest',DAYS=7,MAXC=10,MAXO=6;
const es=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const cls=l=>l.replace(/[^A-Za-z0-9]+/g,'-');
const dk=d=>new Intl.DateTimeFormat('en-CA',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit'}).format(d);
const hm=d=>new Intl.DateTimeFormat('ro-RO',{timeZone:TZ,hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(d);
const nf=n=>new Intl.NumberFormat('ro-RO').format(n);
const cmp=n=>n>=1e6?(n/1e6).toFixed(2).replace('.',',')+'M':n>=1e4?Math.round(n/1e3)+'K':nf(n);
const LUN=['ian','feb','mar','apr','mai','iun','iul','aug','sep','oct','nov','dec'],LUNL=['ianuarie','februarie','martie','aprilie','mai','iunie','iulie','august','septembrie','octombrie','noiembrie','decembrie'];
const WD=['dum','lun','mar','mie','joi','vin','sâm'];
const kd=k=>{const[y,m,d]=k.split('-').map(Number);return{y,m,d,w:new Date(Date.UTC(y,m-1,d,12)).getUTCDay()}};
function keys(){const t=kd(dk(new Date()));const a=[];for(let i=DAYS-1;i>=0;i--)a.push(new Date(Date.UTC(t.y,t.m-1,t.d-i,12)).toISOString().slice(0,10));return a}
const skip=p=>p.jocSlug==='steal-an-egg'&&/part[\s-]*(2|ii)\b/i.test((p.title||'')+' '+(p.slug||'')+' '+(p.excerpt||''));
const plain=s=>String(s).replace(/[\p{Extended_Pictographic}\u{1F1E6}-\u{1F1FF}\uFE0F\u200D]/gu,'').replace(/\s+/g,' ').trim();
let K=keys(),WK=[],CONF=[],OTH=[],PH=null,DATA=null;
function rangeTxt(){const a=kd(K[0]),b=kd(K[K.length-1]);return a.m===b.m?`${a.d} – ${b.d} ${LUNL[b.m-1]} ${b.y}`:`${a.d} ${LUNL[a.m-1]} – ${b.d} ${LUNL[b.m-1]} ${b.y}`}
function row(p){const d=new Date(p.published);return `<a class="rn" href="posts/${es(p.slug)}.html">${(p.labels||[]).map(l=>`<span class="l ${cls(l)}">${es(l)}</span>`).join(' ')}<b>${es(p.title)}</b><i>${p.joc?'🎮 '+es(p.joc)+' · ':''}${kd(dk(d)).d} ${LUN[kd(dk(d)).m-1]}, ${hm(d)}</i></a>`}
function news(ix){K=keys();const ks=new Set(K);
  WK=(ix.posts||[]).filter(p=>p.published&&ks.has(dk(new Date(p.published)))&&!skip(p)).sort((a,b)=>new Date(b.published)-new Date(a.published));
  CONF=WK.filter(p=>(p.labels||[]).includes('CONFIRMAT')).slice(0,MAXC);OTH=WK.filter(p=>!(p.labels||[]).includes('CONFIRMAT')&&(p.labels||[]).includes('ZVON')).slice(0,MAXO);
  document.getElementById('rrange').textContent=rangeTxt();
  document.getElementById('rconf').innerHTML=CONF.length?CONF.map(row).join(''):'<div class="rmeta">Nicio știre CONFIRMAT în ultimele 7 zile.</div>';
  document.getElementById('roth').innerHTML=OTH.length?OTH.map(row).join(''):'<div class="rmeta">Niciun zvon în ultimele 7 zile.</div>';
  const c=l=>WK.filter(p=>(p.labels||[]).includes(l)).length;
  document.getElementById('rnum').innerHTML=[[WK.length,'postări'],[c('CONFIRMAT'),'CONFIRMAT'],[c('ZVON'),'ZVON'],[c('TREND SHORTS'),'TREND SHORTS'],[c('VEXU LIVE'),'VEXU LIVE']].map(([n,t])=>`<div><b>${n}</b><span>${t}</span></div>`).join('')}
function peaks(){const ds=(PH&&PH.days)||{};return K.map(k=>({k,v:ds[k]&&typeof ds[k].peak==='number'?ds[k]:null}))}
function manual(){const ks=new Set(K);return ((PH&&PH.manual)||[]).filter(m=>typeof m.p==='number'&&m.t&&ks.has(dk(new Date(m.t))))}
function chart(){const el=document.getElementById('rchart'),meta=document.getElementById('rcmeta');if(!PH){el.innerHTML='<div class="rmeta">Nu pot încărca istoricul de jucători acum.</div>';return}
  const P=peaks(),have=P.filter(x=>x.v);if(!have.length){el.innerHTML='<div class="rmeta">Încă nu avem măsurători în ultimele 7 zile.</div>';meta.textContent='';return}
  const W=700,H=270,L=10,R=10,T=34,B=46,bw=(W-L-R)/P.length,mx=Math.max(...have.map(x=>x.v.peak))*1.08;let g='';
  P.forEach((x,i)=>{const cx=L+bw*i+bw/2,w=bw*.62,d=kd(x.k),lab=x.k===K[K.length-1]?`azi (${d.d})`:`${WD[d.w]} ${d.d}`;
    if(x.v){const h=(H-T-B)*x.v.peak/mx,y=H-B-h;g+=`<rect x="${(cx-w/2).toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${h.toFixed(1)}" rx="8" fill="url(#rg)"/><text x="${cx}" y="${(y-8).toFixed(1)}" text-anchor="middle" style="fill:#fff;font-weight:700">${cmp(x.v.peak)}</text>`}
    else{g+=`<rect x="${(cx-w/2).toFixed(1)}" y="${T+40}" width="${w.toFixed(1)}" height="${H-B-T-40}" rx="8" fill="none" stroke="#ffffff33" stroke-dasharray="5 5"/><text x="${cx}" y="${(H-B-12)}" text-anchor="middle" style="fill:#9a8fb5;font-size:11px">fără date</text>`}
    g+=`<text x="${cx}" y="${H-B+20}" text-anchor="middle">${lab}</text><text x="${cx}" y="${H-B+36}" text-anchor="middle" style="fill:#7d7399;font-size:10px">${x.v?x.v.n+' măs.':''}</text>`});
  el.innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Steal An Egg: vârful zilnic de jucători în ultimele 7 zile"><defs><linearGradient id="rg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#00f0ff"/><stop offset="1" stop-color="#ff2bd6"/></linearGradient></defs>${g}</svg>`;
  const best=have.reduce((a,x)=>x.v.peak>a.v.peak?x:a),m=manual();let t=`⬆️ Cel mai mare vârf măsurat: ${nf(best.v.peak)} jucători (${WD[kd(best.k).w]} ${kd(best.k).d} ${LUN[kd(best.k).m-1]}, ${hm(new Date(best.v.t))}). `;
  t+=`Date din ${have.length} din ${P.length} zile`+(have.length<P.length?' (zilele fără măsurători apar „fără date”)':'')+'. ';
  m.forEach(x=>{t+=`📌 Citire manuală: ${nf(x.p)} pe ${kd(dk(new Date(x.t))).d} ${LUN[kd(dk(new Date(x.t))).m-1]}, ${hm(new Date(x.t))}${x.note?' ('+x.note+')':''}. `});
  if(DATA&&DATA.game&&typeof DATA.game.playing==='number')t+=`🟢 Ultima citire: ${nf(DATA.game.playing)} jucători (${hm(new Date(DATA.game.fetched||DATA.updated))}).`;
  meta.textContent=t}
// ── card 9:16 (1080×1920), desenat local în canvas ──
function rr(c,x,y,w,h,r){c.beginPath();c.moveTo(x+r,y);c.arcTo(x+w,y,x+w,y+h,r);c.arcTo(x+w,y+h,x,y+h,r);c.arcTo(x,y+h,x,y,r);c.arcTo(x,y,x+w,y,r);c.closePath()}
function wrap(c,t,maxW,maxL){const w=t.split(' '),out=[];let cur='';for(const x of w){const n=cur?cur+' '+x:x;if(c.measureText(n).width>maxW&&cur){out.push(cur);cur=x}else cur=n}if(cur)out.push(cur);if(out.length>maxL){out.length=maxL;let l=out[maxL-1];while(c.measureText(l+'…').width>maxW&&l.length)l=l.slice(0,-1);out[maxL-1]=l.replace(/\s+\S*$/,'')+'…'}return out}
const F='system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans",sans-serif';
function card(){const cv=document.createElement('canvas');cv.width=1080;cv.height=1920;const c=cv.getContext('2d');
  c.fillStyle='#07040f';c.fillRect(0,0,1080,1920);
  let g=c.createRadialGradient(200,0,0,200,0,1100);g.addColorStop(0,'#3b0a5c');g.addColorStop(1,'#3b0a5c00');c.fillStyle=g;c.fillRect(0,0,1080,1920);
  g=c.createRadialGradient(1080,1920,0,1080,1920,1100);g.addColorStop(0,'#002f3d');g.addColorStop(1,'#002f3d00');c.fillStyle=g;c.fillRect(0,0,1080,1920);
  g=c.createLinearGradient(0,1700,0,1920);g.addColorStop(0,'#ff7a0000');g.addColorStop(1,'#ff7a0022');c.fillStyle=g;c.fillRect(0,1700,1080,220);
  c.textAlign='center';c.textBaseline='alphabetic';
  g=c.createLinearGradient(240,0,840,0);g.addColorStop(0,'#ff2bd6');g.addColorStop(.5,'#00f0ff');g.addColorStop(1,'#ff7a00');
  c.font=`900 120px ${F}`;c.fillStyle=g;c.shadowColor='#ff2bd6';c.shadowBlur=30;c.fillText('VEXU HQ',540,180);c.shadowBlur=0;
  c.font=`800 64px ${F}`;c.fillStyle='#fff';c.fillText('REZUMATUL SĂPTĂMÂNII',540,280);
  c.font=`600 40px ${F}`;c.fillStyle='#9a8fb5';c.fillText('🎃 '+rangeTxt()+' 🎃',540,345);
  // top știri
  c.textAlign='left';c.font=`800 38px ${F}`;c.fillStyle='#39ff88';c.fillText('TOP ȘTIRI CONFIRMAT',70,412);
  let y=436;const top=CONF.slice(0,5),LIM=1228;
  if(!top.length){c.font=`600 36px ${F}`;c.fillStyle='#9a8fb5';c.fillText('Nicio știre CONFIRMAT săptămâna asta.',70,y+50)}
  for(let i=0;i<top.length;i++){const p=top[i];c.font=`700 32px ${F}`;const ls=wrap(c,plain(p.title),850,2),h=30+ls.length*40+(p.joc?34:0);
    if(y+h>LIM)break;
    rr(c,60,y,960,h,24);c.fillStyle='#120a22e6';c.fill();c.strokeStyle='#ff2bd666';c.lineWidth=3;c.stroke();
    c.fillStyle='#ff2bd6';c.font=`900 38px ${F}`;c.fillText(String(i+1),88,y+54);
    c.fillStyle='#fff';c.font=`700 32px ${F}`;ls.forEach((l,j)=>c.fillText(l,135,y+50+j*40));
    if(p.joc){c.font=`600 27px ${F}`;c.fillStyle='#ffb066';c.fillText(plain(p.joc),135,y+50+ls.length*40-2)}
    y+=h+10}
  // grafic Steal An Egg (doar zilele cu măsurători reale; restul „fără date”)
  const P=peaks(),have=P.filter(x=>x.v);y=1268;
  c.font=`800 36px ${F}`;c.fillStyle='#00f0ff';c.fillText('STEAL AN EGG · VÂRF ZILNIC DE JUCĂTORI',70,y);
  const top0=y+24,ch=230;rr(c,60,top0,960,ch+66,24);c.fillStyle='#000a';c.fill();c.strokeStyle='#00f0ff55';c.lineWidth=3;c.stroke();
  const base=top0+ch-6;
  if(have.length){const mx=Math.max(...have.map(x=>x.v.peak)),bw=900/P.length,bh=ch-70;
    const bg=c.createLinearGradient(0,base-bh,0,base);bg.addColorStop(0,'#00f0ff');bg.addColorStop(1,'#ff2bd6');
    P.forEach((x,i)=>{const cx=90+bw*i+bw/2,w=bw*.6,d=kd(x.k);c.textAlign='center';
      if(x.v){const h=Math.max(6,bh*x.v.peak/mx),by=base-h;rr(c,cx-w/2,by,w,h,10);c.fillStyle=bg;c.fill();c.fillStyle='#fff';c.font=`800 27px ${F}`;c.fillText(cmp(x.v.peak),cx,by-10)}
      else{c.setLineDash([8,8]);rr(c,cx-w/2,base-bh*.55,w,bh*.55,10);c.strokeStyle='#ffffff44';c.lineWidth=2;c.stroke();c.setLineDash([]);c.fillStyle='#9a8fb5';c.font=`600 21px ${F}`;c.fillText('fără',cx,base-bh*.55+36);c.fillText('date',cx,base-bh*.55+60)}
      c.fillStyle='#bdb3d6';c.font=`600 25px ${F}`;c.fillText(x.k===K[K.length-1]?'azi':`${WD[d.w]} ${d.d}`,cx,base+40)});c.textAlign='left'}
  else{c.textAlign='center';c.font=`600 32px ${F}`;c.fillStyle='#9a8fb5';c.fillText('Încă nu avem măsurători săptămâna asta.',540,top0+ch/2);c.textAlign='left'}
  c.font=`500 23px ${F}`;c.fillStyle='#7d7399';c.fillText('Vârful măsurat de VEXU HQ din API-ul Roblox (ora României).',70,top0+ch+104);
  // CTA
  c.textAlign='center';c.font=`900 58px ${F}`;c.fillStyle='#ff7be6';c.shadowColor='#ff2bd6';c.shadowBlur=24;c.fillText('Follow = Au ce bile! 💥',540,1700);c.shadowBlur=0;
  rr(c,90,1735,430,96,28);c.fillStyle='#000c';c.fill();c.strokeStyle='#00f0ff';c.lineWidth=4;c.stroke();
  rr(c,560,1735,430,96,28);c.fillStyle='#000c';c.fill();c.strokeStyle='#ff3b3b';c.stroke();
  c.font=`800 34px ${F}`;c.fillStyle='#00f0ff';c.fillText('TikTok @vexu_online',305,1796);c.fillStyle='#ff7070';c.fillText('YouTube VEXU Online',775,1796);
  c.font=`600 24px ${F}`;c.fillStyle='#9a8fb5';c.fillText('pyromanc3r777.github.io/vexu-hq',540,1885);
  return cv}
let URLC=null;
function paintCard(){const cv=card();cv.toBlob(b=>{if(!b)return;if(URLC)URL.revokeObjectURL(URLC);URLC=URL.createObjectURL(b);const im=document.getElementById('rcimg');im.src=URLC;
  const a=document.getElementById('rcdl');a.href=URLC;a.download=`vexu-rezumat-${K[K.length-1]}.png`;a.removeAttribute('aria-disabled')},'image/png')}
function all(){chart();paintCard()}
const j=u=>fetch(u+'?'+Date.now(),{cache:'no-store'}).then(r=>r.ok?r.json():null).catch(()=>null);
function load(){Promise.all([j('posts-index.json'),j('player-history.json'),j('data.json')]).then(([ix,ph,d])=>{if(ix)news(ix);PH=ph;DATA=d;all()})}
const go=()=>{load();setInterval(load,300000)};(document.fonts&&document.fonts.ready?document.fonts.ready:Promise.resolve()).then(go);
})();
</script>"""

def build_recap(index_items):
    now = now_ro()
    t = now.date()
    from datetime import timedelta
    keys = [(t - timedelta(days=i)).isoformat() for i in range(RECAP_DAYS - 1, -1, -1)]
    wk, conf, other = recap_pick(index_items, set(keys))
    a, b = date_from(keys[0]), date_from(keys[-1])
    rng = (f'{a.day} – {b.day} {LUNI[b.month-1]} {b.year}' if a.month == b.month
           else f'{a.day} {LUNI[a.month-1]} – {b.day} {LUNI[b.month-1]} {b.year}')
    cnt = lambda l: sum(1 for x in wk if l in x['labels'])
    nums = ''.join(f'<div><b>{n}</b><span>{l}</span></div>' for n, l in [(len(wk), 'postări'), (cnt('CONFIRMAT'), 'CONFIRMAT'), (cnt('ZVON'), 'ZVON'), (cnt('TREND SHORTS'), 'TREND SHORTS'), (cnt('VEXU LIVE'), 'VEXU LIVE')])
    body = (f'<h1>📊 Rezumatul săptămânii</h1>{NAV_BLOG}'
            f'<p class="rsub">Ultimele 7 zile · <span id="rrange">{rng}</span> · ora României · se actualizează singur</p>'
            f'<div class="rc"><h2>📈 Săptămâna în cifre</h2><div class="rnum" id="rnum">{nums}</div></div>'
            f'<div class="rgrid"><div>'
            f'<div class="rc"><h2>✅ Top știri CONFIRMAT</h2><div id="rconf">{"".join(recap_row(x) for x in conf) or "<div class=rmeta>Nicio știre CONFIRMAT în ultimele 7 zile.</div>"}</div></div>'
            f'<div class="rc"><h2>⚠️ Zvonuri de urmărit</h2><div id="roth">{"".join(recap_row(x) for x in other) or "<div class=rmeta>Niciun zvon în ultimele 7 zile.</div>"}</div></div>'
            f'</div><div>'
            f'<div class="rc"><h2>🥚 Steal An Egg · vârful zilnic de jucători</h2><div id="rchart"><div class="rmeta">Se încarcă graficul…</div></div>'
            f'<div class="rmeta" id="rcmeta"></div><div class="rmeta">📏 Măsurat de noi din API-ul Roblox (GitHub Action, de obicei la câteva ore). Vârful zilei e cel mai mare număr pe care l-am prins noi, nu neapărat vârful real. Momentan urmărim doar Steal An Egg.</div></div>'
            f'<div class="rc"><h2>📱 Card 9:16 pentru TikTok / Shorts</h2><div class="rcard"><img id="rcimg" alt="Previzualizare card 9:16 cu rezumatul săptămânii VEXU HQ" width="1080" height="1920">'
            f'<a class="btn" id="rcdl" href="#" aria-disabled="true">⬇️ Descarcă PNG (1080×1920)</a><div class="rmeta" style="text-align:center">Cardul se generează pe telefonul tău, din datele de mai sus.</div></div></div>'
            f'</div></div>'
            f'<div style="text-align:center"><a class="btn" href="blog.html">📰 Toate știrile</a></div>{CTA}'
            '<noscript><p style="text-align:center;color:#9a8fb5">Activează JavaScript pentru grafic și cardul 9:16.</p></noscript>')
    html_ = page('Rezumatul săptămânii · VEXU HQ', body, RECAP_JS).replace('</style>', RECAP_CSS + '\n</style>', 1)
    open(os.path.join(D, 'recap.html'), 'w', encoding='utf-8').write(html_)
    print(f'recap.html: {len(wk)} postări în {keys[0]}…{keys[-1]} ({len(conf)} CONFIRMAT afișate)')

def date_from(k):
    from datetime import date
    return date.fromisoformat(k)

def append_batch(path):
    batch = json.load(open(path, encoding='utf-8'))
    if isinstance(batch, dict):
        batch = [batch]
    for b in batch:  # joc: dacă e dat, se normalizează la numele canonic; dacă lipsește, ensure_meta îl detectează
        if b.get('joc'):
            b['joc'] = canon_joc(b['joc'])
    posts = json.load(open(P, encoding='utf-8'))
    posts.extend(batch)
    with open(P, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'Appended {len(batch)} posts from {path}')

def localize_images(posts):
    """Descarcă local orice imagine remote (ex. tr.rbxcdn 180DAY expiră) în img/; păstrează URL-ul dacă eșuează."""
    import hashlib, urllib.request
    changed = False
    os.makedirs(os.path.join(D, 'img'), exist_ok=True)
    for p in posts:
        u = p.get('img', '')
        if not re.match(r'https?://', u):
            continue
        ext = '.' + (re.search(r'\.(png|jpe?g|webp|gif)', u.lower()) or re.search(r'/(png|jpe?g|webp|gif)/', u.lower()) or [None, 'png'])[1]
        rel = 'img/' + hashlib.sha1(u.encode()).hexdigest()[:12] + ext
        try:
            req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(req, timeout=30).read()
            if len(data) < 100: raise ValueError('empty')
            open(os.path.join(D, rel), 'wb').write(data)
            p['img'] = rel; changed = True
            print('Imagine localizată:', u, '->', rel)
        except Exception as ex:
            print('EROARE descărcare imagine (păstrez URL):', u, ex)
    return changed

def main():
    ap = argparse.ArgumentParser(description='Build VEXU HQ blog/calendar')
    ap.add_argument('--append', metavar='FILE', help='JSON array of posts to append to posts.json')
    args = ap.parse_args()
    if args.append:
        append_batch(args.append)
    posts = json.load(open(P, encoding='utf-8'))
    loc = localize_images(posts)
    if ensure_meta(posts) or loc:
        with open(P, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Auto-filled published/date on some posts')
    index_items = build_post_pages(posts)
    build_game_pages(posts)
    build_blog()
    build_calendar()
    build_recap(index_items)
    print('recap.html / blog.html / calendar.html / posts-index.json / calendar-events.json OK')

if __name__ == '__main__':
    main()
