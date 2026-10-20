"""Eevee renders (transparent bg) at the exact head-detail plate framings from a final blend.
blender -b --factory-startup --python render_panels.py -- <final.blend> <outdir>"""
import sys, math
from pathlib import Path
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, h1render as HR
argv = sys.argv[sys.argv.index('--') + 1:]
blend = Path(argv[0]); out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(blend))
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body = bpy.data.objects['Body_M']
body.data.materials.clear(); body.data.materials.append(H.skin_material())
m_sc = bpy.data.materials.get('Face_Sclera')
if m_sc:
    b = m_sc.node_tree.nodes['Principled BSDF']
    try:
        b.inputs['Emission Color'].default_value = (0.5, 0.49, 0.47, 1); b.inputs['Emission Strength'].default_value = 0.3
    except Exception: pass
H.setup_eevee(res=(900, 900), transparent=True, key=float(argv[2]) if len(argv) > 2 else 3.0, ambient=float(argv[3]) if len(argv) > 3 else 0.55)
K, TOP = H.K, H.TOP
# plate panel framings (2 px per plate px)
PAN = {'front': (5, 62, 433, 352), 'left': (433, 62, 834, 352), 'q3L': (5, 390, 433, 668), 'q3R': (433, 390, 834, 668)}
# 3/4 panels: yaw fitted to each plate (pupil spacing + contour residual: q3L 41 deg, q3R 36 deg), translation fitted so the pupil midpoint coincides
PUP_MID = {'q3L': 176.5, 'q3R': 589.5}
Q3_YAW = {'q3L': 41.0, 'q3R': 36.0}
for name, box in PAN.items():
    c = HR.cam_for(name, 2)
    if name in PUP_MID:
        x0_, y0_, x1_, y1_ = box_ = HR.SETS[name]['box']
        cxp = (x0_ + x1_) / 2; a_ = math.radians(Q3_YAW[name])
        ty = -0.1254 - ((PUP_MID[name] - cxp) * K) / math.sin(a_)
        c = dict(c, az=Q3_YAW[name], target=(0.0, ty, c['target'][2]))
    H.shot(out / f'{name}.png', c['target'], c['az'], c['el'], c['scale'], c['res'])
# right profile panel (same orientation as the left, different anchor): occiput col 1122 <-> y 0.0645
x0, y0, x1, y1 = 834, 62, 1271, 352
w, h = x1 - x0, y1 - y0
cyp = (y0 + y1) / 2; cxp = (x0 + x1) / 2
H.shot(out / 'right.png', (0.0, 0.065 - (1123.0 - cxp) * K, float(H.zrow(cyp))), 90, 0, w * K, (w * 2, h * 2))
# top: head-only copy (neck cut at z=1.43) so shoulders do not enter the silhouette
me = body.data
V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
faces = [list(p.vertices) for p in me.polygons if all(V[i, 2] > 1.43 for i in p.vertices)]
used = sorted({i for f in faces for i in f}); rem = {v: k for k, v in enumerate(used)}
Vh = V[used]; Fh = [[rem[i] for i in f] for f in faces]
head = H.make_mesh_object('HeadOnly', Vh, Fh); head.data.materials.append(H.skin_material())
body.hide_render = True
H.shot(out / 'top.png', (0, -0.03, 1.60), 0, 89.5, 0.26, (1000, 1000))
head.hide_render = True; body.hide_render = False
print('panels done')
