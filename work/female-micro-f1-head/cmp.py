"""compose plate | render | overlay (+ silhouette edges).  python3.13 cmp.py <rdir> <tag> <views comma> <out.png> [title]"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import fl
rdir, tag, views, out = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4]
title = sys.argv[5] if len(sys.argv) > 5 else tag
UP = 3
plate = Image.open(fl.PLATES / 'female_head_detail.jpg').convert('RGB')
BG = np.array([0.84, 0.84, 0.85]) ** (1 / 2.2) * 255
def edge(mask):
    m = mask.astype(np.uint8)
    e = np.zeros_like(m)
    e[1:-1, 1:-1] = ((m[1:-1, 1:-1] != m[:-2, 1:-1]) | (m[1:-1, 1:-1] != m[2:, 1:-1]) | (m[1:-1, 1:-1] != m[1:-1, :-2]) | (m[1:-1, 1:-1] != m[1:-1, 2:]))
    return e.astype(bool)
def dil(m, k=1):
    o = m.copy()
    for _ in range(k):
        p = o.copy(); p[1:] |= o[:-1]; p[:-1] |= o[1:]; p[:, 1:] |= o[:, :-1]; p[:, :-1] |= o[:, 1:]; o = p
    return o
try: f = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 22)
except Exception: f = ImageFont.load_default()
rows = []
for v in views:
    x0, y0, x1, y1 = fl.PANELS[v]['box']
    pl = plate.crop((x0, y0, x1, y1)).resize(((x1 - x0) * UP, (y1 - y0) * UP), Image.LANCZOS)
    rimg = Image.open(f'{rdir}/{tag}_{v}.png')
    if rimg.mode == 'RGBA':
        rimg = rimg.resize(pl.size, Image.LANCZOS); al = np.asarray(rimg)[..., 3].astype(float) / 255.0
        bgc = np.array([40.0, 40.0, 42.0]); rgb = np.asarray(rimg.convert('RGB')).astype(float)
        ra = rgb * al[..., None] + bgc * (1 - al[..., None]); r = Image.fromarray(ra.astype(np.uint8)); rm = al > 0.5
    else:
        r = rimg.convert('RGB').resize(pl.size, Image.LANCZOS); ra = np.asarray(r).astype(float)
        rm = (np.abs(ra - BG).max(axis=2) > 12)
    pa = np.asarray(pl).astype(float)
    sat = pa.max(axis=2) - pa.min(axis=2); V = pa.mean(axis=2)
    pm = ~((sat < 16) & (V > 150))
    ov = (0.5 * pa + 0.5 * ra).astype(np.uint8)
    ovi = Image.fromarray(ov)
    arr = np.asarray(ovi).copy()
    arr[dil(edge(rm), 1)] = (255, 40, 40)     # render silhouette red
    arr[dil(edge(pm), 1)] = (30, 220, 60)      # plate silhouette green
    row = Image.new('RGB', (pl.width * 3, pl.height), (20, 20, 22))
    row.paste(pl, (0, 0)); row.paste(r, (pl.width, 0)); row.paste(Image.fromarray(arr), (pl.width * 2, 0))
    d = ImageDraw.Draw(row); d.rectangle([0, 0, 150, 30], fill=(0, 0, 0)); d.text((6, 3), v, fill=(255, 255, 255), font=f)
    rows.append(row)
W = max(r.width for r in rows); H = sum(r.height for r in rows) + 40
S = Image.new('RGB', (W, H), (20, 20, 22)); ImageDraw.Draw(S).text((8, 8), title, fill=(255, 255, 255), font=f)
y = 40
for r in rows: S.paste(r, (0, y)); y += r.height
S.save(out); print('saved', out, S.size)
