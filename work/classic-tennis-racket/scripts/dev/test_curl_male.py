"""Smoke test: curl the male fingers by fixed angles on a COPY of the hand and render the result. Hero blend untouched.
blender -b --factory-startup --python test_curl_male.py"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import render_lib as R
import male_hand as MH
from handpose import apply_chain

reset_scene()
body = load_body_copy('male')
co = mesh_co(body)
sel, c, u, v, p = MH.frame_from_body(co)
Q = MH.to_hand(co[sel], c, u, v, p)
chains = MH.build_chains(Q)
thumb = MH.build_thumb(Q)
ang = np.radians
pose = {'index': (ang(50), ang(70), ang(40)), 'middle': (ang(55), ang(75), ang(40)), 'ring': (ang(60), ang(80), ang(40)), 'pinky': (ang(65), ang(80), ang(35))}
Qn = Q.copy()
for name, ch in chains.items():
    Qn = Qn + (apply_chain(Q, ch, pose[name]) - Q)
Qn = Qn + (apply_chain(Q, thumb, (ang(25), ang(30))) - Q)
newP = MH.from_hand(Qn, c, u, v, p)
co2 = co.copy()
co2[sel] = newP
body.data.vertices.foreach_set('co', co2.ravel())
body.data.update()
mat = bpy.data.materials.new('G'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.30, 0.30, 0.32, 1)
body.data.materials.clear(); body.data.materials.append(mat)
R.studio(bg=(0.36, 0.37, 0.39), samples=32)
tgt = (-0.60, -0.11, 0.86)
R.shot(str(WORK / 'tmp' / 'curl_front.png'), tgt, az=0, el=5, dist=0.6, lens=70, res=(800, 800))
R.shot(str(WORK / 'tmp' / 'curl_side.png'), tgt, az=-90, el=0, dist=0.6, lens=70, res=(800, 800))
R.shot(str(WORK / 'tmp' / 'curl_medial.png'), tgt, az=90, el=0, dist=0.6, lens=70, res=(800, 800))
print('CURL_DONE')
