"""Render the racket (upright: local +Y -> world +Z, hitting face towards the -Y camera) in the grey studio.
blender -b --python render_racket.py -- <racket.blend> <out_prefix> [set]   set = turn | detail | all"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import render_lib as R

a = args_after_dashes()
blend, prefix = a[0], a[1]
which = a[2] if len(a) > 2 else 'turn'
bpy.ops.wm.open_mainfile(filepath=blend)
sock = bpy.data.objects['Hand_Racket']
sock.rotation_euler = (math.radians(90), 0, 0)       # local Y -> world Z, local Z -> world -Y (face towards camera)
sock.location = (0, 0, 0.60)                          # lift so the butt sits above a floor at z=0.60-0.107
bpy.context.view_layer.update()
for o in bpy.data.objects:
    if o.name == 'Collider_Racket':
        o.hide_render = True
R.studio(bg=(0.36, 0.37, 0.39), samples=64)
zc = 0.60 + 0.24
if which in ('turn', 'all'):
    # front / back / side / three-quarter views of the whole racket
    R.shot(prefix + '_front.png', (0, 0, zc), az=0, el=0, dist=2.4, lens=85, res=(900, 1400))
    R.shot(prefix + '_back.png', (0, 0, zc), az=180, el=0, dist=2.4, lens=85, res=(900, 1400))
    R.shot(prefix + '_side.png', (0, 0, zc), az=90, el=0, dist=2.4, lens=85, res=(900, 1400))
    R.shot(prefix + '_q3.png', (0, 0, zc), az=35, el=14, dist=2.4, lens=85, res=(900, 1400))
if which in ('detail', 'all'):
    R.shot(prefix + '_throat.png', (0, 0, 0.60 + 0.20), az=0, el=0, dist=0.75, lens=85, res=(1000, 1000))
    R.shot(prefix + '_throat_q3.png', (0, 0, 0.60 + 0.17), az=38, el=18, dist=0.8, lens=85, res=(1000, 1000))
    R.shot(prefix + '_grip.png', (0, 0, 0.60 - 0.02), az=0, el=0, dist=0.75, lens=85, res=(1000, 1000))
    R.shot(prefix + '_grip_q3.png', (0, 0, 0.60 - 0.04), az=40, el=-25, dist=0.55, lens=85, res=(1000, 1000))
    R.shot(prefix + '_strings.png', (0.03, 0, 0.60 + 0.30), az=15, el=15, dist=0.45, lens=85, res=(1000, 1000))
print('RENDER_DONE')
