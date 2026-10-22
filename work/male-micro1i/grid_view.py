"""mm-grid overlay on a plate view. python3.13 grid_view.py front|left|... out.png z0 z1 [x0 x1 mm] [zoom]
front: x in mm from face centre (plate col = 227.6 + x/K), z in m."""
import sys; sys.path.insert(0, '.')
from m1i_lib import *
from PIL import ImageFont
view = sys.argv[1]; out = sys.argv[2]; z0 = float(sys.argv[3]); z1 = float(sys.argv[4])
x0 = float(sys.argv[5]); x1 = float(sys.argv[6]); zoom = int(sys.argv[7]) if len(sys.argv) > 7 else 6
# front panel
r0, r1 = rowz(z1), rowz(z0); c0, c1 = colx(x0 * 1e-3), colx(x1 * 1e-3)
im = PLATE.crop((int(c0), int(r0), int(c1) + 1, int(r1) + 1))
im = im.resize((im.width * zoom, im.height * zoom), Image.LANCZOS)
d = ImageDraw.Draw(im)
def X(xmm): return (colx(xmm * 1e-3) - int(c0)) * zoom
def Y(z): return (rowz(z) - int(r0)) * zoom
for xm in range(int(np.ceil(x0 / 10) * 10), int(x1) + 1, 10):
    d.line((X(xm), 0, X(xm), im.height), fill=(255, 255, 0) if xm % 50 == 0 else (120, 120, 0), width=1)
    d.text((X(xm) + 2, 2), f'{xm}', fill=(255, 255, 0))
zz = np.arange(np.ceil(z0 * 100) / 100, z1 + 1e-6, 0.01)
for z in zz:
    d.line((0, Y(z), im.width, Y(z)), fill=(0, 255, 255) if abs(z * 100 - round(z * 100)) < 1e-6 and round(z * 100) % 5 == 0 else (0, 120, 120), width=1)
    d.text((2, Y(z) + 2), f'{z:.2f}', fill=(0, 255, 255))
im.save(out); print(im.size)
