import sys
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
import hole08_look as K
w, rep = K.tee_path_seam_jump()
print("SEAMJUMP", sys.argv[sys.argv.index("--")+1].split("/")[-2], "max %.1f px"%w, rep)
