"""Blender -b --factory-startup --python measure.py -- <blend> <tag>
Game-preview silhouettes (front/side, ortho, C/H frame) + shaded stills (front / 3q / side, head + mouth zoom) -> ../eval/<tag>_*"""
import bpy, sys, numpy as np, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft
argv = sys.argv[sys.argv.index('--') + 1:]
blend, tag = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=blend)
ft.build_preview('Female')
if os.environ.get('GAME_NORMALS'): ft.game_normals('Female')
if False: pass
pass
out = ft.WORK + '/eval'; os.makedirs(out, exist_ok=True)
C = (0, -.05, 1.52); H = .2
for v in ('front', 'side'):
    m = ft.render_mask(['GamePreview_Body'], v, C, H, 1200, out + f'/tmp_{v}.png'); np.save(f'{out}/{tag}_{v}_mask.npy', m)
objs = ['GamePreview_Body', 'GamePreview_Features']
for v in ('front', 'three_quarter', 'side'):
    ft.shaded(objs, v, (0, -.06, 1.53), .125, 700, f'{out}/{tag}_{v}.png')
    ft.shaded(objs, v, (0, -.09, 1.47), .055, 700, f'{out}/{tag}_{v}_mouth.png')
body = bpy.data.objects['GamePreview_Body']
np.save(f'{out}/{tag}_game_co.npy', ft.coords(body.data))
F = ft.frame(bpy.data.objects['Body'], bpy.data.objects['ReferenceFeatures'], next(o for o in bpy.data.objects if o.type == 'ARMATURE'))
json.dump({'eye': list(map(float, F[0])), 'right': list(map(float, F[1])), 'up': list(map(float, F[2])), 'fwd': list(map(float, F[3]))}, open(f'{out}/frame.json', 'w'))
print('MEASURE DONE')
