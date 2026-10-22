"""Scratch: finger component scan (graph cut by u level) for both hands."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_common import *
from handlib import *
tag = args_after_dashes()[0]
h = HERO[tag]
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(SRC[h['body_src']], link=False) as (src, dst):
    dst.objects = [h['body']]
o = dst.objects[0]
bpy.context.scene.collection.objects.link(o)
co = mesh_co(o).astype(float)
me = o.data
E = edges_of(me); adj = adjacency(len(co), E)
hand = hand_region(co, adj, tag)
fr = pca_frame(co[hand])
print(tag, 'frame c', np.round(fr[0],4), 'u', np.round(fr[1],3), 'v', np.round(fr[2],3), 'p', np.round(fr[3],3))
Q = to_hand(co[hand], fr)
print('Q extents U [%.3f,%.3f] V [%.3f,%.3f] W [%.3f,%.3f]' % (Q[:,0].min(), Q[:,0].max(), Q[:,1].min(), Q[:,1].max(), Q[:,2].min(), Q[:,2].max()))
mask_hand = np.zeros(len(co), bool); mask_hand[hand] = True
Qall = np.zeros((len(co),3)); Qall[hand] = Q
for ucut in np.arange(-0.04, 0.09, 0.004):
    m = mask_hand & (Qall[:,0] > ucut)
    comps = components(m, adj)
    big = [c for c in comps if len(c) >= 25]
    print('ucut %+.3f -> %d comps, big sizes %s' % (ucut, len(comps), [len(c) for c in big][:8]))
