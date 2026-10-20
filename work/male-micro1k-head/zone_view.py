"""Hard-light neck renders with the zone line z=1.40 marked: vertices >=1.40 tinted green, <1.40 red (blend of lit clay).
blender -b --factory-startup --python zone_view.py -- <blend> <outdir>"""
import sys, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1k-head/pylib')
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
from PIL import Image, ImageDraw
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body = bpy.data.objects['Body_M']; me = body.data
face = bpy.data.objects.get('Face_M')
if face: face.hide_render = True
# vertex-colour attribute: tint by zone, boundary band 1.395..1.405 white
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
col = np.ones((len(me.vertices), 4)); z = co[:, 2]
col[:, :3] = np.where((z >= 1.40)[:, None], [0.55, 0.95, 0.55], [0.95, 0.55, 0.55])
col[(np.abs(z - 1.40) < 0.0035), :3] = 1.0
att = me.color_attributes.new('zone', 'FLOAT_COLOR', 'POINT'); att.data.foreach_set('color', col.ravel())
m = bpy.data.materials.new('zmat'); m.use_nodes = True; nt = m.node_tree
for n_ in list(nt.nodes): nt.nodes.remove(n_)
a = nt.nodes.new('ShaderNodeVertexColor'); a.layer_name = 'zone'
b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.inputs['Roughness'].default_value = 0.65
o_ = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(a.outputs['Color'], b.inputs['Base Color']); nt.links.new(b.outputs['BSDF'], o_.inputs['Surface'])
me.materials.clear(); me.materials.append(m)
RES = 760
H.setup_eevee(res=(RES, RES), key=3.2, ambient=0.6)
VIEWS = [('side', 90, 0), ('back', 180, 0), ('back145', 145, 0), ('side_lo', 90, -18), ('q35', 35, 0), ('front', 0, 0)]
for n, az, el in VIEWS: H.shot(out / f'{n}.png', (0, -0.015, 1.43), az, el, 0.26, (RES, RES))
tiles = [(n, Image.open(out / f'{n}.png').convert('RGB')) for n, _, _ in VIEWS]
sheet = Image.new('RGB', (3 * RES, 2 * RES))
for i, (n, im) in enumerate(tiles): ImageDraw.Draw(im).text((8, 6), n, fill=(255, 255, 0)); sheet.paste(im, ((i % 3) * RES, (i // 3) * RES))
sheet.resize((sheet.width * 2 // 3, sheet.height * 2 // 3), Image.LANCZOS).save(out / 'sheet.png'); print('zone views done')
