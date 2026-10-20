"""python3 cu.py <tag|base> <side:+1|-1|both> [outdir] -> 6-view clay sheet of the hand(s). env passes through (WIRE, ISO, RES, AO)."""
import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-hands-fingers'
tag = sys.argv[1]; sides = sys.argv[2] if len(sys.argv) > 2 else '+1'
cand = 'base' if tag == 'base' else f'{W}/data/cand_{tag}.npz'
RES = int(os.environ.get('RES', '700'))
def views(side):
    sx = side
    C = f'{0.232*sx:.4f},-0.0200,0.7700'
    sc = os.environ.get('SC', '0.30')
    specs = [  # name, dir
        ('out', (1.0*sx, 0, 0)), ('in', (-1.0*sx, 0, 0)), ('front', (0, -1, 0)), ('back', (0, 1, 0)),
        ('q_out_front', (0.75*sx, -0.66, 0.0)), ('q_in_front', (-0.75*sx, -0.66, 0.1)),
    ]
    return [f'{n}_{"R" if side > 0 else "L"}:{C}:{d[0]},{d[1]},{d[2]}:{sc}' for n, d in specs]
out = sys.argv[3] if len(sys.argv) > 3 else f'{W}/proof/it/{tag}'
os.makedirs(out, exist_ok=True)
allspecs = []
for sd in ((+1, -1) if sides == 'both' else (int(sides),)):
    allspecs += views(sd)
env = dict(os.environ, RES=str(RES))
cmd = ['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', f'{W}/start/start_arms_candidate.blend', '--python', f'{W}/closeup_f.py', '--', cand, out] + allspecs
r = subprocess.run(cmd, capture_output=True, text=True, env=env)
if 'CLOSEUP_DONE' not in r.stdout: print(r.stdout[-2000:], r.stderr[-2000:]); sys.exit(1)
def font(sz):
    for p in ('/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/SFNS.ttf'):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
names = [s.split(':')[0] for s in allspecs]
cols = 6; rows = (len(names) + cols - 1) // cols; sz = RES // 2 + 80
S = Image.new('RGB', (cols * sz, rows * sz), (20, 20, 22)); d = ImageDraw.Draw(S)
for i, n in enumerate(names):
    im = Image.open(f'{out}/{n}.png').convert('RGB').resize((sz, sz), Image.LANCZOS)
    S.paste(im, ((i % cols) * sz, (i // cols) * sz)); d.text(((i % cols) * sz + 6, (i // cols) * sz + 4), f'{tag} {n}', fill=(255, 230, 120), font=font(16))
sheet = f'{out}/sheet_{sides}.png'; S.save(sheet); print(sheet, S.size)
