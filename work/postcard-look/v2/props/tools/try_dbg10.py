import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
sys.argv = [sys.argv[0], "--", "--scratch", R + "/work/postcard-look/v2/props/scratch"]
import bpy, numpy as np
import postcard_lib as P
import postcard_props_lib as PL
import postcard_props_smoke as S
tag = "10"
S.fresh()
D = P.start(f"hole{tag}_design", out_dir=R + f"/work/postcard-look/v2/props/scratch/hole{tag}")
P.build_terrain(D); P.build_play_surfaces(D)
P.build_water(D, 'WATER_LAVA', 'MAT_LAVA', shallow_material=None, foam_material=None, crest=False)
bvh, names = S.ground_bvh()
x0, y0, x1, y1 = P._shore_bbox_m(D, 0.0)
cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
big = max(x1 - x0, y1 - y0) + 300.0
regions = {"None": None, "rect": (x0 - 300, y0 - 300, x1 + 300, y1 + 300), "disc": PL.region_disc(cx, cy, big), "poly": PL.region_polyline([(x0 - 100, y0 - 100), (x1 + 100, y1 + 100), (x0 - 100, y1 + 100)], 60.0), "bandland": PL.region_band(D, 0.2, 6.0)}
kinds_sets = [{"PLANT_TUFT_A": 1}, ["PLANT_SHRUB_A", "PLANT_SHRUB_B"], {"PLANT_FLOWER_PURPLE": 1, "PLANT_FLOWER_WHITE": 1}, ["PLANT_AGAVE_B"], ["PLANT_PINE_A", "PLANT_TREE_A"]]
gs = PL.ground_sampler(D)
for rn, reg in regions.items():
    for ki, ks in enumerate(kinds_sets):
        for safe in (True, False):
            out = PL.scatter(D, ks, 300, region=reg, seed=11 + ki, safe=safe, register=False, respect=False)
            for o in out:
                g = S.ground_z(bvh, o.location.x, o.location.y)
                g2 = float(gs(np.array([o.location.x]), np.array([o.location.y]))[0])
                if g is None or abs(o.location.z - g) > 0.05 or o.location.z < 5.0:
                    code = P.lie_codes_m(D, np.array([o.location.x]), np.array([o.location.y]))[0]
                    print("BAD", rn, ks, safe, o.name, tuple(round(v, 3) for v in o.location), "indep ground", g, "PL ground", g2, "lie", P.LIE_NAMES[code])
            for o in out:
                bpy.data.objects.remove(o, do_unlink=True)
print("done")
