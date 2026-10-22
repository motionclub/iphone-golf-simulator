"""Re-audit any saved look blend with the v2 gates (postcard_look_lib.v2_gates): builds the frozen baseline design handle D in a
scratch dir, opens the blend, runs the gates.
  Blender -b --factory-startup --python measure_blend.py -- --hole 08 --blend PATH [--pockets "x,y,r;x,y,r"] [--skip shelf,surf,path,wall,skin]
"""
import sys, os, runpy, time
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import numpy as np, bpy
import postcard_lib as P
import postcard_look_lib as L
args = sys.argv[sys.argv.index("--") + 1:]
H = args[args.index("--hole") + 1].zfill(2)
BL = args[args.index("--blend") + 1]
PK = []
if "--pockets" in args:
    for t in args[args.index("--pockets") + 1].split(";"):
        PK.append(tuple(float(v) for v in t.split(",")))
SKIP = args[args.index("--skip") + 1].split(",") if "--skip" in args else []
OUT = os.path.join(REPO, "work/postcard-look/v2/ground/tools/_scratch_%s" % H)
os.makedirs(OUT, exist_ok=True)
_o = P.start
P.start = lambda name, out_dir=None: _o(name, out_dir=OUT)
sys.argv = [os.path.join(REPO, "work/postcard-look/baseline/scripts", f"hole{H}_build.py")]
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit:
    pass
P.start = _o
D = P._ST["D"]
bpy.ops.wm.open_mainfile(filepath=BL)
t0 = time.time()
fns = dict(shelf=lambda: L.shelf_gate(D, pockets=PK), surf=lambda: L.surf_gate(D), path=lambda: L.path_gate(D),
           wall=lambda: L.wall_cover_gate(D, strict=(H == "10")), skin=lambda: L.skin_over_water_gate(D))
for k, f in fns.items():
    if k in SKIP:
        continue
    if k in ("shelf", "surf") and H == "10":
        continue
    t1 = time.time()
    name, ok, det = f()
    print(f"GATE: {name} {'PASS' if ok else 'FAIL'} - {det}   [{time.time() - t1:.1f}s]", flush=True)
tort = L.skin_tortuosity(D)
print("INFO: strata skin mid-row tortuosity", tort)
