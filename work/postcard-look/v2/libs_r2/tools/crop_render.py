"""High-resolution crop render of a Game camera. usage: Blender -b --factory-startup --python crop_render.py -- BLEND LANDMARKS.json SHOT OUT.png x0 y0 x1 y1 [scale=6] [samples=16]
(x, y in the 900x1600 frame, y from the top). Not Game-view proof."""
import sys, os, json, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
import postcard_lib as P
import previews_lib as PV
a = sys.argv[sys.argv.index("--") + 1:]
blend, lm, shot, out = a[:4]
x0, y0, x1, y1 = [float(v) for v in a[4:8]]
scale = int(a[8]) if len(a) > 8 else 6
samples = int(a[9]) if len(a) > 9 else 16
bpy.ops.wm.open_mainfile(filepath=blend)
cfg = json.load(open(lm))
LOOK = REPO + "/Unity/Assets/Resources/Course/Look/"
for im in bpy.data.images:
    if im.name.endswith(".png") and os.path.isfile(LOOK + im.name):
        im.filepath = LOOK + im.name
        im.reload()
PV.setup_scene()
class DD: play_z = 6.0
D = DD(); YD = P.YD
sh = {s["name"]: s for s in cfg["shots"]}[shot]
if sh["kind"] == "address":
    c = PV.address_cam("CAM_F", tuple(sh["ball"]), tuple(sh["aim"]), D)
else:
    pos, look = sh["pos"], sh["look"]
    c = PV.cam("CAM_F", (pos[0] * YD, pos[2] * YD, pos[1] * YD), (look[0] * YD, look[2] * YD, look[1] * YD), sh.get("fov", 60.0))
sc = bpy.context.scene
sc.camera = c
sc.render.resolution_x, sc.render.resolution_y = 900, 1600
sc.render.resolution_percentage = scale * 100
sc.render.use_border = True
sc.render.use_crop_to_border = True
sc.render.border_min_x = x0 / 900; sc.render.border_max_x = x1 / 900
sc.render.border_min_y = 1 - y1 / 1600; sc.render.border_max_y = 1 - y0 / 1600
sc.render.film_transparent = False
try:
    sc.eevee.taa_render_samples = samples
except Exception:
    pass
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("RENDERED", out)
