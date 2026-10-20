"""big5.py: large single-candidate renders.  python3 tools/big5.py out.png part tag=coords.npy [--views front,y25,y-25,side] [--looks soft,clay] [--px 640]
cols = looks, rows = views; no plate (use the plate panel from tri5).  part = chest | pelvis"""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
from rr import BL, START, HERE
from viz3 import roi_shot
from tri5 import LOOKS

def shots(part, px, views):
    if part == 'chest':
        zc, half = 1.20, 0.20
        allv = {'front': dict(name='front', yaw=0, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
                'y25': dict(name='y25', yaw=-20, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
                'y-25': dict(name='y-25', yaw=20, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
                'side': dict(name='side', yaw=-90, xc=0.0, zc=zc, w=2 * half, res=[px, px])}
    else:
        zc, half = 0.84, 0.24
        allv = {'back': dict(name='back', yaw=180, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
                'y155': dict(name='y155', yaw=-150, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
                'y-155': dict(name='y-155', yaw=150, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
                'side': dict(name='side', yaw=-90, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
                'y-120': dict(name='y-120', yaw=-120, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
                'y120': dict(name='y120', yaw=120, xc=0.0, zc=zc, w=2 * half, res=[px, px])}
    return [allv[v] for v in views]

def main(out, part, tag, path, views, looks, px):
    sh = shots(part, px, views)
    for lk in looks:
        spec = {"coords": path if path.startswith('/') else HERE + '/' + path, "out": f"{HERE}/scratch/r/big_{part}_{tag}_{lk}", "shots": sh, "look": LOOKS[lk]}
        r = subprocess.run([BL, '-b', START, '--python', HERE + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
        assert 'RENDER_OK' in r.stdout, r.stdout[-800:] + r.stderr[-800:]
    W = Image.new('RGB', (px * len(looks), px * len(views)), (225, 225, 228))
    for i, v in enumerate(views):
        for j, lk in enumerate(looks):
            m = Image.open(f"{HERE}/scratch/r/big_{part}_{tag}_{lk}_{v}.png").convert('RGBA')
            bg = Image.new('RGBA', m.size, (225, 225, 228, 255)); bg.alpha_composite(m)
            im = bg.convert('RGB'); ImageDraw.Draw(im).text((6, 6), f'{tag} {lk} {v}', fill=(255, 0, 0))
            W.paste(im, (j * px, i * px))
    W.save(out); print(out, W.size)

if __name__ == '__main__':
    a = sys.argv[1:]
    out, part = a[0], a[1]
    views = ['front', 'y25'] if part == 'chest' else ['back', 'y155']
    looks = ['soft', 'clay']; px = 640
    rest = []
    i = 2
    while i < len(a):
        if a[i] == '--views': views = a[i + 1].split(','); i += 2
        elif a[i] == '--looks': looks = a[i + 1].split(','); i += 2
        elif a[i] == '--px': px = int(a[i + 1]); i += 2
        else: rest.append(a[i]); i += 1
    tag, path = rest[0].split('=', 1)
    main(out, part, tag, path, views, looks, px)
