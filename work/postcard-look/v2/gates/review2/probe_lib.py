import sys, importlib.util, numpy as np, bpy
REPO="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec=importlib.util.spec_from_file_location("pcv",REPO+"/blender/scripts/postcard_look_verify.py"); m=importlib.util.module_from_spec(spec); sys.modules["pcv"]=m; spec.loader.exec_module(m)
sig,err=m.lib_signature(); print("ERR",err)
import postcard_props_lib as PL
bpy.ops.wm.read_factory_settings(use_empty=True)
S0=m.Snap.__new__(m.Snap); S0.stage="fbx"; S0._loc={}; S0._wld={}
for kind in sorted(sig):
    ob=PL.library_object(kind)
    L=S0.loc(ob)
    r=m.rock_shape(L)
    d=sig[kind]["dims"]
    print("%-22s nv %3d nf %3d r2 %.2f r3 %.2f  bbox %s  ncomp %d ok %s"%(kind,r["nv"],r["nf"],r["r2"],r["r3"],np.round(d,2),r["ncomp"],r["ok"]))
