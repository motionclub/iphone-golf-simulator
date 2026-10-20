"""Micro1g audit: regression vs the Micro1f lock + native silhouette gate (Body_M only, and with Face_M).
blender -b --factory-startup --python audit_head.py -- <final.blend> <outdir>"""
import sys, json, hashlib
from pathlib import Path
import numpy as np
import bpy
argv = sys.argv[sys.argv.index('--') + 1:]
blend = Path(argv[0]); out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
W = Path(__file__).resolve().parent
LOCK = np.load(W.parent / 'male-micro1f/final/k5_verts.npy')
bpy.ops.wm.open_mainfile(filepath=str(blend))
body = bpy.data.objects['Body_M']; face = bpy.data.objects.get('Face_M')
V = np.array([v.co[:] for v in body.data.vertices], float)
d = np.linalg.norm(V - LOCK, axis=1); moved = d > 1e-7
z = LOCK[:, 2]; x = LOCK[:, 0]
head = (z > 1.43) & (np.abs(x) < 0.14)
hands = (np.abs(x) > 0.44) & (z < 1.06)
chin_band = head & (z < 1.47)                       # Micro1e chin lock band
res = dict(blend_sha256=hashlib.sha256(blend.read_bytes()).hexdigest(), verts=len(V), moved=int(moved.sum()),
           moved_outside_head=int((moved & ~head).sum()), hands_changed=int((moved & hands).sum()),
           chin_band_changed=int((moved & chin_band).sum()), chin_band_max_mm=float(d[chin_band].max() * 1000),
           max_disp_mm=float(d.max() * 1000), head_mean_disp_mm=float(d[head & moved].mean() * 1000) if (head & moved).any() else 0.0,
           body_tris=sum(len(p.vertices) - 2 for p in body.data.polygons),
           face_tris=(sum(len(p.vertices) - 2 for p in face.data.polygons) if face else 0), face_verts=(len(face.data.vertices) if face else 0),
           height_m=float(V[:, 2].max() - V[:, 2].min()))
# per-region moved counts (head-detail z bands)
bands = {'cranium z>1.63': head & (z > 1.63), 'brow/eyes 1.57-1.63': head & (z > 1.57) & (z <= 1.63), 'nose/cheeks 1.52-1.57': head & (z > 1.52) & (z <= 1.57),
         'mouth 1.47-1.52': head & (z > 1.47) & (z <= 1.52), 'chin <1.47': chin_band}
res['bands'] = {k: dict(verts=int(m.sum()), moved=int((moved & m).sum()), max_mm=float(d[m].max() * 1000) if m.any() else 0) for k, m in bands.items()}
# silhouette gate renders (blend's own locked workbench setup)
s = bpy.context.scene
s.render.film_transparent = True; s.render.image_settings.color_mode = 'RGBA'; s.render.image_settings.file_format = 'PNG'
s.render.resolution_x = 1280; s.render.resolution_y = 720; s.render.resolution_percentage = 100
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
for tag, show_face in (('body', False), ('withface', True)):
    if face: face.hide_render = not show_face
    for view in ('bald_front', 'bald_back'):
        s.camera = bpy.data.objects['Locked_' + view]; s.render.filepath = str((out / f'{tag}_{view}.png').resolve()); bpy.ops.render.render(write_still=True)
(out / 'audit.json').write_text(json.dumps(res, indent=1)); print('AUDIT_JSON ' + json.dumps(res))
