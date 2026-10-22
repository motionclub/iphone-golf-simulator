import sys, os, math, time, collections
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
import postcard_props_lib as PL
hole = os.environ.get("HOLE", "10")
bpy.ops.wm.open_mainfile(filepath=R + f"/work/postcard-look/baseline/blender/hole_{hole}.blend")
before = len(PL.legacy_rocks())
t = time.time()
rep = []
out = PL.swap_legacy_rocks(None, basalt=(hole == "10"), report=rep, seed=1)
dt = time.time() - t
bpy.context.view_layer.update()
sr = PL.stretch_report()
print(f"HOLE {hole}: legacy {before} -> {len(out)} instances in {dt:.1f}s; stretch ok={sr['ok']} n={sr['n']} scale {sr['min_scale']:.2f}..{sr['max_scale']:.2f} max ratio {sr['max_ratio']:.2f} violations {len(sr['violations'])} {sr['violations'][:3]}")
kinds = collections.Counter(o.data.name for o in out)
print(dict(kinds))
tris = 0
for o in out:
    o.data.calc_loop_triangles(); tris += len(o.data.loop_triangles)
print("tris", tris)
print("assert", PL.assert_no_legacy_rocks(None, raise_on_fail=False))
multi = [r for r in rep if r["instances"] > 1]
print("multi-instance plans", len(multi), multi[:3])
errs = np.array([r["err"] for r in rep])
print("box err (sum |log|) mean %.3f p90 %.3f max %.3f" % (errs.mean(), np.percentile(errs, 90), errs.max()))

import postcard_props_smoke as S
from mathutils import Vector
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1400, 760
S.setup_scene((1400, 760))
for o in list(bpy.data.objects):
    if o.type in ('LIGHT', 'CAMERA'):
        bpy.data.objects.remove(o, do_unlink=True)
# re-add sun/fill + camera
import math
for nm, en, rot, ang, col, sh in (("REF_SUN", 3.3, (48, 0, -32), 5.0, (1.0, 0.94, 0.84), True), ("REF_FILL", 0.6, (60, 0, 150), 30.0, (0.8, 0.88, 1.0), False)):
    L = bpy.data.lights.new(nm, 'SUN'); L.energy = en; L.angle = math.radians(ang); L.color = col
    o = bpy.data.objects.new(nm, L); sc.collection.objects.link(o); o.rotation_euler = [math.radians(a) for a in rot]
pos = {"08": ((-90, -60, 70), (0, 160, 4)), "09": ((-150, -80, 110), (-20, 200, 4)), "10": ((0, -150, 140), (150, 120, 10))}[hole]
cam = S.camera("CAM", Vector(pos[0]), Vector(pos[1]), lens=28, clip=3000)
sc.camera = cam
out = R + f"/work/postcard-look/v2/props/scratch/swap_{hole}.png"
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("wrote", out)
