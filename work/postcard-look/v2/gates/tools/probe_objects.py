"""AREA U probe: every mesh object of a blend (hole stage) with its material shares, size, open-edge fraction, box share, and the welded rock_shape verdict.
usage: blender -b --factory-startup --python probe_objects.py -- <hole> <file.blend>"""
import sys, os, importlib.util, collections
import numpy as np
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
import bpy
argv = sys.argv[sys.argv.index("--") + 1:]
hole = int(argv[0]); f = argv[1]
opts = m.parse_args([str(hole)])
design, dpath = m.load_design(hole, None)
C = m.Ctx(hole, design, dpath, opts)
bpy.ops.wm.open_mainfile(filepath=f, load_ui=False)
S = m.Snap("blend", C)
rows = []
seen = {}
for n, o in S.meshes.items():
    if n.startswith(m.COLL_PREFIXES): continue
    L = S.loc(o)
    ma = S.mat_area(o); tot = sum(ma.values()) or 1.0
    top = sorted(ma.items(), key=lambda kv: -kv[1])[:2]
    lo, hi = S.wbbox(o)
    ext = hi - lo
    k = S.key(o)
    if k not in seen:
        try:
            r = m.rock_shape(L)
        except Exception as e:
            r = dict(ok=False, nv=-1, nf=-1, open=-1, box=-1, why=[str(e)])
        seen[k] = r
    r = seen[k]
    rows.append((n, o.data.name, L["ntri"], r["nv"], r["nf"], round(r.get("open", -1), 2), round(float(r.get("box", -1)), 2), r["ok"],
                 [(a, round(b / tot, 2)) for a, b in top], [round(float(x), 1) for x in ext]))
import re
def stem(n): return re.sub(r"[_.]?\d+$", "", n)
groups = collections.OrderedDict()
for r in rows:
    groups.setdefault((stem(r[0]), tuple(a for a, _ in r[8])), []).append(r)
for (st, mats), rs in groups.items():
    r0 = rs[0]
    ext = np.array([r[9] for r in rs])
    print(f"{st:26s} n={len(rs):4d} mats={r0[8]} ntri {min(r[2] for r in rs)}..{max(r[2] for r in rs)} welded nv {min(r[3] for r in rs)}..{max(r[3] for r in rs)} open {min(r[5] for r in rs)}..{max(r[5] for r in rs)} box {min(r[6] for r in rs)}..{max(r[6] for r in rs)} rock_shape ok {sum(1 for r in rs if r[7])}/{len(rs)} extent max {ext.max(0).round(1).tolist()} min {ext.min(0).round(1).tolist()}")
