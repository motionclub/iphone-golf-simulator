"""Raking-light clay renders to read form.  blender -b --factory-startup --python rake.py -- <blend|npy> <outdir> <views> [light azimuths]
views: front|back|left|q3f|q3b ; each rendered with 2 lights (left-grazing 'a', right-grazing 'b')"""
import sys, math
from pathlib import Path
import numpy as np, bpy
from mathutils import Vector
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso2')
argv = sys.argv[sys.argv.index('--') + 1:]
src = argv[0]; out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True); views = argv[2].split(',')
if src.endswith('.npy'):
    bpy.ops.wm.open_mainfile(filepath=str(W / 'baseline/HeroBase_Male_Silhouette.blend')); V = np.load(src)
    bpy.data.objects['Body_M'].data.vertices.foreach_set('co', V.astype(np.float64).ravel()); bpy.data.objects['Body_M'].data.update()
else: bpy.ops.wm.open_mainfile(filepath=src)
s = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'EMPTY' or o.name == 'Face_M': o.hide_render = True
b = bpy.data.objects['Body_M']; b.data.materials.clear()
m = bpy.data.materials.new('clay'); m.use_nodes = True; bs = m.node_tree.nodes['Principled BSDF']; bs.inputs['Base Color'].default_value = (.55, .55, .55, 1); bs.inputs['Roughness'].default_value = .7
b.data.materials.append(m)
s.render.engine = 'BLENDER_EEVEE'; s.render.film_transparent = False; s.view_settings.view_transform = 'Standard'
try: s.eevee.taa_render_samples = 24; s.eevee.use_shadows = True; s.eevee.use_gtao = True
except Exception: pass
w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.06, .06, .065, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('c', cd); s.collection.objects.link(cam)
YAW = {'front': 0, 'back': 180, 'left': 90, 'q3f': 35, 'q3b': 145, 'q3fr': -35}
def light(name, az_deg, el_deg, energy):
    d = bpy.data.lights.new(name, 'SUN'); d.energy = energy; d.angle = math.radians(3)
    ob = bpy.data.objects.new(name, d); s.collection.objects.link(ob)
    a = math.radians(az_deg); e = math.radians(el_deg)
    pos = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))     # direction TO the light, az measured like the camera yaw
    ob.rotation_euler = (-pos).to_track_quat('-Z', 'Y').to_euler(); return ob
for v in views:
    name, _, a = v.partition(':'); p = [float(x) for x in a.split('_')] if a else []
    tz, sc, ty = (p + [1.10, 0.75, -0.04])[:3] if p else (1.10, 0.75, -0.04)
    yaw = YAW[name]
    t = Vector((0, ty, tz)); aa = math.radians(yaw)
    cam.location = t + Vector((math.sin(aa), -math.cos(aa), 0)) * 5; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cd.ortho_scale = sc
    s.render.resolution_x = 1000; s.render.resolution_y = 1000; s.camera = cam
    for tag, laz in (('a', yaw + 60), ('b', yaw - 60)):
        for o in [o for o in bpy.data.objects if o.type == 'LIGHT']: bpy.data.objects.remove(o, do_unlink=True)
        light('k', laz, 32, 1.7); light('f', yaw, 15, 0.35)
        s.render.filepath = str((out / f'{name}_{tag}.png').resolve()); bpy.ops.render.render(write_still=True)
print('RAKE_DONE')
