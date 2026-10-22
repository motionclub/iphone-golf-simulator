import sys, os, runpy, bpy
REPO="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0,REPO+"/blender/scripts")
import postcard_lib as P, postcard_look_lib as L
H=sys.argv[sys.argv.index("--")+1]; OUTB=sys.argv[sys.argv.index("--")+2]
poly=eval(sys.argv[sys.argv.index("--")+3])
OUT=REPO+"/work/postcard-look/v2/review_G/_scr_mp_"+H; os.makedirs(OUT,exist_ok=True)
_o=P.start; P.start=lambda name,out_dir=None:_o(name,out_dir=OUT)
sys.argv=[REPO+"/work/postcard-look/baseline/scripts/hole%s_build.py"%H]
try: runpy.run_path(sys.argv[0],run_name="__main__")
except SystemExit: pass
D=P._ST["D"]
L.look_materials(D); L.retarget_materials(D)
L.build_path(D,poly,width_m=2.6)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=OUTB)
