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
