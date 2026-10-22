"""frame_classes: what the three still cameras see (first-hit object classes on a ray grid; lower 60 % and whole frame). usage: Blender -b --factory-startup --python frame_classes.py -- BLEND [OUT.json]"""
import sys, json, collections, re
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
args = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0])
import hole08_look as K
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
cams = {}
c, l, _b = K.tee_cam(ball=(0.0, 0.0), aim=(19.0, 178.0), ground_z=None); cams["tee"] = (c, l)
c, l, _b = K.tee_cam(ball=(19.0, 178.0), aim=(-6.0, 340.0), ground_z=6.14); cams["approach"] = (c, l)
cams["arch"] = (Vector(K.ARCH_CAM["pos"]), Vector(K.ARCH_CAM["look"]))
out = {}
for nm, (cam, look) in cams.items():
    cam, look = Vector(cam), Vector(look)
    for part, (y0, y1) in (("lower60", (0.4, 1.0)), ("all", (0.0, 1.0))):
        cnt = collections.Counter()
        n = 0
        for j in range(100):
            py = (y0 + (y1 - y0) * (j + 0.5) / 100) * 1600
            for i in range(56):
                px = (i + 0.5) / 56 * 900
                d = K._cam_ray(cam, look, px, py, 900, 1600, 60.0)
                ok, loc, nrm, idx, ob, _m = sc.ray_cast(dg, cam, d, distance=900.0)
                n += 1
                if not ok or ob is None:
                    cnt["sky"] += 1
                    continue
                k = re.sub(r"[._]?\d+$", "", ob.name)
                k = re.sub(r"\.\d+$", "", k)
                if k.startswith("PLANT_TUFT"):
                    k = "FRINGE_TUFT" if "lk_fringe" in ob.keys() else ("OUTCROP_TUFT" if "lk_outcrop_fringe" in ob.keys() else ("CROWN_TUFT" if "lk_shrub_tuft" in ob.keys() else "CARPET_TUFT"))
                cnt[k] += 1
        out[f"{nm}/{part}"] = {k: round(v / n, 4) for k, v in cnt.most_common(14)}
        out[f"{nm}/{part}"]["_tuft_share"] = round(sum(v for k, v in cnt.items() if k.endswith("_TUFT")) / n, 4)
        out[f"{nm}/{part}"]["_plant_share"] = round(sum(v for k, v in cnt.items() if k.startswith("PLANT_") or k.endswith("_TUFT")) / n, 4)
        print("FRAME", nm, part, {k: f"{v / n:.1%}" for k, v in cnt.most_common(9)}, "tuft share", f"{sum(v for k, v in cnt.items() if k.endswith(chr(95) + chr(84) + chr(85) + chr(70) + chr(84))) / n:.1%}")
if len(args) > 1:
    json.dump(out, open(args[1], "w"), indent=1)
