"""H_TEE_EDGE_CONTRAST: how much darker is the tee pad's edge ribbon than the grass right next to it, on the Blender tee preview (NOT the Game view).

  Blender -b --factory-startup --python rim_contrast.py -- PREVIEW.png TEE_EDGE.json [--max-ratio 0.70] [--json OUT.json]

tools/tee_edge.py (ray casts through the 900 x 1600 address camera) writes, per sampled pixel column, the rows the ribbon covers (`bands`: [x, y0, y1]). Here the preview's luminance (Rec. 709 of the sRGB values)
is averaged over those rows and compared with the 14 rows just above and the 14 just below the band in the same column (grass, minus 3 rows of margin). PASS = the MEDIAN over the columns of
(ribbon luminance / grass luminance) <= max-ratio (default 0.70: at least 30 % darker) and the 90th percentile <= 0.85 (no stretch of the lip where the ribbon vanishes into the grass).
"""
import sys, json, os
import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
png, ej = args[0], args[1]
max_ratio = float(args[args.index("--max-ratio") + 1]) if "--max-ratio" in args else 0.70
out = args[args.index("--json") + 1] if "--json" in args else None
bands = json.load(open(ej))["bands"]
im = bpy.data.images.load(png, check_existing=False)
w, h = im.size
px = np.empty(w * h * 4, np.float32)
im.pixels.foreach_get(px)
a = px.reshape(h, w, 4)[::-1, :, :3] * 255.0            # Blender pixels are bottom-up
L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
ratios, rim_l, grass_l = [], [], []
for x, y0, y1 in bands:
    x = min(max(int(x), 0), w - 1)
    r = L[max(y0, 0):y1 + 1, max(x - 1, 0):x + 2].mean()
    up = L[max(y0 - 3 - 14, 0):max(y0 - 3, 1), max(x - 1, 0):x + 2].mean()
    dn = L[min(y1 + 4, h - 1):min(y1 + 4 + 14, h), max(x - 1, 0):x + 2].mean()
    g = 0.5 * (up + dn)
    ratios.append(r / max(g, 1e-6)); rim_l.append(r); grass_l.append(g)
ratios = np.array(ratios)
med, p90 = float(np.median(ratios)), float(np.percentile(ratios, 90))
ok = len(ratios) >= 0.95 * 90 and med <= max_ratio and p90 <= 0.85
print(f"GATE: H_TEE_EDGE_CONTRAST {'PASS' if ok else 'FAIL'} - {os.path.basename(png)} (Blender preview, not the Game view): {len(ratios)} columns, ribbon luminance {np.median(rim_l):.0f} vs the grass beside it {np.median(grass_l):.0f} "
      f"(ratio median {med:.2f} <= {max_ratio:g}, 90th percentile {p90:.2f} <= 0.85, least-contrast column {ratios.max():.2f})")
if out:
    json.dump(dict(ok=bool(ok), median=med, p90=p90, rim=float(np.median(rim_l)), grass=float(np.median(grass_l))), open(out, "w"), indent=1)
