#!/usr/bin/env python3
"""Generează posts/<slug>.html și blog.html din posts.json. Rulează: python3 build_posts.py"""
import json, re, unicodedata, html, os
D = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(D, 'posts.json')
posts = json.load(open(P, encoding='utf-8'))
changed = False
for p in posts:
    if 'date' not in p: p['date'] = '2026-10-14'; changed = True
if changed:
    with open(P, 'w', encoding='utf-8') as f: json.dump(posts, f, ensure_ascii=False, indent=1)

def slug(t):
    a = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', a).strip('-')

LUNI = ['ianuarie','februarie','martie','aprilie','mai','iunie','iulie','august','septembrie','octombrie','noiembrie','decembrie']
def ro_date(d): y, m, dd = map(int, d.split('-')); return f'{dd} {LUNI[m-1]} {y}'

CSS = """@media(min-width:768px){.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.grid .p{margin:0}a.p.feat{display:grid;grid-template-columns:1.3fr 1fr}.feat img{height:100%;min-height:320px}.feat h2{font-size:1.7em}.hero{max-width:1100px;margin:14px auto}.hero .b{max-width:760px;margin:auto;padding:24px}.hero .txt{font-size:1.15em}}@media(min-width:1200px){.grid{grid-template-columns:repeat(3,1fr)}.hero{display:grid;grid-template-columns:1fr 1fr}.hero .hi{padding:16px}.hero img{border-radius:12px}}
*{box-sizing:border-box}body{margin:0;background:#07040f;color:#eee;font-family:system-ui,sans-serif;background-image:radial-gradient(circle at 20% 0,#3b0a5c 0,transparent 50%),radial-gradient(circle at 100% 100%,#002f3d 0,transparent 50%);min-height:100vh}
.w{max-width:1400px;margin:auto;padding:16px}h1{font-size:2em;margin:8px 0;text-align:center;background:linear-gradient(90deg,#ff2bd6,#00f0ff);-webkit-background-clip:text;color:transparent}
nav{text-align:center;margin:8px 0}nav a,.btn{color:#00f0ff;margin:0 8px;font-weight:700;text-decoration:none}.btn{display:inline-block;margin:14px 0;padding:10px 16px;border:1px solid #00f0ff;border-radius:12px;box-shadow:0 0 12px #00f0ff55;background:#000a}
.p{background:#120a22cc;border:1px solid #ff2bd655;border-radius:16px;margin:14px 0;overflow:hidden;box-shadow:0 0 18px #ff2bd622}a.p{display:block;color:inherit;text-decoration:none}a.p:hover{border-color:#ff2bd6;box-shadow:0 0 24px #ff2bd666}
.p img{width:100%;height:190px;object-fit:cover;display:block}.hero img{height:auto;max-height:420px}.b{padding:14px}h2{margin:6px 0;font-size:1.15em}.l{display:inline-block;padding:3px 9px;border-radius:20px;font-size:.72em;font-weight:800}
.dt{color:#9a8fb5;font-size:.8em;margin-left:6px}.txt{font-size:1.05em;line-height:1.55;margin:10px 0}.more{color:#ff7be6;font-weight:700;font-size:.85em;margin-top:8px}
.CONFIRMAT{background:#39ff8822;color:#39ff88;border:1px solid #39ff88}.VEXU-LIVE{background:#ff2bd622;color:#ff2bd6;border:1px solid #ff2bd6;box-shadow:0 0 10px #ff2bd6aa;text-shadow:0 0 6px #ff2bd6}.txt ul{margin:8px 0;padding-left:22px}.txt li{margin:4px 0}.txt a{color:#00f0ff;word-break:break-all}.TREND-SHORTS{background:#00f0ff22;color:#00f0ff;border:1px solid #00f0ff;box-shadow:0 0 10px #00f0ffaa;text-shadow:0 0 6px #00f0ff}.sec{margin:28px 0 6px;font-size:1.5em;color:#00f0ff;text-shadow:0 0 10px #00f0ff}.bx{border-radius:12px;padding:12px 14px;margin:12px 0}.bx h3{margin:0 0 6px;font-size:1em}.bxC{background:#39ff8814;border:1px solid #39ff88;box-shadow:0 0 12px #39ff8833}.bxC h3{color:#39ff88}.bxZ{background:#ffd40014;border:1px solid #ffd400;box-shadow:0 0 12px #ffd40033}.bxZ h3{color:#ffd400}.ZVON{background:#ffd40022;color:#ffd400;border:1px solid #ffd400}.s a{color:#ff7be6;font-size:.8em;word-break:break-all;display:block;margin-top:4px}"""
def page(title, body):
    return f'<!doctype html><html lang="ro"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>\n{CSS}\n</style></head><body><div class="w">{body}</div></body></html>\n'
