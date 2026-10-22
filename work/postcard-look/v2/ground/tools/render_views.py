"""Blender previews (EEVEE, NOT Game view) of a saved look blend from camera specs.
  Blender -b --factory-startup --python render_views.py -- --blend PATH --out DIR --views 'name:x,y,z>tx,ty,tz@fov@WxH;...'
fov = vertical degrees (default 50), WxH default 1400x900."""
import sys, os, math
sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
args = sys.argv[sys.argv.index("--") + 1:]
BL = args[args.index("--blend") + 1]; OUT = args[args.index("--out") + 1]; VIEWS = args[args.index("--views") + 1]
bpy.ops.wm.open_mainfile(filepath=BL)
sc = bpy.context.scene
try: sc.view_settings.view_transform = 'AgX'
except Exception: pass
bg = sc.world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.30, 0.55, 0.88, 1.0); bg.inputs[1].default_value = 1.0
for nm in ("BALL_START", "HOLE_CUP", "MARKER_TEE", "MARKER_PIN", "MARKER_UP"):
    if bpy.data.objects.get(nm) is not None: bpy.data.objects[nm].hide_render = True
os.makedirs(OUT, exist_ok=True)
for spec in VIEWS.split(";"):
    name, rest = spec.split(":", 1)
    parts = rest.split("@")
    loc, tgt = parts[0].split(">")
    loc = Vector(tuple(float(v) for v in loc.split(","))); tgt = Vector(tuple(float(v) for v in tgt.split(",")))
    fov = float(parts[1]) if len(parts) > 1 and parts[1] else 50.0
    w, h = (int(v) for v in parts[2].split("x")) if len(parts) > 2 else (1400, 900)
    cam = bpy.data.cameras.new("CAMV_" + name); ob = bpy.data.objects.new("CAMV_" + name, cam)
    sc.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    cam.clip_start = 0.1; cam.clip_end = 6000; cam.sensor_fit = 'VERTICAL'; cam.angle_y = math.radians(fov)
    sc.camera = ob; sc.render.resolution_x, sc.render.resolution_y = w, h; sc.render.resolution_percentage = 100
    sc.render.filepath = os.path.join(OUT, name + ".png"); sc.render.image_settings.file_format = 'PNG'
    try: sc.eevee.taa_render_samples = 24
    except Exception: pass
    bpy.ops.render.render(write_still=True)
    print("rendered", name)
