import sys, importlib.util, numpy as np, bpy
REPO="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec=importlib.util.spec_from_file_location("pcv",REPO+"/blender/scripts/postcard_look_verify.py"); m=importlib.util.module_from_spec(spec); sys.modules["pcv"]=m; spec.loader.exec_module(m)
H=int(sys.argv[sys.argv.index("--")+1]); path=sys.argv[sys.argv.index("--")+2]
opts=m.parse_args([str(H)])
design,dp=m.load_design(H,None); C=m.Ctx(H,design,dp,opts)
bpy.ops.wm.open_mainfile(filepath=path,load_ui=False); S=m.Snap("blend",C)
for n,o in S.meshes.items():
    um=S.used_mats(o)
    if um & {"LK_FALL","LK_SURF"} or n.startswith("WATER_FALL"):
        w=S.wld(o); nz=w["N"][:,2]; names=np.array(w["names"],object)[w["mi"]]
        lo,hi=S.wbbox(o)
        print(n, sorted(um), "tris",len(w["T"]), "nz min/mean/max %.2f %.2f %.2f"%(nz.min(),nz.mean(),nz.max()), "area %.1f"%w["A"].sum(), "bbox", np.round(lo,1), np.round(hi,1))
