"""-- BLEND OUT.png X Y Z TX TY TZ FOV W H [samples]   (Blender metres, world)"""
import sys, os
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
import postcard_lib as P
import previews_lib as PV
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
PV.setup_scene()
x, y, z, tx, ty, tz, fov = [float(v) for v in a[2:9]]
W, H = int(a[9]), int(a[10])
s = int(a[11]) if len(a) > 11 else 32
c = PV.cam("CAM_X", (x, y, z), (tx, ty, tz), fov)
PV.render(c, a[1], (W, H), s)
