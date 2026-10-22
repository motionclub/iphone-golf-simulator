"""fullbody_big4.py: large full-body views (front, 3/4, side, 3/4 back, back), one row per item.  python3 tools/fullbody_big4.py out.png soft|clay label=coords.npy|blend:<path> ..."""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
from viz3 import font
from run4 import SOFT, HERE
BL = '/Applications/Blender.app/Contents/MacOS/Blender'
START = HERE + '/START_form3_candidate.blend'
VIEWS = [('front', 0), ('3/4 front', -22), ('side', -90), ('3/4 back', -158), ('back', 180)]
RES = (560, 1120)

def render(tag, look, coords=None, blend=None):
    lk = SOFT if look == 'soft' else 'matcap:clay_studio.exr'
    sh = [dict(name=n.replace('/', '').replace(' ', '_'), yaw=y, xc=0.0, zc=0.86, w=0.95, res=list(RES)) for n, y in VIEWS]
    spec = {"coords": coords, "out": f"{HERE}/scratch/r/big_{tag}_{look}", "shots": sh, "look": lk}
    r = subprocess.run([BL, '-b', blend or START, '--python', HERE + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
    assert 'RENDER_OK' in r.stdout, r.stdout[-600:] + r.stderr[-400:]
    out = []
    for s in sh:
        m = Image.open(f"{HERE}/scratch/r/big_{tag}_{look}_{s['name']}.png").convert('RGBA')
        bg = Image.new('RGBA', m.size, (232, 232, 235, 255)); bg.alpha_composite(m); out.append(bg.convert('RGB'))
    return out

def main(out, rows_spec, width=2000):
    rows = []
    for label, look, src in rows_spec:
        tiles = render(label.split()[0] + look, look, coords=None if src.startswith('blend:') else (src if src.startswith('/') else HERE + '/' + src), blend=src[6:] if src.startswith('blend:') else None)
        row = Image.new('RGB', (RES[0] * len(VIEWS), RES[1]))
        for i, t in enumerate(tiles):
            row.paste(t, (i * RES[0], 0))
        d = ImageDraw.Draw(row); w = d.textlength(label, font=font(26)); d.rectangle([0, 0, w + 24, 42], fill=(0, 0, 0)); d.text((12, 6), label, font=font(26), fill=(255, 255, 255))
        for i, (n, _) in enumerate(VIEWS):
            d.text((i * RES[0] + RES[0] // 2 - 30, RES[1] - 34), n, font=font(22, False), fill=(90, 90, 100))
        rows.append(row)
    W = Image.new('RGB', (rows[0].width, sum(r.height for r in rows)))
    y = 0
    for r in rows:
        W.paste(r, (0, y)); y += r.height
    sc = width / W.width
    W = W.resize((width, int(W.height * sc)), Image.LANCZOS); W.save(out); print(out, W.size)

if __name__ == '__main__':
    out = sys.argv[1]
    spec = []
    for a in sys.argv[2:]:
        label, rest = a.split('|', 1); look, src = rest.split('|', 1); spec.append((label, look, src))
    main(out, spec)
