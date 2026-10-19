"""Labelled proof sheets from the Play-mode proof (proof/shots.json + proof/trace.csv + proof/raw): SERVE (toss, hip coil, jump, contact, landing), WALK (a few steps), RUN (both feet off the court), both sexes.
python3 scripts/make_proof_sheets.py     ->  proof/PROOF_<serve|walk|run>_<male|female>.jpg"""
import csv
import json
import os
from PIL import Image, ImageDraw, ImageFont

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/feet'
P = W + '/proof'
shots = json.load(open(P + '/shots.json'))['shots']
rows = list(csv.DictReader(open(P + '/trace.csv')))
tr = {(r['scenario'], int(r['fc'])): r for r in rows if r['role'] == 'PLAYER'}
try:
    font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 13)
    big = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 16)
except Exception:
    font = big = ImageFont.load_default()
SCEN = {'male': 'vs_Nadia', 'female': 'vs_Viktor'}


def sheet(path, cells, cols, cell, title):
    """cells = [(file, [label lines], highlight)]"""
    rws = (len(cells) + cols - 1) // cols
    lh = 15 * max(len(c[1]) for c in cells) + 6
    S = Image.new('RGB', (cols * cell, 28 + rws * (cell + lh)), (22, 22, 26))
    d = ImageDraw.Draw(S)
    d.text((8, 5), title, fill=(255, 255, 255), font=big)
    for i, (f, lab, hl) in enumerate(cells):
        im = Image.open(P + '/' + f).convert('RGB'); im.thumbnail((cell, cell))
        x, y = (i % cols) * cell, 28 + (i // cols) * (cell + lh)
        S.paste(im, (x, y))
        for k, t in enumerate(lab):
            d.text((x + 4, y + cell + 3 + 15 * k), t, fill=(255, 220, 120) if not (hl and k == 0) else (120, 255, 150), font=font)
    S.save(path, quality=88); print('saved', path, S.size)


def heights(s):
    r = tr.get((s['scenario'], s['frame']))
    if not r or r['footL_mm'] == '':
        return None
    return float(r['footL_mm']), float(r['footR_mm'])


for sex, sc in SCEN.items():
    # ---------------------------------------------------------------- SERVE: the first serve of the match (showcase), key clip times, behind-the-server and high views
    back = [s for s in shots if s['scenario'] == sc and s['kind'] == 'serve']
    high = {s['frame']: s for s in shots if s['scenario'] == sc and s['kind'] == 'serve_high'}
    # the first rising sequence of clip times that starts near the stance
    i0 = next(i for i, s in enumerate(back) if 0.15 <= s['clipTime'] <= 0.3)
    seq = [back[i0]]
    for s in back[i0 + 1:]:
        if s['clipTime'] + 0.05 < seq[-1]['clipTime']:
            break
        seq.append(s)
    targets = [(0.25, 'stance, ball in the fist'), (0.70, 'ball released (toss)'), (1.00, 'toss rising, knees bend'), (1.33, 'trophy'), (1.50, 'deepest bend, hips coiled'), (1.60, 'push-off'), (1.70, 'CONTACT'), (1.90, 'landing'), (2.10, 'right leg through')]
    cells = []
    for tt, name in targets:
        s = min(seq, key=lambda x: abs(x['clipTime'] - tt))
        h = high.get(s['frame'])
        lab = [f'{name}', f'clip t={s["clipTime"]:.2f}s  hips yaw {s["hipsYaw"]:+.0f} deg  chest {s["chestYaw"]:+.0f}']
        cells.append((s['file'], lab, True))
        if h:
            cells.append((h['file'], ['(same frame, high view)', f'clip t={h["clipTime"]:.2f}s'], False))
    sheet(f'{P}/PROOF_serve_{sex}.jpg', cells, 6, 330, f'SERVE ({sex} player vs {"Nadia" if sex == "male" else "Viktor"}): Play mode, game camera moved behind / above the server. hips yaw = Hips bone about the vertical, + = turned to the hero right')
    # ---------------------------------------------------------------- WALK: the serve walk-in, side-on close-ups 0.1 s apart
    walk = [s for s in shots if s['scenario'] == sc and s['kind'] == 'walk']
    pick = walk[3:15]
    cells = []
    for s in pick:
        h = heights(s)
        cells.append((s['file'], [f'frame {s["frame"]}   {s["note"].split("|")[-1].strip()[:44]}', f'foot L {h[0]:5.0f} mm   R {h[1]:5.0f} mm' if h else 'foot heights n/a'], False))
    sheet(f'{P}/PROOF_walk_{sex}.jpg', cells, 6, 330, f'WALK ({sex}): the serve walk-in, side-on, 0.1 s apart; foot height = lowest vertex above the READY floor')
    # ---------------------------------------------------------------- RUN: the close-up window with the most frames where both feet are off the court
    runs = [s for s in shots if s['scenario'] == sc and s['kind'] == 'run' and s['role'] == 'PLAYER']
    wins, cur = [], []
    for s in runs:
        if cur and s['frame'] - cur[-1]['frame'] == 2:
            cur.append(s)
        else:
            if cur:
                wins.append(cur)
            cur = [s]
    if cur:
        wins.append(cur)

    def both_off(s):
        h = heights(s)
        return bool(h and h[0] >= 15 and h[1] >= 15)
    best = max(wins, key=lambda w: sum(both_off(s) for s in w))
    cells = []
    for s in best:
        h = heights(s)
        tag = 'BOTH FEET OFF THE COURT' if both_off(s) else ('left foot planted' if h and h[0] < 10 else ('right foot planted' if h and h[1] < 10 else ''))
        cells.append((s['file'], [tag or '-', f'foot L {h[0]:5.0f} mm   R {h[1]:5.0f} mm' if h else 'n/a', s['note'].split('|')[-1].strip()[:44]], both_off(s)))
    sheet(f'{P}/PROOF_run_{sex}.jpg', cells, 4, 400, f'RUN ({sex}): side-on, 2 frames (1/30 s) apart, the game camera moved to the hero')
