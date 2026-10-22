"""Blender -b --factory-startup --python snap_m.py -- <blend> <out.npz>
Snapshot of the male Body for offline (numpy-only) sculpt work: basis + shape keys + authored corner normals + loop->vertex,
triangles, the warp frame, ReferenceFeatures brow/iris sets, and bone heads used by ft.game_normals."""
import bpy, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; me = body.data; feat = bpy.data.objects['ReferenceFeatures']
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
F = ft.frame(body, feat, rig)
keys = {k.name: ft.coords(me, k.name) for k in me.shape_keys.key_blocks} if me.shape_keys else {}
nrm = np.empty(len(me.loops) * 3); me.corner_normals.foreach_get('vector', nrm)
lv = np.empty(len(me.loops), dtype=np.int64); me.loops.foreach_get('vertex_index', lv)
me.calc_loop_triangles(); t = np.empty(len(me.loop_triangles) * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', t)
bones = {b.name: np.array(b.head_local) for b in rig.data.bones if b.name in ('Head', 'Neck', 'Spine2', 'Spine1', 'Spine', 'Hips')}
np.savez(argv[1], basis=ft.coords(me), normals=nrm.reshape(-1, 3), loopv=lv, tri=t.reshape(-1, 3), eye=F[0], right=F[1], up=F[2], fwd=F[3],
         head_tail=np.array(rig.data.bones['Head'].tail_local), **{'bone_' + k: v for k, v in bones.items()}, **{'key_' + k: v for k, v in keys.items()})
print('SNAP DONE', len(me.vertices), list(keys))
