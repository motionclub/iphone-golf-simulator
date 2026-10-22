"""Render a contact sheet of an action (behind / side / front views) from the working blend.

  blender -b export/HeroBase_<Hero>_MatchAnims.blend --python scripts/render_sheet.py -- <male|female> <Clip> <out_prefix> <frames: comma list | every:N | all> [views: behind,side,front]
Writes <out_prefix>_f<frame>_<view>.png and <out_prefix>_cells.json (compose with scripts/tile_sheet.py)."""
import json
import math
import os
import sys

import numpy as np
import bpy

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
sys.path.insert(0, REPO + '/work/match-anim-set/scripts')
sys.path.insert(0, REPO + '/work/serve-toss-jump/scripts')
import preview as PV
import loco

a = sys.argv[sys.argv.index('--') + 1:]
tag, clip, outp, spec = a[:4]
views = (a[4] if len(a) > 4 else 'behind,side').split(',')
rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
act = bpy.data.actions[clip]
rig_o.animation_data.action = act
try:
    rig_o.animation_data.action_slot = act.slots[0]
except Exception:
    pass
n = int(act.frame_end) + 1
if spec == 'all':
    frames = list(range(n))
elif spec.startswith('every:'):
    frames = list(range(0, n, int(spec.split(':')[1])))
else:
    frames = [float(x) if '.' in x else int(x) for x in spec.split(',')]
cam = PV.setup_scene(rig_o)
if os.environ.get('SCALE_RACKET'):
    k_ = float(os.environ['SCALE_RACKET']); bpy.data.objects['Racket_Classic'].scale = (k_, k_, k_)
EXTRA = {'top': (180.0, 82.0, 6.0, 0.6), 'front': (0.0, 6.0, 5.4, 1.0), 'side_l': (-90.0, 6.0, 5.2, 0.95), 'side_hi': (90.0, 6.0, 7.0, 1.4), 'behind_hi': (180.0, 14.0, 7.0, 1.3)}
sc = bpy.context.scene
res = tuple(int(x) for x in os.environ.get('RES', '300x400').split('x'))
cells = []
root = np.array(loco.kin.Rig(f'{loco.MA}/data/rig_{tag}.json').root_origin)
for f in frames:
    sc.frame_set(math.floor(f), subframe=f-math.floor(f))
    bpy.context.view_layer.update()
    row = []
    for v in views:
        ft = f'{f:03d}' if isinstance(f,int) else str(f).replace('.', 'p')
        p = f'{outp}_f{ft}_{v}.png'
        if v in ('cb', 'cr', 'cf', 'cl'):
            import studio
            psi = float(np.load(f'{loco.DATA}/gen_serve_{tag}.npz', allow_pickle=True)['chest_yaw'][f]) if os.path.exists(f'{loco.DATA}/gen_serve_{tag}.npz') else 0.0
            az = {'cb': -psi + 180.0, 'cr': -psi - 90.0, 'cf': -psi, 'cl': -psi + 90.0}[v]
            studio.shot(p, (root[0], root[1] - 0.05, 1.0), az=az, el=6.0, dist=5.0, lens=50, res=res, turn_lights=True)
        elif v in EXTRA:
            import studio
            az, el, dist, tz = EXTRA[v]
            studio.shot(p, (root[0], root[1] - 0.05, tz), az=az, el=el, dist=dist, lens=50, res=res, turn_lights=True)
        else:
            PV.render(cam, v, root, p, res=res, dist=None)
        row.append(p)
    cells.append(dict(frame=f, files=row))
json.dump(dict(clip=clip, tag=tag, cells=cells), open(outp + '_cells.json', 'w'))
print('SHEET_DONE', clip, len(cells))
