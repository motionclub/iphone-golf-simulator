"""python3 proof_side.py <after_tag> <out.png> [before_tag=base]  -> side placement BA vs the plate profiles (hand region, 1 cm grid, z lines)"""
import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-hands-fingers'
B = W + '/../../ArtDir/hero/base_lock/'
S2 = 1.7039 / 288.5; K = 8
after = sys.argv[1]; outp = sys.argv[2]; before = sys.argv[3] if len(sys.argv) > 3 else 'base'
ANCH = {'pL': 791.5, 'pR': 1093.0}
yc_L = (800 - 791.5) * S2; zc = (338.5 - 172.5) * S2; yc_R = -((1104 - ANCH['pR']) * S2)
specs = [f'pL:0,{yc_L:.5f},{zc:.5f}:1,0,0:{155*S2:.5f}', f'pR:0,{yc_R:.5f},{zc:.5f}:-1,0,0:{155*S2:.5f}']
def render(tag):
    cand = 'base' if tag == 'base' else f'{W}/data/cand_{tag}.npz'
    od = f'{W}/proof/it/{tag}/prof'; os.makedirs(od, exist_ok=True)
    r = subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', f'{W}/start/start_arms_candidate.blend', '--python', f'{W}/closeup_f.py', '--', cand, od] + specs,
                       capture_output=True, text=True, env=dict(os.environ, RES=str(155 * K), ISO='0', AO='0'))
    if 'CLOSEUP_DONE' not in r.stdout: print(r.stdout[-1500:], r.stderr[-1500:]); sys.exit(1)
    return od
odb, oda = render(before), render(after)
multi = Image.open(B + 'female_multiangle_body.jpg').convert('RGB')
def fnt(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
tiles = []
for nm, (x0, x1), flip in (('pL', (750, 850), False), ('pR', (1054, 1154), True)):
    anchor = ANCH[nm]; y0, y1 = 95, 250
    plate = multi.crop((x0, y0, x1, y1)).resize(((x1 - x0) * K, (y1 - y0) * K), Image.LANCZOS)
    def mdl(od):
        m = Image.open(f'{od}/{nm}.png').convert('RGB'); cw = (x1 - x0) * K; off = (m.width - cw) // 2
        return m.crop((off, 0, off + cw, m.height))
    mb, ma = mdl(odb), mdl(oda)
    hx0, hx1, hy0, hy1 = (x0 + 14, x0 + 86, 168, 242)
    box = ((hx0 - x0) * K, (hy0 - y0) * K, (hx1 - x0) * K, (hy1 - y0) * K)
    crops = [plate.crop(box), mb.crop(box), ma.crop(box), Image.blend(plate.crop(box), ma.crop(box), 0.5)]
    Wt, Ht = crops[0].size
    T = Image.new('RGB', (4 * Wt + 18, Ht + 30), (20, 20, 24))
    for i, c in enumerate(crops):
        T.paste(c, (i * (Wt + 6), 30))
        d = ImageDraw.Draw(T); ox = i * (Wt + 6)
        d.text((ox + 6, 6), ['PLATE', f'BEFORE ({before})', f'AFTER ({after})', 'overlay plate+after'][i] + ('   left profile = +x hand' if nm == 'pL' else '   right profile = -x hand'), fill=(255, 230, 120), font=fnt(17))
        for ycm in range(-10, 11):
            px = anchor + (-ycm if flip else ycm) / 100 / S2; xp = (px - hx0) * K
            if 0 <= xp < Wt:
                d.line([(ox + xp, 30), (ox + xp, 30 + Ht)], fill=(255, 0, 0) if ycm == 0 else (255, 170, 0), width=1)
                if ycm % 2 == 0: d.text((ox + xp + 2, 32), f'{ycm}', fill=(255, 100, 70), font=fnt(13))
        for zm in (0.70, 0.75, 0.80, 0.85, 0.90):
            yp = (338.5 - zm / S2 - hy0) * K + 30
            if 30 <= yp < 30 + Ht:
                d.line([(ox, yp), (ox + Wt, yp)], fill=(0, 170, 255), width=1); d.text((ox + 2, yp - 14), f'z{zm:.2f}', fill=(0, 190, 255), font=fnt(13))
    tiles.append(T)
S = Image.new('RGB', (tiles[0].width, tiles[0].height * 2 + 6), (20, 20, 24)); S.paste(tiles[0], (0, 0)); S.paste(tiles[1], (0, tiles[0].height + 6))
S.save(outp); print(outp, S.size)
