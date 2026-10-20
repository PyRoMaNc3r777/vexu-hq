#!/usr/bin/env python3
"""Detectare automată a jocului (câmpul "joc") din titlu / events / text.
Conservator: dacă e ambiguu (mai multe jocuri diferite), întoarce '' (fără joc)."""
import re, unicodedata

PLATFORM = 'Roblox (platformă)'

# (nume canonic, regex) — ordinea contează doar pentru suprapuneri; numele lungi se verifică primele
GAMES = [
    ('Break and Steal an Egg', r'break and steal an egg'),
    ('Steal An Egg', r'steal an? egg|\bsae\b|halloween dimension|dimensiunea de halloween|phantom express'),
    ('Blox Fruits', r'blox fruits|blox bulletin'),
    ('BedWars', r'bed ?wars'),
    ('Dress to Impress', r'dress to impress|\bdti\b'),
    ('Murder Mystery 2', r'murder mystery 2|\bmm2\b'),
    ('Murder Duels', r'murder duels'),
    ('Animal Hospital', r'animal hospital'),
    ('Dark Deception: Hunted', r'dark deception'),
    ('Pet Simulator 99', r'pet simulator 99|\bps99\b'),
    ('Grow a Garden', r'grow a garden'),
    ('Brookhaven', r'brookhaven'),
    ('Piggy', r'\bpiggy\b'),
    ('DOORS', r'\bdoors\b'),
    ('Adopt Me', r'adopt me'),
    ('99 Nights in the Forest', r'99 nights'),
    ('Fisch', r'\bfisch\b|fischfright'),
    ('Fish It', r'\bfish it\b'),
    ("Dandy's World", r"dandy'?s world"),
    ('RIVALS', r'\brivals(ween)?\b'),
    ('Bloxburg', r'bloxburg'),
    ('Evade', r'\bevade\b'),
    ('Creatures of Sonaria', r'creatures of sonaria'),
    ('Jujutsu Shenanigans', r'jujutsu shenanigans'),
    ('Tower Defense Simulator', r'tower defense simulator|\btds\b'),
    ('Ride A Pet', r'ride a pet'),
    ('Grand Piece Online', r'grand piece online|\bgpo\b'),
    ('Violence District', r'violence district'),
    ('The Strongest Battlegrounds', r'strongest battlegrounds'),
    ('Arsenal', r'(?<!the )(?<!„the )\barsenal\b'),
    ('Huss Valley', r'huss valley'),
    ('Sell Fries!', r'sell fries'),
    ('Bubble Gum Simulator INFINITY', r'bubble gum simulator'),
    ('Hunty Zombie', r'hunty zombie'),
    ('Plants vs Brainrots', r'plants vs\.? brainrots'),
    ('Prospecting', r'\bprospecting\b'),
    ('Restaurant Tycoon 3', r'restaurant tycoon'),
    ('Tales of Tanorio', r'tales of tanorio'),
    ('Forsaken', r'\bforsaken\b'),
    ('Dead Rails', r'dead rails'),
    ('+1 Speed Keyboard Escape', r'keyboard escape'),
    ('Vista Springs', r'vista springs'),
    ('Car Dealership Tycoon', r'car dealership tycoon'),
    ('Volleyball Legends', r'volleyball legends'),
    ('Regretevator', r'regretevator'),
    ('Tower Blitz', r'tower blitz'),
    ("Asimo's Dodgeball", r"asimo'?s dodgeball"),
    ('The Forge', r'\bthe forge\b'),
]
# alias-uri pentru events[].game → nume canonic
ALIAS = {'hunted (dark deception)': 'Dark Deception: Hunted', 'roblox': PLATFORM}

# știri despre platformă / companie / Studio / politici (doar dacă NU s-a găsit un joc anume)
PLATFORM_RE = (r'roblox studio|\bstudio\b|creator analytics|creator showdown|\bugc\b|\brobux\b|rate limit|\bapi\b|'
               r'termenii|terms of use|quick words|toolbox|asset manager|package overrides|the hollow|squashbuckler|'
               r'iteme(le)? de avatar|publicarea jocurilor|roblox (simplifică|scoate|lucrează|își schimbă|pregătește)|'
               r'^\W*roblox:|arizona')

def _n(s):
    s = unicodedata.normalize('NFD', s or '')
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    return s.replace('’', "'").replace('‘', "'")

_URL = re.compile(r'https?://\S+')

def _games_in(text):
    t = _URL.sub(' ', _n(text))
    found = []
    for name, rx in GAMES:
        if re.search(rx, t):
            if name == 'Steal An Egg' and 'break and steal an egg' in t and not re.search(rx, t.replace('break and steal an egg', ' ')):
                continue  # „Steal an Egg” apare doar în „Break and Steal an Egg”
            found.append(name)
    return found

def canon(name):
    n = (name or '').strip()
    if not n:
        return ''
    if _n(n) in ALIAS:
        return ALIAS[_n(n)]
    for g, rx in GAMES:
        if _n(g) == _n(n) or re.search(rx, _n(n)):
            return g
    return n

def detect(p):
    """Întoarce numele jocului sau '' dacă nu e clar."""
    title = p.get('titlu', '')
    tg = _games_in(title)
    if len(tg) == 1:
        return tg[0]
    if len(tg) > 1:
        return ''
    evg = {canon(e.get('game')) for e in p.get('events', []) if e.get('game')}
    evg.discard('')
    if len(evg) == 1:
        return evg.pop()
    if len(evg) > 1:
        return ''
    if re.search(PLATFORM_RE, _n(title)):
        return PLATFORM
    body = ' '.join([p.get('text', ''), p.get('confirmat', ''), ' '.join(p.get('zvon', []) if isinstance(p.get('zvon'), list) else [p.get('zvon', '')])])
    # în TREND SHORTS, „Ideea VEXU: …” e adaptarea noastră (de obicei pe Steal An Egg), nu subiectul postării
    body = re.split(r'ideea vexu', _n(body))[0]
    bg = _games_in(body)
    if len(bg) == 1:
        return bg[0]
    if len(bg) > 1:
        return ''
    return ''
