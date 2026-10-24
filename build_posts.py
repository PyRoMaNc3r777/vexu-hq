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
    t = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', t)  # fără markdown de imagine în rezumat
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

def prio_of(p):
    """Importanța pentru „Top știri” din Rezumat: prio (număr, mai mare = mai important) sau major: true (= 50)."""
    v = p.get('prio')
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v
    return 50 if p.get('major') is True else 0

def joc_of(p):
    return (p.get('joc') or '').strip()

def joc_slug(j):
    return slug(j)

# PWA: manifest + service worker (sw.js), căi absolute sub /vexu-hq/
PWA_HEAD = ('<link rel="manifest" href="/vexu-hq/manifest.webmanifest"><meta name="theme-color" content="#08090c">'
            '<link rel="apple-touch-icon" href="/vexu-hq/icon-192.png"><meta name="apple-mobile-web-app-capable" content="yes">'
            '<meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="VEXU HQ">')
PWA_JS = "<script>if('serviceWorker' in navigator)addEventListener('load',()=>navigator.serviceWorker.register('/vexu-hq/sw.js',{scope:'/vexu-hq/'}).catch(()=>{}))</script>"

import hashlib
NE = re.compile('^[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\uFE0F\u200D\\s]+')
def ne(s):
    """Titlu pentru liste/feed: fără emoji-ul de la început (în pagina articolului titlul rămâne neschimbat)."""
    return NE.sub('', s or '')
CSS_V = hashlib.md5(open(os.path.join(D, 'style.css'), 'rb').read()).hexdigest()[:8]  # cache-bust: se schimbă singur când se schimbă style.css
# fade-in pentru imagini (img.fx → .ld la load); fără JS imaginile rămân vizibile (noscript)
FX_HEAD = ("<script>(function(){var d=document;function m(i){i.classList.add('ld')}"
           "d.addEventListener('load',function(e){var i=e.target;if(i&&i.classList&&i.classList.contains('fx'))m(i)},true);"
           "d.addEventListener('error',function(e){var i=e.target;if(i&&i.classList&&i.classList.contains('fx'))m(i)},true);"
           "function s(){var a=d.querySelectorAll('img.fx:not(.ld)');for(var k=0;k<a.length;k++)if(a[k].complete)m(a[k])}"
           "addEventListener('DOMContentLoaded',s);addEventListener('load',s);setTimeout(s,1500)})()</script>"
           '<noscript><style>img.fx{opacity:1}</style></noscript>')
CSS_LINK = ('<link rel="preload" href="/vexu-hq/fonts/geist-latin.woff2" as="font" type="font/woff2" crossorigin>'
            f'<link rel="stylesheet" href="/vexu-hq/style.css?v={CSS_V}">' + FX_HEAD)
TOP_HTML = '<button class="totop" id="totop" type="button" aria-label="Înapoi sus" title="Înapoi sus">↑</button>'
# (Vânătoarea de dovleci a fost scoasă din UI în design v6; pumpkin-hunt.js rămâne în repo, neîncărcat.)
HUNT_JS = ''
TOP_JS = "<script>(function(){var b=document.getElementById('totop');if(!b)return;function u(){b.classList.toggle('on',scrollY>600)}addEventListener('scroll',u,{passive:true});u();b.onclick=function(){scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'})}})()</script>"
NAV_ITEMS = [('index', 'index.html', 'Dashboard'), ('blog', 'blog.html', 'Blog'),
             ('calendar', 'calendar.html', 'Calendar'), ('recap', 'recap.html', 'Rezumat')]
def header(active=None, pre='', section=False):
    """Header comun (brand + Shorts + navigație). pre = '../' pe paginile din posts/ și joc/. section=True: pagina e în secțiunea activă, nu chiar pagina ei."""
    cur = 'true' if section else 'page'
    nav = '<nav class="tn" aria-label="Navigație principală">' + ''.join(
        f'<a href="{pre}{h}"' + (f' aria-current="{cur}"' if k == active else '') + f'>{t}</a>' for k, h, t in NAV_ITEMS) + '</nav>'
    return (f'<header class="top"><div class="top-in"><a class="brand" href="{pre}index.html"><img src="/vexu-hq/icon-192.png" width="28" height="28" alt="">'
            f'<b>VEXU<i>HQ</i></b></a><a class="tn-s" href="{pre}blog.html#f=trend-shorts">Ce merge în Shorts</a>{nav}</div></header>')

def page(title, body, extra_js='', active=None, pre='', section=False):
    return (f'<!doctype html><html lang="ro"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)}</title><link rel="icon" type="image/png" href="/vexu-hq/icon.png">{PWA_HEAD}{CSS_LINK}</head><body>'
            f'{header(active, pre, section)}<div class="w">{body}</div>{TOP_HTML}{extra_js}{TOP_JS}{HUNT_JS}{PWA_JS}</body></html>\n')

e = html.escape
def cls(l): return re.sub(r'[^A-Za-z0-9]+', '-', l).strip('-')
def chips(p):
    return ' '.join(f'<span class="l {cls(l)}">{e(l)}</span>' for l in labels_of(p))
def ribs(p):
    return '<span class="ribs">' + ''.join(f'<span class="rib {cls(l)}">{e(l)}</span>' for l in labels_of(p)) + '</span>'
def gdot(j):
    """Pătrat colorat consecvent pentru fiecare joc (hue din slug) — același algoritm ca gameHue() din events.js."""
    h = 0
    for ch in (joc_slug(j) if j else ''):
        h = (h * 31 + ord(ch)) % 360
    return f'<i class="gd" style="--h:{h}"></i>'
def pcard(q, pre, h='h3', big=False, ex=True):
    """Card cu imagine 16:9 + panglică de etichetă (randat la build: pagini de joc, „Mai citește”)."""
    qs = q.get('slug') or slug(q['titlu']); first = cls(labels_of(q)[0])
    gm = f'<span class="gm">{gdot(joc_of(q))}{e(joc_of(q))}</span>' if joc_of(q) else ''
    return (f'<a class="pc {first}{" big" if big else ""}" href="{pre}{e(qs)}.html"><span class="im"><img class="fx" src="{"../" if pre.startswith("../") or pre == "" else ""}{e(q["img"])}" alt="" width="640" height="360" loading="lazy">{ribs(q)}</span>'
            f'<span class="b"><span class="mt"><span class="dt">{ro_date(q["date"])}</span>{gm}</span><{h}>{e(ne(q["titlu"]))}</{h}>'
            + (f'<span class="ex">{e(excerpt_of(q))}</span>' if ex else '') + '</span></a>')
def prow(q, pre='../posts/'):
    qs = q.get('slug') or slug(q['titlu']); first = cls(labels_of(q)[0])
    gm = f'<span class="gm">{gdot(joc_of(q))}{e(joc_of(q))}</span>' if joc_of(q) else ''
    return (f'<a class="p {first}" href="{pre}{e(qs)}.html"><span class="im"><img class="fx" src="../{e(q["img"])}" alt="" width="296" height="185" loading="lazy"></span>'
            f'<span class="b"><span class="mt">{chips(q)}<span class="dt">{ro_date(q["date"])}</span></span><h2>{e(ne(q["titlu"]))}</h2><span class="ex">{e(excerpt_of(q))}</span>{gm}</span></a>')
