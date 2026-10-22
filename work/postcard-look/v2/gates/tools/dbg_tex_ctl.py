import sys, os, importlib.util
import numpy as np
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
import bpy
d = REPO + "/work/postcard-look/v2/gates/u/tex_dbg"; os.makedirs(d, exist_ok=True)
m.st_textures(d)
for fn in (m.t_fairway_at_stills_level, m.t_fairway_smooth_below_floor):
    fn(d); m.IMG_CACHE.clear()
    px = m.image_stats(d + "/Fairway_C.png")["px"]
    a = m.albedo_structure(px, "Fairway_C")
    print("TEXCTL", fn.__name__, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in a.items()})
    lum = m.lum709(px); print("   global sd", lum.std(), "hue", m.mean_hsv(px[..., :3].reshape(-1, 3).mean(0)))
px = m.image_stats(d + "/Green_C.png")["px"]; a = m.albedo_structure(px, "Green_C"); print("TEXCTL synthetic Green_C", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in a.items()})
