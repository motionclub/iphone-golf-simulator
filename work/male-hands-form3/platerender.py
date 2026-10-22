"""Render the full candidate body through the blend's Locked_* plate cameras (clay).  blender -b blend --python platerender.py -- <cand.npz|base> <outdir> [views...]"""
import bpy, sys, os, math
import numpy as np
from pathlib import Path
argv = sys.argv[sys.argv.index('--')+1:]
cand = argv[0]; out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
views = argv[2:] or ['bald_front', 'bald_back', 'sheet_front', 'sheet_back']
def lin(c): return ((c+0.055)/1.055)**2.4 if c > 0.04045 else c/12.92
W_ = os.path.dirname(os.path.abspath(__file__))
body = bpy.data.objects['Body_M']
if cand != 'base':
    D = np.load(cand)
    V = D['V'].astype(np.float64); cv = D['corner_verts']; ls = D['loop_start']; lt = D['loop_total']
    polys = [tuple(int(x) for x in cv[s_:s_+t]) for s_, t in zip(ls, lt)]
    me = body.data
    # keep custom normals out of the picture: rebuild geometry
    me.clear_geometry(); me.from_pydata(V.tolist(), [], polys); me.update()
    me.polygons.foreach_set('use_smooth', [True]*len(me.polygons)); me.update()
s = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Body_M': o.hide_render = True
    if o.type == 'EMPTY': o.hide_render = True
body.data.materials.clear()
m = bpy.data.materials.new('g'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (lin(.55), lin(.55), lin(.56), 1); b.inputs['Roughness'].default_value = 0.6
body.data.materials.append(m)
s.render.engine = 'BLENDER_EEVEE'; s.render.resolution_x = 1280; s.render.resolution_y = 720; s.render.resolution_percentage = 100
s.render.film_transparent = False; s.render.image_settings.file_format = 'PNG'; s.render.image_settings.color_mode = 'RGB'
s.view_settings.view_transform = 'Standard'; s.view_settings.look = 'None'
try: s.eevee.taa_render_samples = 32
except Exception: pass
w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (lin(.17), lin(.17), lin(.18), 1); bg.inputs['Strength'].default_value = 1.0
def sun(nm, energy, ang, pitch, yaw, parent):
    d = bpy.data.lights.new(nm, 'SUN'); d.energy = energy; d.angle = math.radians(ang)
    o = bpy.data.objects.new(nm, d); s.collection.objects.link(o); o.parent = parent; o.rotation_mode = 'XYZ'
    o.rotation_euler = (math.radians(-pitch), math.radians(yaw), 0); return o
for v in views:
    cam = bpy.data.objects['Locked_' + v]; s.camera = cam
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o)
    sun('k', 2.6, 12, 40, -25, cam); sun('f', 0.9, 30, 25, 50, cam); sun('r', 0.8, 20, 15, 160, cam)
    s.render.filepath = str(out / f'{v}.png'); bpy.ops.render.render(write_still=True)
print('PLATE_DONE')
