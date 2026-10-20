"""Anatomy landmarks of the authority bodies (read-only): per-height torso/pelvis/leg cross-section widths so the kit hems/bands are anchored to the body.
blender -b --factory-startup --python landmarks.py"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *

out = {}
for gender, blend, obj in (('male', MALE_BLEND, 'Body_M'), ('female', FEMALE_BLEND, 'Body_F')):
    bpy.ops.wm.open_mainfile(filepath=blend)
    V, F = mesh_arrays(bpy.data.objects[obj])
    rep = dict(bbox_min=V.min(0).round(4).tolist(), bbox_max=V.max(0).round(4).tolist(), rows=[])
    print('==', gender, 'bbox', rep['bbox_min'], rep['bbox_max'])
    print('   z      loops  [per loop: cx, xmin..xmax, ymin..ymax, area cm2]')
    for z in np.arange(0.40, 1.62, 0.02):
        loops = [P for P in slice_plane(V, F, 2, float(z)) if len(P) >= 6]
        row = []
        for P in loops:
            row.append(dict(cx=float(P[:, 0].mean()), x0=float(P[:, 0].min()), x1=float(P[:, 0].max()), y0=float(P[:, 1].min()), y1=float(P[:, 1].max()), a=abs(poly_area_xy(P)) * 1e4))
        row.sort(key=lambda r: r['cx'])
        rep['rows'].append(dict(z=round(float(z), 3), loops=row))
        s = '  '.join(f"[{r['cx']:+.3f} x{r['x0']:+.3f}..{r['x1']:+.3f} y{r['y0']:+.3f}..{r['y1']:+.3f} A{r['a']:6.1f}]" for r in row)
        print(f'   {z:.2f}  {len(row)}  {s}')
    out[gender] = rep
json.dump(out, open(f'{WORK}/tmp/landmarks.json', 'w'), indent=1)
