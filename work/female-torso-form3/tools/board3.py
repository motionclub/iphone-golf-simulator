"""board3.py: multi-variant, multi-view boards.   python3 tools/board3.py chest|pelvis out.png [--look matcap:soft] tag=coords.npy ...
chest board rows : front crop (same frame as the bald plate crop) / yaw +25 / yaw -25 (plate = sheet 3/4 FL / FR tiles) / side
pelvis board rows: back / yaw -155 / yaw +155 / side  (plate = bald back crop / sheet 3/4 BL / BR tiles)"""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from rr import *

S2b = 1.7039 / 290.5; V0b = 668.5; S2t = 1.7039 / 288.5; V0t = 338.5
def sheet_tile(cx, zc, half, px, bottom=True, enh=1.5):
    S, V0 = (S2b, V0b) if bottom else (S2t, V0t)
    w = half / S; y0 = V0 - (zc + half) / S; y1 = V0 - (zc - half) / S
    c = SHEET.crop((int(cx - w), int(y0), int(cx + w), int(y1))).resize((px, px), Image.LANCZOS)
    return ImageEnhance.Contrast(c).enhance(enh).convert('RGB')

def shots_for(part, px=420):
    if part == 'chest':
        zc, half = 1.20, 0.27
        sh = [roi_shot('front', 'chest'),
              dict(name='y25', yaw=-20, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
              dict(name='y-25', yaw=20, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
              dict(name='side', yaw=-90, xc=0.0, zc=zc, w=2 * half, res=[px, px])]
        plate = [plate_crop('chest', 1.0), sheet_tile(168, zc, half, px), sheet_tile(472, zc, half, px), sheet_tile(790, zc, half, px, bottom=False)]
        names = ['front', '3/4 FL (+25)', '3/4 FR (-25)', 'side']
    else:
        zc, half = 0.90, 0.27
        sh = [roi_shot('back', 'pelvis'),
              dict(name='y155', yaw=-150, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
              dict(name='y-155', yaw=150, xc=0.0, zc=zc, w=2 * half, res=[px, px]),
              dict(name='side', yaw=-90, xc=0.0, zc=zc, w=2 * half, res=[px, px])]
        plate = [plate_crop('pelvis', 1.0), sheet_tile(775, zc, half, px), sheet_tile(1078, zc, half, px), sheet_tile(790, zc, half, px, bottom=False)]
        names = ['back', '3/4 BL (-155)', '3/4 BR (+155)', 'side']
    return sh, plate, names

def board(part, out, items, look='matcap:soft', px=420, cav=0.0):
    sh, plate, names = shots_for(part, px)
    spec = {"variants": [{"tag": t, "coords": c if c.startswith('/') else HERE + '/' + c} for t, c in items],
            "out": f"{HERE}/scratch/r/bd_{part}", "shots": sh, "look": look, "cavity": cav}
    r = subprocess.run([BL, '-b', START, '--python', HERE + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
    if 'RENDER_OK' not in r.stdout:
        print(r.stdout[-1500:], r.stderr[-1500:]); raise SystemExit('render failed')
    rows = []
    for k, s in enumerate(sh):
        ims, labs = [], []
        if plate[k] is not None:
            ims.append(plate[k].resize((px if k else int(px * plate[k].width / plate[k].height), px), Image.LANCZOS) if True else plate[k]); labs.append('PLATE ' + names[k])
        else:
            ims.append(Image.new('RGB', (px, px), (30, 30, 34))); labs.append('(no plate side crop)')
        for t, _ in items:
            ims.append(bgcomp(f"{HERE}/scratch/r/bd_{part}_{t}_{s['name']}.png").resize((px if k else int(px * plate[0].width / plate[0].height) if False else px, px), Image.LANCZOS)); labs.append(f'{t} {names[k]}')
        rows.append(strip(ims, labs))
    W = Image.new('RGB', (max(r.width for r in rows), sum(r.height for r in rows)))
    y = 0
    for r in rows:
        W.paste(r, (0, y)); y += r.height
    W.save(out); print(out, W.size)

if __name__ == '__main__':
    part, out = sys.argv[1], sys.argv[2]
    look = sys.argv[sys.argv.index('--look') + 1] if '--look' in sys.argv else 'matcap:soft'
    items = [a.split('=', 1) for a in sys.argv[3:] if '=' in a and not a.startswith('--')]
    board(part, out, items, look)
