"""python3 proof_wrist.py <out.png>  : wrist weld, REAL custom normals, start blend vs candidate blend, both hands, 4 views"""
import subprocess, os, sys
from PIL import Image, ImageDraw, ImageFont
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-hands-fingers'
outp = sys.argv[1]; RES = 640
VIEWS = [('qif', (-0.75, -0.66, 0.1)), ('front', (0, -1, 0)), ('out', (1, 0, 0)), ('in', (-1, 0, 0))]
def render(blend, od):
    os.makedirs(od, exist_ok=True); specs = []
    for side, nm in ((+1, 'R'), (-1, 'L')):
        zc = 0.8456 if side > 0 else 0.8726
        for v, d in VIEWS:
            specs.append(f'{v}_{nm}:{0.232*side:.4f},-0.0150,{zc-0.012:.4f}:{d[0]*side if v in ("qif","out","in") else d[0]},{d[1]},{d[2]}:0.17')
    r = subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', blend, '--python', f'{W}/closeup_blend.py', '--', 'x', od] + specs, capture_output=True, text=True, env=dict(os.environ, RES=str(RES), AO='0', ISO='0'))
    assert 'CLOSEUP_DONE' in r.stdout, r.stderr[-500:]
odb, oda = f'{W}/proof/it/wrist_before', f'{W}/proof/it/wrist_after'
render(f'{W}/start/start_arms_candidate.blend', odb); render(f'{W}/export/HeroBase_Female_hands_candidate.blend', oda)
def fnt(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
rows = [('BEFORE +x', odb, 'R'), ('AFTER  +x', oda, 'R'), ('BEFORE -x', odb, 'L'), ('AFTER  -x', oda, 'L')]
tile = 460; top = 44; lab = 120
S = Image.new('RGB', (lab + 4 * tile, top + 4 * tile), (20, 20, 22)); d = ImageDraw.Draw(S)
d.text((10, 10), 'Wrist weld with the real custom normals (rings untouched: arm-side geometry bit-identical; only the 36 ring-vertex normals are recomputed)', fill=(255, 230, 120), font=fnt(20))
for ri, (nm, od, sfx) in enumerate(rows):
    d.text((10, top + ri * tile + tile // 2), nm, fill=(255, 255, 255), font=fnt(18))
    for vi, (v, _) in enumerate(VIEWS):
        im = Image.open(f'{od}/{v}_{sfx}.png').convert('RGB').resize((tile, tile), Image.LANCZOS); S.paste(im, (lab + vi * tile, top + ri * tile))
        if ri == 0: d.text((lab + vi * tile + 6, top - 18), {'qif': '3/4 front-medial', 'front': 'front', 'out': 'lateral', 'in': 'medial'}[v], fill=(200, 200, 200), font=fnt(14))
S.save(outp); print(outp, S.size)
