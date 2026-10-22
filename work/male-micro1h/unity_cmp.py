"""Unity captures vs plate crops.  python3 unity_cmp.py out.png  (uses ArtDir/.../male_form_d/unity/*.png)
Unity frame: ortho half-height = size (m); 1280x720.  Crops a square of (2*size_view) around the frame centre."""
import sys, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
U = R / 'ArtDir/hero/base_lock/proof/male_form_d/unity'
K = 0.0013043874429196725; TOP = 1.7046599388122559
plate = Image.open(R / 'ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')
out = Path(sys.argv[1])
S = 520
f = lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', s)
# (unity view, plate kind, centre z, centre y, size(half-height m), square crop side m)
VIEWS = [('head_front', 'front', 1.58, -0.05, 0.30, 0.30), ('head_threequarter', 'q3L', 1.58, -0.05, 0.30, 0.30), ('head_profile', 'side', 1.58, -0.05, 0.30, 0.30),
         ('face_front', 'front', 1.565, -0.05, 0.16, 0.16), ('face_threequarter', 'q3L', 1.565, -0.05, 0.16, 0.16), ('face_profile', 'side', 1.565, -0.03, 0.16, 0.16)]
cells = []
for uv, kind, zc, yt, size, side in VIEWS:
    im = Image.open(U / f'{uv}.png').convert('RGB')
    # unity target in frame centre; crop square of 'side' metres: pixels per metre = 720/(2*size)
    ppm = 720 / (2 * size); n = int(side * ppm)
    cx, cy = im.width // 2, im.height // 2
    mc = im.crop((cx - n // 2, cy - n // 2, cx + n // 2, cy + n // 2)).resize((S, S), Image.LANCZOS)
    npl = side / K
    if kind == 'front':
        col, row = 227.6, 76 + (TOP - zc) / K
    elif kind == 'side':
        col, row = 712 - (0.065 - yt) / K, 76 + (TOP - zc) / K
    else:
        psi = math.radians(32.5); col = 219.0 + ((yt * math.sin(psi)) - (-0.040 * math.sin(psi))) / K; row = 397 + (TOP - zc) / K
    pc = plate.crop((int(round(col - npl / 2)), int(round(row - npl / 2)), int(round(col + npl / 2)), int(round(row + npl / 2)))).resize((S, S), Image.LANCZOS)
    cells.append((uv, pc, mc))
ncol = 3
rows = (len(cells) + ncol - 1) // ncol
Wd = ncol * (S + 8) + 8
Sh = Image.new('RGB', (Wd, rows * (2 * S + 20) + 40), (30, 31, 35)); d = ImageDraw.Draw(Sh)
d.text((10, 8), 'UNITY vs PLATE (top: plate, bottom: Unity capture)', font=f(22), fill=(240, 240, 240))
for i, (uv, pc, mc) in enumerate(cells):
    r, c = divmod(i, ncol)
    x0 = 8 + c * (S + 8); y0 = 40 + r * (2 * S + 20)
    Sh.paste(pc, (x0, y0)); Sh.paste(mc, (x0, y0 + S + 4))
    d.rectangle((x0, y0, x0 + 150, y0 + 22), fill=(14, 14, 18)); d.text((x0 + 6, y0 + 2), uv, font=f(16), fill=(240, 240, 240))
Sh = Sh.resize((Sh.width * 2 // 3, Sh.height * 2 // 3), Image.LANCZOS)
Sh.save(out); print(out, Sh.size)
