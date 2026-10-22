import sys, math, os
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import bpy
from mathutils import Vector
args = sys.argv[sys.argv.index("--") + 1:]
out = args[0]
views = eval(args[1])   # [(name, (loc), (target), fov, (w,h))]
sc = bpy.context.scene
for o in ("BALL_START", "HOLE_CUP"):
    if o in bpy.data.objects: bpy.data.objects[o].hide_render = True
for name, loc, tgt, fov, res in views:
    c = bpy.data.cameras.new(name); ob = bpy.data.objects.new(name, c); sc.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.sensor_fit = 'VERTICAL'; c.angle_y = math.radians(fov); c.clip_start = 0.27; c.clip_end = 6000
    sc.camera = ob; sc.render.resolution_x, sc.render.resolution_y = res; sc.render.filepath = os.path.join(out, name + ".png")
    sc.eevee.taa_render_samples = 24
    bpy.ops.render.render(write_still=True)
