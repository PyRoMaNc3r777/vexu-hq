import json,urllib.request,datetime,os
U=10563114921;EID="2469722483213861487"
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"vexu-hq"}),timeout=15))
old={}
try: old=json.load(open("data.json"))
except: pass
d={"updated":datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
    g=get(f"https://games.roblox.com/v1/games?universeIds={U}")["data"][0]
    d["game"]={"name":g["name"],"playing":g["playing"],"visits":g["visits"],"source":"roblox_api","fetched":d["updated"]}
except Exception as e:
    d["game"]=old.get("game"); d["gameError"]=str(e)
ev={"start":"2026-10-17T15:00:00Z","end":"2026-10-24T14:00:00Z","source":"fallback"}
try:
    for e in get(f"https://apis.roblox.com/virtual-events/v1/universes/{U}/virtual-events?limit=100")["data"]:
        if e["id"]==EID: ev={"title":e["title"],"start":e["eventTime"]["startUtc"],"end":e["eventTime"]["endUtc"],"source":"roblox_api"}
except Exception as e:
    if old.get("event"): ev=old["event"]
d["event"]=ev
d["team"]=json.load(open("team.json")) if os.path.exists("team.json") else []
json.dump(d,open("data.json.tmp","w"),ensure_ascii=False,indent=1);os.replace("data.json.tmp","data.json")

# history.json: un punct real per rulare (doar dacă API-ul Roblox a răspuns acum), păstrăm ultimele 48h, JSON compact
# format: {"v":1,"points":[{"t":"<ISO UTC>","p":<jucători>,"v":<vizite>}, ...]}
H="history.json";KEEP=48*3600
try: h=json.load(open(H))
except Exception: h={}
pts=[x for x in h.get("points",[]) if isinstance(x,dict) and "t" in x and "p" in x]
if "gameError" not in d and d.get("game"):
    pt={"t":d["updated"][:19]+"Z","p":d["game"]["playing"]}
    if isinstance(d["game"].get("visits"),int): pt["v"]=d["game"]["visits"]
    pts.append(pt)
now=datetime.datetime.now(datetime.timezone.utc)
def age(x):
    try: return (now-datetime.datetime.fromisoformat(x["t"].replace("Z","+00:00"))).total_seconds()
    except Exception: return KEEP+1
pts=sorted([x for x in pts if age(x)<=KEEP],key=lambda x:x["t"])
json.dump({"v":1,"points":pts},open(H+".tmp","w"),separators=(",",":"));os.replace(H+".tmp",H)

# player-history.json: vârful zilnic de jucători Steal An Egg (zi = Europe/Bucharest), DOAR din măsurătorile noastre
# (rularea curentă + punctele noastre din history.json), păstrăm ~30 de zile. Nu se completează nimic din alte surse.
# format: {"v":1,"tz":"Europe/Bucharest","updated":"<ISO UTC>","days":{"YYYY-MM-DD":{"peak":<jucători>,"t":"<ISO UTC al vârfului>","n":<măsurători>}}}
from zoneinfo import ZoneInfo
PH="player-history.json";RO=ZoneInfo("Europe/Bucharest");KEEPD=30
try: ph=json.load(open(PH))
except Exception: ph={}
days={k:v for k,v in (ph.get("days") or {}).items() if isinstance(v,dict) and isinstance(v.get("peak"),int)}
seen=set(ph.get("_seen") or [])
def rday(t): return datetime.datetime.fromisoformat(t.replace("Z","+00:00")).astimezone(RO).date().isoformat()
for x in pts:
    if not isinstance(x.get("p"),int) or x["t"] in seen: continue
    seen.add(x["t"]); k=rday(x["t"]); e=days.get(k)
    if e is None: days[k]={"peak":x["p"],"t":x["t"],"n":1}
    else:
        e["n"]=e.get("n",0)+1
        if x["p"]>e["peak"]: e["peak"]=x["p"];e["t"]=x["t"]
today=now.astimezone(RO).date()
cut=(today-datetime.timedelta(days=KEEPD-1)).isoformat()
days={k:days[k] for k in sorted(days) if k>=cut}
seen={t for t in seen if age({"t":t})<=KEEP}  # doar ca să nu numărăm de 2 ori punctele din fereastra de 48h
# puncte manuale (player-history-manual.json, sursa de adevăr) — copiate ca atare, niciodată tăiate/suprascrise
man=[]
try: man=[m for m in json.load(open("player-history-manual.json")).get("manual",[]) if isinstance(m,dict) and isinstance(m.get("p"),int) and "t" in m]
except Exception: man=[m for m in (ph.get("manual") or []) if isinstance(m,dict)]  # dacă fișierul lipsește, păstrăm ce era
json.dump({"v":1,"tz":"Europe/Bucharest","updated":now.isoformat(timespec="seconds").replace("+00:00","Z"),"days":days,"manual":man,"_seen":sorted(seen)},
          open(PH+".tmp","w"),separators=(",",":"));os.replace(PH+".tmp",PH)
