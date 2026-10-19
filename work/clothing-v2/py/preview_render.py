"""quick look: Blender -b <file.blend> --python preview_render.py -- <out_prefix> [obj name filter]: front / side / back / 3-4 workbench renders of
every visible mesh (garment + hero body if present), orthographic, 900 px. For builder iteration only."""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; out = a[0]; flt = a[1] if len(a) > 1 else ''
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'OBJECT'
sc.render.resolution_x = sc.render.resolution_y = 900; sc.render.film_transparent = False
obs = [o for o in sc.objects if o.type == 'MESH' and not o.hide_render and (flt in o.name or 'ody' in o.name)]
for o in sc.objects:
    if o.type == 'MESH': o.hide_render = o not in obs
for o in obs: o.color = (.85, .55, .45, 1) if 'ody' in o.name else (.25, .45, .85, 1)
pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box if 'ody' not in o.name] or [Vector((0, 0, 1.2))]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
c = (mn + mx) / 2; size = max(mx - mn) * 1.25
cam = bpy.data.cameras.new('pv'); cam.type = 'ORTHO'; cam.ortho_scale = size
co = bpy.data.objects.new('pv', cam); sc.collection.objects.link(co); sc.camera = co
for name, az in (('front', 0), ('side', 90), ('back', 180), ('q', 35)):
    r = math.radians(az); d = Vector((math.sin(r), -math.cos(r), .12)).normalized()
    co.location = c + d * 3; co.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = '%s_%s.png' % (out, name); bpy.ops.render.render(write_still=True)
print('PREVIEW done', out)
