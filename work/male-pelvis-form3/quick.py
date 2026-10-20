"""Fast contact sheet of several candidates against plate/start in the butt/groin views.
python3 quick.py render <tag...>        -> r/<tag>_q/*.png (border-cropped renders)
python3 quick.py sheet out.png <view,view,...> <tag...> [--enh]  -> rows = PLATE, tags... ; columns = views
views: back, bl, br, left, right, front, fl, fr"""
import sys, os, json, subprocess
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form3'); R = W.parent.parent
CAMS = {c['name']: c for c in json.load(open(R / 'work/male-silhouette/reference-cameras.json'))['views']}
PLATE_MAIN = Image.open(R / 'ArtDir/hero/base_lock/male_body_bald.jpg').convert('RGB'); PLATE_SHEET = Image.open(R / 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
def axial(view, zlo, zhi, xh):
    c = CAMS['bald_' + view]; mpp = c['metres_per_pixel']; cx = c['centre_x']; sy = c['sole_y']
    return (int(cx - xh / mpp), int(sy - zhi / mpp), int(cx + xh / mpp), int(sy - zlo / mpp))
VIEWS = {   # name: (kind, spec)
    'back': ('main', 'back', axial('back', 0.68, 1.06, 0.20), 4), 'front': ('main', 'front', axial('front', 0.68, 1.00, 0.20), 4),
    'bl': ('sheet', 'reg_q3BL_{c0}_{c1}_{r0}_{r1}_{m}', (745, 495, 865, 600), 6), 'br': ('sheet', 'reg_q3BR_{c0}_{c1}_{r0}_{r1}_{m}', (1020, 495, 1140, 600), 6),
    'fl': ('sheet', 'reg_q3FL_{c0}_{c1}_{r0}_{r1}_{m}', (130, 480, 245, 585), 6), 'fr': ('sheet', 'reg_q3FR_{c0}_{c1}_{r0}_{r1}_{m}', (425, 480, 540, 585), 6),
    'left': ('sheet_axial', 'left@{m}:{b}', (780, 165, 835, 235), 4), 'right': ('sheet_axial', 'right@{m}:{b}', (1025, 165, 1080, 235), 4)}
def vspec(name):
    kind, spec, box, m = VIEWS[name]
    if kind == 'main': x0, y0, x1, y1 = box; return f'{spec}@{m}:{x0}_{y0}_{x1}_{y1}'
    if kind == 'sheet': c0, r0, c1, r1 = box; return spec.format(c0=c0, c1=c1, r0=r0, r1=r1, m=m)
    c0, r0, c1, r1 = box; return spec.format(m=m, b=f'{c0}_{r0}_{c1}_{r1}')   # axial sheet views: locked cameras are aligned to the sheet frame? (see below)
RELIT = '0.35,0.55,0.65'
def render(tags, views=None, look='manneq'):
    names = views or list(VIEWS)
    for tag in tags:
        # second pass: the same views under a single high-key sun (plate-like top light) into r/<tag>_qh
        for lightpass in (0, 1):
            _render_one(tag, names, look, lightpass)
def _render_one(tag, names, look, lightpass):
    if True:
        src = f'data/V_{tag}.npy' if tag != 'start' else 'baseline/HeroBase_Male_Silhouette.blend'
        specs = []
        for n in names:
            kind = VIEWS[n][0]
            if kind == 'sheet_axial':
                # the 'left'/'right' locked cameras cover the 1280x720 SHEET frame
                c0, r0, c1, r1 = VIEWS[n][2]; specs.append(f'{n}@{VIEWS[n][3]}:{c0}_{r0}_{c1}_{r1}')
            else: specs.append(vspec(n))
        env = dict(os.environ, PYTHONPATH=str(R / 'work/male-micro1i/pylib'))
        if lightpass: env['GRAZE'] = RELIT
        r = subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', '--python', 'rig.py', '--', src, f'r/{tag}_q' + ('h' if lightpass else ''), ','.join(specs), look, '0.886,0.627,0.431'], cwd=W, env=env, capture_output=True, text=True)
        if 'Traceback' in r.stdout or 'Error' in r.stderr[-300:]: print(r.stdout[-1500:], r.stderr[-800:])
def font(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
def fname(n):
    kind, spec, box, m = VIEWS[n]
    if kind == 'main': x0, y0, x1, y1 = box; return f'{spec}@{m}:{x0}_{y0}_{x1}_{y1}'
    if kind == 'sheet': return vspec(n)
    c0, r0, c1, r1 = box; return f'{n}@{m}:{c0}_{r0}_{c1}_{r1}'
def getim(n, tag):
    hh = n.endswith('H'); n = n[:-1] if hh else n
    kind, spec, box, m = VIEWS[n]
    if tag == 'PLATE':
        if kind == 'main': im = PLATE_MAIN.crop(box)
        else: c0, r0, c1, r1 = box; im = PLATE_SHEET.crop((c0, r0, c1, r1))
        return im.resize((im.width * (m if kind == 'main' else m), im.height * m), Image.LANCZOS) if kind == 'main' else im.resize((im.width * m, im.height * m), Image.LANCZOS)
    return Image.open(W / f'r/{tag}_q{"h" if hh else ""}/{fname(n)}.png').convert('RGB')
def sheet(out, names, tags, enh=False, labels=None):
    rows = ['PLATE'] + tags; cols = []
    for n in names:
        col = [getim(n, t) for t in rows]
        if enh: col = [ImageOps.autocontrast(i.convert('L'), cutoff=(1, 1)).convert('RGB') for i in col]
        # normalise sizes to the plate cell
        w0, h0 = col[0].size; col = [i.resize((w0, h0), Image.LANCZOS) if i.size != (w0, h0) else i for i in col]; cols.append(col)
    F = font(18); cw = [c[0].width for c in cols]; ch = max(c[0].height for c in cols)
    S = Image.new('RGB', (sum(cw) + 6 * (len(cols) + 1), len(rows) * (ch + 24) + 6), (16, 16, 16)); d = ImageDraw.Draw(S); x = 6
    labs = labels or rows
    for ci, col in enumerate(cols):
        for ri, im in enumerate(col):
            y = 6 + ri * (ch + 24) + 22; S.paste(im, (x, y)); d.text((x + 3, y - 20), labs[ri] + '  ' + names[ci], fill=(255, 200, 80), font=F)
        x += cw[ci] + 6
    S.save(out); print(out, S.size)
if __name__ == '__main__':
    if sys.argv[1] == 'render':
        names = os.environ.get('VIEWSET', '').split(',') if os.environ.get('VIEWSET') else None; render(sys.argv[2:], names)
    else:
        enh = '--enh' in sys.argv; a = [x for x in sys.argv[2:] if x != '--enh']
        sheet(a[0], a[1].split(','), a[2:], enh=enh, labels=os.environ.get('LABELS', '').split(',') if os.environ.get('LABELS') else None)
