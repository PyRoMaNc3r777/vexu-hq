#!/usr/bin/env python3
"""Backfill o singură dată pentru câmpul "joc" în posts.json (nu schimbă nimic altceva).
Folosește joc_detect.detect(); OVERRIDES = corecții manuale unde detecția automată ar greși.
Postările ambigue primesc "joc": "" (verificate, fără joc)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from joc_detect import detect, PLATFORM
from build_posts import slug, P

OVERRIDES = {  # slug → joc
    'creatorul-mm2-nu-mai-exista-jocuri-roblox-fara-cod-ai': PLATFORM,  # declarație despre toate jocurile Roblox, nu despre MM2
    'zvon-valul-de-banuri-false-ajunge-si-la-kreekcraft': PLATFORM,     # banuri pe platformă
}
TITLE_OVERRIDES = {  # început de titlu → joc
    '📱 ZVON (RTC): pe iPhone, căutarea Roblox': PLATFORM,
}

def main(force=False):
    posts = json.load(open(P, encoding='utf-8'))
    n = 0
    for p in posts:
        if 'joc' in p and not force:
            continue
        s = p.get('slug') or slug(p['titlu'])
        j = OVERRIDES.get(s)
        if j is None:
            j = next((v for k, v in TITLE_OVERRIDES.items() if p['titlu'].startswith(k)), None)
        if j is None:
            j = detect(p)
        p['joc'] = j; n += 1
    with open(P, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=1); f.write('\n')
    print(f'joc completat pe {n} postări')

if __name__ == '__main__':
    main('--force' in sys.argv)
