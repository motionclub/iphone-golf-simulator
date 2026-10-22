import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head/pylib')
import numpy as np, bpy
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head'
bpy.ops.wm.open_mainfile(filepath=W + '/baseline/HeroBase_Male_Silhouette.blend')
body = bpy.data.objects['Body_M']; me = body.data; n = len(me.vertices)
V = np.load(W + '/data/V_start.npy'); vn = np.load(W + '/data/vn_stored.npy')
nrm = np.empty(n * 3); me.vertex_normals.foreach_get('vector', nrm); nrm = nrm.reshape(-1, 3)
d0 = np.degrees(np.arccos(np.clip((nrm * vn).sum(1), -1, 1)))
print('iteration 0 (raw vertex normals) vs stored: mean %.4f max %.2f  >0.5deg: %d  >5deg: %d' % (d0.mean(), d0.max(), (d0 > 0.5).sum(), (d0 > 5).sum()))
hd = V[:, 2] > 1.43
print('head part: mean %.4f  >0.5deg: %d / %d' % (d0[hd].mean(), (d0[hd] > 0.5).sum(), hd.sum()))
big = np.where(d0 > 5)[0]
for i in big[:15]: print('   v%d d=%.1f deg  at x=%.4f y=%.4f z=%.4f' % (i, d0[i], V[i, 0], V[i, 1], V[i, 2]))
# which materials / sharp flags?
print('sharp_face attr:', 'sharp_face' in me.attributes, ' sharp_edge:', 'sharp_edge' in me.attributes)
sharp = np.zeros(len(me.edges), bool)
if 'sharp_edge' in me.attributes: me.attributes['sharp_edge'].data.foreach_get('value', sharp)
print('sharp edges:', int(sharp.sum()), ' of', len(me.edges))
sf = np.zeros(len(me.polygons), bool)
if 'sharp_face' in me.attributes: me.attributes['sharp_face'].data.foreach_get('value', sf)
print('sharp faces:', int(sf.sum()))
# angle between stored normal and plain geometric neighbourhood for head verts: histogram
import collections
print('head part angle histogram (deg): ', np.histogram(d0[hd], bins=[0, .05, .2, .5, 1, 2, 5, 90])[0])
