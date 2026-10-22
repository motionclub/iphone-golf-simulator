"""Re-render proof views from a saved on-hand blend.
blender -b <blend> --python render_proofs.py -- <out_prefix> <male|female> <apose|ready> [set]
set: full | crop | close | all"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import render_lib as R

a = args_after_dashes()
prefix, tag, pose = a[0], a[1], a[2]
which = a[3] if len(a) > 3 else 'all'
sock = bpy.data.objects['Hand_Racket']
for n in ('Collider_Racket',):
    if n in bpy.data.objects:
        bpy.data.objects[n].hide_render = True
ctr = tuple(np.array(sock.matrix_world)[:3, 3])
R.studio(bg=(0.36, 0.37, 0.39), samples=64)
H = 1.70
if which in ('full', 'all'):
    if tag == 'male' and pose == 'apose':
        tg, dist = (0.0, -0.06, 0.86), 3.9
    elif pose == 'ready':
        tg, dist = ((-0.12, -0.20, 0.92) if tag == 'male' else (-0.08, -0.18, 0.92)), 3.5
    else:
        tg, dist = (-0.05, -0.05, 0.86), 3.6
    for nm, az, el in (('front', 0, 4), ('side', -90, 4), ('q3', -42, 14)):
        R.shot(f'{prefix}_{nm}.png', tg, az=az, el=el, dist=dist, lens=60, res=(1100, 1100))
if which in ('crop', 'all'):
    if tag == 'male' and pose == 'apose':
        tg, dist = (-0.45, -0.25, 0.78), 1.9
    elif pose == 'ready':
        tg, dist = ((-0.22, -0.28, 1.0) if tag == 'male' else (-0.2, -0.26, 0.98)), 2.2
    else:
        tg, dist = (-0.22, -0.02, 0.85), 2.4
    for nm, az, el in (('front', 22, 6), ('side', -90, 4), ('q3', -42, 14)):
        R.shot(f'{prefix}_crop_{nm}.png', tg, az=az, el=el, dist=dist, lens=60, res=(1100, 1100))
if which in ('close', 'all'):
    R.shot(f'{prefix}_grip_close_a.png', ctr, az=-55, el=10, dist=0.5, lens=70, res=(1100, 1100))
    R.shot(f'{prefix}_grip_close_b.png', ctr, az=-125, el=25, dist=0.5, lens=70, res=(1100, 1100))
    R.shot(f'{prefix}_grip_close_c.png', ctr, az=35, el=-10, dist=0.5, lens=70, res=(1100, 1100))
print('PROOFS_RENDER_DONE')
