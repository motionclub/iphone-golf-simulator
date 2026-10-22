"""Plate | PASS | FORM close-ups of the feet at identical framing (orthographic cameras calibrated to the plates).  PYTHONPATH must include work/male-micro1i/pylib."""
import sys, json, math, subprocess, os
sys.path.insert(0, '.')
import numpy as np
from PIL import Image, ImageDraw
from edges_ref import cam, h_sign
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
W_ = R + '/work/male-legs-feet-form2'
BL = '/Applications/Blender.app/Contents/MacOS/Blender'
bald = Image.open(R + '/ArtDir/hero/base_lock/male_body_bald.jpg').convert('RGB')
sheet = Image.open(R + '/ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
Q3 = json.load(open(W_ + '/data/plates/q3cams.json'))
pass_blend = sys.argv[1]; form_blend = sys.argv[2]; out_png = sys.argv[3]
RW = 1000
# name, az, target (x,y,z), width W (m), height H (m), plate image, mapper
VIEWS = [
    ('front, both feet', 0, (0.0, -0.10, 0.095), 0.56, 0.19, 'bald_front'),
    ('back, both feet', 180, (0.0, 0.0, 0.095), 0.56, 0.19, 'bald_back'),
    ('left side, near foot', 90, (0.0, -0.075, 0.095), 0.40, 0.19, 'left'),
    ('right side, near foot', -90, (0.0, -0.075, 0.095), 0.40, 0.19, 'right'),
    ('3/4 front, feet (q3FR)', 37, (0.0, -0.10, 0.095), 0.50, 0.19, 'q3FR'),
    ('3/4 front, feet (q3FL)', -9, (0.0, -0.10, 0.095), 0.56, 0.19, 'q3FL'),
]
def plate_crop(key, az, tgt, Wm, Hm):
    if key in ('bald_front', 'bald_back'):
        img = bald; mpp, sole, cx = cam(key); u = tgt[0] * h_sign(key)
        px0 = cx + (u * h_sign(key) * 0 + h_sign(key) * tgt[0]) / mpp
        # px = cx + h_sign * x / mpp
        pxc = cx + h_sign(key) * tgt[0] / mpp
    elif key in ('left', 'right'):
        img = sheet; mpp, sole, cx = cam(key); pxc = cx + h_sign(key) * tgt[1] / mpp
    else:
        img = sheet; c = Q3[key]; mpp, sole, ox = c['mpp'], c['sole'], c['ox']; a = math.radians(c['az'])
        u = tgt[0] * math.cos(a) + tgt[1] * math.sin(a); pxc = ox + u / mpp
    pyc = sole - tgt[2] / mpp
    w = Wm / mpp; h = Hm / mpp
    box = (int(round(pxc - w / 2)), int(round(pyc - h / 2)), int(round(pxc + w / 2)), int(round(pyc + h / 2)))
    return img.crop(box)
rows = []
os.makedirs(W_ + '/proof/cu', exist_ok=True)
for i, (title, az, tgt, Wm, Hm, key) in enumerate(VIEWS):
    rh = int(RW * Hm / Wm)
    spec = f'v{i}:{az}:0:{tgt[0]}:{tgt[1]}:{tgt[2]}:{Wm}:r{RW}x{rh}'
    ims = []
    for tag, blend in (('pass', pass_blend), ('form', form_blend)):
        d = f'{W_}/proof/cu/{tag}'; os.makedirs(d, exist_ok=True)
        subprocess.run([BL, '-b', '--factory-startup', '--python', W_ + '/closeup.py', '--', blend, d, spec], capture_output=True)
        ims.append(Image.open(f'{d}/v{i}.png').convert('RGB'))
    pc = plate_crop(key, az, tgt, Wm, Hm).resize((RW, rh), Image.LANCZOS)
    row = Image.new('RGB', (3 * RW + 8, rh + 20), (20, 20, 24))
    for j, (im, lab) in enumerate(((pc, f'PLATE  {title}'), (ims[0], 'PASS (current ArtDir)'), (ims[1], 'FORM2'))):
        row.paste(im, (j * (RW + 4), 20)); ImageDraw.Draw(row).text((j * (RW + 4) + 6, 4), lab, fill=(255, 255, 0))
    rows.append(row)
S = Image.new('RGB', (rows[0].width, sum(r.height for r in rows) + 6 * len(rows)), (10, 10, 12))
y = 0
for r in rows: S.paste(r, (0, y)); y += r.height + 6
S = S.resize((S.width * 2 // 3, S.height * 2 // 3), Image.LANCZOS)
S.save(out_png); print(out_png, S.size)
