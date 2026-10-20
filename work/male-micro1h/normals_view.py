"""Normal-colour diagnostic renders of Body_M (camera-space normals as emission): reveals creases / planes the skin shading hides.
blender -b --factory-startup --python normals_view.py -- <blend> <outdir>"""
import sys, math
from pathlib import Path
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
argv = sys.argv[sys.argv.index('--') + 1:]
out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=argv[0])
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
    if o.name == 'Face_M': o.hide_render = True
body = bpy.data.objects['Body_M']
m = bpy.data.materials.new('nrm'); m.use_nodes = True
nt = m.node_tree; nt.nodes.clear()
g = nt.nodes.new('ShaderNodeNewGeometry'); vt = nt.nodes.new('ShaderNodeVectorTransform'); vt.vector_type = 'NORMAL'; vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'
mm_ = nt.nodes.new('ShaderNodeVectorMath'); mm_.operation = 'MULTIPLY_ADD'; mm_.inputs[1].default_value = (0.5, 0.5, 0.5); mm_.inputs[2].default_value = (0.5, 0.5, 0.5)
em = nt.nodes.new('ShaderNodeEmission'); o = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(g.outputs['Normal'], vt.inputs[0]); nt.links.new(vt.outputs[0], mm_.inputs[0]); nt.links.new(mm_.outputs[0], em.inputs['Color']); nt.links.new(em.outputs[0], o.inputs['Surface'])
body.data.materials.clear(); body.data.materials.append(m)
H.setup_eevee(res=(1200, 1200), transparent=False, key=0.0, fill=0.0, ambient=0.0)
for nm in ('h1_key', 'h1_fill', 'h1_rim'):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
s = bpy.context.scene; s.view_settings.view_transform = 'Standard'
tgt = (0.0, -0.06, 1.545)
for name, az in (('front', 0), ('q3L', 32.5), ('q3R', -30.0), ('left', 90)):
    H.shot(out / f'nrm_{name}.png', tgt, az, 0, 0.30, (1200, 1200))
print('normals done')
