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
import numpy as _np
L0=L.terrain_top_loops(D)[0][0]
import bmesh
xs=[];
# ribbon of constant width 1.5 m following the first 70 m of the first loop, offset 1.5 m outward-ish (towards water)
pts=_np.array(L0)
seg=_np.hypot(*_np.diff(pts,axis=0).T); sc=_np.concatenate([[0],_np.cumsum(seg)])
sel=pts[sc<70]
tx=_np.gradient(sel[:,0]);ty=_np.gradient(sel[:,1]);n=_np.hypot(tx,ty);tx/=n;ty/=n
out=_np.stack([ty,-tx],1)
vs=[];fs=[]
for k,(p,o) in enumerate(zip(sel,out)):
    vs.append((p[0]+o[0]*2.0,p[1]+o[1]*2.0,0.12)); vs.append((p[0]+o[0]*3.2,p[1]+o[1]*3.2,0.12))
    if k: i=2*k; fs.append((i-2,i-1,i+1,i))
me=bpy.data.meshes.new('WATER_SURF_99'); me.from_pydata(vs,[],fs); me.update()
ob=bpy.data.objects.new('WATER_SURF_99',me); bpy.context.scene.collection.objects.link(ob)
ca=me.color_attributes.new('Col','FLOAT_COLOR','POINT')
nv=len(sel)
for vi,c in enumerate(ca.data):
    k=vi//2
    a=min(1.0,(k-4)/4.0,(nv-1-4-k)/4.0)
    c.color=(0.5,0,0,max(a,0.0))
ob['surf_kind']='blob'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/review_G/mutribbon.blend')

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
