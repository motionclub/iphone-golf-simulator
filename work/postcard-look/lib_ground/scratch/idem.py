import sys, os, runpy
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, postcard_lib as P, postcard_look_lib as L
o = P.start; P.start = lambda n, out_dir=None: o(n, out_dir=R + "/work/postcard-look/lib_ground/scratch/idem")
sys.argv = ["x"]
runpy.run_path(R + "/work/postcard-look/baseline/scripts/hole09_build.py", run_name="__main__")
D = P._ST["D"]
snap = L.snapshot_ground(D)
L.look_materials(D); L.retarget_materials(D); L.retarget_materials(D)
L.build_cliff_skin(D, "strata"); n1 = len([x for x in bpy.data.objects if x.name.startswith("ROCK_SKIN")])
L.build_cliff_skin(D, "strata", replace=True); n2 = len([x for x in bpy.data.objects if x.name.startswith("ROCK_SKIN")])
L.build_sea(D); s1 = len([x for x in bpy.data.objects if x.name.startswith("WATER_SURF")])
L.build_sea(D); s2 = len([x for x in bpy.data.objects if x.name.startswith("WATER_SURF")])
L.surf_patch(D, (20.0, 10.0), 5.0); s3 = len([x for x in bpy.data.objects if x.name.startswith("WATER_SURF")])
L.assign_uvs(D); L.assign_uvs(D)
# hole code still able to use the old palette names after retarget (hole09_build.sea_stack reads D.mats['MAT_ROUGH'] ...)
mm = [D.mats[n].name for n in ("MAT_ROUGH", "MAT_CLIFF", "MAT_CLIFF_DARK", "MAT_ROCK")]
print("IDEM skin", n1, n2, "surf", s1, s2, s3, "mats ok", mm, "ground", L.compare_ground(D, snap)[0])
for g in L.audit_look(D): print("IDEM", g[0], g[1])
