"""Do the ROCK_SKIN faces face OUTWARD (toward the sea)? Horizontal rays from 20 m out at several heights; share of first hits that are front faces."""
import sys, os, runpy
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import numpy as np, bpy
from mathutils import Vector
import postcard_lib as P
import postcard_look_lib as L
args = sys.argv[sys.argv.index("--") + 1:]
H = args[0]; BL = args[1]
OUT = os.path.join(REPO, "work/postcard-look/v2/ground/tools/_scratch_%s" % H)
_o = P.start; P.start = lambda name, out_dir=None: _o(name, out_dir=OUT)
sys.argv = [os.path.join(REPO, "work/postcard-look/baseline/scripts", f"hole{H}_build.py")]
try: runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit: pass
P.start = _o; D = P._ST["D"]
bpy.ops.wm.open_mainfile(filepath=BL)
objs = L._skin_objs()
bv = {o.name: L._bvh_of([o]) for o in objs}
allb = L._bvh_of(objs)
res = {}
for li, (Pl, _) in enumerate(L.terrain_top_loops(D)):
    Pc, s, Lp, N, _ = L._loop_columns(Pl, 3.0)
    front = back = 0
    for i in range(len(Pc)):
        for z in (1.0, 3.0, 5.0):
            o = Vector((Pc[i,0]+N[i,0]*20, Pc[i,1]+N[i,1]*20, z)); d = Vector((-N[i,0], -N[i,1], 0))
            r = allb.ray_cast(o, d, 40)
            if r[0] is None: continue
            who = [nm for nm, b in bv.items() if (lambda rr: rr[0] is not None and abs(rr[3]-r[3]) < 1e-5)(b.ray_cast(o, d, 40))]
            kind = "backing/strata" if not who or True else ""
            if r[1].dot(d) < 0: front += 1
            else: back += 1
    print("loop", li, "first hits front", front, "back", back)
