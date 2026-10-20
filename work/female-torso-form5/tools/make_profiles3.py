"""proof/08_relief_profiles.png : plate vs FORM2 vs FORM3 brightness profiles through the mounds / lobes / cleft
(plate-pixel grid, lighting fitted on unedited regions of the plate; each curve = grey level minus its own window mean).
python3 tools/make_profiles3.py [coords.npy]"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
import relief3 as RF
import relief3b as RB
from viz3 import font, banner

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CO3 = np.load(sys.argv[1] if len(sys.argv) > 1 else HERE + '/data/co_FORM3_final.npy')
CO2 = np.load(HERE + '/data/co_start_f2.npy')
COL = {'plate': (255, 255, 255), 'form2': (255, 140, 60), 'form3': (80, 220, 255)}


def draw_curves(d, ox, oy, W, H, curves, xlim, ylim, title, vertical=True, gain=2.0):
    """curves: {name: (coord, value)}; vertical=True -> y axis = z (up), x axis = brightness deviation"""
    d.rectangle([ox, oy, ox + W - 1, oy + H - 1], outline=(60, 60, 70))
    d.text((ox + 6, oy + 4), title, fill=(255, 255, 255), font=font(13, False))
    if vertical:
        z0, z1 = ylim
        for zz in np.arange(np.ceil(z0 * 50) / 50, z1, 0.04):
            yy = oy + H - 24 - (zz - z0) / (z1 - z0) * (H - 48)
            d.line([(ox, yy), (ox + W, yy)], fill=(42, 42, 52)); d.text((ox + 3, yy - 13), f'{zz:.2f}', fill=(120, 120, 130), font=font(11, False))
        d.line([(ox + W / 2, oy + 20), (ox + W / 2, oy + H)], fill=(55, 55, 65))
        for i, (nm, (z, v)) in enumerate(curves.items()):
            v = v - v.mean()
            pts = [(ox + W / 2 + vv * gain * 1.2, oy + H - 24 - (zz - z0) / (z1 - z0) * (H - 48)) for zz, vv in zip(z, v) if z0 <= zz <= z1]
            d.line(pts, fill=COL[nm], width=2); d.text((ox + W - 60, oy + 20 + 14 * i), nm, fill=COL[nm], font=font(12))
    else:
        x0, x1 = xlim
        for xm in np.arange(np.ceil(x0 * 25) / 25, x1, 0.04):
            u = ox + (xm - x0) / (x1 - x0) * W
            d.line([(u, oy + 20), (u, oy + H)], fill=(42, 42, 52)); d.text((u + 2, oy + H - 14), f'{xm*100:+.0f}', fill=(120, 120, 130), font=font(11, False))
        for i, (nm, (x, v)) in enumerate(curves.items()):
            v = v - v.mean()
            pts = [(ox + (xx - x0) / (x1 - x0) * W, oy + H / 2 + 12 - vv * gain * 1.1) for xx, vv in zip(x, v) if x0 <= xx <= x1]
            d.line(pts, fill=COL[nm], width=2); d.text((ox + W - 60, oy + 20 + 14 * i), nm, fill=COL[nm], font=font(12))


def main():
    imgs_f = {'plate': RF.PLATE, 'form2': RF.model_img(CO2), 'form3': RF.model_img(CO3)}
    imgs_b = {'plate': RB.PLATEB, 'form2': RB.model_img(CO2), 'form3': RB.model_img(CO3)}
    cw, ch = 300, 520
    xs_f = [-0.105, -0.09, -0.075, 0.075, 0.09, 0.105]
    xs_b = [-0.07, -0.045, 0.045, 0.07]
    zs_h = [0.85, 0.88, 0.91]
    ncol = max(len(xs_f), len(xs_b) + len(zs_h))
    Wd = Image.new('RGB', (cw * ncol, ch * 2 + 8), (20, 20, 24))
    d = ImageDraw.Draw(Wd)
    for k, x in enumerate(xs_f):
        cur = {}
        for nm, im in imgs_f.items():
            p, zs = RF._prof(im, x)
            cur[nm] = (zs, p)
        tl = '  '.join(f"{nm} dip/rise {RF._dr(im, x)[0]:.0f}/{RF._dr(im, x)[1]:.0f}" for nm, im in imgs_f.items() if nm != 'form2')
        draw_curves(d, k * cw, 0, cw, ch, cur, None, (1.10, 1.32), f'BUST x={x:+.3f}: {tl}', True, 2.5)
    for k, x in enumerate(xs_b):
        cur = {}
        for nm, im in imgs_b.items():
            p, zs = RB.vprof(im, x)
            cur[nm] = (zs, p)
        draw_curves(d, k * cw, ch + 8, cw, ch, cur, None, (0.76, 1.02), f'GLUTE x={x:+.3f} (vertical)', True, 2.5)
    for k, z in enumerate(zs_h):
        cur = {}
        for nm, im in imgs_b.items():
            p, xs = RB.hprof(im, z)
            cur[nm] = (xs, p)
        m = RB.measures(imgs_b['form3'])[f'h{z:.2f}']; pm = RB.PM[f'h{z:.2f}']
        draw_curves(d, (len(xs_b) + k) * cw, ch + 8, cw, ch, cur, (-0.15, 0.15), None, f'CLEFT z={z:.2f}: depth plate {pm:.0f} / form3 {m:.0f}', False, 2.2)
    s_f, _ = RF.score(CO3)
    s_f2, _ = RF.score(CO2)
    s_b, _ = RB.score(CO3)
    s_b2, _ = RB.score(CO2)
    banner(Wd, 'RELIEF PROFILES - plate vs FORM2 vs FORM3 (grey level minus window mean, plate-fitted light)',
           f'bust crescent/highlight |log ratio| FORM2 {s_f2:.2f} -> FORM3 {s_f:.2f} | glute crescents + cleft |log ratio| FORM2 {s_b2:.2f} -> FORM3 {s_b:.2f} (0 = same relief amplitude as the plate). The plate figure is lit/posed slightly asymmetrically, so left/right differ.').save(HERE + '/proof/08_relief_profiles.png')
    import json
    json.dump({'bust_relief_log_ratio': {'form2': s_f2, 'form3': s_f}, 'glute_relief_log_ratio': {'form2': s_b2, 'form3': s_b}}, open(HERE + '/export/form3_relief_metrics.json', 'w'), indent=1)
    print('08_relief_profiles.png written', s_f2, s_f, s_b2, s_b)


main()
