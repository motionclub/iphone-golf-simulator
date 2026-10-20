"""Reviewer probe: build_basalt_skin on the REAL hole-10 pillar (scratch build, undercut terrain walls). Measures what a viewer
sees on the pillar side (ray hits: skin column vs TERRAIN wall) and renders a close-up. Writes only into review_props/."""
import sys
import os
import math
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
OUT = os.path.join(REPO, "work", "postcard-look", "review_props")
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
sys.argv += ["--scratch", os.path.join(OUT, "render")] if "--scratch" not in sys.argv else []
import numpy as np  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import postcard_props_smoke as SM  # noqa: E402
import postcard_props_lib as PL  # noqa: E402
import postcard_lib as P  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
D = P.start("hole10_design", out_dir=os.path.join(OUT, "hole10"))
P.build_terrain(D, undercut_m=6.0)
P.build_play_surfaces(D)
px, py = D.hole.pin[0] * P.YD, D.hole.pin[1] * P.YD
loop = None
for L in D.loops:
    A = np.asarray(L)
    if P.point_in_poly((px, py), [tuple(p) for p in A]):
        loop = [tuple(p) for p in A]
print("PROBE pillar loop", len(loop) if loop else None, "pts; loops", [len(l) for l in D.loops], flush=True)
skins = PL.build_basalt_skin(D, loop, D.play_z - 0.04, -6.0, col_r=1.1, seed=3)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
cx, cy = np.mean([p[0] for p in loop]), np.mean([p[1] for p in loop])
R = max(math.hypot(p[0] - cx, p[1] - cy) for p in loop) + 10
counts = {}
for zi in np.linspace(-0.5, 5.9, 14):
    for a in np.linspace(0, math.tau, 48, endpoint=False):
        o = Vector((cx + math.cos(a) * R, cy + math.sin(a) * R, zi))
        d = Vector((-math.cos(a), -math.sin(a), 0.0))
        hit, loc, nrm, idx, ob, mat = bpy.context.scene.ray_cast(dg, o, d, distance=2 * R)
        key = "none" if not hit else ("SKIN" if ob.name.startswith("ROCK_SKIN") else ob.name.split("_")[0])
        band = "top 0-1 m" if zi > D.play_z - 1.0 else ("1-3 m" if zi > D.play_z - 3.0 else "below 3 m")
        counts.setdefault(band, {}).setdefault(key, 0)
        counts[band][key] += 1
print("PROBE pillar side ray hits by depth below the lip:", counts, flush=True)
print("PROBE skin objects", [(o.name, len(o.data.polygons)) for o in skins], flush=True)
# render close-up from the lava, looking at the pillar
SM.setup_scene((800, 500))
a = math.atan2(-cy, -cx)            # from the tee side
cam = SM.camera("CAM_PILLAR", Vector((cx + math.cos(a) * (R + 25), cy + math.sin(a) * (R + 25), 9.0)), Vector((cx, cy, 2.0)), lens=30)
sc = bpy.context.scene
sc.camera = cam
sc.render.filepath = os.path.join(OUT, "render", "hole10_pillar_skin.png")
bpy.ops.render.render(write_still=True)
print("PROBE rendered", sc.render.filepath, flush=True)
sys.stdout.flush()
os._exit(0)
