import sys, os, runpy
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import numpy as np, bpy
import postcard_lib as P
import postcard_look_lib as L
args = sys.argv[sys.argv.index("--") + 1:]
H = args[args.index("--hole") + 1].zfill(2); BL = args[args.index("--blend") + 1]
OUT = os.path.join(REPO, "work/postcard-look/v2/ground/tools/_scratch_%s" % H)
_o = P.start; P.start = lambda name, out_dir=None: _o(name, out_dir=OUT)
sys.argv = [os.path.join(REPO, "work/postcard-look/baseline/scripts", f"hole{H}_build.py")]
try: runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit: pass
P.start = _o; D = P._ST["D"]
bpy.ops.wm.open_mainfile(filepath=BL)
c = L.skin_over_water(D)
print("cells", c["cells"], "worst", c["worst"], "face_vertex", c["face_vertex"])
print("pts", c["pts"])
ells = L._water_ellipses(D); print("ells", ells)
# which objects
from mathutils import Vector
sb = {o.name: L._bvh_of([o]) for o in L._skin_objs()}
for (x, y, z, d) in c["pts"][:10]:
    for n, b in sb.items():
        h = b.ray_cast(Vector((x, y, 8.0)), Vector((0, 0, -1)), 30)
        if h[0] is not None and abs(h[0].z - z) < 0.02:
            print("pt", (x, y, z, d), "in", n, "normal", tuple(round(v, 2) for v in h[1]))
print("---- face vertices")
for o in L._skin_objs():
    Wv, ls, lt, lv, mi, pn = L._mesh_arrays(o)
    dv = L._ell_depth(ells, Wv[:, 0], Wv[:, 1])
    pol = L._poly_of_loop(ls, lt, len(lv))
    up = pn[:, 2] > 0.3
    for p_ in np.nonzero(up)[0].tolist():
        vs = lv[ls[p_]:ls[p_]+lt[p_]]
        if dv[vs].max() > 0.15:
            print(o.name, "face", p_, "nz %.2f" % pn[p_,2], "verts", [tuple(np.round(Wv[v],2)) for v in vs], "depths", np.round(dv[vs],2).tolist())
