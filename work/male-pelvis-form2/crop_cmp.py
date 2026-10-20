"""Registered plate-vs-render comparison crops of the MAIN bald plate (back / front) at k x magnification.
python3 crop_cmp.py render <tag> <look>  -> r/<tag>_c/{back,front}@K.png (K=4)
python3 crop_cmp.py sheet out.png view zlo zhi xhalf tag... [--enh]   (plate | tags...) same px scale"""
import sys, os, json, subprocess
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form2'); R = W.parent.parent
CAM = {c['name']: c for c in json.load(open(R / 'work/male-silhouette/reference-cameras.json'))['views']}
K = 4
def render(tag, look='manneq', views='back@4,front@4'):
    src = f'data/V_{tag}.npy' if tag != 'start' else 'baseline/HeroBase_Male_Silhouette.blend'
    env = dict(os.environ, PYTHONPATH=str(R / 'work/male-micro1i/pylib'))
    r = subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', '--python', 'rig.py', '--', src, f'r/{tag}_c', views, look, '0.886,0.627,0.431'], cwd=W, env=env, capture_output=True, text=True)
    if 'Traceback' in r.stdout or 'Error' in r.stderr[-300:]: print(r.stdout[-1500:], r.stderr[-800:])
def font(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
def sheet(out, view, zlo, zhi, xhalf, tags, enh=False, labels=None):
    c = CAM['bald_' + view]; mpp = c['metres_per_pixel']; cx = c['centre_x']; sy = c['sole_y']
    x0, x1 = int(cx - xhalf / mpp), int(cx + xhalf / mpp); y0, y1 = int(sy - zhi / mpp), int(sy - zlo / mpp)
    plate = Image.open(R / 'ArtDir/hero/base_lock/male_body_bald.jpg').convert('RGB').crop((x0, y0, x1, y1))
    plate = plate.resize((plate.width * K, plate.height * K), Image.LANCZOS)
    ims = [plate]
    for t in tags:
        im = Image.open(W / f'r/{t}_c/{view}@{K}.png').convert('RGB').crop((x0 * K, y0 * K, x1 * K, y1 * K)); ims.append(im)
    if enh: ims = [ImageOps.autocontrast(i.convert('L'), cutoff=(1, 1)).convert('RGB') for i in ims]
    labs = labels or (['PLATE'] + tags)
    w, h = ims[0].size; S = Image.new('RGB', (w * len(ims) + 8 * (len(ims) + 1), h + 36), (16, 16, 16)); d = ImageDraw.Draw(S); F = font(20)
    for i, im in enumerate(ims):
        S.paste(im, (8 + i * (w + 8), 28)); d.text((12 + i * (w + 8), 4), labs[i], fill=(255, 200, 80), font=F)
    S.save(out); print(out, S.size)
if __name__ == '__main__':
    if sys.argv[1] == 'render':
        render(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'manneq')
    else:
        enh = '--enh' in sys.argv; a = [x for x in sys.argv[2:] if x != '--enh']
        sheet(a[0], a[1], float(a[2]), float(a[3]), float(a[4]), a[5:], enh=enh, labels=os.environ.get('LABELS', '').split(',') if os.environ.get('LABELS') else None)
