"""tiny PIL 2-D plotting for mm-scale curves. curves: list of (Nx2 array in mm (u,v), color, width, label); v up."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
def plot2d(curves, win, S, path, grid=5.0, title='', marks=None, label_every=10):
    u0, u1, v0, v1 = win
    Wd, Ht = int((u1 - u0) * S), int((v1 - v0) * S)
    im = Image.new('RGB', (Wd, Ht), (22, 22, 24)); d = ImageDraw.Draw(im)
    try: font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 14)
    except Exception: font = ImageFont.load_default()
    X = lambda u: (u - u0) * S
    Y = lambda v: (v1 - v) * S
    g = np.arange(np.ceil(u0 / grid) * grid, u1 + 1e-9, grid)
    for k, gu in enumerate(g):
        major = (round(gu / grid) % int(label_every / grid) == 0)
        d.line([(X(gu), 0), (X(gu), Ht)], fill=(70, 70, 78) if major else (40, 40, 44))
        if major: d.text((X(gu) + 2, Ht - 16), f'{gu:.0f}', fill=(170, 170, 180), font=font)
    g = np.arange(np.ceil(v0 / grid) * grid, v1 + 1e-9, grid)
    for k, gv in enumerate(g):
        major = (round(gv / grid) % int(label_every / grid) == 0)
        d.line([(0, Y(gv)), (Wd, Y(gv))], fill=(70, 70, 78) if major else (40, 40, 44))
        if major: d.text((3, Y(gv) - 16), f'{gv:.0f}', fill=(170, 170, 180), font=font)
    for (c, col, w, lab) in curves:
        c = np.asarray(c)
        if c.ndim == 2 and len(c) > 1:
            pts = [(X(a), Y(b)) for a, b in c]
            d.line(pts, fill=col, width=w)
    ty = 6
    for (c, col, w, lab) in curves:
        d.rectangle([8, ty + 3, 22, ty + 11], fill=col); d.text((28, ty), lab, fill=(230, 230, 235), font=font); ty += 18
    if marks:
        for (u, v, col) in marks: d.ellipse([X(u) - 3, Y(v) - 3, X(u) + 3, Y(v) + 3], outline=col)
    if title: d.text((Wd - 8 * len(title) - 10, 6), title, fill=(255, 255, 255), font=font)
    im.save(path); return im
