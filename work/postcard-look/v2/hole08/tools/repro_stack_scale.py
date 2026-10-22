"""LIB_BUGS #6 repro: place_sea_stack on the hole 8 design positions with the first seed only (no re-roll): which pieces sit exactly on the library scale floor 0.5."""
import sys
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy, numpy as np
import postcard_lib as P, postcard_props_lib as PL
import hole08_look as K
D = P.start("hole08_design", out_dir=REPO + "/work/postcard-look/v2/hole08/scratch/repro_scale")
P.build_terrain(D)
for st in D.scenery["stacks"]:
    x_yd, d_yd = K.STACK_MOVE.get(st["seed"], (st["x"], st["d"]))
    x, y = P.m(x_yd, d_yd)
    r = st["radius_yd"] * P.YD
    for attempt in range(8):                                  # the first version of hole08_look.place_stack: shrink the radius until the needle rules hold, no scale check
        objs = PL.place_sea_stack(D, x, y, K.stack_height_m(st["height_yd"]), r, seed=st["seed"])
        ok, det = K._stack_ok(D, objs)
        if ok and det[3] <= K.STACK_CAP_M + 1e-6:
            break
        for o in objs: bpy.data.objects.remove(o, do_unlink=True)
        r *= 0.88
    for o in objs:
        sv = np.linalg.svd(np.array(o.matrix_world)[:3, :3], compute_uv=False)
        if sv.min() < 0.505:
            print(f"REPRO stack seed {st['seed']} (radius {r:.2f} m): {o.name} singular values {[round(float(v), 4) for v in sv]} (library floor 0.5)")
    for o in objs: bpy.data.objects.remove(o, do_unlink=True)
