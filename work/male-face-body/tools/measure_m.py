"""Blender -b --factory-startup --python measure_m.py -- <blend> <tag>
Male game-preview (ft.game_warp = what Unity draws) -> eval/<tag>_*: front/side silhouette masks (ortho, 1200 px, centre C, half H),
shaded stills (front / 3q / side, head + mouth zoom), game-frame mesh (mm, eval/<tag>_mesh.npz: G, tri) and the frame (eval/frame.json)."""
import bpy, sys, numpy as np, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft, sculpt_mouth as S
argv = sys.argv[sys.argv.index('--') + 1:]
blend, tag = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=blend)
ft.build_preview('Male')
if os.environ.get('GAME_NORMALS'): ft.game_normals('Male')
out = ft.WORK + '/eval'; os.makedirs(out, exist_ok=True)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
F = ft.frame(bpy.data.objects['Body'], bpy.data.objects['ReferenceFeatures'], rig)
eye = F[0]
C = (0.0, float(eye[1]) + .02, float(eye[2]) - .03); H = .2
json.dump({'eye': list(map(float, F[0])), 'right': list(map(float, F[1])), 'up': list(map(float, F[2])), 'fwd': list(map(float, F[3])),
           'C': C, 'H': H}, open(f'{out}/frame.json', 'w'))
for v in ('front', 'side'):
    m = ft.render_mask(['GamePreview_Body'], v, C, H, 1200, out + f'/tmp_{v}.png'); np.save(f'{out}/{tag}_{v}_mask.npy', m)
objs = ['GamePreview_Body', 'GamePreview_Features']
for v in ('front', 'three_quarter', 'side'):
    ft.shaded(objs, v, (0, C[1] - .01, eye[2] - .015), .13, 900, f'{out}/{tag}_{v}.png')
    ft.shaded(objs, v, (0, C[1] - .03, eye[2] - .075), .055, 700, f'{out}/{tag}_{v}_mouth.png')
body = bpy.data.objects['GamePreview_Body']
co = ft.coords(body.data)
idx, tri, edges, nu = ft.topology_at(ft.coords(bpy.data.objects['Body'].data), body.data)
U = np.zeros((nu, 3)); U[idx] = co
np.savez(f'{out}/{tag}_mesh.npz', G=S.to_face(U, F), tri=tri, idx=idx)
print('MEASURE DONE', C)
