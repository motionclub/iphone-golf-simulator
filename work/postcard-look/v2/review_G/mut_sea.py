import sys, os, runpy, bpy
REPO="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0,REPO+"/blender/scripts")
import postcard_lib as P, postcard_look_lib as L
a=sys.argv[sys.argv.index("--")+1:]
H,OUTB,seed=a[0],a[1],int(a[2])
OUT=REPO+"/work/postcard-look/v2/review_G/_scr_ms_"+H; os.makedirs(OUT,exist_ok=True)
_o=P.start; P.start=lambda name,out_dir=None:_o(name,out_dir=OUT)
sys.argv=[REPO+"/work/postcard-look/baseline/scripts/hole%s_build.py"%H]
try: runpy.run_path(sys.argv[0],run_name="__main__")
except SystemExit: pass
D=P._ST["D"]
L.look_materials(D)
if H=="10": L.retarget_materials(D,overrides=L.CRATER_OVERRIDES)
else: L.retarget_materials(D)
loops=L.terrain_top_loops(D)
if H=="10":
    pin=P.m(*D.hole.pin)
    pillar=[i for i,(Pl,_) in enumerate(loops) if P.point_in_poly(pin,[tuple(p) for p in Pl])]
    rim=[i for i in range(len(loops)) if i not in pillar]
    L.build_cliff_skin(D,style="basalt",loops=rim,follow_undercut=0.0,seed=seed)
    L.build_cliff_skin(D,style="basalt",loops=pillar,follow_undercut=1.0,seed=seed+1)
    L.build_lava(D,lights=4)
else:
    L.build_cliff_skin(D,style="strata",seed=seed)
    L.build_sea(D,seed=seed,**(eval(os.environ.get('SEAKW','{}'))))
L.assign_uvs(D)
for n,ok,det in L.v2_gates(D,pockets=L.sea_pockets(D,[]) if H!="10" else None): print("LIBGATE",n,"PASS" if ok else "FAIL",det[:160])
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=OUTB)
