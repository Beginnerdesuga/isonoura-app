#!/usr/bin/env python3
"""気象庁の潮位表（テキスト版）から和歌山(WY)の毎時潮位・満干潮を取得し data/tide.json に保存する。"""
import json, datetime as dt, urllib.request
from pathlib import Path

STN, NAME = "WY", "和歌山"
ROOT = Path(__file__).resolve().parent.parent
BASES = [
    "https://www.data.jma.go.jp/gmd/kaiyou/data/db/tide/suisan/txt/{y}/{s}.txt",
    "https://www.data.jma.go.jp/kaiyou/data/db/tide/suisan/txt/{y}/{s}.txt",
]

def get(year):
    for b in BASES:
        try:
            with urllib.request.urlopen(b.format(y=year, s=STN), timeout=60) as r:
                return r.read().decode("ascii", "ignore")
        except Exception as e:
            print("fail", b.format(y=year, s=STN), e)
    return None

def num(s):
    try: return int(s)
    except ValueError: return None

def tides(seg):
    out = []
    for k in range(4):
        t, h = seg[k*7:k*7+4], seg[k*7+4:k*7+7]
        if t.strip() and t != "9999" and h != "999":
            out.append([f"{t[:2]}:{t[2:]}", int(h)])
    return out

today = dt.date.today() + dt.timedelta(hours=0)
lo, hi = today - dt.timedelta(days=1), today + dt.timedelta(days=10)
days = {}
for y in sorted({lo.year, hi.year}):
    txt = get(y)
    if not txt: continue
    for line in txt.splitlines():
        if len(line) < 136 or line[78:80] != STN: continue
        try:
            d = dt.date(2000 + int(line[72:74]), int(line[74:76]), int(line[76:78]))
        except ValueError:
            continue
        if not (lo <= d <= hi): continue
        days[d.isoformat()] = {
            "h": [num(line[i*3:i*3+3]) for i in range(24)],
            "hi": tides(line[80:108]), "lo": tides(line[108:136]),
        }
if not days:
    raise SystemExit("潮位データを取得できませんでした")
(ROOT / "data" / "tide.json").write_text(
    json.dumps({"station": NAME, "days": days}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("days:", len(days))
