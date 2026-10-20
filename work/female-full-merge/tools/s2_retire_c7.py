"""Stage 2: retire chat 7's superseded torso in the hands base. blender -b start/base_hands_candidate.blend --python s2_retire_c7.py -- <out.blend>
Every one of chat 7's 3,317 moved vertices must be EXACTLY at chat 7's position in the base (checked bit-exact); each is set back to the ArtDir original (= chat 7's start_co).
Positions only; raw custom normals are untouched (verified equal to ArtDir's raw in that zone). FORM5 supersedes chat 7 ('apply exactly ONE of them')."""
import bpy, sys, numpy as np, json
out = sys.argv[sys.argv.index('--') + 1]
c7 = np.load('start/chat7_torso_delta.npz'); vm = np.load('data/vmap_artdir_to_base.npz')['base_to_final']
o = bpy.data.objects['Body_F']; me = o.data; n = len(me.vertices); assert n == 23247
co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
t = vm[c7['moved_idx']]; assert (t >= 0).all()
assert (co[t] == c7['new_co']).all(), 'base is not at chat-7 positions'
moved_mm = np.linalg.norm(co[t] - c7['start_co'], axis=1) * 1000
co[t] = c7['start_co']
me.vertices.foreach_set('co', co.ravel()); me.update()
print('RETIRE_C7', json.dumps({'verts_reverted': int(len(t)), 'max_revert_mm': float(moved_mm.max()), 'mean_revert_mm': float(moved_mm.mean())}))
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
