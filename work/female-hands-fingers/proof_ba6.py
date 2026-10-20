"""python3 proof_ba6.py <after_tag> <out.png> [before_tag=base]  -> both hands, 6 views, before (start SDF hands) vs after"""
import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-hands-fingers'
after = sys.argv[1]; outp = sys.argv[2]; before = sys.argv[3] if len(sys.argv) > 3 else 'base'
RES = int(os.environ.get('RES', '620')); SC = os.environ.get('SC', '0.30')
VIEWS = [('out', (1, 0, 0)), ('in', (-1, 0, 0)), ('front', (0, -1, 0)), ('back', (0, 1, 0)), ('qof', (0.75, -0.66, 0)), ('qif', (-0.75, -0.66, 0.1))]
def specs():
    out = []
    for side in (+1, -1):
        for n, d in VIEWS:
            out.append(f'{n}_{"R" if side > 0 else "L"}:{0.232*side:.4f},-0.0250,0.7700:{d[0]*side},{d[1]},{d[2]}:{SC}')
    return out
def render(tag):
    cand = 'base' if tag == 'base' else f'{W}/data/cand_{tag}.npz'
    od = f'{W}/proof/it/{tag}/ba6'; os.makedirs(od, exist_ok=True)
    cmd = ['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', f'{W}/start/start_arms_candidate.blend', '--python', f'{W}/closeup_f.py', '--', cand, od] + specs()
    r = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, RES=str(RES)))
    if 'CLOSEUP_DONE' not in r.stdout: print(r.stdout[-1500:], r.stderr[-1500:]); sys.exit(1)
    return od
odb, oda = render(before), render(after)
def fnt(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
tile = RES * 2 // 3
rows = [('BEFORE  +x hand (R)', odb, 'R'), ('AFTER   +x hand (R)', oda, 'R'), ('BEFORE  -x hand (L)', odb, 'L'), ('AFTER   -x hand (L)', oda, 'L')]
top = 52; lab = 220
S = Image.new('RGB', (lab + len(VIEWS) * tile, top + len(rows) * tile), (20, 20, 22)); d = ImageDraw.Draw(S)
d.text((10, 10), f'Female hands - 6-view before / after   (before = {before}: SDF capsule hands, after = {after}: rebuilt hands)', fill=(255, 230, 120), font=fnt(22))
for ri, (nm, od, sfx) in enumerate(rows):
    y = top + ri * tile
    d.text((10, y + tile // 2 - 10), nm, fill=(255, 255, 255), font=fnt(18))
    for vi, (n, _) in enumerate(VIEWS):
        im = Image.open(f'{od}/{n}_{sfx}.png').convert('RGB').resize((tile, tile), Image.LANCZOS)
        S.paste(im, (lab + vi * tile, y))
        if ri == 0: d.text((lab + vi * tile + 6, top - 20), {'out': 'lateral (dorsum)', 'in': 'medial (palm)', 'front': 'front', 'back': 'back', 'qof': '3/4 front-lateral', 'qif': '3/4 front-medial'}[n], fill=(200, 200, 200), font=fnt(15))
S.save(outp); print(outp, S.size)
