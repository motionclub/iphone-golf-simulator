"""big3.py <part chest|pelvis> <out.png> <enh> tag=coords ... : large plate crops next to model renders (soft) in 3 views (front/back, 3/4 L, 3/4 R)"""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from board3 import *
def big(part, out, items, enh=1.8, px=640, look='matcap:soft'):
    if part == 'chest':
        zc, half = 1.20, 0.17
        views = [('f0', 0, None), ('fl', -20, 168), ('fr', 20, 472)]
        plate0 = lambda: BALD.crop((int(440 - half / S), int(679 - (zc + half) / S), int(440 + half / S), int(679 - (zc - half) / S))).resize((px, px), Image.LANCZOS).convert('RGB')
    else:
        zc, half = 0.90, 0.20
        views = [('b0', 180, None), ('bl', -150, 775), ('br', 150, 1078)]
        plate0 = lambda: BALD.crop((int(847 - half / S), int(679 - (zc + half) / S), int(847 + half / S), int(679 - (zc - half) / S))).resize((px, px), Image.LANCZOS).convert('RGB')
    shots = [dict(name=n, yaw=y, xc=0.0, zc=zc, w=2 * half, res=[px, px]) for n, y, _ in views]
    spec = {"variants": [{"tag": t, "coords": c if c.startswith('/') else HERE + '/' + c} for t, c in items], "out": f"{HERE}/scratch/r/big_{part}", "shots": shots, "look": look}
    r = subprocess.run([BL, '-b', START, '--python', HERE + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
    assert 'RENDER_OK' in r.stdout, r.stdout[-600:]
    E = lambda im: ImageEnhance.Contrast(im).enhance(enh)
    prow = [E(plate0())] + [E(sheet_tile(cx, zc, half, px, enh=1.0)) for _, _, cx in views[1:]]
    rows = [strip(prow, ['PLATE ' + n for n in ('front/back', '3/4 L', '3/4 R')])]
    for t, _ in items:
        rows.append(strip([E(bgcomp(f"{HERE}/scratch/r/big_{part}_{t}_{n}.png")) for n, _, _ in views], [f'{t} {n}' for n in ('front/back', '3/4 L', '3/4 R')]))
    W = Image.new('RGB', (rows[0].width, sum(r.height for r in rows)))
    y = 0
    for r in rows:
        W.paste(r, (0, y)); y += r.height
    W.save(out); print(out, W.size)
if __name__ == '__main__':
    part, out, enh = sys.argv[1], sys.argv[2], float(sys.argv[3])
    items = [a.split('=', 1) for a in sys.argv[4:]]
    big(part, out, items, enh)
