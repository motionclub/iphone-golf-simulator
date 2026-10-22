"""python3 proof_detail.py <tag> <out.png>   thumb + finger close-ups of the +x hand, solid + wire"""
import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-hands-fingers'
tag = sys.argv[1]; outp = sys.argv[2]; RES = int(os.environ.get('RES', '760'))
cand = f'{W}/data/cand_{tag}.npz'
G = [  # name, target, dir, ortho
    ('thumb_front', (0.2150, -0.0500, 0.7950), (0, -1, 0), 0.13), ('thumb_qif', (0.2150, -0.0500, 0.7950), (-0.75, -0.66, 0.1), 0.13), ('thumb_in', (0.2150, -0.0500, 0.7950), (-1, 0, 0), 0.13),
    ('fing_out', (0.2250, -0.0300, 0.7250), (1, 0, 0), 0.13), ('fing_qof', (0.2250, -0.0300, 0.7250), (0.75, -0.66, 0), 0.13), ('fing_front', (0.2250, -0.0300, 0.7250), (0, -1, 0), 0.13)]
specs = [f'{n}:{t[0]},{t[1]},{t[2]}:{d[0]},{d[1]},{d[2]}:{o}' for n, t, d, o in G]
def render(wire):
    od = f'{W}/proof/it/{tag}/detail_{"w" if wire else "s"}'; os.makedirs(od, exist_ok=True)
    env = dict(os.environ, RES=str(RES)); 
    if wire: env['WIRE'] = '1'
    cmd = ['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', f'{W}/start/start_arms_candidate.blend', '--python', f'{W}/closeup_f.py', '--', cand, od] + specs
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if 'CLOSEUP_DONE' not in r.stdout: print(r.stdout[-1500:], r.stderr[-1500:]); sys.exit(1)
    return od
ods, odw = render(False), render(True)
def fnt(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
tile = RES * 3 // 5; top = 46
S = Image.new('RGB', (3 * tile, top + 4 * tile), (20, 20, 22)); d = ImageDraw.Draw(S)
d.text((10, 10), f'Thumb (rows 1-2) and finger (rows 3-4) close-ups - solid then wireframe  [{tag}]', fill=(255, 230, 120), font=fnt(22))
for ri, (grp, od) in enumerate((('thumb', ods), ('thumb', odw), ('fing', ods), ('fing', odw))):
    for ci, n in enumerate([g[0] for g in G if g[0].startswith(grp)]):
        im = Image.open(f'{od}/{n}.png').convert('RGB').resize((tile, tile), Image.LANCZOS)
        S.paste(im, (ci * tile, top + ri * tile)); d.text((ci * tile + 6, top + ri * tile + 4), n + (' wire' if od == odw else ''), fill=(255, 255, 255), font=fnt(15))
S.save(outp); print(outp, S.size)
