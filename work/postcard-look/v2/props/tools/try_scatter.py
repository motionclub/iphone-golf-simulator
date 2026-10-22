import sys, os, math, time
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
import postcard_lib as P
import postcard_props_lib as PL
for tag in ("08", "09", "10"):
    D = P.start(f"hole{tag}_design", out_dir=R + f"/work/postcard-look/v2/props/scratch/hole{tag}")
    P.build_terrain(D); P.build_play_surfaces(D)
    PL._COUNTERS.clear(); PL.reset_scatter(D)
    t = time.time()
    tufts = PL.scatter(D, {"PLANT_TUFT_A": 3, "PLANT_TUFT_B": 2}, 300, seed=1)
    sh = PL.scatter(D, ["PLANT_SHRUB_A", "PLANT_SHRUB_B"], 40, seed=2)
    dt = time.time() - t
    objs = tufts + sh
    X = np.array([o.location.x for o in objs]); Y = np.array([o.location.y for o in objs]); Z = np.array([o.location.z for o in objs])
    codes = P.lie_codes_m(D, X, Y)
    g = PL.ground_sampler(D)(X, Y)
    print(tag, "placed", len(tufts), len(sh), "on water", int((codes == P.LIE_WATER).sum()), "dz max", float(np.abs(Z - g).max()), "z min", float(Z.min()), "ground z", float(np.nanmin(g)), float(np.nanmax(g)), "time %.1fs" % dt)
    # huge explicit region
    big = PL.scatter(D, "PLANT_TUFT_A", 200, region=(-500, -500, 500, 500), seed=5)
    X = np.array([o.location.x for o in big]); Y = np.array([o.location.y for o in big])
    print("   huge region:", len(big), "on water", int((P.lie_codes_m(D, X, Y) == P.LIE_WATER).sum()))
