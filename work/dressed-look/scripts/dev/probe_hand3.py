"""Scratch: gap between the right hand and the thigh (female) -- body = everything not in the arm component."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_common import *
import collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
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
xcut = -0.45 if tag == 'male' else -0.19
sel = co[:,0] < xcut
adj = collections.defaultdict(list)
for a,b in E:
    if sel[a] and sel[b]:
        adj[a].append(b); adj[b].append(a)
seen=set(); comps=[]
for s in np.where(sel)[0]:
    if s in seen: continue
    st=[s]; seen.add(s); comp=[s]
    while st:
        u=st.pop()
        for v in adj[u]:
            if v not in seen: seen.add(v); st.append(v); comp.append(v)
    comps.append(np.array(comp))
comps.sort(key=lambda c: -len(c)); arm = comps[0]
# hand vertices: below wrist z
wz = 0.88 if tag=='female' else 0.97
hand = arm[co[arm,2] < wz]
print(tag, 'hand n', len(hand))
# the rest of the body: all vertices not in 'hand' region and below hip; build BVH of body-without-arm = faces whose verts are all outside 'arm' set for z<1.0
armset = set(arm.tolist())
tris = mesh_tris(o)
keep = np.array([not (a in armset or b in armset or c in armset) for a,b,c in tris])
BT = BVHTree.FromPolygons([tuple(map(float,v)) for v in co], [tuple(int(i) for i in t) for t in tris[keep]], epsilon=0.0)
d = []
for i in hand:
    loc, nrm, idx, dist = BT.find_nearest(Vector(co[i]))
    d.append(dist)
d = np.array(d)
print('hand->rest-of-body distance: min %.1f mm  p5 %.1f  median %.1f mm' % (d.min()*1000, np.percentile(d,5)*1000, np.median(d)*1000))
np.save(os.path.join(WORK,'tmp',f'hand_idx_{tag}.npy'), hand)
