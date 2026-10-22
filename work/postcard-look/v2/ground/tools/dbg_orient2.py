import sys, os, runpy
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import numpy as np, bpy
from mathutils.kdtree import KDTree
import postcard_lib as P
import postcard_look_lib as L
H, BL = sys.argv[sys.argv.index("--") + 1], sys.argv[sys.argv.index("--") + 2]
OUT = os.path.join(REPO, "work/postcard-look/v2/ground/tools/_scratch_%s" % H)
_o = P.start; P.start = lambda name, out_dir=None: _o(name, out_dir=OUT)
sys.argv = [os.path.join(REPO, "work/postcard-look/baseline/scripts", f"hole{H}_build.py")]
try: runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit: pass
D = P._ST["D"]
bpy.ops.wm.open_mainfile(filepath=BL)
pts, nrm = [], []
for li, (Pl, _) in enumerate(L.terrain_top_loops(D)):
    Pc, s, Lp, N, _ = L._loop_columns(Pl, 0.5)
    pts += Pc.tolist(); nrm += N.tolist()
kd = KDTree(len(pts))
for i, p in enumerate(pts): kd.insert((p[0], p[1], 0.0), i)
kd.balance()
for o in L._skin_objs():
    W, ls, lt, lv, mi, pn = L._mesh_arrays(o)
    pol = L._poly_of_loop(ls, lt, len(lv))
    cen = np.zeros((len(ls), 3)); np.add.at(cen, pol, W[lv]); cen /= lt[:, None]
    sgn = []
    for c, n in zip(cen, pn):
        if abs(n[2]) > 0.7: continue
        _, i, _ = kd.find((c[0], c[1], 0.0)); Nl = nrm[i]
        sgn.append(n[0] * Nl[0] + n[1] * Nl[1])
    sgn = np.array(sgn)
    print(o.name, "wall faces", len(sgn), "outward share %.0f%%" % (100 * (sgn > 0).mean()) if len(sgn) else "")
