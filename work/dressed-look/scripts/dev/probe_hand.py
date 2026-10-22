"""Scratch: probe the right-hand vertex region of a body (read-only)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_common import *
tag = args_after_dashes()[0]
h = HERO[tag]
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(SRC[h['body_src']], link=False) as (src, dst):
    dst.objects = [h['body']]
o = dst.objects[0]
bpy.context.scene.collection.objects.link(o)
co = mesh_co(o).astype(float)
print(tag, 'verts', len(co), 'z range', co[:,2].min(), co[:,2].max())
print('vertex groups:', [g.name for g in o.vertex_groups])
# right hand = -X side; look at the extremities in z
for xlim in (-0.20, -0.45):
    for zlim in (0.83, 0.95, 1.0):
        sel = (co[:,0] < xlim) & (co[:,2] < zlim)
        print('x<%.2f z<%.2f -> n=%d  bbox min %s max %s' % (xlim, zlim, sel.sum(), np.round(co[sel].min(0),3) if sel.any() else None, np.round(co[sel].max(0),3) if sel.any() else None))
# vertex-group membership of hand-ish vertices
import collections
me = o.data
cnt = collections.Counter()
sel = np.where((co[:,0] < (-0.45 if tag=='male' else -0.20)) & (co[:,2] < (1.0 if tag=='male' else 0.83)))[0]
names = {g.index: g.name for g in o.vertex_groups}
for i in sel:
    for g in me.vertices[int(i)].groups:
        cnt[names[g.group]] += 1
print('groups on hand verts', dict(cnt))
