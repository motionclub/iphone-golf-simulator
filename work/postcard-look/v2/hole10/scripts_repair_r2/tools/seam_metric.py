"""Row-step seam metric (the review's measure): for every row y of a 900x1600 still, the mean over x of |lum[y] - lum[y-1]| (rec.709 luma of 0..255 sRGB values); a hard
texture / material seam shows as one row far above the others. Prints the 5 worst rows over y 200..1500 (below the horizon, ground only) and the ratio worst / median.

  Blender -b --factory-startup --python seam_metric.py -- IMAGE.png [IMAGE2.png ...] [--json OUT.json] [--row Y]

Calibration: the review's Game-view still hole10_1_tee.png (tee pad LK_GREEN | fairway LK_FAIRWAY): row 590 = 16.4 against about 5.5 elsewhere (ratio ~3).
"""
import sys, json, os
import numpy as np
import bpy
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
files = [a for a in args if a.lower().endswith(".png")]
out = args[args.index("--json") + 1] if "--json" in args else None
# repair round 2: the tee kerb (a DRESS_PATH flagstone edge) is a DELIBERATE edge; tee_edge.py writes the pixel rows it covers, they are left out of the accidental-seam search (+- 4 rows); every other
# ground row, including the pad lip right above the kerb, is judged exactly as before (limit unchanged).
excl = None
if "--exclude-json" in args:
    ej = json.load(open(args[args.index("--exclude-json") + 1]))
    if ej.get("rows"):
        excl = (ej["rows"][0] - 4, ej["rows"][1] + 4)
res = {}
LOCAL_MAX = 1.6
for f in files:
    im = bpy.data.images.load(f, check_existing=False)
    w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
    a = px.reshape(h, w, 4)[::-1, :, :3] * 255.0          # Blender pixels are bottom-up
    bpy.data.images.remove(im)
    L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    step = np.abs(np.diff(L, axis=0)).mean(axis=1)         # step[y-1] = row y vs row y-1
    ys = np.arange(1, h)
    sel = (ys >= 200) & (ys <= 1500)
    med = float(np.median(step[sel]))
    order = np.argsort(step[sel])[::-1][:5]
    worst = [(int(ys[sel][k]), round(float(step[sel][k]), 2)) for k in order]
    ratio = worst[0][1] / max(med, 1e-6)
    res[os.path.basename(f)] = dict(median=round(med, 2), worst=worst, ratio=round(ratio, 2), size=[w, h])
    print(f"SEAM {os.path.basename(f)}: median row step {med:.2f}, worst rows {worst}, worst/median {ratio:.2f}")
    # local ratio: every ground row against the median of the rows within +-40 (a horizontal seam shows as a row that stands out from ITS neighbourhood; the horizon / wall rows are above y 300)
    y1 = np.arange(300, min(1400, h - 41))
    if excl is not None:
        y1 = np.array([y for y in y1.tolist() if not (excl[0] <= y <= excl[1])])
    loc = np.array([step[y - 1] / max(float(np.median(step[max(y - 41, 0):y + 40])), 1e-6) for y in y1])
    k = int(np.argmax(loc))
    res[os.path.basename(f)].update(local_ratio_max=round(float(loc[k]), 2), local_ratio_row=int(y1[k]))
    ok = float(loc[k]) <= LOCAL_MAX
    print(f"GATE: H_TEE_SEAM_PREVIEW {'PASS' if ok else 'FAIL'} - {os.path.basename(f)}: worst ground row {int(y1[k])} steps {float(loc[k]):.2f} x the median of its +-40 rows (limit {LOCAL_MAX}; the review's Game-view still hole10_1_tee.png measures 3.1 at row 590, the round-4 build's preview 1.9)"
          + (f"; the deliberate kerb band rows {excl[0]}..{excl[1]} (DRESS_PATH, H_TEE_EDGE_VISIBLE) are not searched, the {len(y1)} other rows between 300 and 1400 are" if excl is not None else ""))
if out:
    json.dump(res, open(out, "w"), indent=1)
