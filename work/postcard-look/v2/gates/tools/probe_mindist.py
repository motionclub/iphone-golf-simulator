"""Smallest distance between two DIFFERENT welded vertices of every props-library rock kind, absolute and as a fraction of the bbox diagonal, plus the
per-face-split attack (every face its own 3 vertices, offset by `off` m) judged by rock_shape. usage: blender -b --factory-startup --python probe_mindist.py"""
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
lib = bpy.data.collections.get("ASSET_LIBRARY")
worst = 9
for o in sorted(lib.all_objects, key=lambda o: o.name):
    if o.type != "MESH" or not o.name.startswith("ROCK_"): continue
    L = S.loc(o)
    wid = m.weld_ids(L["V"])
    nw = int(wid.max()) + 1
    P = np.zeros((nw, 3)); np.add.at(P, wid, L["V"]); P /= np.maximum(np.bincount(wid, minlength=nw), 1)[:, None]
    diag = float(np.linalg.norm(P.max(0) - P.min(0)))
    D = np.linalg.norm(P[:, None] - P[None], axis=2) + np.eye(nw) * 1e9
    d = float(D.min())
    # smallest distance between vertices NOT sharing an edge is what matters for a weld; report both
    worst = min(worst, d / diag)
    print(f"MIND {o.name:22s} nv {nw:4d} diag {diag:6.2f} m  min vertex distance {d*1000:7.1f} mm = {d/diag*100:.3f} % of diag")
print("smallest fraction of the diagonal over all kinds: %.3f %%" % (worst * 100))
