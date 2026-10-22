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
pz = D.play_z
terr = L._terrain_ob(D); tb = L._bvh_of([terr]); sk = L._bvh_of(L._skin_objs()); allb = L._bvh_of([terr] + L._skin_objs())
rows = []
for li, (Pl, _) in enumerate(L.terrain_top_loops(D)):
    Pc, s, Lp, N, _ = L._loop_columns(Pl, 1.0)
    for i in range(len(Pc)):
        n = N[i]
        for z in (1.5, 3.0, 4.5, 5.4, 5.8):
            o = Vector((Pc[i,0]+n[0]*6, Pc[i,1]+n[1]*6, z))
            # horizontal view: from 6 m straight in; and from a steep aerial
            for name, V in (("flat", o), ("steep", Vector((Pc[i,0]+n[0]*8, Pc[i,1]+n[1]*8, z+10)))):
                h = tb.ray_cast(o, Vector((-n[0], -n[1], 0)), 30)
                if h[0] is None: continue
                W = h[0]
                dv = W - V
                hh = allb.ray_cast(V, dv.normalized(), dv.length + 0.05)
                if hh[0] is None: continue
                ht = tb.ray_cast(V, dv.normalized(), dv.length + 0.05)
                if ht[0] is not None and abs(ht[3]-hh[3]) < 1e-5 and (ht[0]-W).length < 0.3:
                    rows.append((li, round(float(s[i]),1), round(float(Lp),0), z, name, round(W.x,1), round(W.y,1), round(W.z,2)))
print("exposed", len(rows))
import collections
c = collections.Counter((r[0], r[4], r[3]) for r in rows)
print(sorted(c.items()))
# run lengths along s for loop/ z=5.4 flat
for li in set(r[0] for r in rows):
    ss = sorted(set(r[1] for r in rows if r[0]==li and r[3]==5.4 and r[4]=="flat"))
    print("loop", li, "s positions exposed at z5.4 flat:", ss[:60])
print("---- detail loop 1")
ells = L._water_ellipses(D)
loops = L.terrain_top_loops(D)
Pl = loops[1][0]
Pc, s, Lp, N, _ = L._loop_columns(Pl, 1.0)
for i in range(0, 30, 3):
    n = N[i]
    z = 3.0
    o = Vector((Pc[i,0]+n[0]*6, Pc[i,1]+n[1]*6, z))
    h = tb.ray_cast(o, Vector((-n[0], -n[1], 0)), 30)
    hs = sk.ray_cast(o, Vector((-n[0], -n[1], 0)), 30)
    dep = float(L._ell_depth(ells, [Pc[i,0]], [Pc[i,1]])[0])
    print("s %.1f P (%.1f,%.1f) n (%.2f,%.2f) wallhit %s dist %.2f skinhit %s dist %s ell_depth_at_P %.2f" % (s[i], Pc[i,0], Pc[i,1], n[0], n[1], None if h[0] is None else tuple(round(v,2) for v in h[0]), h[3] if h[0] else -1, None if hs[0] is None else tuple(round(v,2) for v in hs[0]), None if hs[0] is None else round(hs[3],2), dep))
