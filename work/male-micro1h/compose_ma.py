"""Overlay of the face_lock multiangle head crops 09-16 (and body_bald crops 07/08): plate | mesh (head-only Eevee) | 50% overlay.
Per crop: best yaw among candidates + scale/translation from the DOME contour (top boundary of the bald skin mask).
python3 compose_ma.py <ma_render_dir> <out.png> [title]"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
FL = R / 'ArtDir/hero/base_lock/face_lock'
rdir = Path(sys.argv[1]); out = Path(sys.argv[2]); title = sys.argv[3] if len(sys.argv) > 3 else 'Micro1h'
CROPS = [('07_body_front_head.png', [0]), ('08_body_back_head.png', [180]), ('09_ma_front.png', [0]), ('10_ma_back.png', [180]), ('11_ma_left_profile.png', [90]),
         ('12_ma_right_profile.png', [-90]), ('13_ma_threequarter_front_left.png', [30, 35, 40, -30, -35, -40]), ('14_ma_threequarter_front_right.png', [-30, -35, -40, 30, 35, 40]),
         ('15_ma_threequarter_back_left.png', [145, -145]), ('16_ma_threequarter_back_right.png', [-145, 145])]
f = lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', s)


def side_extents(mask):
    """per row: outermost left/right skin pixel (the head is bald, so dark brows/eyes inside the row do not matter); nan if < 6 skin pixels"""
    h, w = mask.shape
    L = np.full(h, np.nan); Rr = np.full(h, np.nan)
    for y in range(h):
        idx = np.where(mask[y])[0]
        if len(idx) >= 6: L[y] = idx[0]; Rr[y] = idx[-1]
    return L, Rr


def plate_mask(im):
    a = np.asarray(im.convert('RGB')).astype(float)
    m = ((a[..., 0] - a[..., 2]) > 25) & (a[..., 0] > 105)
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5))) > 127
    return m


def fit_sides(pL, pR, mL, mR):
    """fit scale s, shifts dx, dy: plate(s*r+dy) = s*mesh(r)+dx on the dome+ear rows of the mesh render"""
    rows_m = np.where(~np.isnan(mL))[0]
    top = rows_m.min(); sel = np.arange(top + 4, top + 4 + 290, 3)                 # ~145 mm below the top (dome + ears)
    sel = sel[~np.isnan(mL[sel])]
    best = (1e18, None); H = len(pL)
    for s in np.arange(0.12, 1.3, 0.01):
        for dy in np.arange(-top * s - 40, H - top * s + 40, 2.0):
            yp = np.round(s * sel + dy).astype(int)
            ok = (yp >= 0) & (yp < H)
            if ok.sum() < 0.55 * len(sel): continue
            lp = pL[yp[ok]]; rp = pR[yp[ok]]
            g = ~np.isnan(lp) & ~np.isnan(rp)
            if g.sum() < 0.55 * len(sel): continue
            lm = s * mL[sel[ok]][g]; rm = s * mR[sel[ok]][g]
            dx = np.mean((lp[g] - lm + rp[g] - rm) / 2)
            err = np.mean(((lp[g] - lm - dx) ** 2 + (rp[g] - rm - dx) ** 2) / 2) + 60.0 * (1 - g.sum() / len(sel))
            if err < best[0]: best = (err, (s, dx, dy))
    return best


rows = []; report = []
for fn, azs in CROPS:
    pl = Image.open(FL / fn).convert('RGB')
    pL, pR = side_extents(plate_mask(pl))
    cand = None
    for az in azs:
        m = Image.open(rdir / f'az{az}.png').convert('RGBA')
        al = np.asarray(m)[..., 3] > 127
        mL, mR = side_extents(al)
        if np.isnan(mL).all(): continue
        err, par = fit_sides(pL, pR, mL, mR)
        if par is None: continue
        if cand is None or err < cand[0]: cand = (err, az, par, m)
    err, az, (s, dx, dy), m = cand
    mm = m.resize((int(m.width * s), int(m.height * s)), Image.LANCZOS)
    canvas = Image.new('RGBA', pl.size, (0, 0, 0, 0)); canvas.paste(mm, (int(round(dx)), int(round(dy))), mm)
    bg = Image.new('RGBA', pl.size, (56, 56, 60, 255)); meshv = Image.alpha_composite(bg, canvas).convert('RGB')
    al = canvas.split()[3].point(lambda v: 255 if v > 127 else 0)
    edge = ImageChops.subtract(al.filter(ImageFilter.MaxFilter(3)), al.filter(ImageFilter.MinFilter(3)))
    ov = Image.composite(Image.blend(pl, meshv, 0.5), pl, al); ov.paste((255, 40, 40), mask=edge)
    W = pl.width; Hh = pl.height
    row = Image.new('RGB', (W * 3 + 20, Hh), (0, 0, 0))
    for i, t in enumerate((pl, meshv, ov)): row.paste(t, (i * (W + 10), 0))
    d = ImageDraw.Draw(row); d.rectangle((0, 0, 300, 28), fill=(14, 14, 18)); d.text((8, 4), f'{fn[:2]} {fn[3:-4]}  yaw {az:+d}°', font=f(18), fill=(240, 240, 240))
    rows.append(row); report.append(dict(crop=fn, yaw=az, scale=round(float(s), 3), dx=int(dx), dy=round(float(dy), 1), contour_rms_px=round(float(np.sqrt(err)), 2)))
Wd = max(r.width for r in rows); Ht = sum(r.height for r in rows) + 60
S = Image.new('RGB', (Wd, Ht), (30, 31, 35)); d = ImageDraw.Draw(S)
d.text((16, 14), f'{title} · multiangle + body crops · plate | mesh (Eevee, head-only) | 50% overlay + red edge (dome-contour fit per crop)', font=f(28), fill=(240, 240, 240))
y = 60
for r in rows: S.paste(r, (0, y)); y += r.height
S = S.resize((int(S.width * 0.6), int(S.height * 0.6)), Image.LANCZOS); S.save(out); print(out, S.size)
json.dump(report, open(str(out)[:-4] + '.json', 'w'), indent=1); print(json.dumps(report))
