"""Scratch: slab profile of the right arm / hand of both bodies (read-only)."""
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
me = o.data
E = np.empty(len(me.edges)*2, np.int64); me.edges.foreach_get('vertices', E); E = E.reshape(-1,2)
# components of the right-arm region, graph restricted to vertices with x < xcut
xcut = -0.45 if tag == 'male' else -0.19
sel = co[:,0] < xcut
import collections
adj = collections.defaultdict(list)
for a,b in E:
    if sel[a] and sel[b]:
        adj[a].append(b); adj[b].append(a)
seen = set(); comps = []
for s in np.where(sel)[0]:
    if s in seen: continue
    st=[s]; seen.add(s); comp=[s]
    while st:
        u=st.pop()
        for v in adj[u]:
            if v not in seen:
                seen.add(v); st.append(v); comp.append(v)
    comps.append(np.array(comp))
comps.sort(key=lambda c: -len(c))
print(tag, 'components x<%.2f:' % xcut, [(len(c), np.round(co[c].min(0),3).tolist(), np.round(co[c].max(0),3).tolist()) for c in comps[:5]])
arm = comps[0]
print('arm comp bbox', co[arm].min(0).round(3), co[arm].max(0).round(3))
zlo = co[arm,2].min()
for z0 in np.arange(np.floor(zlo*100)/100, min(co[arm,2].max(), 1.1), 0.02):
    m = (co[arm,2] >= z0) & (co[arm,2] < z0+0.02)
    if m.sum() == 0: continue
    P = co[arm][m]
    print('z %.2f-%.2f n=%4d  x[%.3f,%.3f] y[%.3f,%.3f]' % (z0, z0+0.02, m.sum(), P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
