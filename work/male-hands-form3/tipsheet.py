"""Isolated fingertip close-up sheet.  python3 tipsheet.py out.png k|thumb win_m name1 '<json>' name2 '<json>' ...
rows = candidates, columns = dorsal / radial / palmar / q_palmar_radial; centre = finger tip (local frame)"""
import sys, json, subprocess, os
from PIL import Image, ImageDraw
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-hands-form3'
sys.path.insert(0, W)
from views import specs
from sheetlib import font
out, which, win = sys.argv[1], sys.argv[2], float(sys.argv[3])
cands = [(sys.argv[i], sys.argv[i + 1]) for i in range(4, len(sys.argv), 2)]
V = {'dorsal': ((0, -1, 0), (0, 0, -1)), 'radial': ((1, 0, 0), (0, 0, -1)), 'palmar': ((0, 1, 0), (0, 0, -1)), 'q_palmar_radial': ((0.8, 0.6, 0), (0, 0, -1))}
rows = []
for name, js in cands:
    npz = f'{W}/data/iso_{name}_{which}.npz'
    r = subprocess.run([W + '/py.sh', W + '/fingeriso.py', npz, js, which], capture_output=True, text=True)
    # tip position from the iso candidate: use extents of the mesh
    import numpy as np
    D = np.load(npz); Vv = D['V'][np.unique(D['corner_verts'])].astype(float)
    sys.path.insert(0, W); from hlib import to_local
    L = to_local(Vv, +1); tip = L[np.argmax(L[:, 2])]; cen = (tip[0], tip[1], tip[2] - 0.35 * win)
    sp = specs(+1, win, center=cen, views=V)
    od = f'{W}/proof/it/iso_{name}_{which}'
    env = dict(os.environ); env.update(ISO='0', CLIP='0.10', FAR='0.12', RES='700', AO='1')
    rr = subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', f'{W}/baseline/HeroBase_Male_Silhouette.blend', '--python', f'{W}/closeup3.py', '--', npz, od] + sp, capture_output=True, text=True, env=env)
    if 'CLOSEUP_DONE' not in rr.stdout: print(rr.stdout[-800:], rr.stderr[-800:])
    ims = [Image.open(f'{od}/{n}.png').convert('RGB') for n in V]
    row = Image.new('RGB', (sum(i.width for i in ims), ims[0].height + 26), (20, 20, 22))
    x = 0
    for i in ims: row.paste(i, (x, 26)); x += i.width
    ImageDraw.Draw(row).text((6, 4), f'{name}   {which}   window {win*1000:.0f} mm   [dorsal | radial | palmar | q_palmar_radial]', fill=(255, 230, 120), font=font(16))
    rows.append(row)
S = Image.new('RGB', (rows[0].width, sum(r.height for r in rows)))
y = 0
for r in rows: S.paste(r, (0, y)); y += r.height
S = S.resize((S.width * 2 // 3, S.height * 2 // 3)); S.save(out); print(out, S.size)
