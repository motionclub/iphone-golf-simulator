import sys
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy, numpy as np
import importlib.util
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0], load_ui=False)
opts = m.parse_args(["8"]); design, dpath = m.load_design(8, None); C = m.Ctx(8, design, dpath, opts)
S = m.Snap("blend", C)
bad = 0
for n, o in sorted(S.meshes.items()):
    if not n.startswith("PLANT_VINE"): continue
    pcs = m.mesh_components_world(S, o)
    tops = [round(p[3][2], 1) for p in pcs]
    if min(tops) < 3.0 or len(pcs) > 1:
        bad += 1
        if bad < 12: print(n, "pieces", len(pcs), "tops", tops, "origin z", round(o.location.z, 2), "scale", tuple(round(x, 2) for x in o.scale), "parent", o.parent.name if o.parent else None)
print("bad", bad)
