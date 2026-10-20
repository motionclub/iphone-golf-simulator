"""zoomfold5.py: close-up renders of the fold region (back) for several candidates, clay + mirror-stripe.  python3 tools/zoomfold5.py out.png tag=coords.npy ..."""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
from rr import BL, START, HERE
from tri5 import LOOKS

def main(out, items, looks=('clay', 'stripe'), px=640):
    shots = [dict(name='back', yaw=180, xc=0.0, zc=0.81, w=0.20, res=[px, px]), dict(name='y150', yaw=-150, xc=0.0, zc=0.81, w=0.20, res=[px, px])]
    W = Image.new('RGB', (px * len(items) * len(looks), px * len(shots)), (225, 225, 228))
    for ti, (tag, path) in enumerate(items):
        for li, lk in enumerate(looks):
            spec = {"coords": path if path.startswith('/') else HERE + '/' + path, "out": f"{HERE}/scratch/r/zf_{tag}_{lk}", "shots": shots, "look": LOOKS[lk]}
            r = subprocess.run([BL, '-b', START, '--python', HERE + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
            assert 'RENDER_OK' in r.stdout, r.stdout[-500:]
            for si, s in enumerate(shots):
                m = Image.open(f"{HERE}/scratch/r/zf_{tag}_{lk}_{s['name']}.png").convert('RGBA')
                bg = Image.new('RGBA', m.size, (225, 225, 228, 255)); bg.alpha_composite(m)
                im = bg.convert('RGB'); ImageDraw.Draw(im).text((6, 6), f'{tag} {lk} {s["name"]}', fill=(255, 0, 0))
                W.paste(im, ((ti * len(looks) + li) * px, si * px))
    W.save(out); print(out, W.size)

if __name__ == '__main__':
    main(sys.argv[1], [a.split('=', 1) for a in sys.argv[2:]])
