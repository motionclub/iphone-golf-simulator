"""Blender -b <sock.blend> --python trim_sock.py -- <shoe.blend> <out.blend> : delete sock faces that lie UNDER the shoe (a ray straight up, or
out along the face normal, meets the shoe within 8 cm). The sock then ends hidden inside the shoe instead of at a straight cut."""
import bpy, bmesh, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; shoe_path, out = a[0], a[1]
sock = [o for o in bpy.data.objects if o.type == 'MESH'][0]
with bpy.data.libraries.load(shoe_path) as (src, dst): dst.objects = [n for n in src.objects]
shoe = [o for o in dst.objects if o and o.type == 'MESH'][0]
sm = shoe.data; sm.calc_loop_triangles()
P = [shoe.matrix_world @ v.co for v in sm.vertices]
tris = [tuple(t.vertices) for t in sm.loop_triangles]
tree = BVHTree.FromPolygons(P, tris, all_triangles=True)
s4 = np.zeros(len(sm.vertices), np.float32); sm.attributes['s4'].data.foreach_get('value', s4) if 's4' in sm.attributes else None
tri_s = s4[np.array(tris)].mean(1)
fk = np.zeros(len(sm.polygons), np.int32); sm.attributes['face_kind'].data.foreach_get('value', fk)
tri_k = fk[np.array([t.polygon_index for t in sm.loop_triangles])]
T0 = float(a[2]) if len(a) > 2 else .47
DEEP = float(a[3]) if len(a) > 3 else .015
# the opening rim = the padded collar / eyestay roll (face_kind 12): its height at each place, horizontally
roll_v = sorted({v for p_ in sm.polygons if fk[p_.index] == 12 for v in p_.vertices})
RV = np.array([tuple(shoe.matrix_world @ sm.vertices[int(v)].co) for v in roll_v])
bm = bmesh.new(); bm.from_mesh(sock.data); bm.faces.ensure_lookup_table(); bm.normal_update()
kill = []
for f in bm.faces:
    c = sock.matrix_world @ f.calc_center_median(); n = (sock.matrix_world.to_3x3() @ f.normal).normalized()
    up = tree.ray_cast(c + Vector((0, 0, .0005)), Vector((0, 0, 1)), .08)
    out_ = tree.ray_cast(c + n * .0005, n, .03)
    k_ = np.argmin(np.hypot(RV[:, 0] - c.x, RV[:, 1] - c.y))
    if c.z < RV[k_, 2] - DEEP: kill.append(f); continue                      # deeper than DEEP under the opening rim: always inside the shoe
    dn = tree.ray_cast(c - Vector((0, 0, .0005)), Vector((0, 0, -1)), .035)
    if up[0] is not None and (out_[0] is not None or (up[0].z - c.z) > DEEP): kill.append(f)      # under the shoe: inside it, or deeper than DEEP below its surface
    elif dn[0] is not None and tri_s[dn[2]] > T0 - .02 and tri_k[dn[2]] in (19, 21): kill.append(f)      # over the throat / vamp (poking out of the eyestays)
bmesh.ops.delete(bm, geom=kill, context='FACES'); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
# drop small loose islands the trim leaves behind (they wreck the UV packing scale)
bm.faces.ensure_lookup_table(); seen = set(); small = []
for f0 in bm.faces:
    if f0.index in seen: continue
    comp = [f0]; seen.add(f0.index); st = [f0]
    while st:
        f_ = st.pop()
        for e_ in f_.edges:
            for g_ in e_.link_faces:
                if g_.index not in seen: seen.add(g_.index); comp.append(g_); st.append(g_)
    if len(comp) < 200: small += comp
bmesh.ops.delete(bm, geom=small, context='FACES'); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
print('TRIMSOCK dropped', len(small), 'faces in small islands')
bm.to_mesh(sock.data); bm.free()
for o in list(bpy.data.objects):
    if o is not sock: bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=out); print('TRIMSOCK removed', len(kill), 'faces')
