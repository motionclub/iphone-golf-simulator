"""arch_fold_probe: the ARCH_FOLD_SOFT numbers of a staged blend. usage: Blender -b --factory-startup --python arch_fold_probe.py -- BLEND [OUT.json]"""
import sys, json
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy
args = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0])
import hole08_look as K
r = K.arch_fold_metric()
print("ARCHFOLD", json.dumps(r))
if len(args) > 1:
    json.dump(r, open(args[1], "w"), indent=1)
