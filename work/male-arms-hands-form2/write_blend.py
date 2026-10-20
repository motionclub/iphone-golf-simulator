"""Write a candidate into a copy of the baseline blend with bmesh (keeps custom normals + vertex groups of all kept loops).
blender -b baseline.blend --python write_blend.py -- <cand.npz> <out.blend> <removed_faces.npy>
The candidate is Mesh(V, polys) where polys = kept original polygons (original order) + new polygons; vertex indices < N0 never change meaning."""
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
cand, out, remp = a[0], a[1], a[2]
D = np.load(cand); V = D['V'].astype(np.float32); cv = D['corner_verts']; ls = D['loop_start']; lt = D['loop_total']
polys = [tuple(int(x) for x in cv[s:s + t]) for s, t in zip(ls, lt)]
removed = np.load(remp)
o = bpy.data.objects['Body_M']; me = o.data
n0 = len(me.vertices); f0 = len(me.polygons)
bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
assert len(bm.faces) == f0
# --- delete the old hand shell faces (keep verts; they are reused as slots)
rem_faces = [bm.faces[int(i)] for i in removed]
rem_edges = set(); 
for f in rem_faces:
    for e in f.edges: rem_edges.add(e)
bmesh.ops.delete(bm, geom=rem_faces, context='FACES_ONLY')
dead = [e for e in rem_edges if e.is_valid and len(e.link_faces) == 0]
for e in dead:
    bm.edges.remove(e)          # edge only (no faces use it); vertices are kept so indices stay stable
# --- set vertex positions of the reused slots and append the new vertices
bm.verts.ensure_lookup_table()
assert len(bm.verts) == n0
for i in range(n0):
    c = bm.verts[i].co
    if (c.x != V[i, 0]) or (c.y != V[i, 1]) or (c.z != V[i, 2]):
        bm.verts[i].co = (float(V[i, 0]), float(V[i, 1]), float(V[i, 2]))
for i in range(n0, len(V)):
    bm.verts.new((float(V[i, 0]), float(V[i, 1]), float(V[i, 2])))
bm.verts.ensure_lookup_table()
# --- new faces = candidate polygons after the kept ones
nkept = f0 - len(removed)
new_polys = polys[nkept:]
for p in new_polys:
    f = bm.faces.new([bm.verts[i] for i in p])
    f.smooth = True
    for e in f.edges: e.smooth = True
bm.faces.ensure_lookup_table()
assert len(bm.faces) == len(polys), (len(bm.faces), len(polys))
bm.to_mesh(me); bm.free(); me.update()
me.polygons.foreach_set('use_smooth', [True] * len(me.polygons)) if False else None
print('WROTE verts', len(me.vertices), 'polys', len(me.polygons), 'loops', len(me.loops))
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
