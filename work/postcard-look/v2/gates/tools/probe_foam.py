import sys, importlib.util, numpy as np
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
import bpy
argv = sys.argv[sys.argv.index("--")+1:]
hole = int(argv[0]); f = argv[1]; cx, cy, rad = float(argv[2]), float(argv[3]), float(argv[4])
opts = m.parse_args([str(hole), "--look-dir", REPO + "/work/postcard-look/v2/gates/fixtures/look_at_run"])
design, dpath = m.load_design(hole, None); C = m.Ctx(hole, design, dpath, opts)
bpy.ops.wm.open_mainfile(filepath=f, load_ui=False)
S = m.Snap("blend", C)
V, T, A, own = m.white_geometry(S, C)
cen = V[T].mean(axis=1)
sel = np.hypot(cen[:,0]-cx, cen[:,1]-cy) < rad
names = sorted(set(np.array(own, object)[sel].tolist()))
print("owners", names)
for n in names:
    o = S.meshes[n]; lo, hi = S.wbbox(o)
    print(" ", n, "bbox", np.round(lo,1).tolist(), np.round(hi,1).tolist())
# distance to shore loops
loops = m.terrain_loops(S)
d = np.min(np.stack([m.dist_polyline(cen[sel][:, :2], L_[0], closed=True) for L_ in loops]), axis=0)
print("dist to shore of the white tris: min %.1f max %.1f" % (d.min(), d.max()))
