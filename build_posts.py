#!/usr/bin/env python3
"""Generează posts/<slug>.html, posts-index.json, posts-search.json, calendar-events.json, blog.html, calendar.html din posts.json.

Utilizare:
  python3 build_posts.py              # rebuild complet
  python3 build_posts.py --append batch.json   # adaugă postări din fișier (array JSON) apoi rebuild

Fiecare post: titlu, text, eticheta (sau listă), img, surse[], date (YYYY-MM-DD).
Opțional: published (ISO +03/+02), featured, section ("shorts"), slug (fixează URL-ul), old_slugs[], events[],
          confirmat/zvon (blocuri separate).
Dacă lipsește published → se completează automat cu ora curentă Europe/Bucharest.
Dacă lipsește date → se ia din published (sau azi).
"""
import json, re, unicodedata, html, os, sys, argparse
from datetime import datetime
from zoneinfo import ZoneInfo

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
    return changed

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
.cal .row{display:grid;grid-template-columns:72px 1fr;gap:12px;align-items:start;margin:14px 0}.cal .ico{width:72px;height:72px;border-radius:14px;object-fit:cover;border:1px solid #ff2bd655;background:#000a}.cal .card{background:#120a22cc;border:1px solid #ff2bd655;border-radius:16px;padding:14px;box-shadow:0 0 18px #ff2bd622}.cal .st{font-weight:800;margin:6px 0;color:#ffd400}.cal .st.live{color:#39ff88;text-shadow:0 0 10px #39ff88}.cal .st.done{color:#9a8fb5}.cal .cd{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}.cal .cd div{background:#000a;border:1px solid #00f0ff66;border-radius:10px;padding:8px 6px;min-width:58px;text-align:center}.cal .cd b{display:block;font-size:1.3em;color:#ff2bd6}.cal .cd span{font-size:.65em;color:#aaa}.cal .meta{color:#9a8fb5;font-size:.85em}.cal a.golink{color:#00f0ff;font-weight:700;text-decoration:none}.note{font-size:.8em;color:#ffd400;margin-top:6px}@media(max-width:520px){.cal .row{grid-template-columns:56px 1fr}.cal .ico{width:56px;height:56px}}"""

CSS_FX = 'h1{background-image:linear-gradient(90deg,#ff2bd6,#00f0ff,#ff7a00,#ff2bd6);background-size:300% auto;-webkit-background-clip:text;background-clip:text;animation:shm 8s linear infinite}h1 .em{color:#fff;-webkit-text-fill-color:#fff;filter:drop-shadow(0 0 8px #ff7a00aa)}@keyframes shm{to{background-position:300% center}}.moon{position:fixed;top:-46px;right:-46px;width:150px;height:150px;border-radius:50%;background:radial-gradient(circle at 38% 38%,#fff8de,#ffd27a 42%,#ff8a1f 70%,#ff7a0000 72%);box-shadow:0 0 70px 24px #ff7a0033;opacity:.28;pointer-events:none;z-index:0;animation:mn 6s ease-in-out infinite}@keyframes mn{50%{opacity:.45}}@media(min-width:768px){.moon{top:-30px;right:-30px;width:220px;height:220px}}@media(prefers-reduced-motion:reduce){h1,.moon{animation:none}}'
EMO = re.compile('([\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF][\uFE0F\u200D\U0001F000-\U0001FAFF\u2600-\u27BF]*)')
def emo_h1(body):
    # emoji din <h1> primesc span.em ca să nu fie colorate de gradient (altfel apar ca pătrate)
    return re.sub(r'(<h1[^>]*>)(.*?)(</h1>)', lambda m: m.group(1) + EMO.sub(r'<span class="em">\1</span>', m.group(2)) + m.group(3), body, flags=re.S)

def page(title, body, extra_js=''):
    body = emo_h1(body)
    return (f'<!doctype html><html lang="ro"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)}</title><link rel="icon" type="image/png" href="/vexu-hq/icon.png"><style>\n{CSS}\n{CSS_FX}\n</style></head><body>'
            f'<div class="moon" aria-hidden="true"></div>'
            f'<div class="fx" aria-hidden="true"><span>🎃</span><span>🦇</span><span>👻</span><span>🦇</span><span>🎃</span><span>🕸️</span></div>'
            f'<div class="w">{body}</div>{extra_js}</body></html>\n')

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
            '<a href="calendar.html">📅 Calendar Halloween</a></nav>')
