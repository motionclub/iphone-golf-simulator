"""python3 cu2.py <tag> <side> <viewlist> [sc] [res]  -> large single views, optional WIRE=1; views: out,in,front,back,qof,qif,qib,top,bottom
writes proof/it/<tag>/L_<view>_<R|L>[_w].png and a horizontal strip"""
import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-hands-fingers'
tag = sys.argv[1]; side = int(sys.argv[2]); vl = sys.argv[3].split(','); sc = sys.argv[4] if len(sys.argv) > 4 else '0.24'; res = sys.argv[5] if len(sys.argv) > 5 else '900'
cz = os.environ.get('CZ', '0.7700'); cy = os.environ.get('CY', '-0.0400'); cx = os.environ.get('CX', '0.2250')
cand = 'base' if tag == 'base' else f'{W}/data/cand_{tag}.npz'
DIRS = {'out': (1, 0, 0), 'in': (-1, 0, 0), 'front': (0, -1, 0), 'back': (0, 1, 0), 'qof': (0.75, -0.66, 0), 'qif': (-0.75, -0.66, 0.1), 'qib': (-0.75, 0.66, 0.1), 'qob': (0.75, 0.66, 0),
        'top': (0, 0, 1), 'bottom': (0, 0, -1), 'qpalm': (-0.9, -0.3, -0.3)}
sfx = 'R' if side > 0 else 'L'
specs = []
for v in vl:
    d = DIRS[v]; C = f'{float(cx)*side:.4f},{cy},{cz}'
    up = ',0,0,1' if v not in ('top', 'bottom') else ',0,-1,0'
    specs.append(f'{v}_{sfx}:{C}:{d[0]*side},{d[1]},{d[2]}:{sc}::' + up.replace(',', ':', 1).replace(',', ',') if False else f'{v}_{sfx}:{C}:{d[0]*side},{d[1]},{d[2]}:{sc}:55:-40' + (':0,0,1' if v not in ('top', 'bottom') else ':0,-1,0'))
od = f'{W}/proof/it/{tag}'; os.makedirs(od, exist_ok=True)
env = dict(os.environ, RES=res)
wire = os.environ.get('WIRE') == '1'
cmd = ['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', f'{W}/start/start_arms_candidate.blend', '--python', f'{W}/closeup_f.py', '--', cand, od + ('/w' if wire else '/s')] + specs
r = subprocess.run(cmd, capture_output=True, text=True, env=env)
if 'CLOSEUP_DONE' not in r.stdout: print(r.stdout[-2000:], r.stderr[-2000:]); sys.exit(1)
sub = od + ('/w' if wire else '/s')
ims = [Image.open(f'{sub}/{v}_{sfx}.png').convert('RGB') for v in vl]
S = Image.new('RGB', (sum(i.width for i in ims), ims[0].height), (20, 20, 22)); x = 0
try: f = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 22)
except Exception: f = ImageFont.load_default()
for v, im in zip(vl, ims):
    S.paste(im, (x, 0)); ImageDraw.Draw(S).text((x + 8, 6), f'{tag} {v} {sfx}' + (' wire' if wire else ''), fill=(255, 230, 120), font=f); x += im.width
out = f'{od}/strip_{sfx}_{"w" if wire else "s"}_{"-".join(vl)}.png'; S.save(out); print(out, S.size)
