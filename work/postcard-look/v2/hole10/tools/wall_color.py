"""wall_color.py COLOUR_DIR MASK_DIR : mean colour of the wall / rock pixels (mask blue) of the aerial previews (Unity-like patch: tint, fog, lava lights) - information, not a gate."""
import sys, os
import numpy as np
from PIL import Image
import colorsys
cd, md = sys.argv[1], sys.argv[2]
for n in ("hole10_aerial", "hole10_aerial2", "hole10_aerial3", "hole10_aerial4", "hole10_wallclose"):
    cp, mp = os.path.join(cd, n + ".png"), os.path.join(md, n + ".png")
    if not (os.path.exists(cp) and os.path.exists(mp)):
        continue
    a = np.asarray(Image.open(cp).convert("RGB")).astype(np.float32)
    m = np.asarray(Image.open(mp).convert("RGB")).astype(np.float32)
    rock = (m[..., 2] > 150) & (m[..., 0] < 100) & (m[..., 1] < 100)
    if rock.sum() < 100:
        continue
    px = a[rock]
    mean = px.mean(0)
    lum = px @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    h, s, v = colorsys.rgb_to_hsv(*(mean / 255.0))
    print(f"{n:20s} wall px {int(rock.sum()):7d} mean RGB ({mean[0]:.0f},{mean[1]:.0f},{mean[2]:.0f}) hue {h * 360:.0f} S {s:.2f} V {v:.2f}, median luminance {np.median(lum):.0f}, share < 60: {float((lum < 60).mean()):.0%}")
