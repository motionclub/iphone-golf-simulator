"""fbx_fold_check: the arch fold numbers on the FBX RE-IMPORT (do the custom normals survive the exporter?). usage: Blender -b --factory-startup --python fbx_fold_check.py -- STAGED.fbx [OUT.json]"""
import sys, json
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy
args = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=args[0], axis_forward='-Z', axis_up='Y')
import hole08_look as K
r = K.arch_fold_metric()
print("FBXFOLD", json.dumps(r))
if len(args) > 1:
    json.dump(r, open(args[1], "w"), indent=1)
