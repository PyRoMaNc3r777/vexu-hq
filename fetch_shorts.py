#!/usr/bin/env python3
"""Citește vizionările reale de pe YouTube pentru Short-urile din shorts.json și le scrie în shorts-views.json.
Nu inventează nimic: dacă o citire eșuează, rămâne valoarea veche (cu data ei veche). Rulează la ~6 ore în GitHub Actions (refresh-shorts.yml)
și poate fi rulat și manual: python3 fetch_shorts.py"""
import json, os, re, sys, time, datetime, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def read_views(vid):
    req = urllib.request.Request("https://www.youtube.com/watch?v=" + vid, headers={
        "User-Agent": UA, "Accept-Language": "en-US,en;q=0.9", "Cookie": "CONSENT=YES+1; SOCS=CAI"})
    page = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
    # viewCount din videoDetails-ul AL ACELUI videoId (nu din videoclipuri recomandate)
    m = re.search(r'"videoDetails":\{"videoId":"' + re.escape(vid) + r'".{0,4000}?"viewCount":"(\d+)"', page, re.S)
    if not m:
        raise ValueError("viewCount negăsit")
    return int(m.group(1))

def main():
    S = json.load(open(os.path.join(HERE, "shorts.json"), encoding="utf-8"))["shorts"]
    out_p = os.path.join(HERE, "shorts-views.json")
    try:
        old = json.load(open(out_p, encoding="utf-8")).get("videos", {})
    except Exception:
        old = {}
    vids = dict(old)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    ok = fail = 0
    for s in S:
        vid = s["id"]
        try:
            v = read_views(vid)
            vids[vid] = {"views": v, "t": now}
            ok += 1
        except Exception as e:
            fail += 1
            print("eșec", vid, e, file=sys.stderr)
        time.sleep(0.8)
    if ok == 0:
        print("nicio citire reușită; nu scriu nimic")
        return 0
    keep = {s["id"] for s in S}
    vids = {k: v for k, v in vids.items() if k in keep}
    json.dump({"v": 1, "source": "YouTube (pagina publică a clipului)", "updated": now, "videos": vids},
              open(out_p + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(out_p + ".tmp", out_p)
    print(f"shorts-views.json: {ok} citite, {fail} eșuate, {len(vids)} în total")
    return 0

if __name__ == "__main__":
    sys.exit(main())
