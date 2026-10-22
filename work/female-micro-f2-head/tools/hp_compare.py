"""high-pass shading comparison, plate vs render (lower face). python3 hp_compare.py <render_dir> <tag> <out.png>"""
import sys
import numpy as np
from PIL import Image, ImageFilter
ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
rd, tag, out = sys.argv[1], sys.argv[2], sys.argv[3]
UP = 3
src = Image.open(ROOT + 'ArtDir/hero/base_lock/female_head_detail.jpg').convert('RGB')
PAN = {'front': (85, 55, 430, 342), 'left': (440, 55, 800, 342), 'right': (830, 55, 1195, 342), 'q3L': (85, 385, 430, 656), 'q3R': (440, 385, 800, 656)}
WIN = {'front': (0.12, 0.38, 0.88, 0.80), 'left': (0.05, 0.30, 0.80, 0.80), 'q3L': (0.10, 0.38, 0.90, 0.88), 'q3R': (0.05, 0.38, 0.90, 0.88)}
def hp(img, s=14, g=5):
    L = img.convert('L'); a = np.asarray(L).astype(float); b = np.asarray(L.filter(ImageFilter.GaussianBlur(s))).astype(float)
    return Image.fromarray(np.clip(128 + (a - b) * g, 0, 255).astype(np.uint8)).convert('RGB')
rows = []
for v in ('front', 'left', 'q3L', 'q3R'):
    box = PAN[v]; pl = src.crop(box); w, h = pl.size; big = (w * UP, h * UP)
    plb = pl.resize(big, Image.LANCZOS)
    r = Image.open(f'{rd}/{tag}_{v}.png').convert('RGBA').resize(big, Image.LANCZOS)
    af = (np.asarray(r)[..., 3] / 255.0)[..., None]; rgb = np.asarray(r.convert('RGB')).astype(float)
    rr = Image.fromarray((rgb * af + np.array([128., 128., 128.]) * (1 - af)).astype(np.uint8))
    f0, f1, f2, f3 = WIN[v]; c = (int(f0 * big[0]), int(f1 * big[1]), int(f2 * big[0]), int(f3 * big[1]))
    row = np.concatenate([np.asarray(plb.crop(c)), np.asarray(hp(plb).crop(c)), np.asarray(rr.crop(c)), np.asarray(hp(rr).crop(c))], axis=1)
    rows.append(row)
W_ = max(r.shape[1] for r in rows)
sheet = Image.new('RGB', (W_, sum(r.shape[0] for r in rows)), (20, 20, 22)); y = 0
for r in rows: sheet.paste(Image.fromarray(r), (0, y)); y += r.shape[0]
sheet.save(out); print(sheet.size)
