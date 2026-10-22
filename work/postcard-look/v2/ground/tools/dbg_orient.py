import sys, os, runpy
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import numpy as np, bpy
import postcard_lib as P
import postcard_look_lib as L
H = sys.argv[sys.argv.index("--") + 1]
OUT = os.path.join(REPO, "work/postcard-look/v2/ground/tools/_scratch_%s" % H)
_o = P.start; P.start = lambda name, out_dir=None: _o(name, out_dir=OUT)
sys.argv = [os.path.join(REPO, "work/postcard-look/baseline/scripts", f"hole{H}_build.py")]
try: runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit: pass
D = P._ST["D"]
for li, (Pl, _) in enumerate(L.terrain_top_loops(D)):
    Pc, s, Lp, N, _ = L._loop_columns(Pl, 1.0)
    sd = P.signed_dist_m(D, Pc[:, 0] + 0.8 * N[:, 0], Pc[:, 1] + 0.8 * N[:, 1])
    print("loop", li, "signed area %.0f" % P.signed_area(Pl), "N points to water at %.0f%% of columns" % (100 * (sd > 0).mean()), "n", len(Pc))
