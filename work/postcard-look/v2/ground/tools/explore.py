"""Exploration: build baseline hole N into a scratch dir and print loops, hazards, ROCK objects. Blender -b ... -- --hole 08"""
import sys, os, runpy
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import numpy as np, bpy
import postcard_lib as P
import postcard_look_lib as L
args = sys.argv[sys.argv.index("--") + 1:]
H = args[args.index("--hole") + 1].zfill(2)
OUT = os.path.join(REPO, "work/postcard-look/v2/ground/tools/_scratch_%s" % H)
os.makedirs(OUT, exist_ok=True)
_o = P.start
P.start = lambda name, out_dir=None: _o(name, out_dir=OUT)
sys.argv = [os.path.join(REPO, "work/postcard-look/baseline/scripts", f"hole{H}_build.py")]
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit:
    pass
D = P._ST["D"]
print("play_z", D.play_z, "number", D.number)
loops = L.terrain_top_loops(D)
tot = 0
for i, (Pl, _) in enumerate(loops):
    seg = np.roll(Pl, -1, 0) - Pl
    ln = float(np.hypot(seg[:, 0], seg[:, 1]).sum())
    tot += ln
    print("loop", i, "verts", len(Pl), "len %.1f" % ln, "area %.0f" % P.signed_area(Pl), "bbox", Pl.min(0).round(1), Pl.max(0).round(1))
print("total loop length", round(tot, 1))
for h in D.hole.hazards:
    print("hazard", h)
print("shore bbox", P._shore_bbox_m(D))
rocks = [o for o in bpy.data.objects if o.name.startswith(("ROCK", "CLIFF_ROCK")) and o.type == 'MESH']
print("rocks", len(rocks))
for o in rocks[:200]:
    W = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
    c = W.mean(0)
    print(o.name, "verts", len(o.data.vertices), "zmin %.2f zmax %.2f" % (W[:, 2].min(), W[:, 2].max()), "c", c.round(1), "sd %.1f" % float(P.signed_dist_m(D, np.array([c[0]]), np.array([c[1]]))[0]))
print("SCENERY keys", list(D.SCENERY.keys()) if hasattr(D, "SCENERY") else None)
