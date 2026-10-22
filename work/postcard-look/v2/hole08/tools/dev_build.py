"""dev driver: scoring build of hole 8 + look pass, save blend, render quick views.  Blender -b --factory-startup --python dev_build.py -- OUTDIR [--no-render]"""
import sys, os, time
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
import postcard_lib as P
import postcard_look_lib as L
import hole08_build as B
import hole08_look as K
args = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(args[0])
os.makedirs(OUT, exist_ok=True)
t0 = time.time()
D = P.start("hole08_design", out_dir=OUT)
P.build_terrain(D)
B.weld_terrain(D); B.fix_overhangs(D); B.split_deep_band(D)
P.build_play_surfaces(D)
P.build_water(D)
B.tidy_all_flat(D)
B.trim_lip_off_green(D)
P.build_gameplay(D)
P.build_cameras_and_light(D, overview_rot_deg=B.OVERVIEW_ROT)
print(f"[dev] scoring build {time.time()-t0:.1f}s", flush=True)
t1 = time.time()
info = K.look_pass(D)
print(f"[dev] look pass {time.time()-t1:.1f}s", flush=True)
for name, ok, detail in K.look_gates(D, info):
    print(f"GATE: {name} {'PASS' if ok else 'FAIL'} - {detail}", flush=True)
print("COMPARE", info["compare_ok"])
st = P.stats(D); print("TRIS", st["tris"], "objects", st["objects"])
for name, ok, detail in L.audit_look(D) + L.v2_gates(D, pockets=L.sea_pockets(D, info["pockets"])):
    print(f"GATE: {name} {'PASS' if ok else 'FAIL'} - {detail}", flush=True)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "dev_hole_08.blend"))
if "--no-render" not in args:
    import previews_lib as PV
    PV.quick(OUT)
