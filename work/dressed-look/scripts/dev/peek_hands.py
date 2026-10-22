"""Quick look at the right hands (bind pose) with the racket at the OLD socket numbers. Scratch use only."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from dl_common import *
import render_lib as R   # read-only reuse of the racket chat's studio helper

tag = args_after_dashes()[0]
out = args_after_dashes()[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
h = HERO[tag]
with bpy.data.libraries.load(SRC[h['body_src']], link=False) as (src, dst):
    dst.objects = [h['body'], h['face']]
for o in dst.objects:
    bpy.context.scene.collection.objects.link(o)
with bpy.data.libraries.load(SRC['racket'], link=False) as (src, dst):
    dst.objects = list(src.objects)
rk = {o.name: o for o in dst.objects}
for o in rk.values():
    bpy.context.scene.collection.objects.link(o)
rk['Collider_Racket'].hide_render = True
sj = json.load(open(SRC['socket_json']))['bodies'][tag]['socket_bind_pose_blender']
M = Matrix.Identity(4)
for i, k in enumerate(('X', 'Y', 'Z')):
    for j in range(3):
        M[j][i] = sj[k][j]
for j in range(3):
    M[j][3] = sj['position'][j]
rk['Hand_Racket'].matrix_world = M
R.studio(bg=(0.36, 0.37, 0.39), samples=32)
body = bpy.data.objects[h['body']]
mat = bpy.data.materials.new('Proof_Grey'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.5, 0.5, 0.52, 1)
body.data.materials.clear(); body.data.materials.append(mat)
ctr = tuple(M.translation)
for nm, az, el, dist in (('a', -55, 10, 0.55), ('b', -120, 25, 0.55), ('c', 0, 5, 0.6), ('d', -90, 5, 0.6), ('e', 0, 60, 0.6)):
    R.shot(f'{out}_{nm}.png', ctr, az=az, el=el, dist=dist, lens=70, res=(900, 900))
print('PEEK_DONE')
