"""Quick look at the hero hands (read-only copy): grey-studio close-ups of the right hand (character's right = world -X)."""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import render_lib as R

tag = sys.argv[sys.argv.index('--') + 1]
reset_scene()
o = load_body_copy(tag)
mat = bpy.data.materials.new('Grey')
mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.35, 0.35, 0.37, 1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6
o.data.materials.clear()
o.data.materials.append(mat)
R.studio()
co = mesh_co(o)
if tag == 'male':
    tgt = (-0.62, -0.10, 0.88)
else:
    tgt = (-0.18, -0.03, 0.74)
out = WORK / 'tmp'
for name, az, el in (('front', 0, 0), ('side', -90, 0), ('top', 0, 89), ('q3', -40, 20), ('back', 180, 0)):
    R.shot(out / f'look_{tag}_{name}.png', tgt, az=az, el=el, dist=0.7, lens=70, res=(900, 900))
R.shot(out / f'look_{tag}_full.png', (0, -0.05, 0.85), az=0, el=0, dist=4.2, lens=60, res=(900, 1100))
print('LOOK_DONE')
