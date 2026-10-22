"""fullbody_vs_plate4.py: FULL-BODY views framed exactly like the plate's multi-angle sheet panels (same scale, same sole row), rows = plate | variants.
python3 tools/fullbody_vs_plate4.py out.png soft|clay label=coords.npy|blend:<path> ...      (coords = positions applied to Body_F of START_form3; blend: renders that blend as is)"""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
from viz3 import font, SHEET
from run4 import SOFT, HERE
BL = '/Applications/Blender.app/Contents/MacOS/Blender'
START = HERE + '/START_form4_candidate.blend'
S_TOP, SOLE_TOP = 1.7039 / 288.5, 338.5                 # sheet row 1 (front / back / profiles): m per px, sole row inside the 360-px panel
S_BOT, SOLE_BOT = 1.7039 / 290.5, 668.5 - 360.0         # sheet row 2 (3/4 views)
PW, PH = 320, 360
VIEWS = [('front', 0, 168, 'top'), ('3/4 front L', -20, 168, 'bot'), ('left profile', -90, 791.5, 'top'), ('3/4 back L', -150, 775, 'bot'), ('back', 180, 485, 'top')]
RES = (480, 540)

def shots():
    out = []
    for name, yaw, cx, row in VIEWS:
        S, sole = (S_TOP, SOLE_TOP) if row == 'top' else (S_BOT, SOLE_BOT)
        out.append(dict(name=name.replace(' ', '_').replace('/', ''), yaw=yaw, xc=0.0, zc=(sole - PH / 2) * S, w=PW * S, res=list(RES)))
    return out

def plate_tiles():
    ts = []
    for name, yaw, cx, row in VIEWS:
        y0 = 0 if row == 'top' else 360
        ts.append(SHEET.crop((int(cx - PW / 2), y0, int(cx + PW / 2), y0 + PH)).resize(RES, Image.LANCZOS).convert('RGB'))
    return ts

def render(tag, look, coords=None, blend=None):
    lk = SOFT if look == 'soft' else 'matcap:clay_studio.exr'
    sh = shots()
    spec = {"coords": coords, "out": f"{HERE}/scratch/r/fbp_{tag}_{look}", "shots": sh, "look": lk}
    r = subprocess.run([BL, '-b', blend or START, '--python', HERE + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
    assert 'RENDER_OK' in r.stdout, r.stdout[-600:] + r.stderr[-400:]
    tiles = []
    for s in sh:
        m = Image.open(f"{HERE}/scratch/r/fbp_{tag}_{look}_{s['name']}.png").convert('RGBA')
        bg = Image.new('RGBA', m.size, (225, 225, 228, 255)); bg.alpha_composite(m); tiles.append(bg.convert('RGB'))
    return tiles

def lab(im, t):
    d = ImageDraw.Draw(im); w = d.textlength(t, font=font(17)); d.rectangle([0, 0, w + 14, 26], fill=(0, 0, 0)); d.text((7, 4), t, font=font(17), fill=(255, 255, 255)); return im

def main(out, look, items, scale=0.62):
    rows = [('PLATE (multi-angle sheet)', plate_tiles())]
    for label, src in items:
        tiles = render(label.replace(' ', '_').replace('(', '').replace(')', '').replace('+', ''), look, coords=None if src.startswith('blend:') else (src if src.startswith('/') else HERE + '/' + src), blend=src[6:] if src.startswith('blend:') else None)
        rows.append((label, tiles))
    W = RES[0] * len(VIEWS); H = RES[1] * len(rows)
    im = Image.new('RGB', (W, H), (30, 30, 34))
    for r, (label, tiles) in enumerate(rows):
        for c, t in enumerate(tiles):
            t = t.copy(); lab(t, f'{label} - {VIEWS[c][0]}' if c == 0 else VIEWS[c][0]); im.paste(t, (c * RES[0], r * RES[1]))
    im = im.resize((int(W * scale), int(H * scale)), Image.LANCZOS); im.save(out); print(out, im.size)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], [a.split('=', 1) for a in sys.argv[3:]])
