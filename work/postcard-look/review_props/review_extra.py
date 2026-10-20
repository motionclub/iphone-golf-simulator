"""Reviewer extra probes (writes nothing outside work/postcard-look/review_props/)."""
import sys
import os
import math
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
OUT = os.path.join(REPO, "work", "postcard-look", "review_props")
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import numpy as np  # noqa: E402
import bpy  # noqa: E402
import postcard_props_lib as PL  # noqa: E402
import postcard_lib as P  # noqa: E402


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    PL._COUNTERS.clear()
    PL.reset_scatter(None)


def wxy(ob):
    me = ob.data
    co = np.array([v.co[:] for v in me.vertices])
    M = np.array(ob.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]


for tag in ("08", "09", "10"):
    fresh()
    D = P.start(f"hole{tag}_design", out_dir=os.path.join(OUT, f"hole{tag}"))
    P.build_terrain(D)
    P.build_play_surfaces(D)
    # 1. default region (None): where do tufts / shrubs land?
    tu = PL.scatter(D, {"PLANT_TUFT_A": 1}, 300, seed=1)
    sh = PL.scatter(D, ["PLANT_SHRUB_A"], 40, seed=2)
    bpy.context.view_layer.update()
    for nm, objs in (("tufts", tu), ("shrubs", sh)):
        X = np.array([o.location.x for o in objs])
        Y = np.array([o.location.y for o in objs])
        Z = np.array([o.location.z for o in objs])
        wet = P.lie_codes_m(D, X, Y) == P.LIE_WATER
        print(f"PROBE region=None hole {tag} {nm}: {len(objs)} placed, {int(wet.sum())} on WATER lie at z {np.round(Z[wet][:4], 2).tolist()}", flush=True)
    # 2. land rim rocks: share of vertices outside the terrain (over the cliff edge) and the worst one
    PL.reset_scatter(D)
    rocks = PL.scatter_rocks(D, 30, zone="rim", seed=4) + PL.scatter_rocks(D, 20, zone="ledge", seed=6)
    shr = PL.scatter(D, ["PLANT_SHRUB_A", "PLANT_SHRUB_B"], 40, region=PL.region_band(D, 0.6, 6.0), seed=2)
    bpy.context.view_layer.update()
    worst = []
    for o in rocks + shr:
        w = wxy(o)
        sd = P.signed_dist_m(D, w[:, 0], w[:, 1])        # > 0 outside the land
        worst.append((float(sd.max()), float((sd > 0).mean()), o.name))
    worst.sort(reverse=True)
    print(f"PROBE overhang hole {tag}: worst vertex past the cliff edge {[(round(a, 2), round(b, 2), n) for a, b, n in worst[:4]]}", flush=True)
    # 3. vines on the cliff: horizontal gap between the hanging vine bottom and the (undercut) wall
    pts = PL.cliff_lip_points(D, spacing_m=7.0, seed=6)
    vines = PL.hang_vines(D, pts, seed=6, max_drop=lambda p: p[2] - 0.4, skip=0.3)
    bpy.context.view_layer.update()
    gaps = []
    for v in vines:
        w = wxy(v)
        lo = w[w[:, 2].argmin()]
        sd = float(P.signed_dist_m(D, np.array([lo[0]]), np.array([lo[1]]))[0])
        gaps.append(sd)
    gaps = np.array(gaps)
    print(f"PROBE vines hole {tag}: {len(vines)} vines, bottom tip distance outside the lip median {np.median(gaps):.2f} m, max {gaps.max():.2f} m "
          f"(walls undercut 3 m toward z -6)", flush=True)
sys.stdout.flush()
os._exit(0)
