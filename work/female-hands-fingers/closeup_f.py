"""Clay close-ups of a candidate Body_F mesh (EEVEE, parented sun lights).
blender -b start.blend --python closeup_f.py -- <cand.npz|base> <outdir> <spec>...
spec = name:tx,ty,tz:dx,dy,dz:ortho[:lightpitch:lightyaw][:up=x,y,z]   (camera sits at target + d*6 looking at the target)
env: WIRE=1 wire overlay, ISO=1 isolate arm zone + hands (default), ISO=0 whole body, RES=900, AO=1, CLIP/FAR slab"""
import bpy, sys, os, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index('--') + 1:]
cand = argv[0]; out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True); specs = argv[2:]
def lin(c): return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
W_ = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-hands-fingers'
body = bpy.data.objects['Body_F']
if cand == 'base': cand = W_ + '/data/mesh_start.npz'
D = np.load(cand)
V = D['V'].astype(np.float64); cv = D['corner_verts']; ls = D['loop_start']; lt = D['loop_total']
polys = [tuple(int(x) for x in cv[s_:s_ + t]) for s_, t in zip(ls, lt)]
N0 = 22419
if os.environ.get('ISO', '1') == '1':
    arm = np.load(W_ + '/../female-arms-form2/data/zones_cur.npz')['arm']
    flag = np.zeros(len(V), bool); flag[:N0] = arm
    for side in (1, -1): flag[np.load(W_ + f'/data/start_hand_verts_{side}.npy')] = True
    flag[N0:] = True
    polys = [p for p in polys if all(flag[i] for i in p)]
    # keep the arm zone from the start mesh only where it is connected to the hand: drop nothing else
me = body.data
me.clear_geometry(); me.from_pydata(V.tolist(), [], polys); me.update()
me.polygons.foreach_set('use_smooth', [True] * len(me.polygons)); me.update()
s = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Body_F': o.hide_render = True
    if o.type == 'EMPTY': o.hide_render = True
    if o.type == 'LIGHT': bpy.data.objects.remove(o)
body.data.materials.clear()
m = bpy.data.materials.new('g'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (lin(.62), lin(.62), lin(.63), 1); b.inputs['Roughness'].default_value = 0.55
body.data.materials.append(m)
RES = int(os.environ.get('RES', '900'))
s.render.engine = 'BLENDER_EEVEE'; s.render.resolution_x = RES; s.render.resolution_y = RES; s.render.film_transparent = False
s.render.image_settings.file_format = 'PNG'; s.render.image_settings.color_mode = 'RGB'
s.view_settings.view_transform = 'Standard'; s.view_settings.look = 'None'
try:
    s.eevee.taa_render_samples = 24; s.eevee.use_shadows = (os.environ.get('AO', '1') == '1'); s.eevee.use_gtao = (os.environ.get('AO', '1') == '1'); s.eevee.gtao_distance = 0.04
except Exception: pass
w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (lin(.26), lin(.26), lin(.28), 1); bg.inputs['Strength'].default_value = (0.7 if os.environ.get('AO', '1') == '1' else 1.6)
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); s.collection.objects.link(cam); s.camera = cam
cam.data.type = 'ORTHO'; cam.data.clip_end = 50; cam.data.clip_start = 0.01
CLIP = float(os.environ.get('CLIP', '0')); FAR = float(os.environ.get('FAR', '0'))
def sun(nm, energy, ang=8):
    d = bpy.data.lights.new(nm, 'SUN'); d.energy = energy; d.angle = math.radians(ang)
    o = bpy.data.objects.new(nm, d); s.collection.objects.link(o); return o
k = sun('k', 3.4); f = sun('f', 0.6, 25)
if os.environ.get('WIRE'):
    wo = body.copy(); wo.data = body.data.copy(); s.collection.objects.link(wo)
    md = wo.modifiers.new('wf', 'WIREFRAME'); md.thickness = float(os.environ.get('WIRE_T', '0.00022')); md.use_even_offset = True; md.use_replace = True
    wm = bpy.data.materials.new('wm'); wm.use_nodes = True; wb = wm.node_tree.nodes['Principled BSDF']
    wb.inputs['Base Color'].default_value = (0.9, 0.55, 0.1, 1)
    try: wb.inputs['Emission Color'].default_value = (0.9, 0.55, 0.1, 1); wb.inputs['Emission Strength'].default_value = 1.0
    except Exception: pass
    wo.data.materials.clear(); wo.data.materials.append(wm)
for sp in specs:
    parts = sp.split(':'); name = parts[0]
    t = Vector([float(v) for v in parts[1].split(',')]); d = Vector([float(v) for v in parts[2].split(',')]).normalized(); osc = float(parts[3])
    lp = float(parts[4]) if len(parts) > 4 and parts[4] else 55; ly = float(parts[5]) if len(parts) > 5 and parts[5] else -40
    up = Vector([float(v) for v in parts[6].split(',')]) if len(parts) > 6 else Vector((0, 0, 1))
    cam.location = t + d * 6; cam.data.ortho_scale = osc
    if CLIP > 0: cam.data.clip_start = 6.0 - CLIP
    if FAR > 0: cam.data.clip_end = 6.0 + FAR
    fwd = (-d).normalized(); right = fwd.cross(up).normalized(); upv = right.cross(fwd).normalized()
    rot = Matrix([[right.x, upv.x, -fwd.x], [right.y, upv.y, -fwd.y], [right.z, upv.z, -fwd.z]])
    cam.rotation_euler = rot.to_euler()
    for o, (pitch, yaw) in ((k, (lp, ly)), (f, (20, 60))):
        o.parent = cam; o.rotation_mode = 'XYZ'; o.rotation_euler = (math.radians(-pitch), math.radians(yaw), 0)
    bpy.context.view_layer.update()
    s.render.filepath = str(out / f'{name}.png'); bpy.ops.render.render(write_still=True)
print('CLOSEUP_DONE')
