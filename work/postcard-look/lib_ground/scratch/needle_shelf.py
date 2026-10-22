import sys, runpy
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, postcard_lib as P, postcard_look_lib as L
o = P.start; P.start = lambda n, out_dir=None: o(n, out_dir=R + "/work/postcard-look/lib_ground/scratch/needle_tmp")
sys.argv = ["x"]
try:
    runpy.run_path(R + "/work/postcard-look/baseline/scripts/hole08_build.py", run_name="__main__")
except SystemExit:
    pass
D = P._ST["D"]; snap = L.snapshot_ground(D)
L.look_materials(D); L.retarget_materials(D); L.build_cliff_skin(D, "strata"); L.build_sea(D, shelf_m=(6.0, 14.0)); L.assign_uvs(D)
print("NEEDLE ground", L.compare_ground(D, snap))
for g in L.audit_look(D): print("NEEDLE", g[0], g[1], g[2][:150])
