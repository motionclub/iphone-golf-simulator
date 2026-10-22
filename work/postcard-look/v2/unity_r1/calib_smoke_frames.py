# Blender -b --factory-startup --python calib_smoke_frames.py -- <hole blend>   : geometric smoke share per proof frame (+ the aerial) at several effective-alpha thresholds
import sys, os, importlib.util, json
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
import bpy
argv = sys.argv[sys.argv.index("--") + 1:]
blend = argv[0] if argv else REPO + "/blender/hole_10.blend"
opts = m.parse_args(["10"])
design, dpath = m.load_design(10, None)
C = m.Ctx(10, design, dpath, opts)
bpy.ops.wm.open_mainfile(filepath=blend, load_ui=False)
S = m.Snap("blend", C)
cams = m.smoke_shot_cameras(S, C)
cams += m.smoke_shot_cameras(S, C, [dict(name="hole10_aerial", kind="landmark", pos=[-25, 60, 20], look=[170, 0, 120], fov=60)])
grids, why = m.smoke_frame_alpha(S, C, cams)
out = {}
for k, g in grids.items():
    out[k] = {str(a): round(float((g >= a).mean()) * 100, 3) for a in (0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6)}
    print("CAL", k, out[k])
json.dump(out, open(os.path.join(REPO, "work/postcard-look/v2/unity_r1/calib_smoke_frames.json"), "w"), indent=1)
