"""sheet3.py <tag> <coords.npy|-> [looks]  -> scratch/r/sheet_<tag>_{chest,pelvis}_<look>.png
chest sheet : plate | front | y+25 | y-25 | side      (one row per look)
pelvis sheet: plate | back  | y155 | y-155 | side
looks: soft (plate-like matcap), clay (clay_studio), stripe (mirror stripes)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from rr import *

LOOKS = {'soft': 'matcap:soft', 'clay': 'matcap:clay_studio.exr', 'stripe': 'matcap:check_reflection_vertical.exr'}


def sheet(tag, coords, looks=('soft', 'clay'), part='both', cav=0.0):
    outs = []
    parts = ['chest', 'pelvis'] if part == 'both' else [part]
    for pt in parts:
        rows = []
        for lk in looks:
            if pt == 'chest':
                shots = [roi_shot('front', 'chest'),
                         dict(name='y25', yaw=-25, xc=0.0, zc=1.19, w=0.389, res=[750, 900]),
                         dict(name='y-25', yaw=25, xc=0.0, zc=1.19, w=0.389, res=[750, 900]),
                         dict(name='side', yaw=-90, xc=0.0, zc=1.19, w=0.389, res=[750, 900])]
                plate = plate_crop('chest', 1.0)
            else:
                shots = [roi_shot('back', 'pelvis'),
                         dict(name='y155', yaw=-155, xc=0.0, zc=0.893, w=0.519, res=[1000, 850]),
                         dict(name='y-155', yaw=155, xc=0.0, zc=0.893, w=0.519, res=[1000, 850]),
                         dict(name='side', yaw=-90, xc=0.0, zc=0.893, w=0.519, res=[1000, 850])]
                plate = plate_crop('pelvis', 1.0)
            files = render([], coords, f'sh_{tag}_{pt}_{lk}', LOOKS[lk], cav, shots_extra=shots)
            ims = [plate] + files if lk == looks[0] else [Image.new('RGB', plate.size, (40, 40, 44))] + files
            labs = ['PLATE'] + [s['name'] for s in shots] if lk == looks[0] else [''] + [s['name'] for s in shots]
            rows.append(strip(ims, [f'{l} [{lk}]' if l else lk for l in labs], scale=0.5))
        W = max(r.width for r in rows)
        S = Image.new('RGB', (W, sum(r.height for r in rows)))
        y = 0
        for r in rows:
            S.paste(r, (0, y))
            y += r.height
        p = f'{HERE}/scratch/r/sheet_{tag}_{pt}.png'
        S.save(p)
        outs.append(p)
    return outs


if __name__ == '__main__':
    tag, coords = sys.argv[1], sys.argv[2]
    looks = tuple(sys.argv[3].split(',')) if len(sys.argv) > 3 else ('soft', 'clay')
    part = sys.argv[4] if len(sys.argv) > 4 else 'both'
    if not coords.startswith('/'):
        coords = HERE + '/' + coords
    for p in sheet(tag, coords, looks, part):
        print(p)
