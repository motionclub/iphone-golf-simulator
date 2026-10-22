"""Colour-map a per-vertex scalar (mm) on Body_M and render Unity-framed views.
blender -b --factory-startup --python heat_views.py -- <blend> <scalar.npy> <vmax_mm> <outdir> [views comma list] [res]
diverging map: blue = negative, white = 0, red = positive; lit with the Unity-like camera-relative rig so form stays readable."""
import sys, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head/pylib')
from pathlib import Path
import numpy as np, bpy
from mathutils import Vector
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
from PIL import Image, ImageDraw
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); S = np.load(argv[1]); vmax = float(argv[2]); out = Path(argv[3]); out.mkdir(parents=True, exist_ok=True)
views = argv[4].split(',') if len(argv) > 4 and argv[4] else ['face_front', 'face_threequarter', 'face_profile']; RES = int(argv[5]) if len(argv) > 5 else 700
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body = bpy.data.objects['Body_M']; me = body.data; face = bpy.data.objects.get('Face_M')
if face: face.hide_render = False
t = np.clip(S / vmax, -1, 1); base = np.array([0.78, 0.66, 0.58])
col = np.ones((len(S), 4)); neg = t < 0; a = np.abs(t)[:, None]
red = np.array([0.95, 0.15, 0.12]); blue = np.array([0.12, 0.30, 0.95])
col[:, :3] = np.where(neg[:, None], base * (1 - a) + blue * a, base * (1 - a) + red * a)
att = me.color_attributes.new('heat', 'FLOAT_COLOR', 'POINT'); att.data.foreach_set('color', col.ravel())
m = bpy.data.materials.new('hmat'); m.use_nodes = True; nt = m.node_tree
for n_ in list(nt.nodes): nt.nodes.remove(n_)
v = nt.nodes.new('ShaderNodeVertexColor'); v.layer_name = 'heat'; b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.inputs['Roughness'].default_value = 0.7; o_ = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(v.outputs['Color'], b.inputs['Base Color']); nt.links.new(b.outputs['BSDF'], o_.inputs['Surface'])
me.materials.clear(); me.materials.append(m)
H.setup_eevee(res=(RES, RES), key=3.2, ambient=0.6)
CLOSE = {'face_front': (0, 0, (0, 1.565, -0.05), .16), 'face_threequarter': (38, 2, (0, 1.565, -0.05), .16), 'face_profile': (90, 0, (0, 1.565, -0.03), .16), 'face_q_lo': (38, -14, (0, 1.52, -0.05), .16),
         'jaw_side': (90, 0, (0, 1.50, -0.07), .13), 'jaw_q': (62, 0, (0, 1.50, -0.07), .13), 'neck_q': (38, 2, (0, 1.44, -0.05), .15), 'neck_side': (90, 0, (0, 1.44, -0.02), .15), 'head_back_q': (140, 5, (0, 1.50, -0.02), .20),
         'face_front_lo': (0, -18, (0, 1.52, -0.05), .16), 'under_q': (40, -26, (0, 1.47, -0.05), .15)}
tiles = []
for vname in views:
    yaw, pitch, tu, size = CLOSE[vname]; tgt = (tu[0], tu[2], tu[1])
    H.shot(out / f'{vname}.png', tgt, yaw, pitch, size * 2, (RES, RES)); tiles.append((vname, Image.open(out / f'{vname}.png').convert('RGB')))
sheet = Image.new('RGB', (RES * len(tiles), RES))
for i, (n, im) in enumerate(tiles): ImageDraw.Draw(im).text((8, 6), f'{n}  (red +, blue -, full scale {vmax} mm)', fill=(0, 0, 0)); sheet.paste(im, (i * RES, 0))
sheet.save(out / 'sheet.png'); print('heat done', out)
