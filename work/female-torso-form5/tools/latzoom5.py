"""latzoom5.py: stripe + clay close-ups of the lateral thigh-top / hip region (back view): python3 tools/latzoom5.py out.png xc zc w tag=coords.npy ..."""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
from rr import BL, START, HERE
from tri5 import LOOKS

def main(out, xc, zc, w, items, px=520, yaw=180):
    shots = [dict(name='back', yaw=yaw, xc=xc, zc=zc, w=w, res=[px, px])]
    looks = ('clay', 'stripe')
    W = Image.new('RGB', (px * len(items) * len(looks), px), (225, 225, 228))
    for ti, (tag, path) in enumerate(items):
        for li, lk in enumerate(looks):
            spec = {"coords": path if path.startswith('/') else HERE + '/' + path, "out": f"{HERE}/scratch/r/lz_{tag}_{lk}", "shots": shots, "look": LOOKS[lk]}
            r = subprocess.run([BL, '-b', START, '--python', HERE + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
            assert 'RENDER_OK' in r.stdout, r.stdout[-500:]
            m = Image.open(f"{HERE}/scratch/r/lz_{tag}_{lk}_back.png").convert('RGBA')
            bg = Image.new('RGBA', m.size, (225, 225, 228, 255)); bg.alpha_composite(m)
            im = bg.convert('RGB'); ImageDraw.Draw(im).text((6, 6), f'{tag} {lk}', fill=(255, 0, 0))
            W.paste(im, ((ti * len(looks) + li) * px, 0))
    W.save(out); print(out, W.size)

if __name__ == '__main__':
    out, xc, zc, w = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    yaw = 180.0
    args = sys.argv[5:]
    if args and args[0].startswith('--yaw='):
        yaw = float(args[0].split('=')[1]); args = args[1:]
    main(out, xc, zc, w, [a.split('=', 1) for a in args], yaw=yaw)
