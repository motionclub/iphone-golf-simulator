"""horizontal luminance profiles across the face: plate vs mesh Lambert prediction (plate-fitted light), front view.  blender -b --python profiles.py -- <nrmdir> <out.png> z1,z2,...  (needs bpy for EXR)"""
import sys
sys.path.insert(0, '.')
exec(open("photo.py").read().split("if __name__ == '__main__':")[0])
from PIL import ImageDraw
nd, out = sys.argv[sys.argv.index('--') + 1:][:2]
zs = [float(v) for v in sys.argv[sys.argv.index('--') + 3].split(',')]
up = 2
N, m = load_normals(Path(nd) / 'front_nrm.exr'); lum = plate_lum('front', up)
az, el, a, b = (4.0, 40.0, 100.0, 93.4)
l = light_vec(az, el); pred = a + b * np.clip(N @ l, 0, None)
box = BOX['front']
Wd, Hd = 900, 190 * len(zs)
im = Image.new('RGB', (Wd, Hd), (24, 24, 28)); d = ImageDraw.Draw(im)
for k, z in enumerate(zs):
    row = (76 + (H.TOP - z) / K - box[1]) * up           # row in the 2x panel
    r = int(round(row))
    xs_mm = np.arange(-45, 45.01, 0.65)
    cols = (H.CX + xs_mm * 1e-3 / K - box[0]) * up
    ci = np.clip(cols.astype(int), 0, lum.shape[1] - 1)
    pl = lum[r, ci]; pr = np.where(m[r, ci], pred[r, ci], np.nan)
    y0 = k * 190 + 10
    def Y(v): return y0 + 170 - (v - 60) / 200 * 170
    def X(xm): return (xm + 45) / 90 * (Wd - 20) + 10
    d.line((10, y0 + 170, Wd - 10, y0 + 170), fill=(70, 70, 70))
    for xm in range(-40, 41, 10): d.line((X(xm), y0, X(xm), y0 + 170), fill=(50, 50, 55)); d.text((X(xm) + 2, y0 + 172), str(xm), fill=(120, 120, 120))
    d.text((12, y0 + 2), f'z={z:.3f}  plate (white)  mesh pred (orange)', fill=(220, 220, 220))
    pts = [(X(xm), Y(v)) for xm, v in zip(xs_mm, pl)]; d.line(pts, fill=(255, 255, 255), width=2)
    seg = []
    for xm, v in zip(xs_mm, pr):
        if np.isnan(v):
            if len(seg) > 1: d.line(seg, fill=(255, 150, 40), width=2)
            seg = []
        else: seg.append((X(xm), Y(v)))
    if len(seg) > 1: d.line(seg, fill=(255, 150, 40), width=2)
im.save(out); print(out)
