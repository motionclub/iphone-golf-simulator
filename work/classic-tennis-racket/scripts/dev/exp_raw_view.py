import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import racket_geom as G, sdf_tools as S
import render_lib as R
d = np.load(WORK / 'tmp' / 'frame_raw.npz')
V, T = d['V'], d['T']
reset_scene()
me = bpy.data.meshes.new('raw'); me.from_pydata([tuple(v) for v in V], [], [tuple(int(i) for i in t) for t in T]); me.update()
o = bpy.data.objects.new('raw', me); bpy.context.scene.collection.objects.link(o)
me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
mat = bpy.data.materials.new('W'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.85, 0.85, 0.84, 1)
me.materials.append(mat)
o.rotation_euler = (math.radians(90), 0, 0); o.location = (0, 0, 0.60)
R.studio(bg=(0.36, 0.37, 0.39), samples=48)
R.shot(str(WORK / 'tmp' / 'exp_raw_throat.png'), (0, 0, 0.60 + 0.20), az=38, el=18, dist=0.8, lens=85, res=(900, 900))
R.shot(str(WORK / 'tmp' / 'exp_raw_front.png'), (-0.05, 0, 0.60 + 0.25), az=0, el=0, dist=0.55, lens=85, res=(900, 900))
