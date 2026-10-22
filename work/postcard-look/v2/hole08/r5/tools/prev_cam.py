import sys, os, json
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools"); sys.dont_write_bytecode = True
import bpy
import postcard_lib as P
import previews_lib as PV
a=sys.argv[sys.argv.index("--")+1:]; blend,lm,out=a[0],a[1],a[2]
bpy.ops.wm.open_mainfile(filepath=blend); PV.setup_scene()
YD=P.YD
cfg=json.load(open(lm))
sh=[s for s in cfg["shots"] if s["kind"]=="landmark"][0]
pos,look=sh["pos"],sh["look"]
c=PV.cam("CAM_lm",(pos[0]*YD,pos[2]*YD,pos[1]*YD),(look[0]*YD,look[2]*YD,look[1]*YD),sh.get("fov",60.0))
PV.render(c,out,(900,1600),32)
