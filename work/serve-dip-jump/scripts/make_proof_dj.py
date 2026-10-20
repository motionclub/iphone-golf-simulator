"""make_proof_dj.py <male|female> : in-game clip from the ball in the hand through the landing, from the Unity film frames (film_<sex>/).
  film/serve_dip_jump_<sex>.mp4          game camera + HUD, 30 fps, from 0.5 s before the wind-up (ball in the hand) to the end of the capture (serve landing + follow-through)
  film/serve_dip_jump_<sex>_views.mp4    back | side camera, same frames
  proof/<sex>_game_sheet.jpg             every 4th film frame of the same span (game camera)"""
import csv, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-dip-jump'
sys.path.insert(0, W + '/scripts')
from read_trace import load
sex = sys.argv[1]
d = f'{W}/film_{sex}'
rows = load(d + '/trace.csv')
m, n = {}, 0
for i, r in enumerate(rows):
    if i % 2 == 0 and (r['flow'] in ('PlayerServeHold', 'PlayerServeToss') or r['state'].startswith('Serve')):
        m[i] = n; n += 1
i_w = next(i for i, r in enumerate(rows) if r['prep'] > 0.0005 and r['flow'] != 'Rally')
i_rel = next(i for i, r in enumerate(rows) if r['flow'] == 'PlayerServeToss')
i_sw = next(i for i, r in enumerate(rows) if r['sw'] == 'True')
r0 = max(0, i_w - 30); r1 = max(m)
sel = [i for i in range(r0 - (r0 % 2), r1 + 1, 2) if i in m]
print('film rows', r0, '->', r1, 'wind-up at', i_w, 'release at', i_rel, 'swing at', i_sw, 'frames', len(sel))
f = lambda v, k: f'{d}/{v}_{m[k]:05d}.png'
enc = W + '/scripts/enc'
os.makedirs(W + '/film', exist_ok=True); os.makedirs(W + '/proof', exist_ok=True)
subprocess.run([enc, f'{W}/film/serve_dip_jump_{sex}.mp4', '30', '1280', '720'] + [f('game', k) for k in sel], check=True)
tmp = f'{W}/proof/tmp_{sex}'; os.makedirs(tmp, exist_ok=True)
files = []
for j, k in enumerate(sel):
    im = Image.new('RGB', (1440, 720), (20, 20, 24)); im.paste(Image.open(f('back', k)).convert('RGB'), (0, 0)); im.paste(Image.open(f('side', k)).convert('RGB'), (720, 0))
    p = f'{tmp}/v_{j:04d}.png'; im.save(p); files.append(p)
subprocess.run([enc, f'{W}/film/serve_dip_jump_{sex}_views.mp4', '30', '1440', '720'] + files, check=True)
# sheet
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 14)
pick = sel[::2]
cols = 8; cw, ch = 320, 180
S = Image.new('RGB', (cols * cw, ((len(pick) + cols - 1) // cols) * (ch + 18)), (20, 20, 24)); dr = ImageDraw.Draw(S)
for j, k in enumerate(pick):
    im = Image.open(f('game', k)).convert('RGB').resize((cw, ch)); x, y = (j % cols) * cw, (j // cols) * (ch + 18)
    S.paste(im, (x, y)); dr.text((x + 3, y + ch + 1), f'row{k} clip {rows[k]["clip"]:.2f} t{rows[k]["t"]:.2f}', fill=(255, 220, 120), font=font)
S.save(f'{W}/proof/{sex}_game_sheet.jpg', quality=85); print('sheet', S.size)
