"""python3 plate_cmp.py <tag|base> [out.png]  : plate | model | overlay at the bald front/back cameras for both hands (and the multi sheet front/back)"""
import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-hands-fingers'
B = W + '/../../ArtDir/hero/base_lock/'
S = 0.0025954198473282443
tag = sys.argv[1]; outp = sys.argv[2] if len(sys.argv) > 2 else f'{W}/proof/it/{tag}/plate_cmp.png'
cand = 'base' if tag == 'base' else f'{W}/data/cand_{tag}.npz'
od = f'{W}/proof/it/{tag}/pl'; os.makedirs(od, exist_ok=True)
K = 8
ROIS = [('front_p', 'bald', (500, 338, 560, 424), (0, -1, 0)), ('front_m', 'bald', (320, 338, 380, 424), (0, -1, 0)),
        ('back_p', 'bald', (730, 338, 790, 424), (0, 1, 0)), ('back_m', 'bald', (910, 338, 970, 424), (0, 1, 0))]
specs = []
for nm, src, box, d in ROIS:
    cxp = 0.5 * (box[0] + box[2]); cyp = 0.5 * (box[1] + box[3])
    if d[1] < 0: x = (cxp - 440) * S
    else: x = (847 - cxp) * S
    z = (679 - cyp) * S
    specs.append(f'{nm}:{x:.5f},0,{z:.5f}:{d[0]},{d[1]},{d[2]}:{(box[3]-box[1])*S:.5f}')
env = dict(os.environ, RES=str((box[3] - box[1]) * K), ISO='0', AO='0')
cmd = ['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', f'{W}/start/start_arms_candidate.blend', '--python', f'{W}/closeup_f.py', '--', cand, od] + specs
r = subprocess.run(cmd, capture_output=True, text=True, env=env)
if 'CLOSEUP_DONE' not in r.stdout: print(r.stdout[-2000:], r.stderr[-2000:]); sys.exit(1)
bald = Image.open(B + 'female_body_bald.jpg').convert('RGB')
def fnt(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
tiles = []
for nm, src, box, d in ROIS:
    plate = bald.crop(box).resize(((box[2] - box[0]) * K, (box[3] - box[1]) * K), Image.LANCZOS)
    mdl = Image.open(f'{od}/{nm}.png').convert('RGB'); cw = (box[2] - box[0]) * K; off = (mdl.width - cw) // 2
    mdl = mdl.crop((off, 0, off + cw, mdl.height))
    pa = np.array(plate).astype(float); ma = np.array(mdl).astype(float)
    # outline of the model silhouette (background colour = world) over the plate
    bgc = ma[2, 2]; sil = (np.abs(ma - bgc).sum(2) > 18)
    edge = sil ^ np.roll(sil, 2, 0) | sil ^ np.roll(sil, 2, 1)
    ov = pa.copy(); ov[edge] = (255, 40, 40)
    T = Image.new('RGB', (cw * 3 + 12, plate.height), (20, 20, 24)); T.paste(plate, (0, 0)); T.paste(mdl, (cw + 6, 0)); T.paste(Image.fromarray(ov.astype(np.uint8)), (2 * cw + 12, 0))
    ImageDraw.Draw(T).text((6, 4), f'{nm} plate | {tag} | outline', fill=(255, 255, 0), font=fnt(16)); tiles.append(T)
Wt = max(t.width for t in tiles); Ht = sum(t.height + 6 for t in tiles)
# 2 columns
cols = 2; rows = 2
S_ = Image.new('RGB', (cols * (Wt + 6), rows * (tiles[0].height + 6)), (20, 20, 24))
for i, t in enumerate(tiles): S_.paste(t, ((i % cols) * (Wt + 6), (i // cols) * (t.height + 6)))
S_.save(outp); print(outp, S_.size)
