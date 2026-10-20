"""fullbody4.py: full-torso views (front, 3/4, side, back 3/4, back) for several variants, one row per variant.
python3 tools/fullbody4.py out.png soft|clay tag=coords.npy ..."""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
from run4 import SOFT, HERE
from viz3 import font
BL = '/Applications/Blender.app/Contents/MacOS/Blender'
START = HERE + '/START_form3_candidate.blend'
def main(out, look, items, views=(('front', 0), ('q3F', -22), ('side', -90), ('q3B', -158), ('back', 180)), zc=1.08, w=0.80, res=(600, 820)):
    lk = SOFT if look == 'soft' else 'matcap:clay_studio.exr'
    shots = [dict(name=n, yaw=y, xc=0.0, zc=zc, w=w, res=list(res)) for n, y in views]
    spec = {"variants": [{"tag": f'fb_{t}_{look}', "coords": p if p.startswith('/') else HERE + '/' + p} for t, p in items], "out": f"{HERE}/scratch/r/fbody", "shots": shots, "look": lk}
    r = subprocess.run([BL, '-b', START, '--python', HERE + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
    assert 'RENDER_OK' in r.stdout, r.stdout[-800:] + r.stderr[-500:]
    rows = []
    for t, _ in items:
        row = Image.new('RGB', (res[0] * len(views), res[1]), (225, 225, 228))
        for i, (n, _) in enumerate(views):
            m = Image.open(f"{HERE}/scratch/r/fbody_fb_{t}_{look}_{n}.png").convert('RGBA')
            bg = Image.new('RGBA', m.size, (225, 225, 228, 255)); bg.alpha_composite(m)
            im = bg.convert('RGB'); d = ImageDraw.Draw(im); d.rectangle([0, 0, 260, 26], fill=(0, 0, 0)); d.text((6, 4), f'{t} {n}', fill=(255, 255, 255), font=font(16))
            row.paste(im, (i * res[0], 0))
        rows.append(row)
    W = Image.new('RGB', (rows[0].width, sum(r.height for r in rows)))
    y = 0
    for r in rows:
        W.paste(r, (0, y)); y += r.height
    W = W.resize((W.width // 2, W.height // 2), Image.LANCZOS)
    W.save(out); print(out, W.size)
if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], [a.split('=', 1) for a in sys.argv[3:]])
