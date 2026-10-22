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
gb = L._bvh_of([o for o in L._export_meshes(D) if o.name.startswith(L.GROUND_PREFIXES)], up_only=True, nz_min=0.5)
for po in [o for o in bpy.data.objects if o.name.startswith("DRESS_PATH")]:
    Wp = L._mesh_arrays(po)[0]
    bad = []
    for k in range(len(Wp)):
        hit = gb.ray_cast(Vector((Wp[k,0], Wp[k,1], 9.0)), Vector((0,0,-1)), 20)
        if hit[0] is None: continue
        ex = Wp[k,2]-hit[0].z
        if ex > 0.0125: bad.append((k, round(ex,3), Wp[k].round(2).tolist(), round(hit[0].z,3)))
    print(po.name, len(Wp), "bad", len(bad)); print(bad[:12])