URL = re.compile(r'https?://[^\s()<>]+[^\s()<>.,;:!?]')
def link(t): return URL.sub(lambda m: f'<a href="{m.group(0)}" target="_blank" rel="noopener">{m.group(0)}</a>', e(t))
THUMB = re.compile(r'^!\[([^\]]*)\]\((img/[A-Za-z0-9._-]+)\)$')  # thumbnail în text: ![alt](img/x.jpg)
def rich(t):
    out, ul = [], False
    for ln in t.split('\n'):
        m = THUMB.match(ln)
        if m:
            if ul: out.append('</ul>'); ul = False
            out.append(f'<img class="th" src="../{e(m.group(2))}" alt="{e(m.group(1))}" loading="lazy">')
            continue
        if ln.startswith('- '):
            if not ul: out.append('<ul>'); ul = True
            out.append(f'<li>{link(ln[2:])}</li>')
        else:
            if ul: out.append('</ul>'); ul = False
            out.append(f'<p>{link(ln)}</p>')
    if ul: out.append('</ul>')
    return ''.join(out)


CTA = ('<div class="cta"><b>Follow = Au ce bile! 💥</b>'
       '<a href="https://www.tiktok.com/@vexu_online" target="_blank" rel="noopener">TikTok @vexu_online</a>'
       '<a class="yt" href="https://www.youtube.com/@VexuOnline" target="_blank" rel="noopener">YouTube VEXU Online</a></div>')

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
const ne=s=>String(s||'').replace(/^[\p{Extended_Pictographic}\uFE0F\u200D\s]+/u,'');
function hay(p){if(p._h===undefined||(SEARCH&&!p._full)){p._full=!!SEARCH; p._h=norm(p.title+' '+(p.excerpt||'')+' '+(p.labels||[]).join(' ')+' '+(p.joc||'')+' '+((SEARCH&&SEARCH[p.slug])||''))} return p._h}
function qmatch(p,t){return !t.length||t.every(w=>hay(p).includes(w))}
function fmatch(p,f){return f==='toate'||(p.labels||[]).some(l=>fid(l)===f)}
function loadSearch(){if(SEARCH||sLoading)return; sLoading=true;
  fetch('posts-search.json?'+Date.now()).then(r=>r.json()).then(d=>{SEARCH=d; if(q.trim()) paint()}).catch(()=>{sLoading=false})}
function chipsHtml(labels,date){return labels.map(l=>`<span class="l ${cls(l)}">${es(l)}</span>`).join(' ')+`<span class="dt">${es(date)}</span>`}
// insignă „NOU” pentru postările publicate în ultimele 6 ore (din câmpul published, ora reală)
function newBadge(p){const t=Date.parse(p.published||''); if(!t)return ''; const m=Math.floor((Date.now()-t)/6e4); if(m<0||m>=360)return '';
  return `<span class="nou">NOU · ${m<1?'acum':m<60?m+' min':Math.floor(m/60)+' h'}</span>`}
