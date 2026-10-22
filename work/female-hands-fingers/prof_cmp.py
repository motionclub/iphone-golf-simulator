"""python3 prof_cmp.py <tag|base> [out.png]   plate | model | overlay for both profile panels, hand region, 1 cm grid"""
import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageOps
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-hands-fingers'
B = W + '/../../ArtDir/hero/base_lock/'
S2 = 1.7039 / 288.5
tag = sys.argv[1]; outp = sys.argv[2] if len(sys.argv) > 2 else f'{W}/proof/it/{tag}/prof_cmp.png'
cand = 'base' if tag == 'base' else f'{W}/data/cand_{tag}.npz'
od = f'{W}/proof/it/{tag}/prof'; os.makedirs(od, exist_ok=True)
K = 8
# left profile: crop px x 750..850, y 95..250 (anchor 791.5) ; right profile: x 1054..1154 (anchor 1095.5)
yc_L = (800 - 791.5) * S2; zc = (338.5 - 172.5) * S2
yc_R = -((1104 - 1095.5) * S2)
specs = [f'pL:0,{yc_L:.5f},{zc:.5f}:1,0,0:{155*S2:.5f}', f'pR:0,{yc_R:.5f},{zc:.5f}:-1,0,0:{155*S2:.5f}']
env = dict(os.environ, RES=str(155 * K), ISO='0', AO='0')
cmd = ['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', f'{W}/start/start_arms_candidate.blend', '--python', f'{W}/closeup_f.py', '--', cand, od] + specs
r = subprocess.run(cmd, capture_output=True, text=True, env=env)
if 'CLOSEUP_DONE' not in r.stdout: print(r.stdout[-2000:], r.stderr[-2000:]); sys.exit(1)
multi = Image.open(B + 'female_multiangle_body.jpg').convert('RGB')
def fnt(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
tiles = []
for nm, (x0, x1), anchor, flip in (('pL', (750, 850), 791.5, False), ('pR', (1054, 1154), 1095.5, True)):
    y0, y1 = 95, 250
    plate = multi.crop((x0, y0, x1, y1)).resize(((x1 - x0) * K, (y1 - y0) * K), Image.LANCZOS)
    mdl = Image.open(f'{od}/{nm}.png').convert('RGB')
    # square render of 155 px vertical extent -> central 100 px wide part
    cw = (x1 - x0) * K; off = (mdl.width - cw) // 2
    mdl = mdl.crop((off, 0, off + cw, mdl.height))
    # hand ROI box in plate px
    hx0, hx1, hy0, hy1 = (x0 + 18, x0 + 82, 165, 240)
    box = ((hx0 - x0) * K, (hy0 - y0) * K, (hx1 - x0) * K, (hy1 - y0) * K)
    p = plate.crop(box); m = mdl.crop(box)
    ov = Image.blend(p, m, 0.5)
    Wt = p.width; Ht = p.height
    T = Image.new('RGB', (Wt * 3 + 12, Ht), (20, 20, 24)); T.paste(p, (0, 0)); T.paste(m, (Wt + 6, 0)); T.paste(ov, (2 * Wt + 12, 0))
    d = ImageDraw.Draw(T)
    for panel in range(3):
        ox = panel * (Wt + 6)
        for ycm in range(-10, 11):
            px = anchor + (-ycm if flip else ycm) / 100 / S2
            xp = (px - hx0) * K
            if 0 <= xp < Wt:
                d.line([(ox + xp, 0), (ox + xp, Ht)], fill=(255, 0, 0) if ycm == 0 else (255, 170, 0), width=1)
                if panel == 0: d.text((ox + xp + 2, 2), f'{ycm}', fill=(255, 90, 60), font=fnt(14))
        for zm in (0.70, 0.75, 0.80, 0.85, 0.90):
            yp = (338.5 - zm / S2 - hy0) * K
            if 0 <= yp < Ht:
                d.line([(ox, yp), (ox + Wt, yp)], fill=(0, 170, 255), width=1)
                if panel == 0: d.text((ox + 2, yp - 15), f'z{zm:.2f}', fill=(0, 190, 255), font=fnt(14))
    d.text((6, Ht - 22), ('left profile (+x hand)' if nm == 'pL' else 'right profile (-x hand)') + f'  plate | {tag} | overlay', fill=(255, 255, 0), font=fnt(16))
    tiles.append(T)
S = Image.new('RGB', (tiles[0].width, tiles[0].height + tiles[1].height + 6), (20, 20, 24)); S.paste(tiles[0], (0, 0)); S.paste(tiles[1], (0, tiles[0].height + 6))
S.save(outp); print(outp, S.size)
