"""Registered plate-vs-render crops of the multi-angle SHEET panels at M x magnification (same px scale).
python3 panel_cmp.py render <tag> [look]            -> r/<tag>_p/<name>.png for the standard butt crops
python3 panel_cmp.py sheet out.png <panel list comma> [--enh] tag...   -> rows: PLATE, tags... ; columns: panels
Panels (name: (kind, sheet box c0,c1,r0,r1, mag)): q_bl, q_br, left, right, q_fl, q_fr, back, front (sheet axial views)"""
import sys, os, subprocess, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form3'); R = W.parent.parent
M = 6
BOX = {  # name: (rig view template, c0,c1,r0,r1)
    'q_bl': ('reg_q3BL_{c0}_{c1}_{r0}_{r1}_{m}', 730, 870, 480, 610),
    'q_br': ('reg_q3BR_{c0}_{c1}_{r0}_{r1}_{m}', 1010, 1150, 480, 610),
    'q_fl': ('reg_q3FL_{c0}_{c1}_{r0}_{r1}_{m}', 120, 250, 470, 590),
    'q_fr': ('reg_q3FR_{c0}_{c1}_{r0}_{r1}_{m}', 415, 545, 470, 590),
    'left': ('left@{m}', 760, 840, 160, 240, 3),
    'right': ('right@{m}', 1020, 1090, 160, 240, 3),
    'back': ('sheet_back@{m}', 410, 560, 150, 250, 3),
    'front': ('sheet_front@{m}', 115, 255, 150, 250, 3),
    'bq_bl': ('reg_q3BL_{c0}_{c1}_{r0}_{r1}_{m}', 745, 865, 495, 600, 10),
    'bq_br': ('reg_q3BR_{c0}_{c1}_{r0}_{r1}_{m}', 1020, 1140, 495, 600, 10),
    'bleft': ('left@{m}', 770, 835, 165, 235, 3),
    'bright': ('right@{m}', 1025, 1085, 165, 235, 3),
}
def _mag(p): return BOX[p][5] if len(BOX[p]) > 5 else M
def vname(p):
    t, c0, c1, r0, r1 = BOX[p][:5]; return t.format(c0=c0, c1=c1, r0=r0, r1=r1, m=_mag(p))
def render(tag, look='manneq'):
    src = f'data/V_{tag}.npy' if tag != 'start' else 'baseline/HeroBase_Male_Silhouette.blend'
    sel = os.environ.get('PANELS', '').split(',') if os.environ.get('PANELS') else list(BOX)
    views = ','.join(dict.fromkeys(vname(p) for p in sel))
    env = dict(os.environ, PYTHONPATH=str(R / 'work/male-micro1i/pylib'))
    r = subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', '--python', 'rig.py', '--', src, f'r/{tag}_p', views, look, '0.886,0.627,0.431'], cwd=W, env=env, capture_output=True, text=True)
    if 'Traceback' in r.stdout or 'Error' in r.stderr[-300:]: print(r.stdout[-1500:], r.stderr[-800:])
def font(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
def get(p, tag):
    t, c0, c1, r0, r1 = BOX[p][:5]; MM = _mag(p)
    if tag == 'PLATE':
        sh = Image.open(R / 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB').crop((c0, r0, c1, r1))
        return sh.resize((sh.width * MM, sh.height * MM), Image.LANCZOS)
    im = Image.open(W / f'r/{tag}_p/{vname(p)}.png').convert('RGB')
    if t.startswith(('left@', 'right@', 'sheet_back@', 'sheet_front@')): im = im.crop((c0 * MM, r0 * MM, c1 * MM, r1 * MM))
    return im
def sheet(out, panels, tags, enh=False, labels=None):
    rows = ['PLATE'] + tags; cols = []
    for p in panels:
        col = [get(p, t) for t in rows]
        if enh: col = [ImageOps.autocontrast(i.convert('L'), cutoff=(1, 1)).convert('RGB') for i in col]
        cols.append(col)
    F = font(20); cw = [c[0].width for c in cols]; ch = max(c[0].height for c in cols)
    S = Image.new('RGB', (sum(cw) + 8 * (len(cols) + 1), len(rows) * (ch + 30) + 8), (16, 16, 16)); d = ImageDraw.Draw(S); x = 8
    labs = labels or rows
    for ci, col in enumerate(cols):
        for ri, im in enumerate(col):
            y = 8 + ri * (ch + 30) + 24; S.paste(im, (x, y)); d.text((x + 4, y - 22), labs[ri] + '  ' + panels[ci], fill=(255, 200, 80), font=F)
        x += cw[ci] + 8
    S.save(out); print(out, S.size)
if __name__ == '__main__':
    if sys.argv[1] == 'render': render(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'manneq')
    else:
        enh = '--enh' in sys.argv; a = [x for x in sys.argv[2:] if x != '--enh']
        sheet(a[0], a[1].split(','), a[2:], enh=enh, labels=os.environ.get('LABELS', '').split(',') if os.environ.get('LABELS') else None)
