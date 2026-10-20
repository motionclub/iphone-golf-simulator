"""Normalized band-pass difference map (render - plate) in the back view (main plate), plus the two images.
python3 diffmap.py out.png tag [s1 s2]  -> [plate bp | render bp | diff] (red: render brighter than plate, blue: darker) + metrics inside the glute box"""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
import crop_cmp as CC
from metric import dog
W = CC.W; R = CC.R
c = CC.CAM['bald_back']; mpp = c['metres_per_pixel']; cx = c['centre_x']; sy = c['sole_y']
PL = np.asarray(Image.open(R / 'ArtDir/hero/base_lock/male_body_bald.jpg').convert('L')).astype('float32')
out, tag = sys.argv[1], sys.argv[2]; s1, s2 = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (2.0, 10.0)
K = 4
rend = np.asarray(Image.open(W / f'r/{tag}_c/back@{K}.png').convert('L')).astype('float32')
rend1 = np.asarray(Image.fromarray(rend.astype(np.uint8)).resize((1280, 720), Image.BOX)).astype('float32')
A = dog(PL, s1, s2); B = dog(rend1, s1, s2)
z0, z1, xh = 0.72, 1.02, 0.20
x0, x1 = int(cx - xh / mpp), int(cx + xh / mpp); y0, y1 = int(sy - z1 / mpp), int(sy - z0 / mpp)
a = A[y0:y1, x0:x1]; b = B[y0:y1, x0:x1]
def nz(v): return v / (v.std() + 1e-6)
an = nz(a); bn = nz(b); diff = bn - an
def col(v, lim=2.5):
    t = np.clip(v / lim, -1, 1); r = np.where(t > 0, 255 * t, 0); bl = np.where(t < 0, 255 * -t, 0); g = 255 * (1 - np.abs(t)) * 0.35
    return np.stack([r + 40, g + 40, bl + 40], -1).clip(0, 255).astype(np.uint8)
def up(img): return Image.fromarray(img).resize((img.shape[1] * 3, img.shape[0] * 3), Image.NEAREST)
panels = [up(col(an)), up(col(bn)), up(col(diff))]
Wd = sum(p.width for p in panels) + 40; Hd = panels[0].height + 30
S = Image.new('RGB', (Wd, Hd), (16, 16, 16)); d = ImageDraw.Draw(S); F = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 18); x = 10
for nm, p in zip(('PLATE bandpass', f'{tag} bandpass', 'render - plate (red: render brighter)'), panels):
    S.paste(p, (x, 24)); d.text((x + 4, 2), nm, fill=(255, 200, 80), font=F); x += p.width + 10
S.save(out); print(out, S.size, 'r=%.3f  sr=%.2f' % (np.corrcoef(a.ravel(), b.ravel())[0, 1], b.std() / a.std()))
