"""foldwide5.py: wide close-up of the underbutt fold (back view + 3/4) for several candidates, soft + clay.  python3 tools/foldwide5.py out.png tag=coords.npy ..."""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
from rr import BL, START, HERE
from tri5 import LOOKS

def main(out, items, px=900, looks=('soft', 'clay'), views=('back',)):
    shot = {'back': dict(name='back', yaw=180, xc=0.0, zc=0.81, w=0.36, res=[px, px // 2]),
            'y155': dict(name='y155', yaw=-150, xc=0.0, zc=0.82, w=0.36, res=[px, px // 2]),
            'side': dict(name='side', yaw=-90, xc=0.0, zc=0.80, w=0.36, res=[px, px // 2])}
    shots = [shot[v] for v in views]
    W = Image.new('RGB', (px * len(looks), (px // 2) * len(items) * len(shots)))
    r_ = 0
    for tag, path in items:
        for sh in shots:
            for col, lk in enumerate(looks):
                spec = {"coords": path if path.startswith('/') else HERE + '/' + path, "out": f"{HERE}/scratch/r/fw_{tag}_{lk}", "shots": [sh], "look": LOOKS[lk]}
                r = subprocess.run([BL, '-b', START, '--python', HERE + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
                assert 'RENDER_OK' in r.stdout, r.stdout[-400:]
                m = Image.open(f"{HERE}/scratch/r/fw_{tag}_{lk}_{sh['name']}.png").convert('RGBA'); bg = Image.new('RGBA', m.size, (225, 225, 228, 255)); bg.alpha_composite(m)
                im = bg.convert('RGB'); ImageDraw.Draw(im).text((6, 6), f'{tag} {lk} {sh["name"]}', fill=(255, 0, 0)); W.paste(im, (col * px, r_ * (px // 2)))
            r_ += 1
    W.save(out); print(out, W.size)

if __name__ == '__main__':
    a = sys.argv[1:]
    views = ('back',)
    if '--views' in a:
        i = a.index('--views'); views = tuple(a[i + 1].split(',')); del a[i:i + 2]
    main(a[0], [x.split('=', 1) for x in a[1:]], views=views)
