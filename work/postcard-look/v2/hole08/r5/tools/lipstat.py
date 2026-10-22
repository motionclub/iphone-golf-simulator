import sys
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
import hole08_look as K
print("LIPSTAT", sys.argv[sys.argv.index("--")+1], K.lip_uv_stats())
