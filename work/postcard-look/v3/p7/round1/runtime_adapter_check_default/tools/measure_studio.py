#!/usr/bin/env python3
"""POSTCARD_LOOK area I (repair round 1): the same 9 Game-view stills under HeroBaseStudioURP (GOLF_STILLS_PIPELINE, in memory) vs the stills under the active asset.
usage: python3 measure_studio.py      (system python3: numpy + Pillow)  -> proof/studio_compare.json, prints the table
Reads ArtDir/.../look/hole0N_k_*.png + stills_stats.json  and  proof/stills_studio/*.png + stills_studio/stills_stats.json.
Numbers only (no threshold is relaxed anywhere): per still mean |diff| per channel, share of pixels with a summed channel difference > 8, the central-lower-third hue / S / V of the studio frame
(the user's line 1: fairway / green h64-73) and the lava band share of the crater stills under the studio asset.
"""
import json, math, os
import numpy as np
from PIL import Image

R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
A = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v3/p7/round1/runtime_adapter_check_default/stills'
B = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v3/p7/round1/runtime_adapter_check_default/stills_studio'
NAMES = ["hole08_1_tee", "hole08_2_approach", "hole08_3_arch", "hole09_1_tee", "hole09_2_approach", "hole09_3_ruin", "hole10_1_tee", "hole10_2_approach", "hole10_3_lavarim"]


def hsv(a):
    a = a.astype(np.float64) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-9
    rm = m & (mx == r); gm = m & (mx == g) & ~rm; bm = m & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6; h[gm] = (b - r)[gm] / d[gm] + 2; h[bm] = (r - g)[bm] / d[bm] + 4
    return h * 60.0, np.where(mx > 1e-9, d / np.maximum(mx, 1e-9), 0.0), mx


def main():
    if not os.path.exists(B + "/stills_stats.json"):
        print("NOT MEASURED: no stills_studio (run_proof.sh studio)")
        json.dump({"measured": False}, open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v3/p7/round1/runtime_adapter_check_default/studio_compare.json', "w"))
        return 1
    sa = {s["name"]: s for s in json.load(open(A + "/stills_stats.json"))["shots"]}
    sb_all = json.load(open(B + "/stills_stats.json"))
    sb = {s["name"]: s for s in sb_all["shots"]}
    out = dict(measured=True, pipeline=sb_all.get("pipeline"), pipeline_active=json.load(open(A + "/stills_stats.json")).get("pipeline"), shots={})
    for n in NAMES:
        a = np.asarray(Image.open(f"{A}/{n}.png").convert("RGB")).astype(int)
        b = np.asarray(Image.open(f"{B}/{n}.png").convert("RGB")).astype(int)
        d = np.abs(a - b)
        row = dict(mean_abs_diff_per_channel=round(float(d.mean()), 3), share_sum_diff_gt8=round(float((d.sum(-1) > 8).mean()), 4),
                   signed_mean_studio_minus_active=[round(float(x), 2) for x in (b - a).mean((0, 1))])
        c = sb[n]["central_lower_third"]
        row["studio_central_lower_third_hsv"] = c["mean_hsv"]
        row["active_central_lower_third_hsv"] = sa[n]["central_lower_third"]["mean_hsv"]
        if n.startswith("hole10"):
            h, s, v = hsv(b.astype(np.uint8))
            lava = (h >= 8) & (h <= 28) & (s >= 0.75) & (v >= 0.7)
            hh, ss, vv = hsv(a.astype(np.uint8))
            lava_a = (hh >= 8) & (hh <= 28) & (ss >= 0.75) & (vv >= 0.7)
            row["lava_band_px_studio"] = int(lava.sum()); row["lava_band_px_active"] = int(lava_a.sum())
        out["shots"][n] = row
    out["max_mean_abs_diff"] = max(r["mean_abs_diff_per_channel"] for r in out["shots"].values())
    out["max_share_gt8"] = max(r["share_sum_diff_gt8"] for r in out["shots"].values())
    out["grass_hue_studio"] = {n: out["shots"][n]["studio_central_lower_third_hsv"][0] for n in NAMES if "tee" in n or "approach" in n}
    json.dump(out, open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v3/p7/round1/runtime_adapter_check_default/studio_compare.json', "w"), indent=1)
    for n, r in out["shots"].items():
        print(f"{n}: mean|d| {r['mean_abs_diff_per_channel']} share>8 {r['share_sum_diff_gt8'] * 100:.2f}%  signed {r['signed_mean_studio_minus_active']}  grass hsv studio {r['studio_central_lower_third_hsv']} vs active {r['active_central_lower_third_hsv']}")
    print(f"STUDIO max mean|d| {out['max_mean_abs_diff']}, max share>8 {out['max_share_gt8'] * 100:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
