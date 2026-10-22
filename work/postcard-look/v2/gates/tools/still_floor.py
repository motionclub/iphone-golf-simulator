"""AREA U (2026-10-04): window statistics of the user's target stills (needle.jpg / split.jpg / crater.jpg), measured with Pillow (system python3, no numpy).
The statistic is the verifier's own (postcard_look_verify.window_sd): luminance (Rec. 709 weights on the STORED sRGB values 0..1) standard deviation of every
non-overlapping w x w window of a crop. Output: v2/gates/calib/still_floor.txt + still_floor.json (the floors the verifier uses, with their provenance).
usage: python3 still_floor.py"""
import json, math, os, sys
from PIL import Image
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
OUT = R + "/work/postcard-look/v2/gates/calib"
CROPS = {   # clean MOWN grass only (no rock, sand, ball, flag): (x0, y0, x1, y1) in the 1280 x 720 stills
    "needle.jpg": {"mid_green": (770, 265, 930, 310), "top_green": (885, 62, 1055, 95)},
    "split.jpg": {"upper_green": (655, 112, 790, 150), "lower_green": (600, 575, 700, 640), "fairway_strip": (862, 235, 898, 328),
                  "fairway_long": (842, 165, 878, 228), "lower_fairway": (735, 475, 815, 535)},
    "crater.jpg": {"pillar_green": (800, 352, 990, 418), "tee_box_a": (140, 462, 200, 512), "tee_box_b": (245, 462, 296, 512), "fairway_mid": (540, 238, 610, 275)},
}
WINDOWS = (8, 12, 16, 24, 32)

def lum_grid(im, box):
    c = im.crop(box)
    w, h = c.size
    px = list(c.getdata())
    return w, h, [(0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0 for r, g, b in px], px

def window_sds(w, h, L, win):
    out = []
    for y0 in range(0, h - win + 1, win):
        for x0 in range(0, w - win + 1, win):
            vals = [L[(y0 + j) * w + x0 + i] for j in range(win) for i in range(win)]
            m = sum(vals) / len(vals)
            out.append(math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals)))
    return out

def pct(a, q):
    s = sorted(a)
    if not s:
        return float("nan")
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return s[lo] + (s[hi] - s[lo]) * (k - lo)

def hsv(rgb):
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(*[c / 255.0 for c in rgb])
    return h * 360, s, v

def main():
    rows, lines = [], []
    for f, cs in CROPS.items():
        im = Image.open(f"{R}/ArtDir/environments/refs/{f}").convert("RGB")
        lines.append(f"{f} size {im.size[0]}x{im.size[1]}")
        for n, box in cs.items():
            w, h, L, px = lum_grid(im, box)
            mean = [sum(p[i] for p in px) / len(px) for i in range(3)]
            hh, ss, vv = hsv(mean)
            row = dict(still=f, crop=n, box=box, size=[w, h], mean_rgb=[round(x) for x in mean], hue=round(hh), s=round(ss, 2), v=round(vv, 2), global_sd=round(math.sqrt(sum((x - sum(L) / len(L)) ** 2 for x in L) / len(L)), 4), win={})
            txt = []
            for win in WINDOWS:
                s = window_sds(w, h, L, win)
                if len(s) < 4:
                    continue
                row["win"][win] = dict(n=len(s), med=round(pct(s, 50), 4), p10=round(pct(s, 10), 4), p90=round(pct(s, 90), 4), ge03=round(sum(1 for x in s if x >= 0.03) / len(s), 2))
                txt.append(f"w{win}: n {len(s)} med {pct(s, 50):.4f} p10 {pct(s, 10):.4f} p90 {pct(s, 90):.4f} ge.03 {sum(1 for x in s if x >= 0.03) / len(s):.0%}")
            rows.append(row)
            lines.append(f"  {n:14s} {w}x{h} mean {row['mean_rgb']} h{row['hue']} S{row['s']} V{row['v']} global sd {row['global_sd']} | " + " | ".join(txt))
    os.makedirs(OUT, exist_ok=True)
    with open(OUT + "/still_floor_crops.txt", "w") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(OUT + "/still_floor_crops.json", "w") as fh:
        json.dump(rows, fh, indent=1)
    print("\n".join(lines))
    for win in WINDOWS:
        p10s = [r["win"][win]["p10"] for r in rows if win in r["win"]]
        meds = [r["win"][win]["med"] for r in rows if win in r["win"]]
        print(f"WINDOW {win:2d}px: min over {len(p10s)} mown-grass crops of p10 = {min(p10s):.4f}, of median = {min(meds):.4f}")

main()
