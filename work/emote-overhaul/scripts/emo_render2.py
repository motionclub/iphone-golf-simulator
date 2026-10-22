"""EMOTES preview renderer (runs inside Blender, headless, on a DRESSED hero blend: kit + racket; the racket is drawn at the game's 1.3x).

  blender -b work/hero-dressed/export/HeroBase_<Hero>_Dressed.blend --python emo_render.py -- <male|female> <clip> <t1,t2,...|every:N|frames:a-b> <view,view,..> <outdir> [res WxH]

Writes <outdir>/<clip>_<tag>_<frame>_<view>.png and <outdir>/<clip>_<tag>_cells.json (read by tile.py).  Poses come from emo_clips.build(<clip>) (numpy solver), applied to the rig
frame by frame (no baking); a detached racket is put on Racket_Classic.matrix_world."""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/emotes/scripts')
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import numpy as np
import bpy
from mathutils import Matrix, Quaternion, Vector

import emo_hero as EH
import emo_clips2 as EC
import preview as PV

a = sys.argv[sys.argv.index('--') + 1:]
tag, clip, spec, views, outdir = a[0], a[1], a[2], a[3].split(','), a[4]
res = tuple(int(x) for x in a[5].split('x')) if len(a) > 5 else (360, 480)
os.makedirs(outdir, exist_ok=True)
H = EH.EmoHero(tag)
C = EC.build(clip, H)
nF = int(round(C.length * 30)) + 1
if spec.startswith('every:'):
    frames = list(range(0, nF, int(spec[6:])))
elif spec.startswith('frames:'):
    lo, hi = spec[7:].split('-')
    frames = list(range(int(lo), int(hi) + 1))
else:
    frames = [int(round(float(x) * 30)) for x in spec.split(',')]
rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
rk = bpy.data.objects['Racket_Classic']
rk.scale = (1.0, 1.0, 1.0)
# colour the parts so a skin-through-shirt poke shows: skin tan, shirt white, shorts navy, face tan
def _mat(name, rgb, rough=0.55):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    b.inputs['Roughness'].default_value = rough
    return m
if os.environ.get('EMO_COLORS', '1') == '1':
    paint = {'Body_M': (0.80, 0.52, 0.38), 'Body_F': (0.80, 0.52, 0.38), 'Face_M': (0.80, 0.52, 0.38), 'Face_F': (0.80, 0.52, 0.38), 'Kit_Top': (0.92, 0.92, 0.90), 'Kit_Bottom': (0.10, 0.16, 0.34),
             'Kit_Shoe_L': (0.9, 0.9, 0.9), 'Kit_Shoe_R': (0.9, 0.9, 0.9), 'Kit_Sock_L': (0.95, 0.95, 0.95), 'Kit_Sock_R': (0.95, 0.95, 0.95)}
    for nm, rgb in paint.items():
        ob = bpy.data.objects.get(nm)
        if ob is not None and ob.type == 'MESH':
            m = _mat('EMO_' + nm, rgb)
            ob.data.materials.clear()
            ob.data.materials.append(m)
cam = PV.setup_scene(rig_o, samples=12)
VIEWS = {'behind': (180.0, 8.0, 5.0, 50, 0.95), 'side': (90.0, 6.0, 5.0, 50, 0.95), 'front': (0.0, 6.0, 5.0, 50, 0.95), 'q_front': (35.0, 8.0, 4.4, 50, 0.95),
         'q_behind': (150.0, 12.0, 5.0, 50, 0.95), 'face': (20.0, 4.0, 1.5, 85, 1.5), 'face_side': (90.0, 4.0, 1.5, 85, 1.5), 'top': (0.0, 70.0, 5.0, 50, 0.9),
         'low_side': (90.0, 3.0, 4.0, 50, 0.5), 'low_front': (25.0, 10.0, 4.0, 50, 0.5), 'low_behind': (160.0, 10.0, 4.0, 50, 0.5), 'upper_front': (20.0, 6.0, 2.6, 70, 1.25),
         'upper_behind': (160.0, 6.0, 2.6, 70, 1.25), 'hands_front': (15.0, 6.0, 2.2, 70, 1.15)}
import studio
cells = []
prev = None
S = H.S
S.reset()
for fr in frames:
    t = fr / 30.0
    d = C.solve(t)
    basis, hips, info = d['basis'], d['hips'], d['info']
    prev = PV.apply_pose(rig_o, H.rig, basis, hips, prev)
    bpy.context.view_layer.update()
    rkw = d.get('racket')
    if rkw is not None:
        M = Matrix.Translation(Vector(rkw['pos'].tolist())) @ Matrix(rkw['R'].tolist()).to_4x4() @ Matrix.Diagonal((1.0, 1.0, 1.0, 1.0))
        rk.matrix_world = M
    else:
        rk.matrix_basis = Matrix.Diagonal((1.0, 1.0, 1.0, 1.0))
    bpy.context.view_layer.update()
    files = []
    for v in views:
        az, el, dist, lens, tz = VIEWS[v]
        f = f'{outdir}/{clip}_{tag}_{fr:03d}_{v}.png'
        studio.shot(f, (H.O[0], H.O[1] - 0.05, tz), az=az, el=el, dist=dist, lens=lens, res=res, turn_lights=True)
        files.append(f)
    cells.append(dict(t=t, frame=fr, files=files, src=[], sweet=[0, 0, 0], diag={}))
json.dump(dict(clip=clip, tag=tag, cells=cells, contact=None, views=views), open(f'{outdir}/{clip}_{tag}_cells.json', 'w'))
print('RENDERED', len(cells), 'cells', views)
