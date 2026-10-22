"""plant_share.py BEFORE_DIR NOW_DIR [--json OUT] : share of the frame covered by the grass tufts (mask category 'tuft': PLANT_TUFT_*) and by all plants in the three 900 x 1600 phone stills, whole frame and lower 60 %
(rows >= 640), of two mask-render folders (tools/render_views.py --mask --only tee,approach,lavarim): the round-3 stage (the 170-tuft carpet) and this stage (the edge fringe).
BLENDER PREVIEW GEOMETRY, NOT THE GAME VIEW (flat emission masks of the same camera rigs): an area-of-silhouette measure for 'do tufts show', not GRASS_STILL_ALIVE (that needs the Game-view stills and the skeptic)."""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from mask_stats import COL


def share(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    names = list(COL)
    d = np.stack([((a - np.array(COL[n], np.float32)) ** 2).sum(-1) for n in names], -1)
    k = d.argmin(-1)
    H = k.shape[0]
    ti, pi = names.index("tuft"), names.index("plant")
    low = k[int(0.4 * H):]
    return dict(tuft=float((k == ti).mean()), tuft_low60=float((low == ti).mean()), plant=float(((k == ti) | (k == pi)).mean()), plant_low60=float(((low == ti) | (low == pi)).mean()))


def main():
    a, b = sys.argv[1], sys.argv[2]
    out = {}
    for f in sorted(os.listdir(b)):
        if f.endswith(".png") and os.path.exists(os.path.join(a, f)):
            out[f] = dict(before=share(os.path.join(a, f)), now=share(os.path.join(b, f)))
    for f, v in out.items():
        print(f"{f:22s} tuft pixels whole frame {100 * v['before']['tuft']:.3f}% -> {100 * v['now']['tuft']:.3f}%  lower 60 % {100 * v['before']['tuft_low60']:.3f}% -> {100 * v['now']['tuft_low60']:.3f}%   (all plants {100 * v['before']['plant']:.3f}% -> {100 * v['now']['plant']:.3f}%)")
    if "--json" in sys.argv:
        json.dump(out, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)


main()
