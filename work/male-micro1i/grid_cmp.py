"""Front-view feature comparison with an mm grid: plate | mesh render.  python3.13 grid_cmp.py <panels_dir> <out.png> z0 z1 x0 x1 [zoom]"""
import sys; sys.path.insert(0, '.')
from m1i_lib import *
pdir, out = sys.argv[1], sys.argv[2]
z0, z1, x0, x1 = (float(v) for v in sys.argv[3:7]); zoom = int(sys.argv[7]) if len(sys.argv) > 7 else 6
box = (5, 62, 433, 352)
m = Image.open(f'{pdir}/front.png').convert('RGBA')                  # 2 px per plate px
bg = Image.new('RGBA', m.size, (56, 56, 60, 255)); m = Image.alpha_composite(bg, m).convert('RGB')
r0, r1 = rowz(z1), rowz(z0); c0, c1 = colx(x0 * 1e-3), colx(x1 * 1e-3)
def crop_scale(img, scale_in):
    # img pixel = (plate px - box origin) * scale_in
    b = (int((c0 - box[0]) * scale_in), int((r0 - box[1]) * scale_in), int((c1 - box[0]) * scale_in) + 1, int((r1 - box[1]) * scale_in) + 1)
    t = img.crop(b); return t.resize((int((b[2] - b[0]) / scale_in * zoom), int((b[3] - b[1]) / scale_in * zoom)), Image.LANCZOS), b
pl, bp = crop_scale(PLATE.crop(box), 1.0)
me, bm = crop_scale(m, 2.0)
def grid(im, bx, sc):
    d = ImageDraw.Draw(im)
    ox = bx[0] / sc + box[0]; oy = bx[1] / sc + box[1]
    X = lambda xm: (colx(xm * 1e-3) - ox) * zoom
    Y = lambda z: (rowz(z) - oy) * zoom
    for xm in range(int(np.ceil(x0 / 10) * 10), int(x1) + 1, 10):
        d.line((X(xm), 0, X(xm), im.height), fill=(255, 255, 0) if xm % 50 == 0 else (110, 110, 0)); d.text((X(xm) + 2, 2), str(xm), fill=(255, 255, 0))
    for zc in np.arange(np.ceil(z0 * 100) / 100, z1 + 1e-6, 0.01):
        d.line((0, Y(zc), im.width, Y(zc)), fill=(0, 255, 255) if round(zc * 100) % 5 == 0 else (0, 110, 110)); d.text((2, Y(zc) + 2), f'{zc:.2f}', fill=(0, 255, 255))
grid(pl, bp, 1.0); grid(me, bm, 2.0)
W = pl.width + me.width + 10
sheet = Image.new('RGB', (W, max(pl.height, me.height)), (0, 0, 0)); sheet.paste(pl, (0, 0)); sheet.paste(me, (pl.width + 10, 0))
sheet.save(out); print(sheet.size)
