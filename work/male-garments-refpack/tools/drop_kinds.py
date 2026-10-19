"""Blender -b <in.blend> --python drop_kinds.py -- <out.blend> <kind,kind,...> : delete the faces of those part kinds (e.g. the shorts' drawcord)."""
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]; out = a[0]; kinds = {int(k) for k in a[1].split(',')}
ob = [o for o in bpy.data.objects if o.type == 'MESH'][0]; me = ob.data
attr = 'face_kind' if 'face_kind' in me.attributes else 'kind'
kk = np.zeros(len(me.polygons), np.int32); me.attributes[attr].data.foreach_get('value', kk)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
kill = [bm.faces[i] for i in np.nonzero(np.isin(kk, list(kinds)))[0]]
bmesh.ops.delete(bm, geom=kill, context='FACES'); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out); print('DROPPED', len(kill), 'faces of kinds', sorted(kinds), 'from', ob.name, 'attr', attr)