NAV_POST = ('<nav><a href="../blog.html">← Blog</a><a href="../calendar.html">📅 Calendar</a>'
            '<a href="../index.html">⚡ Dashboard</a></nav>')

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
// hash: #f=<eticheta>&q=<căutare>
function parseHash(){const h=(location.hash||'').replace(/^#/,''); const o={f:'toate',q:''};
  h.split('&').forEach(kv=>{const i=kv.indexOf('='); if(i<0)return; const k=kv.slice(0,i); let v=kv.slice(i+1); try{v=decodeURIComponent(v.replace(/\+/g,' '))}catch(e){}
    if(k==='f'&&/^[\w-]+$/.test(v)) o.f=v; if(k==='q') o.q=v;}); return o}
function setHash(){const parts=[]; if(filter!=='toate') parts.push('f='+filter); if(q.trim()) parts.push('q='+encodeURIComponent(q.trim()));
  const h=parts.length?'#'+parts.join('&'):''; if((location.hash||'')!==h) history.replaceState(null,'',h||location.pathname+location.search)}
let ALL=[], FILTERS=[{id:'toate',label:'Toate'}], shown=0, filter='toate', q='', SEARCH=null, sLoading=false;
// lista de etichete derivată din date (posts-index.json ← posts.json), ordonată după numărul de postări
function buildFilters(){const m=new Map(); ALL.forEach(p=>(p.labels||[]).forEach(l=>{const id=fid(l); if(!id)return; const x=m.get(id)||{id,label:l,n:0}; x.n++; m.set(id,x)}));
  FILTERS=[{id:'toate',label:'Toate'}].concat([...m.values()].sort((a,b)=>b.n-a.n||a.label.localeCompare(b.label,'ro')))}
function validFilter(){if(!FILTERS.some(f=>f.id===filter)) filter='toate'}
function terms(){return norm(q).split(/\s+/).filter(Boolean)}
function hay(p){if(p._h===undefined||(SEARCH&&!p._full)){p._full=!!SEARCH; p._h=norm(p.title+' '+(p.excerpt||'')+' '+(p.labels||[]).join(' ')+' '+((SEARCH&&SEARCH[p.slug])||''))} return p._h}
function qmatch(p,t){return !t.length||t.every(w=>hay(p).includes(w))}
function fmatch(p,f){return f==='toate'||(p.labels||[]).some(l=>fid(l)===f)}
function loadSearch(){if(SEARCH||sLoading)return; sLoading=true;
  fetch('posts-search.json?'+Date.now()).then(r=>r.json()).then(d=>{SEARCH=d; if(q.trim()) paint()}).catch(()=>{sLoading=false})}
function chipsHtml(labels,date){return labels.map(l=>`<span class="l ${cls(l)}">${es(l)}</span>`).join(' ')+`<span class="dt">📅 ${es(date)}</span>`}
function cardHtml(p, feat){
  return `<a class="p${feat?' feat':''}" href="posts/${es(p.slug)}.html"><img src="${es(p.img)}" alt="" loading="lazy"><div class="b">${chipsHtml(p.labels,p.dateRo)}<h2>${es(p.title)}</h2><div>${es(p.excerpt)}</div><div class="more">Citește tot →</div></div></a>`;
}
function renderFilters(t){
  const base=ALL.filter(p=>qmatch(p,t));
  document.getElementById('filters').innerHTML=FILTERS.map(f=>`<button type="button" class="chip${filter===f.id?' on':''}" data-f="${es(f.id)}" aria-pressed="${filter===f.id}">${es(f.label)}<span class="n">(${base.filter(p=>fmatch(p,f.id)).length})</span></button>`).join('');
  document.querySelectorAll('#filters .chip').forEach(b=>b.onclick=()=>{filter=b.dataset.f; setHash(); shown=0; paint()});
}
function paint(){
  const t=terms();
  renderFilters(t);
  const ok=p=>fmatch(p,filter)&&qmatch(p,t);
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
  if(!feat && !slice.length) html=t.length?`<div class="empty">Nicio știre găsită pentru „${es(q.trim())}”${filter!=='toate'?' pe filtrul ăsta':''}.</div>`:'<div class="empty">Nicio postare pe filtrul ăsta.</div>';
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
({f:filter,q}=parseHash()); qi.value=q; if(q) loadSearch();
fetch('posts-index.json?'+Date.now()).then(r=>r.json()).then(data=>{
  ALL=data.posts||data; buildFilters(); validFilter(); paint();
}).catch(err=>{document.getElementById('feed').innerHTML='<div class="empty">Nu pot încărca indexul.</div>'});
window.addEventListener('hashchange',()=>{({f:filter,q}=parseHash()); qi.value=q; if(q) loadSearch(); validFilter(); shown=0; paint()});
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
      <div style="margin-top:8px"><a class="golink" href="posts/${es(ev.slug)}.html">Vezi postarea →</a></div>
    </div></div>`;
  }).join('');
}
fetch('calendar-events.json?'+Date.now()).then(r=>r.json()).then(d=>{EVENTS=d.events||d; paint(); setInterval(paint,1000)}).catch(()=>{document.getElementById('cal').innerHTML='<div class="empty">Nu pot încărca calendarul.</div>'});
</script>
"""

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
                f'<h1 style="text-align:left;font-size:1.6em">{e(p["titlu"])}</h1>'
                f'<div class="txt">{txt}</div><div class="s">Surse:{src}</div></div></div>'
                f'<a class="btn" href="../blog.html">← Înapoi la blog</a>')
        open(os.path.join(D, 'posts', s + '.html'), 'w', encoding='utf-8').write(page(p['titlu'] + ' · VEXU HQ', body))
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
        }
        index_items.append(item)
        search[s] = search_text(p)
        for ev in p.get('events', []):
            ce = dict(ev)
            ce['slug'] = s
            ce['img'] = p['img']
            ce['post_title'] = p['titlu']
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

def build_blog():
    noscript = '<noscript><p style="text-align:center;color:#9a8fb5">Activează JavaScript pentru feed-ul grupat pe zile. Postările individuale rămân în <code>posts/</code>.</p></noscript>'
    body = (f'<h1>📰 VEXU HQ · Știri</h1>{NAV_BLOG}'
            f'<div class="shorts-entry"><button type="button" id="shortsBtn">🔥 Ce merge în Shorts</button></div>'
            f'<form class="srch" id="qform" role="search"><input type="search" id="q" placeholder="Caută în știri…" aria-label="Caută în știri" autocomplete="off" enterkeyhint="search"><button type="button" id="qx" aria-label="Șterge căutarea">✕</button></form>'
            f'<div class="qinfo" id="qinfo" aria-live="polite"></div>'
            f'<div class="filters" id="filters"></div>'
            f'<div id="featSlot"></div><div id="feed"></div>'
            f'<div id="moreWrap"><button type="button" class="btn" id="moreBtn" style="display:none">Vezi mai multe</button></div>'
            f'{noscript}')
    open(os.path.join(D, 'blog.html'), 'w', encoding='utf-8').write(page('VEXU HQ · Știri', body, BLOG_JS))

def build_calendar():
    body = (f'<h1>📅 Calendar Halloween</h1>{NAV_BLOG}'
            f'<p style="text-align:center;color:#9a8fb5">Doar ferestre CONFIRMAT din blog · ora României · countdown live</p>'
            f'<div class="cal" id="cal">Se încarcă…</div>')
    open(os.path.join(D, 'calendar.html'), 'w', encoding='utf-8').write(page('Calendar Halloween · VEXU HQ', body, CAL_JS))

def append_batch(path):
    batch = json.load(open(path, encoding='utf-8'))
    if isinstance(batch, dict):
        batch = [batch]
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
    build_post_pages(posts)
    build_blog()
    build_calendar()
    print('blog.html / calendar.html / posts-index.json / calendar-events.json OK')

if __name__ == '__main__':
    main()
