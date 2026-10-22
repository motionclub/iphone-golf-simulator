import bpy
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/golf-tailoring/export/Golf_Female_Draft.blend")
r=bpy.data.objects["Rig_Female"]
for n in ["Head","LeftUpperArm","RightUpperArm"]:
 b=r.data.bones[n];print(n,tuple(b.head_local),"forwardlocal",tuple(b.matrix_local.inverted().to_3x3()@Vector((0,-1,0))))