e = html.escape
def cls(l): return re.sub(r'[^A-Za-z0-9]+', '-', l).strip('-')
def chips(p):
    ls = p['eticheta'] if isinstance(p['eticheta'], list) else [p['eticheta']]
    return ' '.join(f'<span class="l {cls(l)}">{e(l)}</span>' for l in ls)
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
order = sorted(range(len(posts)), key=lambda i: (bool(posts[i].get('featured')), posts[i]['date'], -i), reverse=True)
os.makedirs(os.path.join(D, 'posts'), exist_ok=True)
cards = []
shorts = []
for i in order:
    p = posts[i]; s = slug(p['titlu'])
    lab = f'{chips(p)}<span class="dt">📅 {ro_date(p["date"])}</span>'
    src = ''.join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(u)}</a>' for u in p.get('surse', []))
    def sl(us): return '<div class="s">Sursă:' + ''.join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(u)}</a>' for u in us) + '</div>'
    if 'confirmat' in p or 'zvon' in p:
        txt = ''
        if 'confirmat' in p: txt += f'<div class="bx bxC"><h3>✅ CONFIRMAT</h3><div>{link(p["confirmat"])}</div>{sl(p.get("confirmat_surse", []))}</div>'
        if 'zvon' in p: txt += '<div class="bx bxZ"><h3>⚠️ ZVON</h3><ul>' + ''.join(f'<li>{link(z)}</li>' for z in p['zvon']) + f'</ul>{sl(p.get("zvon_surse", []))}</div>'
    else: txt = rich(p['text'])
    for o in p.get('old_slugs', []):
        open(os.path.join(D, 'posts', o + '.html'), 'w', encoding='utf-8').write(f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={s}.html"><link rel="canonical" href="{s}.html"><a href="{s}.html">Mutat aici →</a>\n')
    body = (f'<nav><a href="../blog.html">← Înapoi la blog</a><a href="../index.html">⚡ Dashboard</a></nav>'
            f'<div class="p hero"><div class="hi"><img src="../{e(p["img"])}" alt=""></div><div class="b">{lab}<h1 style="text-align:left;font-size:1.6em">{e(p["titlu"])}</h1>'
            f'<div class="txt">{txt}</div><div class="s">Surse:{src}</div></div></div>'
            f'<a class="btn" href="../blog.html">← Înapoi la blog</a>')
    open(os.path.join(D, 'posts', s + '.html'), 'w', encoding='utf-8').write(page(p['titlu'] + ' · VEXU HQ', body))
    flat = ' '.join(p['text'].replace('\n- ', ' • ').split())
    short = flat if len(flat) < 140 else flat[:137].rsplit(' ', 1)[0] + '…'
    tgt = shorts if p.get('section') == 'shorts' else cards
    tgt.append(f'<a class="p{" feat" if tgt is cards and not cards else ""}" href="posts/{s}.html"><img src="{e(p["img"])}" alt=""><div class="b">{lab}<h2>{e(p["titlu"])}</h2><div>{e(short)}</div><div class="more">Citește tot →</div></div></a>')
    print('posts/' + s + '.html')
open(os.path.join(D, 'blog.html'), 'w', encoding='utf-8').write(page('VEXU HQ · Știri', '<h1>📰 VEXU HQ · Știri</h1><nav><a href="index.html">← Înapoi la dashboard</a></nav>' + ''.join(cards[:1]) + '<div class="grid">' + ''.join(cards[1:]) + '</div>' + ('<h2 class="sec">🔥 Ce merge în Shorts</h2><div class="grid">' + ''.join(shorts) + '</div>' if shorts else '')))
