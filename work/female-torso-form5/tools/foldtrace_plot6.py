"""foldtrace_plot6.py: proof image of the traced under-butt fold line.  python3 tools/foldtrace_plot6.py proof/06z_underbutt_zoom_soft_clay.png proof/06t_fold_line_trace.png
3 panels (plate | FORM4 soft | FORM5 soft), each shown high-pass enhanced (x4) with the traced fold-line centres (dots) of the plate (red), FORM4 (blue), FORM5 (green); bottom strip = the rows table."""
import sys, os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bandtrace_panel6 as bp

src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('L'); W = im.size[0] // 5; H = 272      # the back-view row of the 06z sheet is ~277 px tall (rows have different heights): crop above the next row
res, sm = bp.analyse(src)
names = [('plate', 0, 'PLATE'), ('F4soft', 1, 'FORM4 soft'), ('F5soft', 3, 'FORM5 soft')]
SC = 2
out = Image.new('RGB', (W * SC * 3, H * SC + 70), (20, 20, 24))
d = ImageDraw.Draw(out)
cols = {'plate': (255, 60, 60), 'F4soft': (80, 140, 255), 'F5soft': (60, 230, 90)}
for k, (n, i, lab) in enumerate(names):
    p = im.crop((i * W, 0, (i + 1) * W, H))
    a = np.asarray(p, dtype=np.float32); b = np.asarray(p.filter(ImageFilter.GaussianBlur(10)), dtype=np.float32)
    e = Image.fromarray(np.clip(128 + (a - b) * 4.0, 0, 255).astype(np.uint8)).convert('RGB').resize((W * SC, H * SC), Image.LANCZOS)
    out.paste(e, (k * W * SC, 0))
    dd = ImageDraw.Draw(out)
    for key in ('plate', n):
        c = cols[key]
        pts = [((k * W + bp.CX + dx) * SC, res[key][dx] * SC) for dx in bp.DXS]
        for (x, y) in pts: dd.ellipse((x - 4, y - 4, x + 4, y + 4), fill=c)
        left = [pt for pt, dx in zip(pts, bp.DXS) if dx < 0]; right = [pt for pt, dx in zip(pts, bp.DXS) if dx > 0]
        if len(left) > 1: dd.line(left, fill=c, width=2)
        if len(right) > 1: dd.line(right, fill=c, width=2)
    dd.text((k * W * SC + 8, 6), lab, fill=(255, 255, 255))
    if n != 'plate':
        dd.text((k * W * SC + 8, 22), f"rms err vs plate {sm[n]['rms_err_px']:.1f} px, lateral rise {sm[n]['rise_px']:+.1f} px (plate {sm['plate']['rise_px']:+.1f})", fill=(255, 255, 255))
d.text((8, H * SC + 8), 'traced fold line (centroid of the high-pass luminance deficit, sigma 10 px): plate = red, FORM4 = blue, FORM5 = green; panel scale ~0.8 px/mm. A smile = line rising toward the sides (|dx| 105) from the cleft side (|dx| 45).', fill=(220, 220, 220))
rows = ' '.join(f'{dx:+d}' for dx in bp.DXS)
d.text((8, H * SC + 26), 'dx (px):      ' + rows, fill=(200, 200, 200))
for j, (n, lab) in enumerate((('plate', 'plate rows: '), ('F4soft', 'FORM4 rows: '), ('F5soft', 'FORM5 rows: '))):
    d.text((8, H * SC + 40 + j * 0), '', fill=(0, 0, 0))
d.text((8, H * SC + 40), 'rows  plate: ' + ' '.join(f"{res['plate'][dx]:.0f}" for dx in bp.DXS) + '   F4: ' + ' '.join(f"{res['F4soft'][dx]:.0f}" for dx in bp.DXS) + '   F5: ' + ' '.join(f"{res['F5soft'][dx]:.0f}" for dx in bp.DXS), fill=(200, 200, 200))
out.save(dst); print('saved', dst, out.size)
