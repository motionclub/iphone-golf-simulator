"""plate | unity-like mesh at the plate framing with an mm grid (front view). python3.13 grid_ul.py <ul_dir> <out.png> z0 z1 x0 x1 [zoom]"""
import sys; sys.path.insert(0, '.')
from m1i_lib import *
d, out = sys.argv[1], sys.argv[2]
z0, z1, x0, x1 = (float(v) for v in sys.argv[3:7]); zoom = int(sys.argv[7]) if len(sys.argv) > 7 else 6
box = (5, 62, 433, 352)
m = Image.open(f'{d}/plate_front.png').convert('RGB')        # 2 px per plate px
r0, r1 = rowz(z1), rowz(z0); c0, c1 = colx(x0 * 1e-3), colx(x1 * 1e-3)
def crop_scale(img, sc):
    b = (int((c0 - box[0]) * sc), int((r0 - box[1]) * sc), int((c1 - box[0]) * sc) + 1, int((r1 - box[1]) * sc) + 1)
    t = img.crop(b); return t.resize((int((b[2] - b[0]) / sc * zoom), int((b[3] - b[1]) / sc * zoom)), Image.LANCZOS), b
pl, bp = crop_scale(PLATE.crop(box), 1.0); me, bm = crop_scale(m, 2.0)
def grid(im, bx, sc):
    dr = ImageDraw.Draw(im); ox = bx[0] / sc + box[0]; oy = bx[1] / sc + box[1]
    X = lambda xm: (colx(xm * 1e-3) - ox) * zoom; Y = lambda z: (rowz(z) - oy) * zoom
    for xm in range(int(np.ceil(x0 / 10) * 10), int(x1) + 1, 10):
        dr.line((X(xm), 0, X(xm), im.height), fill=(255, 255, 0) if xm % 50 == 0 else (110, 110, 0)); dr.text((X(xm) + 2, 2), str(xm), fill=(255, 255, 0))
    for zc in np.arange(np.ceil(z0 * 100) / 100, z1 + 1e-6, 0.01):
        dr.line((0, Y(zc), im.width, Y(zc)), fill=(0, 255, 255) if round(zc * 100) % 5 == 0 else (0, 110, 110)); dr.text((2, Y(zc) + 2), f'{zc:.2f}', fill=(0, 255, 255))
grid(pl, bp, 1.0); grid(me, bm, 2.0)
sheet = Image.new('RGB', (pl.width + me.width + 10, max(pl.height, me.height))); sheet.paste(pl, (0, 0)); sheet.paste(me, (pl.width + 10, 0)); sheet.save(out); print(sheet.size)
