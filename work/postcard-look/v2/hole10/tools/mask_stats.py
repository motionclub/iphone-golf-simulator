"""mask_stats.py DIR_OF_MASK_PNGS : per image class shares (lava red, rock blue, ground green, plant dark green, cone cyan, smoke yellow, sky black).
Classification = nearest of the mask colours (EEVEE emission-only render, Standard view transform)."""
import sys, json, os
from PIL import Image
import numpy as np
COL = {"lava": (255, 0, 0), "rock": (0, 0, 255), "ground": (0, 255, 0), "plant": (0, 102, 0), "tuft": (0, 204, 51), "cone": (0, 255, 255), "smoke": (255, 255, 0), "other": (128, 128, 128), "sky": (0, 0, 0)}
def stats(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    names = list(COL)
    d = np.stack([((a - np.array(COL[n], np.float32)) ** 2).sum(-1) for n in names], -1)
    k = d.argmin(-1)
    n = k.size
    out = {nm: float((k == i).sum()) / n for i, nm in enumerate(names)}
    land = 1.0 - out["sky"]
    out["lava_of_nonsky"] = out["lava"] / max(land, 1e-9)
    out["rock_of_nonsky"] = (out["rock"] + out["cone"]) / max(land, 1e-9)
    return out
if __name__ == "__main__":
    d = sys.argv[1]
    res = {}
    for f in sorted(os.listdir(d)):
        if f.endswith(".png"):
            res[f] = stats(os.path.join(d, f))
            r = res[f]
            print(f"{f:28s} lava {r['lava']:.3f} (of non-sky {r['lava_of_nonsky']:.3f})  rock {r['rock']:.3f} cone {r['cone']:.3f} ground {r['ground']:.3f} plant {r['plant']:.3f} sky {r['sky']:.3f} smoke {r['smoke']:.3f}")
    if len(sys.argv) > 2:
        json.dump(res, open(sys.argv[2], "w"), indent=1)
