"""Blender -b --factory-startup --python apply_m.py -- <delta tag> [export]
Applies eval/<tag>_delta.npy (per source vertex, metres, from sculpt_off.py) to the production male head
(work/jaw-sculpt-2026-10-12/Male_JawSculpt.blend = installed OriginalSeamBlinkFinish/Male.fbx): basis + every shape key get the same
delta, the authored corner normals are rotated with the 4-ring-smoothed surface normal (never left stale), then the blend is saved to
export/Male_<tag>.blend and (with 'export') written to export/Male_<tag>.fbx with the 10-12 jaw-sculpt FBX options."""
import bpy, sys, os, hashlib, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft
argv = sys.argv[sys.argv.index('--') + 1:]; tag = argv[0]
W = ft.WORK; SRC = W + '/source_male_1017.npz'
bpy.ops.wm.open_mainfile(filepath=ft.JAW + '/Male_JawSculpt.blend')
body = bpy.data.objects['Body']; me = body.data
d = np.load(SRC); base = d['basis']; nrm = d['normals']
assert np.abs(ft.coords(me) - base).max() < 1e-7, 'production blend differs from the snapshot'
D = np.load(f'{W}/eval/{tag}_delta.npy'); assert D.shape == base.shape
for k in me.shape_keys.key_blocks: ft.set_coords(me, d['key_' + k.name] + D, k.name)
ft.set_coords(me, base + D); me.update()
idx, tri, edges, nu = ft.topology_at(base, me)
i, j = edges[:, 0], edges[:, 1]
def sn(co):
    P = np.zeros((nu, 3)); P[idx] = co; N = ft.vertex_normals(P, tri)
    for _ in range(4):
        acc = N.copy(); np.add.at(acc, i, N[j]); np.add.at(acc, j, N[i]); N = acc / np.maximum(np.linalg.norm(acc, axis=1), 1e-12)[:, None]
    return N
n0 = sn(base); n1 = sn(base + D)
lv = d['loopv']; a = n0[idx[lv]]; b = n1[idx[lv]]
k = np.cross(a, b); s = np.linalg.norm(k, axis=1); c = np.einsum('ij,ij->i', a, b); kk = k / np.maximum(s, 1e-12)[:, None]
rot = nrm * c[:, None] + np.cross(kk, nrm) * s[:, None] + kk * (np.einsum('ij,ij->i', kk, nrm) * (1 - c))[:, None]
out = np.where((s > 1e-7)[:, None], rot, nrm); out /= np.linalg.norm(out, axis=1)[:, None]
me.normals_split_custom_set(out.tolist()); me.update()
print('NORMALS turned', int((s > 1e-4).sum()), 'max deg', round(float(np.degrees(np.arcsin(np.clip(s.max(), 0, 1)))), 2))
os.makedirs(W + '/export', exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=f'{W}/export/Male_{tag}.blend')
if 'export' in argv:
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE' and o.name.startswith('Rig_'))
    rig.data.pose_position = 'REST'; rig.animation_data_clear()
    for ob in (body, bpy.data.objects['ReferenceFeatures'], rig):
        ob.hide_set(False); ob.hide_viewport = False; ob.hide_select = False
    for ob in bpy.context.scene.objects:
        if ob.name.startswith(('GamePreview', 'NormTest')): ob.hide_set(True)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in bpy.context.scene.objects:
        ob.select_set(ob.name in ('Body', 'ReferenceFeatures') or ob is rig)
        if ob.type == 'MESH' and ob.data.shape_keys:
            for key in ob.data.shape_keys.key_blocks: key.value = 0
    bpy.context.view_layer.objects.active = body
    assert sorted(o.name for o in bpy.context.selected_objects) == sorted(['Body', 'ReferenceFeatures', rig.name])
    fbx = f'{W}/export/Male_{tag}.fbx'
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'ARMATURE', 'MESH'}, global_scale=1.0, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', use_mesh_modifiers=False, mesh_smooth_type='OFF',
                             add_leaf_bones=False, bake_anim=False, path_mode='STRIP', use_armature_deform_only=False)
    print('EXPORT DONE', fbx, hashlib.sha256(open(fbx, 'rb').read()).hexdigest(), len(me.vertices))
print('APPLY DONE', tag)
