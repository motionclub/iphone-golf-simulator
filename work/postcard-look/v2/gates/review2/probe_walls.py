import sys, importlib.util, numpy as np, bpy
REPO="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec=importlib.util.spec_from_file_location("pcv",REPO+"/blender/scripts/postcard_look_verify.py"); m=importlib.util.module_from_spec(spec); sys.modules["pcv"]=m; spec.loader.exec_module(m)
H=int(sys.argv[sys.argv.index("--")+1]); path=sys.argv[sys.argv.index("--")+2]; fbx = len(sys.argv)>sys.argv.index("--")+3
opts=m.parse_args([str(H)])
design,dp=m.load_design(H,None); C=m.Ctx(H,design,dp,opts)
if fbx:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=path); S=m.Snap("fbx",C)
else:
    bpy.ops.wm.open_mainfile(filepath=path,load_ui=False); S=m.Snap("blend",C)
for o in m.coll_objects(S):
    w=S.wld(o); up=(w["N"][:,2]>0.5)
    A=w["A"]
    print(f"{path.split('/')[-1]} {o.name:14s} tris {len(w['T']):6d} up {int(up.sum()):6d} area_up {A[up].sum():10.3f} area_other {A[~up].sum():10.3f} n_other {int((~up).sum())}")
