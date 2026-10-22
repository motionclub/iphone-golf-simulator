import sys, os
sys.dont_write_bytecode = True
HERE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "..", "blender", "scripts"))
sys.path.insert(0, HERE)
import numpy as np, bpy
import postcard_props_lib as PL
bpy.ops.wm.read_factory_settings(use_empty=True)
lib = PL.ensure_library()
TH = dict(root_max=0.05, tip_min=0.6, tip_min_low=0.25, b_max=0.02, a_min=0.98, rise_corr=0.5, root_frac=0.04)
for k in sorted(PL.PLANT_KINDS):
    me = lib[k].data
    c = PL.mesh_sway(me)
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); V = co.reshape(-1, 3)
    z = V[:, 2]; h = max(float(z.max() - z.min()), 1e-6)
    vine = k.startswith("PLANT_VINE")
    t = (z.max() - z) / h if vine else (z - z.min()) / h
    R = c["R"]
    root = t <= TH["root_frac"]
    r_root = float(R[root].max()) if root.any() else float(R[np.argmin(t)])
    corr = float(np.corrcoef(R, t)[0, 1]) if R.std() > 1e-6 and t.std() > 1e-6 else 0.0
    low = k.startswith(("PLANT_SHRUB", "PLANT_TREE", "PLANT_PINE"))
    tmin = TH["tip_min_low"] if low else TH["tip_min"]
    ok = r_root <= TH["root_max"] and float(R.max()) > tmin and corr >= TH["rise_corr"]
    print(f"{k:22s} root {r_root:.3f} tip {float(R.max()):.2f} (> {tmin}) corr {corr:.2f} (>= 0.5) -> {'ok' if ok else 'FAIL'}")
