import sys, os, runpy
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import numpy as np, bpy
from mathutils import Vector
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
c = L.wall_cover_test(D, 2.0)
pts = [p for p in c["pts"] if p[0] == "aerial"]
print("aerial exposed", len(pts)); print(pts)
