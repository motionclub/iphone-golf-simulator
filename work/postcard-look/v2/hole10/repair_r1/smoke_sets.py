"""smoke_sets.py: evaluate many smoke-group sets in ONE Blender session.
  Blender -b STAGE.blend --python smoke_sets.py -- SETS.json [--shot tee|approach|lavarim|all]
SETS.json = {"name": [ {"cam":[x,y], "p":[x,y,z], "wh":[w,h], "n":3, "seed":1, "spread":0.1}, ... ], ...}
Uses hole10_look.smoke_group (the builder of the real build) and the verifier's smoke_frame_alpha."""
import sys, os, json, importlib.util
import numpy as np
import bpy
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
args = sys.argv[sys.argv.index("--") + 1:]
sets = json.load(open(args[0]))
spec = importlib.util.spec_from_file_location("plv", REPO + "/blender/scripts/postcard_look_verify.py")
V = importlib.util.module_from_spec(spec); sys.modules["plv"] = V; spec.loader.exec_module(V)
import postcard_props_lib as PL
import hole10_look as HL
design, dpath = V.load_design(10, None)
C = V.Ctx(10, design, dpath, V.parse_args(["10"]))
root = bpy.data.objects["HOLE_10_ROOT"]
for name, groups in sets.items():
    for o in [o for o in bpy.data.objects if o.name.startswith("DRESS_SMOKE")]:
        bpy.data.objects.remove(o, do_unlink=True)
    for g in groups:
        for ob in HL.smoke_group(None, tuple(g["cam"]), tuple(g["p"]), tuple(g["wh"]), g.get("n", 3), g.get("seed", 1), g.get("spread", 0.10)):
            ob.parent = root
    bpy.context.view_layer.update()
    S = V.Snap("blend", C)
    grids, why = V.smoke_frame_alpha(S, C)
    row = {k.split("_", 1)[1][:8]: round(100 * float((g >= 0.3).mean()), 2) for k, g in grids.items()}
    print("SET", name, row, flush=True)
    if "--ppm" in args:
        outd = args[args.index("--ppm") + 1]; os.makedirs(outd, exist_ok=True)
        for k, g in grids.items():
            h, w = g.shape
            rgb = np.zeros((h, w, 3), np.uint8); rgb[..., 0] = np.clip(g * 255, 0, 255).astype(np.uint8); rgb[..., 1] = np.where(g >= 0.3, 255, 0).astype(np.uint8)
            open(os.path.join(outd, "%s__%s.ppm" % (name, k)), "wb").write(b"P6 %d %d 255\n" % (w, h) + rgb.tobytes())
