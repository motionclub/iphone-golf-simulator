"""Displacement heat-map / zone render. blender -b --factory-startup --python zonemap.py -- <final.blend> <baseline coords npz> <outdir>
colours: grey = not moved (bit-identical); blue->yellow->red = |d| 0..22 mm"""
import sys, numpy as np, bpy, math
from pathlib import Path
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
final, base_npz, out = a[0], a[1], Path(a[2]); out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=final)
b = bpy.data.objects['Body_M']; me = b.data
V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
B = np.load(base_npz)['co']; d = np.linalg.norm(V - B, axis=1) * 1000
t = np.clip(d / 20.0, 0, 1)
def ramp(t):
    # blue (0) -> cyan -> yellow -> red (1)
    stops = [(0.0, (0.15, 0.25, 0.85)), (0.35, (0.1, 0.8, 0.85)), (0.7, (0.95, 0.9, 0.2)), (1.0, (0.9, 0.15, 0.1))]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1: u = (t - t0) / (t1 - t0); return tuple(c0[i] + (c1[i] - c0[i]) * u for i in range(3))
    return stops[-1][1]
col = np.zeros((len(V), 4)); col[:, 3] = 1
for i in range(len(V)):
    if d[i] < 0.005: col[i, :3] = (0.62, 0.62, 0.62)
    else: col[i, :3] = ramp(t[i])
if 'zonecol' in me.color_attributes: me.color_attributes.remove(me.color_attributes['zonecol'])
ca = me.color_attributes.new('zonecol', 'FLOAT_COLOR', 'POINT'); ca.data.foreach_set('color', col.ravel())
s = bpy.context.scene; s.render.engine = 'BLENDER_WORKBENCH'; sh = s.display.shading
sh.light = 'FLAT'; sh.color_type = 'VERTEX'; sh.show_object_outline = False; s.render.film_transparent = False
s.view_settings.view_transform = 'Standard'
s.world = bpy.data.worlds.new('w'); s.world.use_nodes = True; s.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.1, 0.1, 0.11, 1)
for o in bpy.data.objects:
    if o.type == 'EMPTY' or o.name == 'Face_M': o.hide_render = True
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('c', cd); s.collection.objects.link(cam)
for name, yaw in (('front', 0), ('back', 180), ('left', 90), ('q3', 35)):
    tt = Vector((0, -0.03, 0.88)); aa = math.radians(yaw)
    cam.location = tt + Vector((math.sin(aa), -math.cos(aa), 0)) * 5; cam.rotation_euler = (tt - cam.location).to_track_quat('-Z', 'Y').to_euler(); cd.ortho_scale = 1.9
    s.render.resolution_x = 760; s.render.resolution_y = 1000; s.camera = cam; s.render.filepath = str((out / f'{name}.png').resolve()); bpy.ops.render.render(write_still=True)
print('ZONEMAP_DONE', int((d > 0.005).sum()), 'moved verts; max mm', float(d.max()))
