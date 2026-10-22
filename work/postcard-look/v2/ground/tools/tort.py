import sys, os, runpy, time
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import numpy as np, bpy
import postcard_lib as P
import postcard_look_lib as L
args = sys.argv[sys.argv.index("--") + 1:]
H = args[args.index("--hole") + 1].zfill(2)
OUT = os.path.join(REPO, "work/postcard-look/v2/ground/tools/_scratch_%s" % H)
_o = P.start; P.start = lambda name, out_dir=None: _o(name, out_dir=OUT)
sys.argv = [os.path.join(REPO, "work/postcard-look/baseline/scripts", f"hole{H}_build.py")]
try: runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit: pass
P.start = _o; D = P._ST["D"]
L.look_materials(D); L.retarget_materials(D)
def rowtort(NR=13):
    out = np.zeros(NR); k = 9
    for r in range(NR):
        t = []
        for o in L._skin_objs():
            Wv = L._mesh_arrays(o)[0].reshape(-1, NR, 3)
            Wm = Wv[:, r, :2]
            raw = np.linalg.norm(np.diff(Wm, axis=0), axis=1).sum()
            sm = np.stack([np.convolve(Wm[:, c], np.ones(k) / k, mode="valid") for c in range(2)], 1)
            ls_ = np.linalg.norm(np.diff(sm, axis=0), axis=1).sum() * len(Wm) / max(len(sm), 1)
            t.append(raw / ls_)
        out[r] = np.mean(t)
    return out
for jag in [float(v) for v in args[args.index("--jag") + 1].split(",")]:
    L.build_cliff_skin(D, style="strata", jag_m=jag, replace=True)
    rt = rowtort()
    print("jag", jag, "row6 %.3f" % rt[6], "rows", np.round(rt, 3).tolist())
