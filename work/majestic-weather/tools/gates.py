#!/usr/bin/env python3
"""gates.py <run dir> [<run dir> ...] — summarize MajesticWeatherShots results.json files into gate lines (markdown).
Later runs override earlier ones per key."""
import json, os, sys

res = {}
for d in sys.argv[1:]:
    p = os.path.join(d, "results.json")
    if os.path.exists(p):
        try:
            res.update(json.load(open(p)))
        except Exception as e:
            print(f"<!-- {p}: {e} -->")

def rows(suffix):
    return sorted((k[: -len(suffix)], v) for k, v in res.items() if k.endswith(suffix))

out = []
cost = rows("_cost")
if cost:
    out.append("### WEATHER_COST (pixel GPU at 1080p, interleaved A/B, ms)\n")
    out.append("| slot | clear | Majestic | Δ Majestic | today (legacy) | Δ today | FTM Δ Majestic | result |\n|---|---:|---:|---:|---:|---:|---:|---|")
    for s, v in cost:
        out.append(f"| {s} | {v['pixelClear']:.2f} | {v['pixelMajestic']:.2f} | **{v['deltaMajestic']:+.2f}** | {v['pixelLegacy']:.2f} | {v['deltaLegacy']:+.2f} | {v['ftmDeltaMajestic']:+.2f} | {'PASS' if v['pass'] else 'FAIL'} |")
    out.append(f"\nWEATHER_COST: {'PASS' if all(v['pass'] for _, v in cost) else 'FAIL'} ({sum(v['pass'] for _, v in cost)}/{len(cost)})\n")
read = rows("_read")
if read:
    out.append("### READABILITY\n")
    out.append("| slot | ball contrast (today) | flag contrast (today) | fall layer in corridor (px hit / px) | near drops in corridor | max drops | URP fog ball / flag | result |\n|---|---:|---:|---:|---:|---:|---:|---|")
    for s, v in read:
        ok = v["contrastPass"] and v["corridorPass"] and v["fogPass"]
        f = lambda x: "n/a" if x < 0 else f"{x:.2f}:1"
        out.append(f"| {s} | {f(v['ball'])} ({f(v.get('ballToday', -1))}) | {f(v['flag'])} ({f(v.get('flagToday', -1))}) | {v['corridorHit']} / {v['corridorPx']} | {v['dropsInCorridor']} | {v['maxDrops']} | {v['fogBall']:.3f} / {v['fogFlag']:.3f} | {'PASS' if ok else 'FAIL'} |")
    out.append("")
for k in ("determinism_rules",):
    if k in res:
        out.append(f"DETERMINISM rules: {'PASS' if res[k]['pass'] else 'FAIL ' + ', '.join(res[k]['fails'])}")
tiers = rows("_tiers")
if tiers:
    out.append("DETERMINISM tiers: " + ", ".join(f"{s} {'PASS' if v['pass'] else 'FAIL'} ({v['tiers']} tiers, {v['distinct']} distinct)" for s, v in tiers))
tog = rows("_toggle")
for s, v in tog:
    out.append(f"TOGGLE_RESTORES {s}: off-before vs off-after max diff {v['offVsOffMax']} ({v['offVsOffPixels']} px); off vs unpatched shader max diff {v['offVsUnpatchedMax']} ({v['offVsUnpatchedPixels']} px); on vs off {v['onVsOffPixels']} px -> {'PASS' if v['pass'] else 'FAIL'}")
for s, v in rows("_rally_hold"):
    out.append(f"TENNIS_RALLY_HOLD {s}: precip {v['before']:.2f} -> {v['during']:.3f}, fall layer {v['fallLayer']}, drops {v['drops']}, court wet {v['wet']} -> {'PASS' if v['pass'] else 'FAIL'}")
print("\n".join(out))
