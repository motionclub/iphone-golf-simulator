"""Build the whole props library (ASSET_LIBRARY) in a scratch scene and print per-component numbers of every ROCK_ kind (read-only use of the props lib)."""
import sys, os, importlib.util, collections
import numpy as np, bpy
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
import postcard_props_lib as PL
[PL.library_object(k) for k in sorted(PL.BUILDERS)]   # NOT ensure_library(): it writes Plants_C.png
exec(open(REPO + "/work/postcard-look/v2/gates/tools/probe_rocks.py").read().split("cnt = 0")[0].split("seen = set()")[1].split("def comp_report")[0]) if False else None
src = open(REPO + "/work/postcard-look/v2/gates/tools/probe_rocks.py").read()
# reuse comp_report / comp_numbers
ns = dict(m=m, np=np, bpy=bpy, collections=collections)
exec(src[src.index("def comp_report"):src.index("cnt = 0")], ns)
exec(src[src.index("def comp_numbers"):src.index("seen2 = set()")], ns)
lib = bpy.data.collections.get("ASSET_LIBRARY")
for o in sorted(lib.all_objects, key=lambda o: o.name):
    if o.type != "MESH" or not (o.name.startswith("ROCK_") or o.name.startswith("DRESS_BLOCK")): continue
    cr = ns["comp_report"](o.name, o.data)
    big = sorted(cr, key=lambda c: -c[0])
    cn = ns["comp_numbers"](o.data)
    allsame = [c for c in cr if c[3] and c[0] >= 6 and len(c[4]) <= 2]
    print(f"KIND {o.name:22s} ncomp {len(cr):3d} regular(<=2 valences) {len(allsame):3d} | vertshare(max) {max(x['vert'] for x in cn):.2f} | firstcomps {[(c[0], c[4]) for c in big[:2]]}")