function gHue(k){let h=0;k=String(k||'');for(let i=0;i<k.length;i++)h=(h*31+k.charCodeAt(i))%360;return h}
const gmHtml=p=>p.joc?`<span class="gm"><i class="gd" style="--h:${gHue(p.jocSlug)}"></i>${es(p.joc)}</span>`:'';
const ribs=p=>`<span class="ribs">${(p.labels||[]).map(l=>`<span class="rib ${cls(l)}">${es(l)}</span>`).join('')}</span>`;
// card mare cu imagine 16:9 (primele postări)
function bigHtml(p, big){
  return `<a class="pc ${cls((p.labels||[''])[0])}${big?' big':''}" href="posts/${es(p.slug)}.html"><span class="im"><img class="fx" src="${es(p.img)}" alt="" width="640" height="360"${big?' fetchpriority="high"':' loading="lazy"'}>${ribs(p)}</span><span class="b"><span class="mt"><span class="dt">${es(p.dateRo)}</span>${gmHtml(p)}${newBadge(p)}</span><h2>${es(ne(p.title))}</h2><span class="ex">${es(p.excerpt)}</span></span></a>`;
}
// rând dens (restul feed-ului)
function cardHtml(p){
  return `<a class="p ${cls((p.labels||[''])[0])}" href="posts/${es(p.slug)}.html"><span class="im"><img class="fx" src="${es(p.img)}" alt="" width="296" height="185" loading="lazy"></span><span class="b"><span class="mt">${chipsHtml(p.labels||[],p.dateRo)}${newBadge(p)}</span><h2>${es(ne(p.title))}</h2><span class="ex">${es(p.excerpt)}</span>${gmHtml(p)}</span></a>`;
}
function renderFilters(t){
  const base=ALL.filter(p=>qmatch(p,t));
  document.getElementById('filters').innerHTML=FILTERS.map(f=>`<button type="button" class="chip${filter===f.id?' on':''}" data-f="${es(f.id)}" aria-pressed="${filter===f.id}">${es(f.label)}<span class="n">${base.filter(p=>gmatch(p,game)&&fmatch(p,f.id)).length}</span></button>`).join('');
  document.querySelectorAll('#filters .chip').forEach(b=>b.onclick=()=>{filter=b.dataset.f; setHash(); shown=0; paint()});
  const gb=base.filter(p=>fmatch(p,filter));
  const gf=document.getElementById('gfilters');
  gf.innerHTML=GAMES.map(g=>`<button type="button" class="chip${game===g.id?' on':''}" data-g="${es(g.id)}" aria-pressed="${game===g.id}">${es(g.label)}<span class="n">${gb.filter(p=>gmatch(p,g.id)).length}</span></button>`).join('');
  gf.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{game=b.dataset.g; setHash(); shown=0; paint()});
  const on=gf.querySelector('.chip.on'); if(on&&game!=='toate'&&gf.scrollWidth>gf.clientWidth) gf.scrollLeft=on.offsetLeft-gf.clientWidth/2+on.offsetWidth/2;
  const cur=GAMES.find(g=>g.id===game);
  document.getElementById('gpage').innerHTML=game!=='toate'&&cur?`<a href="joc/${es(cur.id)}.html">Pagina jocului ${es(cur.label)} →</a>`:'';
}
function paint(){
  const t=terms();
  renderFilters(t);
  const ok=p=>fmatch(p,filter)&&gmatch(p,game)&&qmatch(p,t);
  // un singur post evidențiat sus; celelalte marcate featured rămân în feed (cronologic), nu dispar
  const feat=ALL.find(p=>p.featured && ok(p) && (Date.now()-(Date.parse(p.published)||0))<72*36e5); // fixat sus doar cât e proaspăt (72h)
  const rest=ALL.filter(p=>p!==feat && ok(p)).sort((a,b)=>(Date.parse(b.published)||0)-(Date.parse(a.published)||0));
  const ordered=feat?[feat].concat(rest):rest, TOP=5;
  const top=ordered.slice(0,TOP), list=ordered.slice(TOP);
  document.getElementById('featSlot').innerHTML=top.length?`<div class="cards mag">${top.map((p,i)=>bigHtml(p,i===0)).join('')}</div>`:'';
  const slice=list.slice(0, Math.max(shown, PAGE));
  shown=slice.length;
  let html='', last='', open=false;
  for(const p of slice){
    const k=dayKey(p.published||p.date);
    if(k!==last){ if(open) html+='</div>'; html+=`<h2 class="dayh">${es(dayLabel(k))}</h2><div class="grid">`; open=true; last=k; }
    html+=cardHtml(p);
  }
  if(open) html+='</div>';
  if(!top.length) html=t.length?`<div class="empty">Nicio știre găsită pentru „${es(q.trim())}”${filter!=='toate'?' pe filtrele astea':''}.</div>`:'<div class="empty">Nicio postare pe filtrele astea.</div>';
  document.getElementById('feed').innerHTML=html;
  const n=ordered.length;
  document.getElementById('qinfo').textContent=t.length?(n===1?'1 rezultat':`${n} rezultate`)+(SEARCH?'':' (se încarcă textul complet…)'):(filter!=='toate'||game!=='toate'?`${n} ${n===1?'știre':'știri'}`:'');
  document.getElementById('qx').style.visibility=q?'visible':'hidden';
  const more=document.getElementById('moreBtn');
  const left=list.length-shown;
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
document.querySelector('.tn-s').onclick=e=>{e.preventDefault();filter=FILTERS.some(f=>f.id==='trend-shorts')?'trend-shorts':'toate'; setHash(); shown=0; paint(); document.getElementById('filters').scrollIntoView({behavior:'smooth'})};
({f:filter,g:game,q}=parseHash()); qi.value=q; if(q) loadSearch();
fetch('posts-index.json?'+Date.now()).then(r=>r.json()).then(data=>{
  ALL=data.posts||data; buildFilters(); buildGames(); validFilter(); paint();
}).catch(err=>{document.getElementById('feed').innerHTML='<div class="empty">Nu pot încărca indexul.</div>'});
window.addEventListener('hashchange',()=>{({f:filter,g:game,q}=parseHash()); qi.value=q; if(q) loadSearch(); validFilter(); shown=0; paint()});
</script>
"""

EVENTS_SRC = '<script src="/vexu-hq/events.js?v=' + hashlib.md5(open(os.path.join(D, 'events.js'), 'rb').read()).hexdigest()[:8] + '"></script>'

CAL_JS = r"""
<script>
(()=>{const {es,fmt,dayKey,status,evRow,tick}=VX;
let EVENTS=[],game='toate',GAMES=[{id:'toate',label:'Toate'}];const opened=new Map();
function parseHash(){const m=(location.hash||'').match(/(?:^#|&)g=([\w-]+)/);return m?m[1]:'toate'}
function setHash(){const h=game!=='toate'?'#g='+game:'';if((location.hash||'')!==h) history.replaceState(null,'',h||location.pathname+location.search)}
const gid=ev=>ev.gameSlug||'';
function buildGames(){const m=new Map();EVENTS.forEach(ev=>{const id=gid(ev);if(!id)return;const x=m.get(id)||{id,label:ev.gameLabel||ev.game||id,n:0};x.n++;m.set(id,x)});
  GAMES=[{id:'toate',label:'Toate',n:EVENTS.length}].concat([...m.values()].sort((a,b)=>b.n-a.n||a.label.localeCompare(b.label,'ro')))}
function validGame(){if(!GAMES.some(g=>g.id===game)) game='toate'}
function paintChips(){const gf=document.getElementById('gfilters');
  gf.innerHTML=GAMES.map(g=>{const evs=g.id==='toate'?EVENTS:EVENTS.filter(ev=>gid(ev)===g.id);
    return `<button type="button" class="chip${game===g.id?' on':''}" data-g="${es(g.id)}" aria-pressed="${game===g.id}">${es(g.label)}<span class="n">${evs.length}</span></button>`}).join('');
  gf.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{game=b.dataset.g;setHash();paintChips();paint()});
  const on=gf.querySelector('.chip.on');if(on&&game!=='toate'&&gf.scrollWidth>gf.clientWidth) gf.scrollLeft=on.offsetLeft-gf.clientWidth/2+on.offsetWidth/2;
  const gi=document.getElementById('ginfo');const g=GAMES.find(x=>x.id===game);gi.innerHTML=game==='toate'?'':`Arăt doar: <b>${es(g?g.label:game)}</b> · <a href="#" id="gclr">vezi toate</a>`;
  const c=document.getElementById('gclr');if(c) c.onclick=e=>{e.preventDefault();game='toate';setHash();paintChips();paint()}}
function dayName(k,today,tom){if(k===today)return'Azi';if(k===tom)return'Mâine';const [Y,M,D]=k.split('-').map(Number);return new Intl.DateTimeFormat('ro-RO',{timeZone:'UTC',weekday:'long'}).format(new Date(Date.UTC(Y,M-1,D,12)))}
function dayFull(k){const [Y,M,D]=k.split('-').map(Number);return new Intl.DateTimeFormat('ro-RO',{timeZone:'UTC',day:'numeric',month:'long'}).format(new Date(Date.UTC(Y,M-1,D,12)))}
function paint(){
  const now=new Date(),today=dayKey(now),tom=dayKey(new Date(+now+864e5));
  const items=EVENTS.filter(ev=>game==='toate'||gid(ev)===game).map(ev=>({ev,st:status(ev,now)}));
  const days=new Map(),nodate=[],done=[];let nLive=0,nSoon24=0;
  items.forEach(i=>{const k=i.st.kind;if(k==='done'){done.push(i);return}
    if(k==='live')nLive++;else if(i.st.target&&i.st.target-now<864e5)nSoon24++;
    if(!i.st.target){nodate.push(i);return}
    const dk=dayKey(i.st.target);if(!days.has(dk))days.set(dk,[]);days.get(dk).push(i)});
  const keys=[...days.keys()].sort();
  const row=i=>evRow(i.ev,now,{meta:true,note:true});
  const sortT=(a,b)=>(a.st.target||0)-(b.st.target||0);
  const grp=(id,title,sub,n,list,open,cls)=>`<details class="dg" data-id="${id}"${open?' open':''}><summary class="dh ${cls||''}"><b>${title}</b><span>${sub}</span><em>${n}<s> ${n===1?'eveniment':'evenimente'}</s></em></summary><div class="evl two">${list}</div></details>`;
  let h=`<div class="sm" style="margin:0 0 12px"><b>${nLive}</b> live acum · <b>${nSoon24}</b> încep în următoarele 24 de ore · <b>${keys.length}</b> zile cu evenimente. Zilele sunt grupate după următorul moment important (start sau final).</div>`;
  keys.forEach(k=>{const list=days.get(k).sort(sortT);const open=opened.has(k)?opened.get(k):(k<=tom);
    const ends=list.filter(i=>i.st.kind==='live').length,starts=list.length-ends;
    h+=grp(k,dayName(k,today,tom),dayFull(k)+(ends&&starts?` · ${ends} final · ${starts} start`:ends?` · final`:` · start`),list.length,list.map(row).join(''),open,k===today?'today':'')});
  if(nodate.length){const id='nodate';h+=grp(id,'Fără oră fixă','live sau încă neanunțate',nodate.length,nodate.map(row).join(''),opened.has(id)?opened.get(id):false)}
  if(done.length){const id='done';h+=grp(id,'Terminate','istoric',done.length,done.sort((a,b)=>(+new Date(b.ev.end||b.ev.end_date||0))-(+new Date(a.ev.end||a.ev.end_date||0))).map(row).join(''),opened.has(id)?opened.get(id):false)}
  const el=document.getElementById('cal');
  el.innerHTML=h||`<div class="empty">${game==='toate'?'Niciun event încă.':'Niciun event pentru jocul ăsta.'}</div>`;
  el.querySelectorAll('details.dg').forEach(d=>d.addEventListener('toggle',()=>opened.set(d.dataset.id,d.open)));
}
game=parseHash();
fetch('calendar-events.json?'+Date.now()).then(r=>r.json()).then(d=>{EVENTS=d.events||d; buildGames(); validGame(); paintChips(); paint();
  setInterval(()=>{if(tick(document.getElementById('cal'),new Date()))paint()},1000); setInterval(paint,60000)}).catch(()=>{document.getElementById('cal').innerHTML='<div class="empty">Nu pot încărca calendarul.</div>'});
window.addEventListener('hashchange',()=>{game=parseHash();validGame();paintChips();paint()});
})();
</script>
"""

POST_JS = r"""<script>(()=>{const b=document.querySelector('.rp');if(b){let r=0;const u=()=>{r=0;const h=document.documentElement,m=h.scrollHeight-innerHeight;b.style.transform='scaleX('+(m>0?Math.min(1,scrollY/m):1)+')'};addEventListener('scroll',()=>{if(!r){r=1;requestAnimationFrame(u)}},{passive:true});addEventListener('resize',u);u()}
const s=document.getElementById('shr');if(s)s.onclick=async()=>{const d={title:document.title,url:location.href.split('#')[0]};try{if(navigator.share){await navigator.share(d);return}await navigator.clipboard.writeText(d.url);s.textContent='Link copiat';s.classList.add('ok');setTimeout(()=>{s.textContent='Distribuie';s.classList.remove('ok')},2200)}catch(e){}}})()</script>"""

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
    cards = ''.join(pcard(posts[j], '', 'h3', ex=False) for j in related(posts, i))
    return f'<section class="rel"><h2>Mai citește</h2><div class="cards c3">{cards}</div></section>' if cards else ''

def set_game(ce, joc):
    # slug pentru filtrul de jocuri din calendar = același jocSlug ca în blog când eventul ține de jocul postării
    g = (ce.get('game') or '').strip()
    js = joc_slug(joc) if joc else ''
    gs = joc_slug(g) if g else ''
    if js and (not gs or gs == js or js.startswith(gs + '-') or gs.startswith(js + '-')):
        ce['gameSlug'], ce['gameLabel'] = js, joc
    elif gs:
        ce['gameSlug'], ce['gameLabel'] = gs, g

def build_post_pages(posts):
    os.makedirs(os.path.join(D, 'posts'), exist_ok=True)
    index_items = []
    cal_events = []
    search = {}
    order = sorted(range(len(posts)), key=lambda i: (bool(posts[i].get('featured')), pub_key(posts[i]), -i), reverse=True)
    for i in order:
        p = posts[i]
        s = p.get('slug') or slug(p['titlu'])
        lab = f'{chips(p)}<span class="dt">{ro_date(p["date"])}</span>'
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
        body = ('<div class="rp" aria-hidden="true"></div>'
                f'<article class="art"><div class="art-m">{lab}'
                + (f'<a class="jl" href="../joc/{e(joc_slug(joc_of(p)))}.html">{e(joc_of(p))}</a>' if joc_of(p) else '') +
                f'</div><h1>{e(p["titlu"])}</h1><div class="hi"><img src="../{e(p["img"])}" alt="" width="1280" height="720" fetchpriority="high"></div>'
                f'<div class="txt">{txt}</div><div class="s">Surse:{src}</div></article>'
                f'<div class="acts"><a class="btn" href="../blog.html">← Înapoi la blog</a>'
                f'<button type="button" class="btn shr" id="shr">Distribuie</button></div>'
                + related_html(posts, i))
        open(os.path.join(D, 'posts', s + '.html'), 'w', encoding='utf-8').write(page(p['titlu'] + ' · VEXU HQ', body, POST_JS, 'blog', '../', True))
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
            'prio': prio_of(p),
            'views': p['views'] if isinstance(p.get('views'), int) and p['views'] > 0 else None,
            'updated': p.get('updated'),
            'republish': bool(p.get('republish')),
            'recap': RECAP_OVR.get(s),
        }
        index_items.append(item)
        search[s] = search_text(p)
        for ev in p.get('events', []):
            ce = dict(ev)
            ce['slug'] = s
            ce['img'] = ev.get('img') or p['img']
            ce['post_title'] = p['titlu']
            set_game(ce, joc_of(p))
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
            set_game(ce, '')
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
        top = ''.join(pcard(q, '../posts/', 'h2', big=(k == 0)) for k, q in enumerate(ps[:5]))
        rows = ''.join(prow(q) for q in ps[5:])
        cards = f'<div class="cards mag">{top}</div>' + (f'<h2 class="dayh">Mai vechi</h2><div class="grid">{rows}</div>' if rows else '')
        n = len(ps)
        body = (f'<span class="kick">Joc</span><h1>{e(j)}</h1>'
                f'<p class="gcount">{n} {"postare" if n == 1 else "postări"} · cele mai noi primele · '
                f'<a href="../blog.html#g={e(js)}">vezi în blog cu filtre</a></p>'
                f'{cards}{CTA}'
                f'<div class="acts"><a class="btn" href="../blog.html">← Toate știrile</a></div>')
        open(os.path.join(jd, js + '.html'), 'w', encoding='utf-8').write(page(f'{j} · VEXU HQ', body, '', 'blog', '../', True))
        made.add(js + '.html')
    for f in os.listdir(jd):
        if f.endswith('.html') and f not in made:
            os.remove(os.path.join(jd, f))
    print(f'joc/: {len(made)} pagini de joc')
    return groups

def build_blog():
    noscript = '<noscript><p class="rsub">Activează JavaScript pentru feed-ul grupat pe zile. Postările individuale rămân în <code>posts/</code>.</p></noscript>'
    body = (f'<h1>Știri</h1>'
            f'<form class="srch" id="qform" role="search"><input type="search" id="q" placeholder="Caută în știri…" aria-label="Caută în știri" autocomplete="off" enterkeyhint="search"><button type="button" id="qx" aria-label="Șterge căutarea">✕</button></form>'
            f'<div class="qinfo" id="qinfo" aria-live="polite"></div>'
            f'<div class="filters" id="filters"></div>'
            f'<div class="ftitle">Jocuri</div><div class="filters" id="gfilters" role="toolbar" aria-label="Filtru după joc"></div>'
            f'<div class="gpage" id="gpage"></div>'
            f'<div id="featSlot"></div><div id="feed"></div>'
            f'<div id="moreWrap"><button type="button" class="btn" id="moreBtn" style="display:none">Vezi mai multe</button></div>'
            f'{noscript}{CTA}')
    open(os.path.join(D, 'blog.html'), 'w', encoding='utf-8').write(page('VEXU HQ · Știri', body, BLOG_JS, 'blog'))

def build_calendar():
    body = (f'<h1>Calendar</h1>'
            f'<p class="rsub">Doar ferestre CONFIRMAT din blog · ora României · countdown live</p>'
            f'<div class="ftitle">Jocuri</div><div class="filters" id="gfilters" role="toolbar" aria-label="Filtru după joc"></div><div class="ginfo" id="ginfo"></div>'
            f'<div class="cal" id="cal">Se încarcă…</div>')
    open(os.path.join(D, 'calendar.html'), 'w', encoding='utf-8').write(page('Calendar evenimente · VEXU HQ', body, EVENTS_SRC + CAL_JS, 'calendar'))

# ───────────── Rezumatul săptămânii (recap.html) ─────────────
# Generat la build din posts.json (știrile din ultimele 7 zile, ora României), iar în browser se recalculează
# din posts-index.json + player-history.json + data.json (ultimele date scrise de GitHub Action), deci e mereu la zi.
# Doar date reale: zilele fără măsurători apar „fără date”, nimic nu se completează.
RECAP_DAYS = 7
RECAP_MAX_CONF = 10
RECAP_MAX_OTHER = 6

def load_recap_overrides():
    """recap-overrides.json: {slug: {allow, prio, title, until, title_after}} — doar pentru Rezumat, nu atinge postarea."""
    fp = os.path.join(D, 'recap-overrides.json')
    if not os.path.exists(fp):
        return {}
    o = json.load(open(fp, encoding='utf-8'))
    return {k: v for k, v in o.items() if not k.startswith('_') and isinstance(v, dict)}
RECAP_OVR = load_recap_overrides()

def recap_eff_prio(x):
    r = x.get('recap') or {}
    return max(x.get('prio') or 0, r.get('prio') or 0)

def recap_title(x, now=None):
    """Titlul afișat în rezumat: override (title / title_after după until) sau titlul postării. None = nu se afișează."""
    r = x.get('recap') or {}
    if r.get('until') and (now or now_ro()) >= datetime.fromisoformat(r['until']):
        return r.get('title_after')
    return r.get('title') or x['title']

def recap_skip(p):
    """Niciodată în rezumat: conținut Steal An Egg PART 2 și republicări SAE fără note noi (republish: true / Throwback)."""
    if (p.get('recap') or {}).get('allow'):  # excepție explicită, pe slug (recap-overrides.json)
        return recap_title(p) is None
    if (p.get('jocSlug') or '') != 'steal-an-egg':
        return False
    blob = (p.get('title', '') + ' ' + p.get('slug', '') + ' ' + (p.get('excerpt') or '')).lower()
    return bool(re.search(r'part[\s-]*(2|ii)\b', blob)) or bool(p.get('republish')) or 'throwback' in blob

NEWS_LABELS = ('CONFIRMAT', 'ZVON')
def recap_score(x):
    """Ordine: prio ↓, views reale ↓ (doar dacă postarea le are), CONFIRMAT > ZVON, apoi cele mai noi."""
    lr = 2 if 'CONFIRMAT' in x['labels'] else 1 if 'ZVON' in x['labels'] else 0
    ts = datetime.fromisoformat(x['published']).timestamp()
    return (recap_eff_prio(x), 1 if x.get('views') else 0, x.get('views') or 0, lr, ts)

def recap_top(cands, n):
    """Clasament + maxim 1 postare per joc (postările fără joc contează fiecare separat)."""
    out, seen = [], set()
    for x in sorted(cands, key=recap_score, reverse=True):
        g = x.get('jocSlug') or ('#' + x['slug'])
        if g in seen:
            continue
        seen.add(g); out.append(x)
        if len(out) >= n:
            break
    return out

def recap_pick(items, keys):
    rday = lambda iso: datetime.fromisoformat(iso).astimezone(TZ).date().isoformat()
    wk = [x for x in items if rday(x['published']) in keys and not recap_skip(x)]
    wk.sort(key=lambda x: x['published'], reverse=True)
    # eligibile pentru top: publicate în ultimele 7 zile SAU cu prio și actualizate (updated) în ultimele 7 zile
    el = [x for x in items if not recap_skip(x) and any(l in x['labels'] for l in NEWS_LABELS)
          and (rday(x['published']) in keys or (recap_eff_prio(x) > 0 and x.get('updated') and rday(x['updated']) in keys))]
    top = recap_top(el, RECAP_MAX_CONF)
    ids = {x['slug'] for x in top}
    other = [x for x in wk if x['slug'] not in ids and 'CONFIRMAT' not in x['labels'] and 'ZVON' in x['labels']][:RECAP_MAX_OTHER]
    return wk, top, other

def recap_row(x, rk=None):
    lab = ' '.join(f'<span class="l {cls(l)}">{e(l)}</span>' for l in x['labels'])
    d = datetime.fromisoformat(x['published']).astimezone(TZ)
    u = datetime.fromisoformat(x['updated']).astimezone(TZ) if x.get('updated') else None
    upd = f' · actualizat {u.day} {LUNI[u.month-1][:3]}' if u and u.date() != d.date() else ''
    r = f'<span class="rk">{rk:02d}</span>' if rk else ''
    return (f'<a class="rn {cls(x["labels"][0])}{"" if rk else " nr"}" href="posts/{e(x["slug"])}.html">{r}<span class="rl">{lab}</span><b>{e(ne(recap_title(x) or x["title"]))}</b>'
            f'<i>{e(x["joc"]) + " · " if x.get("joc") else ""}{d.day} {LUNI[d.month-1][:3]}, {d:%H:%M}{upd}</i></a>')

def recap_games(wk, n=8):
    cnt = {}
    for x in wk:
        if x.get('jocSlug') and x.get('joc'):
            c = cnt.setdefault(x['jocSlug'], [x['joc'], 0]); c[1] += 1
    top = sorted(cnt.items(), key=lambda kv: (-kv[1][1], kv[1][0]))[:n]
    mx = max([c[1] for _, c in top] or [1])
    out = ''
    for js, (j, c) in top:
        h = 0
        for ch in js:
            h = (h * 31 + ord(ch)) % 360
        out += (f'<a class="hbar" href="joc/{e(js)}.html" style="--h:{h}"><span class="gm"><i class="gd" style="--h:{h}"></i>{e(j)}</span><span class="v">{c}</span>'
                f'<span class="pbar"><u style="width:{c / mx * 100:.1f}%"></u></span></a>')
    return out or '<div class="rmeta">Nicio postare cu joc în ultimele 7 zile.</div>'

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
const ne=s=>String(s||'').replace(/^[\p{Extended_Pictographic}\uFE0F\u200D\s]+/u,'');
const ttl=p=>{const r=p.recap||{};if(r.until&&Date.now()>=Date.parse(r.until))return r.title_after||null;return r.title||p.title};
const eprio=p=>Math.max(p.prio||0,(p.recap&&p.recap.prio)||0);
const skip=p=>(p.recap&&p.recap.allow)?!ttl(p):p.jocSlug==='steal-an-egg'&&(/part[\s-]*(2|ii)\b|throwback/i.test((p.title||'')+' '+(p.slug||'')+' '+(p.excerpt||''))||!!p.republish);
const lr=p=>(p.labels||[]).includes('CONFIRMAT')?2:(p.labels||[]).includes('ZVON')?1:0;
const sc=(a,b)=>(eprio(b)-eprio(a))||((b.views?1:0)-(a.views?1:0))||((b.views||0)-(a.views||0))||(lr(b)-lr(a))||(new Date(b.published)-new Date(a.published));
function top(c,n){const o=[],seen=new Set();for(const p of [...c].sort(sc)){const g=p.jocSlug||('#'+p.slug);if(seen.has(g))continue;seen.add(g);o.push(p);if(o.length>=n)break}return o}
const plain=s=>String(s).replace(/[\p{Extended_Pictographic}\u{1F1E6}-\u{1F1FF}\uFE0F\u200D]/gu,'').replace(/\s+/g,' ').trim();
let K=keys(),WK=[],CONF=[],OTH=[],PH=null,DATA=null;
function rangeTxt(){const a=kd(K[0]),b=kd(K[K.length-1]);return a.m===b.m?`${a.d} – ${b.d} ${LUNL[b.m-1]} ${b.y}`:`${a.d} ${LUNL[a.m-1]} – ${b.d} ${LUNL[b.m-1]} ${b.y}`}
function gh(k){let h=0;k=String(k||'');for(let i=0;i<k.length;i++)h=(h*31+k.charCodeAt(i))%360;return h}
function row(p,rk){const d=new Date(p.published);return `<a class="rn ${cls((p.labels||[''])[0])}${rk?'':' nr'}" href="posts/${es(p.slug)}.html">${rk?`<span class="rk">${String(rk).padStart(2,'0')}</span>`:''}<span class="rl">${(p.labels||[]).map(l=>`<span class="l ${cls(l)}">${es(l)}</span>`).join(' ')}</span><b>${es(ne(ttl(p)||p.title))}</b><i>${p.joc?es(p.joc)+' · ':''}${kd(dk(d)).d} ${LUN[kd(dk(d)).m-1]}, ${hm(d)}${p.updated&&dk(new Date(p.updated))!==dk(d)?` · actualizat ${kd(dk(new Date(p.updated))).d} ${LUN[kd(dk(new Date(p.updated))).m-1]}`:''}</i></a>`}
function games(){const m=new Map();WK.forEach(p=>{if(!p.joc||!p.jocSlug)return;const x=m.get(p.jocSlug)||{s:p.jocSlug,j:p.joc,n:0};x.n++;m.set(p.jocSlug,x)});
  const L=[...m.values()].sort((a,b)=>b.n-a.n||a.j.localeCompare(b.j,'ro')).slice(0,8),mx=Math.max(1,...L.map(x=>x.n));
  document.getElementById('rgames').innerHTML=L.length?L.map(x=>`<a class="hbar" href="joc/${es(x.s)}.html" style="--h:${gh(x.s)}"><span class="gm"><i class="gd" style="--h:${gh(x.s)}"></i>${es(x.j)}</span><span class="v">${x.n}</span><span class="pbar"><u style="width:${(x.n/mx*100).toFixed(1)}%"></u></span></a>`).join(''):'<div class="rmeta">Nicio postare cu joc în ultimele 7 zile.</div>'}
function news(ix){K=keys();const ks=new Set(K);
  WK=(ix.posts||[]).filter(p=>p.published&&ks.has(dk(new Date(p.published)))&&!skip(p)).sort((a,b)=>new Date(b.published)-new Date(a.published));
  const EL=(ix.posts||[]).filter(p=>p.published&&!skip(p)&&lr(p)>0&&(ks.has(dk(new Date(p.published)))||(eprio(p)>0&&p.updated&&ks.has(dk(new Date(p.updated))))));
  CONF=top(EL,MAXC);const ids=new Set(CONF.map(p=>p.slug));OTH=WK.filter(p=>!ids.has(p.slug)&&lr(p)===1).slice(0,MAXO);
  document.getElementById('rrange').textContent=rangeTxt();
  document.getElementById('rconf').innerHTML=CONF.length?CONF.map((p,i)=>row(p,i+1)).join(''):'<div class="rmeta">Nicio știre în ultimele 7 zile.</div>';
  document.getElementById('roth').innerHTML=OTH.length?OTH.map(p=>row(p)).join(''):'<div class="rmeta">Niciun zvon în ultimele 7 zile.</div>';
  const c=l=>WK.filter(p=>(p.labels||[]).includes(l)).length;
  document.getElementById('rnum').innerHTML=[[WK.length,'postări','all'],[c('CONFIRMAT'),'CONFIRMAT','CONFIRMAT'],[c('ZVON'),'ZVON','ZVON'],[c('TREND SHORTS'),'TREND SHORTS','TREND-SHORTS'],[c('VEXU LIVE'),'VEXU LIVE','VEXU-LIVE']].map(([n,t,k])=>`<div class="${k}"><b>${n}</b><span>${t}</span></div>`).join('');games()}
function peaks(){const ds=(PH&&PH.days)||{};return K.map(k=>({k,v:ds[k]&&typeof ds[k].peak==='number'?ds[k]:null}))}
function manual(){const ks=new Set(K);return ((PH&&PH.manual)||[]).filter(m=>typeof m.p==='number'&&m.t&&ks.has(dk(new Date(m.t))))}
function chart(){const el=document.getElementById('rchart'),meta=document.getElementById('rcmeta');if(!PH){el.innerHTML='<div class="rmeta">Nu pot încărca istoricul de jucători acum.</div>';return}
  const P=peaks(),have=P.filter(x=>x.v);if(!have.length){el.innerHTML='<div class="rmeta">Încă nu avem măsurători în ultimele 7 zile.</div>';meta.textContent='';return}
  const W=700,H=270,L=10,R=10,T=34,B=46,bw=(W-L-R)/P.length,mx=Math.max(...have.map(x=>x.v.peak))*1.08;let g='';
  P.forEach((x,i)=>{const cx=L+bw*i+bw/2,w=bw*.62,d=kd(x.k),lab=x.k===K[K.length-1]?`azi (${d.d})`:`${WD[d.w]} ${d.d}`;
    if(x.v){const h=(H-T-B)*x.v.peak/mx,y=H-B-h;g+=`<rect x="${(cx-w/2).toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${h.toFixed(1)}" rx="2" class="bar"/><text x="${cx}" y="${(y-8).toFixed(1)}" text-anchor="middle" class="bv">${cmp(x.v.peak)}</text>`}
    else{g+=`<rect x="${(cx-w/2).toFixed(1)}" y="${T+40}" width="${w.toFixed(1)}" height="${H-B-T-40}" rx="2" class="gap"/><text x="${cx}" y="${(H-B-12)}" text-anchor="middle">fără date</text>`}
    g+=`<text x="${cx}" y="${H-B+20}" text-anchor="middle">${lab}</text><text x="${cx}" y="${H-B+36}" text-anchor="middle" class="nd">${x.v?x.v.n+' măs.':''}</text>`});
  el.innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Steal An Egg: vârful zilnic de jucători în ultimele 7 zile">${g}</svg>`;
  const best=have.reduce((a,x)=>x.v.peak>a.v.peak?x:a),m=manual();let t=`Cel mai mare vârf măsurat: ${nf(best.v.peak)} jucători (${WD[kd(best.k).w]} ${kd(best.k).d} ${LUN[kd(best.k).m-1]}, ${hm(new Date(best.v.t))}). `;
  t+=`Date din ${have.length} din ${P.length} zile`+(have.length<P.length?' (zilele fără măsurători apar „fără date”)':'')+'. ';
  m.forEach(x=>{t+=`Citire manuală: ${nf(x.p)} pe ${kd(dk(new Date(x.t))).d} ${LUN[kd(dk(new Date(x.t))).m-1]}, ${hm(new Date(x.t))}${x.note?' ('+x.note+')':''}. `});
  if(DATA&&DATA.game&&typeof DATA.game.playing==='number')t+=`Ultima citire: ${nf(DATA.game.playing)} jucători (${hm(new Date(DATA.game.fetched||DATA.updated))}).`;
  meta.textContent=t}
// ── card 9:16 (1080×1920), desenat local în canvas ──
function rr(c,x,y,w,h,r){c.beginPath();c.moveTo(x+r,y);c.arcTo(x+w,y,x+w,y+h,r);c.arcTo(x+w,y+h,x,y+h,r);c.arcTo(x,y+h,x,y,r);c.arcTo(x,y,x+w,y,r);c.closePath()}
function wrap(c,t,maxW,maxL){const w=t.split(' '),out=[];let cur='';for(const x of w){const n=cur?cur+' '+x:x;if(c.measureText(n).width>maxW&&cur){out.push(cur);cur=x}else cur=n}if(cur)out.push(cur);if(out.length>maxL){out.length=maxL;let l=out[maxL-1];while(c.measureText(l+'…').width>maxW&&l.length)l=l.slice(0,-1);out[maxL-1]=l.replace(/\s+\S*$/,'')+'…'}return out}
const F='system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans",sans-serif';
function card(){const cv=document.createElement('canvas');cv.width=1080;cv.height=1920;const c=cv.getContext('2d');
  c.fillStyle='#08090c';c.fillRect(0,0,1080,1920);
  let g=c.createRadialGradient(200,0,0,200,0,1100);g.addColorStop(0,'#12170a');g.addColorStop(1,'#12170a00');c.fillStyle=g;c.fillRect(0,0,1080,1920);
  g=c.createRadialGradient(1080,1920,0,1080,1920,1100);g.addColorStop(0,'#08090c');g.addColorStop(1,'#08090c00');c.fillStyle=g;c.fillRect(0,0,1080,1920);
  g=c.createLinearGradient(0,1700,0,1920);g.addColorStop(0,'#c6f13500');g.addColorStop(1,'#c6f13514');c.fillStyle=g;c.fillRect(0,1700,1080,220);
  c.textAlign='center';c.textBaseline='alphabetic';
  g=c.createLinearGradient(240,0,840,0);g.addColorStop(0,'#eef0f3');g.addColorStop(1,'#eef0f3');
  c.font=`900 120px ${F}`;c.fillStyle=g;c.shadowBlur=0;c.fillText('VEXU HQ',540,180);c.shadowBlur=0;
  c.font=`800 64px ${F}`;c.fillStyle='#fff';c.fillText('REZUMATUL SĂPTĂMÂNII',540,280);
  c.font=`600 40px ${F}`;c.fillStyle='#a2a5b0';c.fillText(rangeTxt(),540,345);
  // top știri
  c.textAlign='left';c.font=`800 38px ${F}`;c.fillStyle='#3ecf8e';c.fillText('TOP ȘTIRILE SĂPTĂMÂNII',70,412);
  let y=436;const top=CONF.slice(0,5),LIM=1228;
  if(!top.length){c.font=`600 36px ${F}`;c.fillStyle='#a2a5b0';c.fillText('Nicio știre săptămâna asta.',70,y+50)}
  for(let i=0;i<top.length;i++){const p=top[i];c.font=`700 32px ${F}`;const ls=wrap(c,plain(ttl(p)||p.title),850,2),h=30+ls.length*40+(p.joc?34:0);
    if(y+h>LIM)break;
    rr(c,60,y,960,h,24);c.fillStyle='#121317';c.fill();c.strokeStyle='#2a2c35';c.lineWidth=3;c.stroke();
    c.fillStyle='#c6f135';c.font=`900 38px ${F}`;c.fillText(String(i+1),88,y+54);
    c.fillStyle='#fff';c.font=`700 32px ${F}`;ls.forEach((l,j)=>c.fillText(l,135,y+50+j*40));
    if(p.joc){c.font=`600 27px ${F}`;c.fillStyle='#a2a5b0';c.fillText(plain(p.joc),135,y+50+ls.length*40-2)}
    y+=h+10}
  // grafic Steal An Egg (doar zilele cu măsurători reale; restul „fără date”)
  const P=peaks(),have=P.filter(x=>x.v);y=1268;
  c.font=`800 36px ${F}`;c.fillStyle='#c6f135';c.fillText('STEAL AN EGG · VÂRF ZILNIC DE JUCĂTORI',70,y);
  const top0=y+24,ch=230;rr(c,60,top0,960,ch+66,24);c.fillStyle='#000a';c.fill();c.strokeStyle='#2a2c35';c.lineWidth=3;c.stroke();
  const base=top0+ch-6;
  if(have.length){const mx=Math.max(...have.map(x=>x.v.peak)),bw=900/P.length,bh=ch-70;
    const bg=c.createLinearGradient(0,base-bh,0,base);bg.addColorStop(0,'#c6f135');bg.addColorStop(1,'#c6f135');
    P.forEach((x,i)=>{const cx=90+bw*i+bw/2,w=bw*.6,d=kd(x.k);c.textAlign='center';
      if(x.v){const h=Math.max(6,bh*x.v.peak/mx),by=base-h;rr(c,cx-w/2,by,w,h,10);c.fillStyle=bg;c.fill();c.fillStyle='#fff';c.font=`800 27px ${F}`;c.fillText(cmp(x.v.peak),cx,by-10)}
      else{c.setLineDash([8,8]);rr(c,cx-w/2,base-bh*.55,w,bh*.55,10);c.strokeStyle='#ffffff44';c.lineWidth=2;c.stroke();c.setLineDash([]);c.fillStyle='#a2a5b0';c.font=`600 21px ${F}`;c.fillText('fără',cx,base-bh*.55+36);c.fillText('date',cx,base-bh*.55+60)}
      c.fillStyle='#a2a5b0';c.font=`600 25px ${F}`;c.fillText(x.k===K[K.length-1]?'azi':`${WD[d.w]} ${d.d}`,cx,base+40)});c.textAlign='left'}
  else{c.textAlign='center';c.font=`600 32px ${F}`;c.fillStyle='#a2a5b0';c.fillText('Încă nu avem măsurători săptămâna asta.',540,top0+ch/2);c.textAlign='left'}
  c.font=`500 23px ${F}`;c.fillStyle='#6b6e7a';c.fillText('Vârful măsurat de VEXU HQ din API-ul Roblox (ora României).',70,top0+ch+104);
  // CTA
  c.textAlign='center';c.font=`900 58px ${F}`;c.fillStyle='#c6f135';c.shadowBlur=0;c.fillText('Follow = Au ce bile! 💥',540,1700);c.shadowBlur=0;
  rr(c,90,1735,430,96,28);c.fillStyle='#000c';c.fill();c.strokeStyle='#c6f135';c.lineWidth=4;c.stroke();
  rr(c,560,1735,430,96,28);c.fillStyle='#000c';c.fill();c.strokeStyle='#c6f135';c.stroke();
  c.font=`800 34px ${F}`;c.fillStyle='#eef0f3';c.fillText('TikTok @vexu_online',305,1796);c.fillStyle='#eef0f3';c.fillText('YouTube VEXU Online',775,1796);
  c.font=`600 24px ${F}`;c.fillStyle='#a2a5b0';c.fillText('pyromanc3r777.github.io/vexu-hq',540,1885);
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
    nums = ''.join(f'<div class="{c}"><b>{n}</b><span>{l}</span></div>' for n, l, c in [(len(wk), 'postări', 'all'), (cnt('CONFIRMAT'), 'CONFIRMAT', 'CONFIRMAT'), (cnt('ZVON'), 'ZVON', 'ZVON'), (cnt('TREND SHORTS'), 'TREND SHORTS', 'TREND-SHORTS'), (cnt('VEXU LIVE'), 'VEXU LIVE', 'VEXU-LIVE')])
    body = (f'<h1>Rezumatul săptămânii</h1>'
            f'<p class="rsub">Ultimele 7 zile · <span id="rrange">{rng}</span> · ora României · se actualizează singur</p>'
            f'<div class="sec" style="margin-top:12px"><h2 style="margin-bottom:12px">Săptămâna în cifre</h2><div class="rnum" id="rnum">{nums}</div></div>'
            f'<div class="rgrid"><div>'
            f'<div class="rc"><h2>Top știri ale săptămânii</h2><div id="rconf">{"".join(recap_row(x, k + 1) for k, x in enumerate(conf)) or "<div class=rmeta>Nicio știre în ultimele 7 zile.</div>"}</div></div>'
            f'<div class="rc"><h2>Zvonuri de urmărit</h2><div id="roth">{"".join(recap_row(x) for x in other) or "<div class=rmeta>Niciun zvon în ultimele 7 zile.</div>"}</div></div>'
            f'</div><div>'
            f'<div class="rc"><h2>Jocurile săptămânii · postări</h2><div class="hbars" id="rgames">{recap_games(wk)}</div></div>'
            f'<div class="rc"><h2>Steal An Egg · vârful zilnic de jucători</h2><div id="rchart"><div class="rmeta">Se încarcă graficul…</div></div>'
            f'<div class="rmeta" id="rcmeta"></div><div class="rmeta">Măsurat de noi din API-ul Roblox (GitHub Action, de obicei la câteva ore). Vârful zilei e cel mai mare număr pe care l-am prins noi, nu neapărat vârful real. Momentan urmărim doar Steal An Egg.</div></div>'
            f'<div class="rc"><h2>Card 9:16 pentru TikTok / Shorts</h2><div class="rcard"><img id="rcimg" alt="Previzualizare card 9:16 cu rezumatul săptămânii VEXU HQ" width="1080" height="1920">'
            f'<a class="btn pri" id="rcdl" href="#" aria-disabled="true">Descarcă PNG (1080×1920)</a><div class="rmeta">Cardul se generează pe telefonul tău, din datele de mai sus.</div></div></div>'
            f'</div></div>'
            f'<div class="acts"><a class="btn" href="blog.html">Toate știrile</a></div>{CTA}'
            '<noscript><p class="rsub">Activează JavaScript pentru grafic și cardul 9:16.</p></noscript>')
    html_ = page('Rezumatul săptămânii · VEXU HQ', body, RECAP_JS, 'recap')
    open(os.path.join(D, 'recap.html'), 'w', encoding='utf-8').write(html_)
    print(f'recap.html: {len(wk)} postări în {keys[0]}…{keys[-1]}; top: ' + ' | '.join(recap_title(x) or x['title'] for x in conf))

def sync_index():
    """index.html e static (cu JS propriu): îi sincronizăm doar <head>-ul de stil și header-ul/nav-ul, ca să fie identice cu restul paginilor.
    Markere: <!--css-->…<!--/css--> (în <head>) și <!--nav-->…<!--/nav--> (imediat după <body>)."""
    f = os.path.join(D, 'index.html')
    t = open(f, encoding='utf-8').read()
    t = re.sub(r'<!--css-->.*?<!--/css-->', lambda m: '<!--css-->' + CSS_LINK + '<!--/css-->', t, count=1, flags=re.S)
    t = re.sub(r'<!--ev-->.*?<!--/ev-->', lambda m: '<!--ev-->' + EVENTS_SRC + '<!--/ev-->', t, count=1, flags=re.S)
    t = re.sub(r'<!--nav-->.*?<!--/nav-->', lambda m: '<!--nav-->' + header('index') + '<!--/nav-->', t, count=1, flags=re.S)
    open(f, 'w', encoding='utf-8').write(t)

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
    sync_index()
    print('recap.html / blog.html / calendar.html / posts-index.json / calendar-events.json OK')

if __name__ == '__main__':
    main()
