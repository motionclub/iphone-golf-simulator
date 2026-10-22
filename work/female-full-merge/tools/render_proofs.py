"""Studio-light proof renders of the merged female (EEVEE, camera-parented suns; NOT plate-matched).
blender -b --factory-startup export/HeroBase_Female_FULL_STAGED.blend --python tools/render_proofs.py -- <outdir> <mode> <spec>...
mode: clay   = grey clay Body_F (+ Face_F with its own materials)       seams = provenance colours on Body_F + ring tubes (Face_F hidden)       wire = clay + orange wire overlay
spec = name:tx,ty,tz:dx,dy,dz:ortho_scale   (camera at target + d*6, ortho; up = +Z)      env RESX/RESY (default 900/1300), AO=1
Never saves the blend."""
import bpy, sys, os, math, collections
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index('--') + 1:]
out = Path(argv[0]); out.mkdir(parents=True, exist_ok=True); mode = argv[1]; specs = argv[2:]
R = np.load('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-full-merge/data/rings_final.npz')
def lin(c): return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
s = bpy.context.scene
body = bpy.data.objects['Body_F']; face = bpy.data.objects['Face_F']
for o in list(bpy.data.objects):
    if o.type == 'LIGHT' or o.type == 'CAMERA': bpy.data.objects.remove(o)
    elif o.type == 'EMPTY' or o.name == 'Hair_F': o.hide_render = True; o.hide_viewport = True
me = body.data; nV = len(me.vertices)
def mat_solid(name, rgb, rough=0.55, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (lin(rgb[0]), lin(rgb[1]), lin(rgb[2]), 1); b.inputs['Roughness'].default_value = rough
    if emit > 0:
        try: b.inputs['Emission Color'].default_value = (lin(rgb[0]), lin(rgb[1]), lin(rgb[2]), 1); b.inputs['Emission Strength'].default_value = emit
        except Exception: pass
    return m
clay = mat_solid('clay', (.62, .62, .63))
PROV = {0: (.78, .78, .78), 1: (.95, .55, .35), 2: (.35, .55, .95), 3: (.35, .80, .45), 4: (.70, .45, .90), 5: (.30, .75, .78), 6: (.98, .90, .20), 7: (.60, .55, .85)}
if mode == 'seams':
    face.hide_render = True
    ca = me.color_attributes.new('prov', 'FLOAT_COLOR', 'POINT')
    col = np.zeros((nV, 4), np.float32); col[:, 3] = 1
    for k, c in PROV.items():
        col[R['prov'] == k, :3] = [lin(x) for x in c]
    ca.data.foreach_set('color', col.ravel())
    pm = bpy.data.materials.new('prov'); pm.use_nodes = True; nt = pm.node_tree; b = nt.nodes['Principled BSDF']
    an = nt.nodes.new('ShaderNodeAttribute'); an.attribute_name = 'prov'; nt.links.new(an.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.6
    for i in range(len(me.materials)): me.materials[i] = pm
else:
    for i in range(len(me.materials)): me.materials[i] = clay
# ring tubes (seams mode / wire mode extra)
nbr = collections.defaultdict(set)
for p in me.polygons:
    vs = list(p.vertices)
    for i in range(len(vs)): a, b = vs[i], vs[(i + 1) % len(vs)]; nbr[a].add(b); nbr[b].add(a)
co = np.empty(nV * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
RING_COL = {'collar': (1.0, 0.1, 0.1), 'neck': (1.0, 0.85, 0.0), 'armpit': (0.9, 0.1, 0.9), 'pins': (0.0, 0.95, 0.95), 'wrist': (0.1, 1.0, 0.2), 'floor': (1.0, 0.5, 0.0)}
def add_ring(name, idx, rgb, radius=0.0011):
    S = set(int(i) for i in idx); cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = radius; cu.bevel_resolution = 2
    for a in S:
        for b in nbr[a]:
            if b in S and a < b:
                sp = cu.splines.new('POLY'); sp.points.add(1); sp.points[0].co = (*co[a], 1); sp.points[1].co = (*co[b], 1)
    ob = bpy.data.objects.new(name, cu); s.collection.objects.link(ob)
    m = mat_solid(name + '_m', rgb, 0.4, 1.5); cu.materials.append(m); return ob
if mode in ('seams', 'wire_rings'):
    for k in ('collar', 'neck', 'armpit', 'pins', 'wrist', 'floor'): add_ring('ring_' + k, R[k], RING_COL[k])
RESX = int(os.environ.get('RESX', '900')); RESY = int(os.environ.get('RESY', '1300'))
s.render.engine = 'BLENDER_EEVEE'; s.render.resolution_x = RESX; s.render.resolution_y = RESY; s.render.film_transparent = False
s.render.image_settings.file_format = 'PNG'; s.render.image_settings.color_mode = 'RGB'
s.view_settings.view_transform = 'Standard'; s.view_settings.look = 'None'
AO = os.environ.get('AO', '1') == '1'
try:
    s.eevee.taa_render_samples = 24; s.eevee.use_shadows = AO; s.eevee.use_gtao = AO; s.eevee.gtao_distance = 0.04
except Exception: pass
w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (lin(.26), lin(.26), lin(.28), 1); bg.inputs['Strength'].default_value = 0.7 if AO else 1.6
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); s.collection.objects.link(cam); s.camera = cam
cam.data.type = 'ORTHO'; cam.data.clip_end = 50; cam.data.clip_start = 0.01
def sun(nm, energy, ang=8):
    d = bpy.data.lights.new(nm, 'SUN'); d.energy = energy; d.angle = math.radians(ang); o = bpy.data.objects.new(nm, d); s.collection.objects.link(o); return o
k = sun('k', 3.4); f = sun('f', 0.6, 25)
if mode == 'wire':
    wo = body.copy(); wo.data = body.data.copy(); s.collection.objects.link(wo)
    md = wo.modifiers.new('wf', 'WIREFRAME'); md.thickness = float(os.environ.get('WIRE_T', '0.00022')); md.use_even_offset = True; md.use_replace = True
    wm = mat_solid('wm', (0.9, 0.55, 0.1), 0.5, 1.0); wo.data.materials.clear(); wo.data.materials.append(wm)
for sp in specs:
    parts = sp.split(':'); name = parts[0]
    t = Vector([float(v) for v in parts[1].split(',')]); d = Vector([float(v) for v in parts[2].split(',')]).normalized(); osc = float(parts[3])
    cam.location = t + d * 6; cam.data.ortho_scale = osc
    up = Vector((0, 0, 1)); fwd = (-d).normalized(); right = fwd.cross(up).normalized(); upv = right.cross(fwd).normalized()
    cam.rotation_euler = Matrix([[right.x, upv.x, -fwd.x], [right.y, upv.y, -fwd.y], [right.z, upv.z, -fwd.z]]).to_euler()
    for o, (pitch, yaw) in ((k, (55, -40)), (f, (20, 60))):
        o.parent = cam; o.rotation_mode = 'XYZ'; o.rotation_euler = (math.radians(-pitch), math.radians(yaw), 0)
    bpy.context.view_layer.update()
    s.render.filepath = str(out / f'{name}.png'); bpy.ops.render.render(write_still=True)
print('PROOF_RENDER_DONE', mode, len(specs))
