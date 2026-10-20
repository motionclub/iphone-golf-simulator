"""extract the 30-vertex collar ring (weld ring) of the START blend + body bookkeeping.  blender -b start.blend --python ring.py -> data/ring.npz"""
import sys, collections
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, bpy, fl
o = bpy.data.objects['Body_F']; me = o.data
V, F = fl.mesh_arrays(me)
mi = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('material_index', mi)
names = [m.name for m in me.materials]
grey = names.index('Base_Grey_F'); skin = names.index('Skin_F')
par = list(range(len(V)))
def find(a):
    while par[a] != a:
        par[a] = par[par[a]]; a = par[a]
    return a
for f, m in zip(F, mi):
    if m == grey: continue
    for v in f[1:]:
        ra, rb = find(int(f[0])), find(int(v))
        if ra != rb: par[ra] = rb
comp = collections.defaultdict(list)
for fi, (f, m) in enumerate(zip(F, mi)):
    if m != grey: comp[find(int(f[0]))].append(fi)
big = sorted(comp.values(), key=len, reverse=True)
head_faces = set(big[0])                                     # 6336 head grid faces
# neck skin component (z 1.396..1.456) and head feature patches (all non-grey comps whose verts z > 1.39)
zone_faces = []
for fl_ in comp.values():
    vs = {int(v) for fi in fl_ for v in F[fi]}
    zmin = V[list(vs), 2].min()
    if zmin > 1.39:
        zone_faces += fl_
zone_faces = sorted(set(zone_faces))
print('head-zone faces (above collar, non-grey):', len(zone_faces), 'of', len(F))
# ring = vertices shared between grey faces and the zone faces
zset = set(zone_faces); zverts = {int(v) for fi in zone_faces for v in F[fi]}
gverts = {int(v) for fi, f in enumerate(F) if mi[fi] == grey for v in f}
ring = sorted(zverts & gverts)
print('ring verts', len(ring))
R = V[ring]
cx, cy = 0.0, float(R[:, 1].mean()); print('ring centre y', cy, 'z', R[:, 2].mean(), 'x range', R[:, 0].min(), R[:, 0].max(), 'y range', R[:, 1].min(), R[:, 1].max())
ang = np.arctan2(R[:, 1] - cy, R[:, 0] - cx)
order = np.argsort(ang); ring_ord = [ring[i] for i in order]
# the ring vertices must form the boundary of the grey region: verify consecutive adjacency in the edge graph
adj = collections.defaultdict(set)
for f in F:
    n = len(f)
    for i in range(n): a, b = int(f[i]), int(f[(i + 1) % n]); adj[a].add(b); adj[b].add(a)
ok = sum(1 for i in range(len(ring_ord)) if ring_ord[(i + 1) % len(ring_ord)] in adj[ring_ord[i]])
print('consecutive-adjacent pairs', ok, 'of', len(ring_ord))
# grey-material faces touching the ring (the first grey row)
np.savez(fl.W / 'data/ring.npz', ring=np.array(ring_ord), pos=V[ring_ord], zone_faces=np.array(zone_faces))
print(np.round(V[ring_ord], 4))
