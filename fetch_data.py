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
