"""Idempotency: build_sea / build_cliff_skin(replace=True) / build_path twice give the same object sets and counts."""
import sys, os, runpy
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import numpy as np, bpy
import postcard_lib as P
import postcard_look_lib as L
H = "08"
OUT = os.path.join(REPO, "work/postcard-look/v2/ground/tools/_scratch_%s" % H)
_o = P.start; P.start = lambda name, out_dir=None: _o(name, out_dir=OUT)
sys.argv = [os.path.join(REPO, "work/postcard-look/baseline/scripts", f"hole{H}_build.py")]
try: runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit: pass
P.start = _o; D = P._ST["D"]
L.look_materials(D); L.retarget_materials(D)
def census():
    c = {}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(("WATER_", "ROCK_SKIN", "DRESS_PATH")):
            k = o.name.rsplit("_", 1)[0] if o.name[-2:].isdigit() else o.name
            c[k] = c.get(k, 0) + 1
    tri = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(("WATER_", "ROCK_SKIN", "DRESS_PATH")))
    return c, tri
for rep in range(2):
    L.build_cliff_skin(D, style="strata", replace=True)
    fp = L.open_shore_point(D, (30.0, 160.0), free_m=40.0)
    foot = (fp[0] + fp[2] * 3.0, fp[1] + fp[3] * 3.0)
    L.build_sea(D, pockets=[(foot[0], foot[1], 6.0)])
    if rep == 0:
        L.surf_patch(D, foot, radius_m=4.0)
    L.build_path(D, [(-9.0, -6.0), (-8.5, 12.0), (-6.0, 28.0), (-3.0, 40.0)], width_m=2.6) if rep == 0 else None
    print("CENSUS", rep, census())
