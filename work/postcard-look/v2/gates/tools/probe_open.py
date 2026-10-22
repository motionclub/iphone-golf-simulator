"""Open-edge fraction (edges of the polygon mesh used by ONE polygon, after the 1e-4 weld) of every props-library rock kind, of the synthetic hull rocks / spires, and of the
'every face split off by 2 mm' soup attack. usage: blender -b --factory-startup --python probe_open.py"""
import sys, importlib.util
import numpy as np, bpy, bmesh
from mathutils import Vector
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
import postcard_props_lib as PL
[PL.library_object(k) for k in sorted(PL.BUILDERS)]
S = m.Snap.__new__(m.Snap); S.stage = "fbx"; S._loc = {}; S._wld = {}


def open_frac(L, tol=1e-4):
    wid = m.weld_ids(L["V"], tol)
    T = wid[L["T"]]
    ok = (T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])
    T, tp, A = T[ok], L["tp"][ok], L["A"][ok]
    ed = {}
    for t, pid, a in zip(T.tolist(), tp.tolist(), A.tolist()):
        for u, v in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            k = (u, v) if u < v else (v, u)
            e = ed.setdefault(k, set()); e.add(pid)
    n = len(ed)
    opn = sum(1 for k, p in ed.items() if len(p) == 1 and False)   # placeholder
    # an edge shared by two triangles of ONE polygon is a diagonal, not an edge of the polygon mesh: count polygon edges via triangle multiplicity
    cnt = {}
    for t, pid in zip(T.tolist(), tp.tolist()):
        for u, v in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            k = (u, v) if u < v else (v, u)
            cnt.setdefault(k, []).append(pid)
    poly_edges = {k: v for k, v in cnt.items() if not (len(v) == 2 and v[0] == v[1])}
    nop = sum(1 for k, v in poly_edges.items() if len(v) == 1)
    nnm = sum(1 for k, v in poly_edges.items() if len(v) > 2)
    return nop / max(len(poly_edges), 1), nnm / max(len(poly_edges), 1), len(poly_edges)


lib = bpy.data.collections.get("ASSET_LIBRARY")
mx = 0
for o in sorted(lib.all_objects, key=lambda o: o.name):
    if o.type != "MESH" or not o.name.startswith("ROCK_"): continue
    f, nm, ne = open_frac(S.loc(o))
    mx = max(mx, f)
    print(f"OPEN {o.name:22s} edges {ne:5d} open {f*100:5.1f} %  non-manifold {nm*100:5.1f} %")
print("largest open-edge fraction over the library: %.1f %%" % (mx * 100))
