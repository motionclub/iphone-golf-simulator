import sys, importlib.util, math
import numpy as np, bpy
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("plv", REPO + "/blender/scripts/postcard_look_verify.py")
V = importlib.util.module_from_spec(spec); sys.modules["plv"] = V; spec.loader.exec_module(V)
design, dpath = V.load_design(10, None); C = V.Ctx(10, design, dpath, V.parse_args(["10"])); S = V.Snap("blend", C)
for (name, pos, fwd, up, right, fov) in V.smoke_shot_cameras(S, C):
    az = math.degrees(math.atan2(fwd.x, fwd.y)); el = math.degrees(math.asin(fwd.z))
    print("CAM", name, "pos", tuple(round(c, 2) for c in pos), "fwd az(deg from +Y toward +X) %.1f el %.1f fov %.0f" % (az, el, fov))
for n, o in S.meshes.items():
    if n.startswith("DRESS_SMOKE") or n == "DRESS_CONE":
        w = S.wld(o); lo = w["W"].min(axis=0); hi = w["W"].max(axis=0)
        print("OBJ", n, "bbox lo", lo.round(1), "hi", hi.round(1))
print("PIN", [round(v, 1) for v in S.pos(S.all["MARKER_PIN"])])
