import sys, importlib.util, numpy as np, bpy
REPO="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec=importlib.util.spec_from_file_location("pcv",REPO+"/blender/scripts/postcard_look_verify.py"); m=importlib.util.module_from_spec(spec); sys.modules["pcv"]=m; spec.loader.exec_module(m)
sys.path.insert(0, REPO+"/blender/scripts")
bpy.ops.wm.read_factory_settings(use_empty=True)
mt=bpy.data.materials.new("LK_ROCK")
S0=m.Snap.__new__(m.Snap); S0.stage="fbx"; S0._loc={}; S0._wld={}
def rep(name, me):
    ob=bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    L=S0.loc(ob); r=m.rock_shape(L)
    print("%-28s nv %3d nf %3d r2 %.3f r3 %.3f ok %s"%(name, r["nv"], r["nf"], r["r2"], r["r3"], r["ok"]))
for seed in (77, 5, 9, 4):
    for (bx,by,bz) in ((1,1,1),(4,0.5,1),(5,0.4,1),(3,1,1),(2,1,1),(2,0.5,1)):
        me=m.st_hull_rock("H%d"%seed, seed, "LK_ROCK", dims=(2.0,1.6,1.2))
        for v in me.vertices:
            v.co.x*=bx; v.co.y*=by; v.co.z*=bz
        me.update()
        rep("hull%d_%g_%g_%g"%(seed,bx,by,bz), me)
