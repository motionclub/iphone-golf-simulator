import sys, importlib.util, numpy as np
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
look = REPO + "/work/postcard-look/v2/gates/fixtures/look_at_run"
for stem in ("Fairway_C", "Green_C", "Rough_C", "Scrub_C"):
    px = m.image_stats(f"{look}/{stem}.png")["px"]
    print("REP", stem, round(m.repeat_peak(m.lum709(px)), 3))
rng = np.random.default_rng(11)
cell = rng.uniform(0.8, 1.2, (16, 16)); t = np.tile(cell, (32, 32))
print("REP tiled-16px-cell", round(m.repeat_peak(t), 3))
import os
for n in (512,):
    for stem in ("Fairway", "Green", "Rough", "Scrub"):
        h, s_, v, vsd, hw, sd = m.ST_ALBEDO[stem]
        img = m.st_albedo_img(stem, 512)
        print("REP synthetic", stem, round(m.repeat_peak(m.lum709(np.dstack([img, np.ones((512,512))]))), 3))
