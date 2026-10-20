"""lower-face plate vs mesh overlay (python3 + PIL). usage: lowover.py <render_dir> <tag> <out.png>   (renders from ul.py: front,left,right,q3L,q3R)"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
crops = json.load(open(ROOT + 'ArtDir/hero/base_lock/face_lock_f/crop_boxes.json'))
rd, tag, out = sys.argv[1], sys.argv[2], sys.argv[3]
UP = 3
def fgm(a):
    sat = a.max(axis=2) - a.min(axis=2); V = a.mean(axis=2)
    return ~((sat < 16) & (V > 150))
def edge(m):
    m = m.astype(np.uint8); e = np.zeros_like(m)
    e[1:-1, 1:-1] = ((m[1:-1, 1:-1] != m[:-2, 1:-1]) | (m[1:-1, 1:-1] != m[2:, 1:-1]) | (m[1:-1, 1:-1] != m[1:-1, :-2]) | (m[1:-1, 1:-1] != m[1:-1, 2:]))
    return e.astype(bool)
def dil(m, k=1):
    o = m.copy()
    for _ in range(k):
        p = o.copy(); p[1:] |= o[:-1]; p[:-1] |= o[1:]; p[:, 1:] |= o[:, :-1]; p[:, :-1] |= o[:, 1:]; o = p
    return o
src = Image.open(ROOT + 'ArtDir/hero/base_lock/female_head_detail.jpg').convert('RGB')
PAN = {'front': (85, 55, 430, 342), 'left': (440, 55, 800, 342), 'right': (830, 55, 1195, 342), 'q3L': (85, 385, 430, 656), 'q3R': (440, 385, 800, 656)}
tiles = []
for v, row0 in (('front', 150), ('left', 150), ('right', 150), ('q3L', 150), ('q3R', 150)):
    box = PAN[v]; pl = src.crop(box); w, h = pl.size
    pl_big = pl.resize((w * UP, h * UP), Image.LANCZOS)
    r = Image.open(f'{rd}/{tag}_{v}.png').convert('RGBA').resize((w * UP, h * UP), Image.LANCZOS)
    al = np.asarray(r)[..., 3] > 127
    rgb = np.asarray(r.convert('RGB')).astype(float); al_f = (np.asarray(r)[..., 3] / 255.0)[..., None]
    rr = (rgb * al_f + np.array([40., 40., 42.]) * (1 - al_f)).astype(np.uint8)
    pa = np.asarray(pl_big).astype(float); pm = fgm(pa)
    # row range: from the nose base down to just below the chin
    y0 = row0 * UP - box[1] * 0 if False else 0
    ov = (0.5 * pa + 0.5 * rr.astype(float)).astype(np.uint8)
    cut = 215 * UP - 0     # head rows only (plate rows relative to panel: ~ chin at ~ row 250-55=195..)
    ov[dil(edge(al), 1)] = (255, 40, 40); ov[dil(edge(pm), 1)] = (30, 220, 60)
    tiles.append((v, Image.fromarray(ov), pl_big, Image.fromarray(rr)))
# crop the lower face region of every tile: plate rows 130..250 within the panel (panel starts at plate row 55 for head-detail top row; use fractions)
rows = []
for v, ov, pl, rr in tiles:
    h = ov.height; y0 = int(h * 0.50); y1 = int(h * 0.90)
    rows.append(np.concatenate([np.asarray(pl.crop((0, y0, pl.width, y1))), np.asarray(rr.crop((0, y0, pl.width, y1))), np.asarray(ov.crop((0, y0, pl.width, y1)))], axis=1))
W = max(r.shape[1] for r in rows)
sheet = Image.new('RGB', (W, sum(r.shape[0] for r in rows)), (20, 20, 22)); y = 0
for r in rows: sheet.paste(Image.fromarray(r), (0, y)); y += r.shape[0]
sheet.save(out); print(sheet.size)
