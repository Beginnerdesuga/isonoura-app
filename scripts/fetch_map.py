#!/usr/bin/env python3
"""Open-Meteo から波高マップ用データを取得して data/map-data.json に保存する。
GitHub Actions から定期実行する想定（標準ライブラリのみ）。"""
import json, time, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cfg = json.loads((ROOT / "data" / "map-config.json").read_text(encoding="utf-8"))
g = cfg["grid"]
DAYS = cfg.get("days", 3)

def frange(a, b, s):
    n = int(round((b - a) / s))
    return [round(a + i * s, 4) for i in range(n + 1)]

lats = frange(g["lat0"], g["lat1"], g["step"])
lons = frange(g["lon0"], g["lon1"], g["step"])
points = [(la, lo) for la in lats for lo in lons]

def get(url):
    for k in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if k == 2:
                raise
            time.sleep(5)

def as_list(j):
    return j if isinstance(j, list) else [j]

def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]

def r1(v, n):
    return None if v is None else round(v, n)

grid, times = [], None
for ch in chunks(points, 40):
    q = urllib.parse.urlencode({
        "latitude": ",".join(str(p[0]) for p in ch),
        "longitude": ",".join(str(p[1]) for p in ch),
        "hourly": "wave_height,wave_direction",
        "timezone": "Asia/Tokyo",
        "forecast_days": DAYS,
    }, safe=",")
    res = as_list(get("https://marine-api.open-meteo.com/v1/marine?" + q))
    for (la, lo), item in zip(ch, res):
        h = item["hourly"]
        times = times or h["time"]
        grid.append({
            "lat": la, "lon": lo,
            "h": [r1(v, 2) for v in h["wave_height"]],
            "d": [None if v is None else int(round(v)) for v in h["wave_direction"]],
        })
    time.sleep(1)

spots = cfg["spots"]
q = urllib.parse.urlencode({
    "latitude": ",".join(str(s["lat"]) for s in spots),
    "longitude": ",".join(str(s["lon"]) for s in spots),
    "hourly": "wind_speed_10m,wind_direction_10m",
    "wind_speed_unit": "ms",
    "timezone": "Asia/Tokyo",
    "forecast_days": DAYS,
}, safe=",")
wres = as_list(get("https://api.open-meteo.com/v1/forecast?" + q))
wind = [{
    "wspd": [r1(v, 1) for v in w["hourly"]["wind_speed_10m"]],
    "wdir": [None if v is None else int(round(v)) for v in w["hourly"]["wind_direction_10m"]],
} for w in wres]

out = {
    "generated": time.strftime("%Y-%m-%dT%H:%M:%S+09:00", time.gmtime(time.time() + 9 * 3600)),
    "times": times, "grid": grid, "wind": wind,
}
(ROOT / "data" / "map-data.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("points:", len(grid), "hours:", len(times))
