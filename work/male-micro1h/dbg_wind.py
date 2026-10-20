import sys
import numpy as np
import bpy
bpy.ops.wm.open_mainfile(filepath='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h/final/HeroBase_Male_Silhouette_f3.blend')
face = bpy.data.objects['Face_M']
me = face.data
names = [m.name for m in me.materials]
V = np.array([v.co[:] for v in me.vertices])
res = {}
for p in me.polygons:
    n = np.array(p.normal[:]); c = np.array(p.center[:])
    # outward for a front-facing part: normal.y < 0 (faces toward -y)
    key = names[p.material_index]
    r = res.setdefault(key, [0, 0])
    r[0 if n[1] < 0 else 1] += 1
for k, v in res.items(): print(k, 'front-facing(-y)', v[0], 'back-facing', v[1])
# per object eye side
for side in (-1, 1):
    sel = [p for p in me.polygons if names[p.material_index] in ('Face_Iris', 'Face_Sclera', 'Face_Pupil', 'Face_Limbal') and np.sign(p.center[0]) == side]
    print('eye side', side, 'n', len(sel), 'front-facing', sum(1 for p in sel if p.normal[1] < 0))
for nm in ('Face_Brow',):
    for side in (-1, 1):
        sel = [p for p in me.polygons if names[p.material_index] == nm and np.sign(p.center[0]) == side]
        print(nm, 'side', side, 'n', len(sel), 'front-facing', sum(1 for p in sel if p.normal[1] < 0))
