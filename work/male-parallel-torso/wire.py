"""Workbench wireframe renders of the torso.  blender -b --python wire.py -- <blend|npy> <outdir> <views: front,back,left,q3> """
import sys, math
from pathlib import Path
import numpy as np, bpy
from mathutils import Vector
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso')
argv = sys.argv[sys.argv.index('--') + 1:]
src = argv[0]; out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True); views = argv[2].split(',')
if src.endswith('.npy'):
    bpy.ops.wm.open_mainfile(filepath=str(W / 'baseline/HeroBase_Male_Silhouette.blend')); V = np.load(src)
    bpy.data.objects['Body_M'].data.vertices.foreach_set('co', V.astype(np.float64).ravel()); bpy.data.objects['Body_M'].data.update()
else: bpy.ops.wm.open_mainfile(filepath=src)
s = bpy.context.scene; s.render.engine = 'BLENDER_WORKBENCH'
sh = s.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.75, 0.75); sh.show_object_outline = False
s.render.film_transparent = False
for o in bpy.data.objects:
    if o.type == 'EMPTY' or o.name == 'Face_M': o.hide_render = True
b = bpy.data.objects['Body_M']
wf = b.modifiers.new('wf', 'WIREFRAME'); wf.thickness = 0.0006; wf.use_replace = False
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('c', cd); s.collection.objects.link(cam)
for v in views:
    name, _, a = v.partition(':'); p = [float(x) for x in a.split('_')] if a else []
    yaw = {'front': 0, 'back': 180, 'left': 90, 'right': -90, 'q3': 35}[name]
    tz, sc, ty, res = (p + [1.0, 0.9, 0.0, 1000])[:4] if p else (1.05, 0.8, 0.0, 1000)
    t = Vector((0, ty, tz)); aa = math.radians(yaw)
    cam.location = t + Vector((math.sin(aa), -math.cos(aa), 0)) * 5; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cd.ortho_scale = sc
    s.render.resolution_x = s.render.resolution_y = int(res); s.camera = cam; s.render.filepath = str((out / f'{name}.png').resolve()); bpy.ops.render.render(write_still=True)
print('WIRE_DONE')
