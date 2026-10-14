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

CSS = """*{box-sizing:border-box}body{margin:0;background:#07040f;color:#eee;font-family:system-ui,sans-serif;background-image:radial-gradient(circle at 20% 0,#3b0a5c 0,transparent 50%),radial-gradient(circle at 100% 100%,#002f3d 0,transparent 50%);min-height:100vh}
.w{max-width:900px;margin:auto;padding:16px}h1{font-size:2em;margin:8px 0;text-align:center;background:linear-gradient(90deg,#ff2bd6,#00f0ff);-webkit-background-clip:text;color:transparent}
nav{text-align:center;margin:8px 0}nav a,.btn{color:#00f0ff;margin:0 8px;font-weight:700;text-decoration:none}.btn{display:inline-block;margin:14px 0;padding:10px 16px;border:1px solid #00f0ff;border-radius:12px;box-shadow:0 0 12px #00f0ff55;background:#000a}
.p{background:#120a22cc;border:1px solid #ff2bd655;border-radius:16px;margin:14px 0;overflow:hidden;box-shadow:0 0 18px #ff2bd622}a.p{display:block;color:inherit;text-decoration:none}a.p:hover{border-color:#ff2bd6;box-shadow:0 0 24px #ff2bd666}
.p img{width:100%;height:190px;object-fit:cover;display:block}.hero img{height:auto;max-height:420px}.b{padding:14px}h2{margin:6px 0;font-size:1.15em}.l{display:inline-block;padding:3px 9px;border-radius:20px;font-size:.72em;font-weight:800}
.dt{color:#9a8fb5;font-size:.8em;margin-left:6px}.txt{font-size:1.05em;line-height:1.55;margin:10px 0}.more{color:#ff7be6;font-weight:700;font-size:.85em;margin-top:8px}
.CONFIRMAT{background:#39ff8822;color:#39ff88;border:1px solid #39ff88}.ZVON{background:#ffd40022;color:#ffd400;border:1px solid #ffd400}.s a{color:#ff7be6;font-size:.8em;word-break:break-all;display:block;margin-top:4px}"""
def page(title, body):
    return f'<!doctype html><html lang="ro"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>\n{CSS}\n</style></head><body><div class="w">{body}</div></body></html>\n'
e = html.escape
order = sorted(range(len(posts)), key=lambda i: (posts[i]['date'], -i), reverse=True)
os.makedirs(os.path.join(D, 'posts'), exist_ok=True)
cards = []
for i in order:
    p = posts[i]; s = slug(p['titlu'])
    lab = f'<span class="l {e(p["eticheta"])}">{e(p["eticheta"])}</span><span class="dt">📅 {ro_date(p["date"])}</span>'
    src = ''.join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(u)}</a>' for u in p.get('surse', []))
    body = (f'<nav><a href="../blog.html">← Înapoi la blog</a><a href="../index.html">⚡ Dashboard</a></nav>'
            f'<div class="p hero"><img src="../{e(p["img"])}" alt=""><div class="b">{lab}<h1 style="text-align:left;font-size:1.6em">{e(p["titlu"])}</h1>'
            f'<div class="txt">{e(p["text"])}</div><div class="s">Surse:{src}</div></div></div>'
            f'<a class="btn" href="../blog.html">← Înapoi la blog</a>')
    open(os.path.join(D, 'posts', s + '.html'), 'w', encoding='utf-8').write(page(p['titlu'] + ' · VEXU HQ', body))
    short = p['text'] if len(p['text']) < 140 else p['text'][:137].rsplit(' ', 1)[0] + '…'
    cards.append(f'<a class="p" href="posts/{s}.html"><img src="{e(p["img"])}" alt=""><div class="b">{lab}<h2>{e(p["titlu"])}</h2><div>{e(short)}</div><div class="more">Citește tot →</div></div></a>')
    print('posts/' + s + '.html')
open(os.path.join(D, 'blog.html'), 'w', encoding='utf-8').write(page('VEXU HQ · Știri', '<h1>📰 VEXU HQ · Știri</h1><nav><a href="index.html">← Înapoi la dashboard</a></nav>' + ''.join(cards)))
