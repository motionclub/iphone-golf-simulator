"""Sheet-scale judging sheets in the look of the user's REF/NOW sheet (grey mannequin body + skin head).
python3 judge.py render <tag> [look]      -> r/<tag>_j/ : sheet_back, left, right, sheet_front + whole-panel 3/4 cameras (reg_) at 3x
python3 judge.py sheet <out.png> <region pelvis|nape|full> <tag> [tag...]  -> REF | start | tags... for 5 views (back,left,right,q_bl,q_br) [+front,q_fl,q_fr for pelvis]"""
import sys, os, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin'); R = W.parent.parent
PANELS = {  # name: (ref box c0,r0,c1,r1 on the multiangle sheet, render file, mag)
    'front': ((55, 49, 315, 347), 'sheet_front@3', 3), 'back': ((350, 49, 620, 347), 'sheet_back@3', 3), 'left': ((739, 49, 825, 347), 'left@3', 3), 'right': ((1038, 49, 1138, 347), 'right@3', 3),
    'q_fl': ((85, 370, 285, 690), 'reg_q3FL_85_285_370_690_3', 3), 'q_fr': ((378, 370, 578, 690), 'reg_q3FR_378_578_370_690_3', 3),
    'q_bl': ((695, 370, 895, 690), 'reg_q3BL_695_895_370_690_3', 3), 'q_br': ((973, 370, 1173, 690), 'reg_q3BR_973_1173_370_690_3', 3)}
VIEWS = 'sheet_front@3,sheet_back@3,left@3,right@3,' + ','.join(v[1] for k, v in PANELS.items() if k.startswith('q_'))
def render(tag, look='manneq'):
    src = f'data/V_{tag}.npy' if tag != 'start' else 'baseline/HeroBase_Male_Silhouette.blend'
    env = dict(os.environ, PYTHONPATH=str(R / 'work/male-micro1i/pylib'))
    r = subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', '--python', 'rig.py', '--', src, f'r/{tag}_j', VIEWS, look, '0.886,0.627,0.431'], cwd=W, env=env, capture_output=True, text=True)
    if 'Traceback' in r.stdout or 'Error' in r.stderr[-300:]: print(r.stdout[-1500:], r.stderr[-800:])
def font(sz):
    for f in ('/System/Library/Fonts/Helvetica.ttc',):
        try: return ImageFont.truetype(f, sz)
        except Exception: pass
    return ImageFont.load_default()
REGION = {'pelvis': (0.55, 1.12), 'nape': (1.22, 1.62), 'full': (0.0, 1.74)}
def sheet(out, region, tags, views=('back', 'q_bl', 'q_br', 'left', 'right'), Z=3):
    sh = Image.open(R / 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB'); z0, z1 = REGION[region]
    cols = []; F = font(18)
    for v in views:
        box, fn, mag = PANELS[v]; c0, r0, c1, r1 = box
        # rows of the sheet for z range: sole row 343 (axial) / 673 (3/4 panels), 0.00582 m/px
        sole = 343 if v in ('front', 'back', 'left', 'right') else 673; mpp = 0.00582
        ra, rb = int(sole - z1 / mpp), int(sole - z0 / mpp)
        ra = max(ra, r0); rb = min(rb, r1)
        ref = sh.crop((c0, ra, c1, rb)); w, h = ref.size; pan = [ref.resize((w * Z, h * Z), Image.LANCZOS)]
        for t in ['start'] + tags:
            im = Image.open(W / f'r/{t}_j/{fn}.png').convert('RGB')
            if v in ('front', 'back', 'left', 'right'): im = im.crop((c0 * mag, ra * mag, c1 * mag, rb * mag))      # locked cams are sheet-pixel aligned to the full 1280x720 sheet (rendered at mag x)
            else: im = im.crop((0, (ra - r0) * mag, (c1 - c0) * mag, (rb - r0) * mag))
            pan.append(im.resize((w * Z, h * Z), Image.LANCZOS))
        cols.append((v, pan))
    n = 2 + len(tags); widths = [p[0].width for _, p in cols]; ch = max(p[0].height for _, p in cols)
    S = Image.new('RGB', (sum(widths) + 8 * (len(cols) + 1), n * (ch + 24) + 8), (16, 16, 16)); d = ImageDraw.Draw(S); x = 8
    for ci, (v, pan) in enumerate(cols):
        for ri, im in enumerate(pan):
            y = 8 + ri * (ch + 24) + 20; S.paste(im, (x, y)); d.text((x + 4, y - 18), (os.environ.get('LABELS', '').split(',') if os.environ.get('LABELS') else ['REF', 'NOW start'] + tags)[ri] + '  ' + v, fill=(255, 200, 80), font=F)
        x += widths[ci] + 8
    S.save(out); print(out, S.size)
if __name__ == '__main__':
    if sys.argv[1] == 'render':
        for t in sys.argv[2:]: render(t)
    else:
        vs = os.environ.get('VIEWS'); Zs = int(os.environ.get('ZOOM', 3))
        sheet(sys.argv[2], sys.argv[3], sys.argv[4:], views=tuple(vs.split(',')) if vs else ('back', 'q_bl', 'q_br', 'left', 'right'), Z=Zs)
