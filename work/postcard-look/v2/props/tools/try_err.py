import sys
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, random
import postcard_props_lib as PL
bpy.ops.wm.read_factory_settings(use_empty=True)
rng = random.Random(1)
for box in ((9.0, 7.0, 20.0), (6.9, 6.0, 20.0), (13.0, 13.0, 24.0), (3.0, 3.0, 40.0), (60, 5, 3)):
    p = PL.fit_plan(*box, PL.SWAP_BASALT_FAMILY, rng)
    print(box, p["kind"], p["n"], tuple(round(v, 2) for v in p["scale"]), "err", round(p["err"], 2), "ideal", tuple(round(v, 2) for v in p["ideal"]))
for box in ((9.0, 7.0, 20.0), (3, 3, 40), (60, 5, 3), (0.4, 0.3, 0.2)):
    p = PL.fit_plan(*box, PL.SWAP_ROCK_FAMILY, rng)
    print("rock", box, p["kind"], p["n"], tuple(round(v, 2) for v in p["scale"]), "err", round(p["err"], 2))
