"""Solid + wireframe render of the jaw band: blender -b --factory-startup --python wire_l.py -- <blend> <out.png> <az> <el> <tx> <ty> <tz> <scale> [arc.npy]"""
import sys, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head/pylib')
import numpy as np, bpy
from mathutils import Vector
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out = argv[1]; az, el = float(argv[2]), float(argv[3]); tgt = tuple(float(v) for v in argv[4:7]); sc = float(argv[7])
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body = bpy.data.objects['Body_M']; face = bpy.data.objects.get('Face_M')
if face: face.hide_render = True
body.data.materials.clear(); body.data.materials.append(H.skin_material(rough=0.7, sss=0.0))
w = body.copy(); w.data = body.data; bpy.context.scene.collection.objects.link(w)
md = w.modifiers.new('wf', 'WIREFRAME'); md.thickness = 0.00022; md.use_even_offset = True
m2 = bpy.data.materials.new('wm'); m2.use_nodes = True; m2.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.02, 0.02, 0.03, 1); m2.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 1
w.data = body.data.copy(); w.data.materials.clear(); w.data.materials.append(m2); w.location = (0, 0, 0)
H.setup_eevee(res=(1100, 800), key=2.2, ambient=0.8)
if len(argv) > 8:
    arc = np.load(argv[8]); 
    for i, p in enumerate(arc):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0007, location=tuple(p)); bpy.context.object.data.materials.append(bpy.data.materials.new('ar')); 
H.shot(out, tgt, az, el, sc, (1100, 800))
print('wire done')
