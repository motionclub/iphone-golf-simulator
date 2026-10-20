"""zoomed plate vs mesh silhouette comparison of the chin/jaw: python3 chin_zoom.py <render_dir> <tag> <out.png>"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw
ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
rd, tag, out = sys.argv[1], sys.argv[2], sys.argv[3]
UP = 3
src = Image.open(ROOT + 'ArtDir/hero/base_lock/female_head_detail.jpg').convert('RGB')
PAN = {'front': (85, 55, 430, 342), 'left': (440, 55, 800, 342), 'right': (830, 55, 1195, 342), 'q3L': (85, 385, 430, 656), 'q3R': (440, 385, 800, 656)}
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
# chin windows (fractions of the panel)
WIN = {'front': (0.18, 0.55, 0.82, 0.86), 'left': (0.10, 0.50, 0.75, 0.86), 'right': (0.25, 0.50, 0.90, 0.86), 'q3L': (0.15, 0.55, 0.85, 0.92), 'q3R': (0.10, 0.55, 0.85, 0.92)}
rows = []
for v in ('front', 'left', 'right', 'q3L', 'q3R'):
    box = PAN[v]; pl = src.crop(box); w, h = pl.size
    r = Image.open(f'{rd}/{tag}_{v}.png').convert('RGBA')
    big = (w * UP, h * UP)
    plb = pl.resize(big, Image.LANCZOS); rb = r.resize(big, Image.LANCZOS)
    al = np.asarray(rb)[..., 3] > 127
    pa = np.asarray(plb).astype(float); pm = fgm(pa)
    rgb = np.asarray(rb.convert('RGB')).astype(float); af = (np.asarray(rb)[..., 3] / 255.0)[..., None]
    rr = (rgb * af + np.array([40., 40., 42.]) * (1 - af)).astype(np.uint8)
    ov = (0.55 * pa + 0.45 * rr.astype(float)).astype(np.uint8)
    ov[dil(edge(al), 1)] = (255, 40, 40); ov[dil(edge(pm), 1)] = (30, 220, 60)
    f0, f1, f2, f3 = WIN[v]; c = (int(f0 * big[0]), int(f1 * big[1]), int(f2 * big[0]), int(f3 * big[1]))
    row = np.concatenate([np.asarray(plb.crop(c)), rr[c[1]:c[3], c[0]:c[2]], ov[c[1]:c[3], c[0]:c[2]]], axis=1)
    rows.append(row)
W_ = max(r.shape[1] for r in rows)
sheet = Image.new('RGB', (W_, sum(r.shape[0] for r in rows)), (20, 20, 22)); y = 0
for r in rows: sheet.paste(Image.fromarray(r), (0, y)); y += r.shape[0]
sheet.save(out); print(sheet.size)
