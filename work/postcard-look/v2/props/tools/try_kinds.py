import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
sys.argv = [sys.argv[0], "--", "--scratch", R + "/work/postcard-look/v2/props/scratch"]
import bpy, numpy as np
from mathutils import Vector
import postcard_props_smoke as S
import postcard_props_lib as PL
S.fresh()
kinds = os.environ.get("KINDS", "ROCK_CRAG_A,ROCK_CRAG_B").split(",")
for k in kinds:
    ob = PL.library_object(k)
    me = ob.data
    rep = PL.rock_shape_report(me)
    d = ob.dimensions
    print(k, "faces", len(me.polygons), "verts", rep["verts"], "dims", [round(x,1) for x in d], "ok", rep["ok"], {k2: (round(v,3) if isinstance(v,float) else v) for k2,v in rep.items() if k2 in ("facets","radius_cv","edge_cv","area_cv")}, rep["why"])
if os.environ.get("RENDER"):
    S.setup_scene((1400, 600))
    water = S.ref_mat("REF_WATER", (36, 104, 168), rough=0.15)
    S.ref_plane("REF_WATER_B", 0, 0, 0.0, 800, 800, water.name)
    x = 0.0
    sc = float(os.environ.get("SC", "1"))
    for k in kinds:
        mn, mx = PL.lib_bbox(k)
        w = (mx.x - mn.x) * sc
        PL.place(None, k, (x + w / 2, 0, 0), 0.3, sc)
        x += w + 4
    S.ref_figure(-3, -6, 0.0)
    ctr = x / 2
    cam = S.camera("CAM", Vector((ctr, -float(os.environ.get("DIST", "60")), float(os.environ.get("CZ", "10"))), ), Vector((ctr, 0, float(os.environ.get("TZ", "5")))), lens=float(os.environ.get("LENS", "30")))
    bpy.context.scene.camera = cam
    out = R + "/work/postcard-look/v2/props/scratch/kinds_%s.png" % os.environ.get("TAG", "a")
    bpy.context.scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("wrote", out)
