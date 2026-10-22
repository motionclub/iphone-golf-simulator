import sys, os
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools"); sys.dont_write_bytecode = True
import bpy
import previews_lib as PV
a=sys.argv[sys.argv.index("--")+1:]; blend,out=a[0],a[1]
tag=os.path.basename(os.path.dirname(blend))
bpy.ops.wm.open_mainfile(filepath=blend); PV.setup_scene()
VIEWS = {"aerial_all": ((70.0, -45.0, 62.0), (-5.0, 215.0, 3.0), 36), "aerial_green": ((-60.0, 200.0, 40.0), (8.0, 300.0, 2.0), 40)}
for n,(loc,look,fov) in VIEWS.items():
    PV.render(PV.cam("CAM_"+n,loc,look,fov), os.path.join(out,f"{n}_{tag}.png"), (1600,900), 24)
