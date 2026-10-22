import sys, os, runpy, time
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender/scripts"))
sys.dont_write_bytecode = True
import postcard_lib as P
OUT = sys.argv[sys.argv.index("--") + 1]
hole = sys.argv[sys.argv.index("--") + 2]
os.makedirs(OUT, exist_ok=True)
_orig = P.start
P.start = lambda name, out_dir=None: _orig(name, out_dir=OUT)
t = time.time()
script = os.path.join(REPO, "work/postcard-look/baseline/scripts", f"hole{hole}_build.py")
sys.argv = [script]
try:
    runpy.run_path(script, run_name="__main__")
except SystemExit as e:
    print("build exit", e.code)
D = P._ST["D"]
print("BUILD SECONDS", time.time() - t)
import numpy as np
for L, k in zip(D.loops, D.loop_kinds):
    A = np.array(L); per = np.hypot(*(np.roll(A, -1, 0) - A).T).sum()
    print("loop", k, len(L), "perimeter m", round(per, 1))
for ob in sorted(bpy.data.objects, key=lambda o: o.name) if False else []:
    pass
import bpy
names = sorted(o.name for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith(("ROCK_", "CLIFF_ROCK")))
for n in names:
    o = bpy.data.objects[n]
    print(n, len(o.data.vertices), len(o.data.polygons), [m.name for m in o.data.materials], tuple(round(c, 3) for c in o.matrix_world.translation))
