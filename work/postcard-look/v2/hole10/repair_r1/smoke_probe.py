"""Smoke-card iteration tool: Blender -b STAGE.blend --python smoke_probe.py -- [--cards JSON | --keep] [--out DIR] [--alpha 0.3]
Runs the verifier's own smoke_frame_alpha (postcard_look_verify imported as a module) on the blend, optionally replacing the DRESS_SMOKE cards by
the cards of a JSON list [[x,y,z,w,h,seed,fx,fy], ...] (Blender metres; face = (fx, fy)). Writes <out>/smoke_<shot>.png (alpha grid) and prints shares."""
import sys, os, json, importlib.util
import numpy as np
import bpy
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def opt(n, d=None): return args[args.index(n) + 1] if n in args else d
spec = importlib.util.spec_from_file_location("plv", REPO + "/blender/scripts/postcard_look_verify.py")
V = importlib.util.module_from_spec(spec); sys.modules["plv"] = V; spec.loader.exec_module(V)
import postcard_props_lib as PL
if opt("--cards"):
    items = json.load(open(opt("--cards")))
    for o in [o for o in bpy.data.objects if o.name.startswith("DRESS_SMOKE")]:
        bpy.data.objects.remove(o, do_unlink=True)
    root = bpy.data.objects["HOLE_10_ROOT"]
    for k, (x, y, z, w, h, seed, fx, fy) in enumerate(items):
        obs = PL.build_smoke_cards(None, [((x, y, z), w, h)], seed=seed, face=(fx, fy))
        for ob in obs:
            ob.parent = root
bpy.context.view_layer.update()
design, dpath = V.load_design(10, None)
opts = V.parse_args(["10"])
C = V.Ctx(10, design, dpath, opts)
S = V.Snap("blend", C)
alpha = float(opt("--alpha", "0.3"))
grids, why = V.smoke_frame_alpha(S, C)
out = opt("--out")
if out: os.makedirs(out, exist_ok=True)
for k, g in grids.items():
    print("SMOKE", k, "share>=%.2f: %.2f %%" % (alpha, 100 * float((g >= alpha).mean())), "max alpha %.2f" % float(g.max()), "share>0.05: %.1f %%" % (100 * float((g > 0.05).mean())))
    if out:
        h, w = g.shape
        rgb = np.zeros((h, w, 3), np.uint8)
        rgb[..., 0] = np.clip(g * 255 * 1.0, 0, 255).astype(np.uint8)
        rgb[..., 1] = np.where(g >= alpha, 255, 0).astype(np.uint8)
        with open(os.path.join(out, "smoke_%s.ppm" % k), "wb") as fh:
            fh.write(b"P6 %d %d 255\n" % (w, h)); fh.write(rgb.tobytes())
