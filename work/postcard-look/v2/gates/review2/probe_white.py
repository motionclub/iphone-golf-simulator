import sys, importlib.util, numpy as np, bpy
REPO="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec=importlib.util.spec_from_file_location("pcv",REPO+"/blender/scripts/postcard_look_verify.py"); m=importlib.util.module_from_spec(spec); sys.modules["pcv"]=m; spec.loader.exec_module(m)
a=sys.argv[sys.argv.index("--")+1:]
H=int(a[0]); path=a[1]; look=a[2] if len(a)>2 else m.LOOK_DIR
opts=m.parse_args([str(H)]); opts["look_dir"]=look
design,dp=m.load_design(H,None); C=m.Ctx(H,design,dp,opts)
bpy.ops.wm.open_mainfile(filepath=path,load_ui=False); S=m.Snap("blend",C)
print("WHITE", sorted(m.white_materials(S,C)))
V,T,A,own=m.white_geometry(S,C)
import collections
print("WHITEGEO tris",len(T),"area %.1f"%A.sum(), collections.Counter(own).most_common(6))
for k,(tile,cf,nf,ef) in m.LK.items():
    px=m.look_png(C,cf) if cf else None
    if px is not None:
        op=px[...,3]>0.05
        if op.any():
            h,s,v=m.mean_hsv(px[...,:3][op].mean(0)); print(k,cf,"hsv %.0f %.2f %.2f"%(h,s,v))
