"""make_proof.py : contact sheets + mp4 clips from the in-game films (film_before2_<sex>, film_after_<sex>).
  proof/<sex>_sheet_back.jpg   BEFORE (top) and AFTER (bottom), the back view, every 2nd film frame from the first wind-up frame; the ball-at-head frame (T_H) is outlined
  proof/<sex>_sheet_game.jpg   AFTER, the game camera (HUD on), same frames
  film/serve_toss_<sex>.mp4            AFTER, game camera, from 0.5 s before the wind-up (ball in the hand) to 1.5 s after the release (30 fps)
  film/serve_toss_<sex>_compare.mp4    BEFORE | AFTER, back view, aligned on the first wind-up frame
python3 scripts/make_proof.py"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/serve'
sys.path.insert(0, W + '/scripts')
from read_trace import load
os.makedirs(W + '/proof', exist_ok=True); os.makedirs(W + '/film', exist_ok=True); os.makedirs(W + '/proof/tmp', exist_ok=True)
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 15); big = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 20)
def info(d):
    rows = load(d + '/trace.csv')
    i_w = next(i for i, r in enumerate(rows) if r['prep'] > 0.0005 and r['flow'] != 'Rally')
    i_rel = next(i for i, r in enumerate(rows) if r['flow'] == 'PlayerServeToss')
    i_h = next(i for i in range(i_w, i_rel + 60) if rows[i]['ball'][1] >= rows[i]['head'][1])
    return rows, i_w, i_rel, i_h
def flexL(r):
    u, v = np.array(r['Ls']) - np.array(r['Lel']), np.array(r['Lh']) - np.array(r['Lel'])
    return 180 - np.degrees(np.arccos(np.clip(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))
_maps = {}
def _map(d):
    # ServeTossFilm saves an image on every 2nd frame while the hero is serving: image n = the n-th such row (checked against the file counts)
    if d not in _maps:
        rows = load(d + '/trace.csv'); m = {}; n = 0
        for i, r in enumerate(rows):
            if i % 2 == 0 and (r['flow'] in ('PlayerServeHold', 'PlayerServeToss') or r['state'].startswith('Serve')):
                m[i] = n; n += 1
        _maps[d] = m
    return _maps[d]
def img(d, view, row):
    m = _map(d)
    if row % 2: row -= 1
    while row not in m and row > 0: row -= 2
    return d + f'/{view}_{m[row]:05d}.png'
for sex in ('male', 'female'):
    B = info(f'{W}/film_before2_{sex}'); A = info(f'{W}/film_after_{sex}')
    # ---- sheets
    steps = list(range(0, 60, 4))                # 0 .. 0.93 s after the first wind-up frame, every 4 rows = 1/15 s
    cell = 230
    def sheet(view, which, path, title):
        sets = []
        for lab, (rows, i_w, i_rel, i_h), d in which:
            sets.append((lab, rows, i_w, i_h, d))
        cols = 10; rws = (len(steps) + cols - 1) // cols
        S = Image.new('RGB', (cols * cell, 30 + len(sets) * rws * (cell + 36)), (24, 24, 28)); dr = ImageDraw.Draw(S); dr.text((8, 5), title, fill=(255, 255, 255), font=big)
        for si, (lab, rows, i_w, i_h, d) in enumerate(sets):
            for k, s in enumerate(steps):
                row = i_w + s; r = rows[row]
                im = Image.open(img(d, view, row)).convert('RGB')
                if view == 'game':
                    cx, cy = 700, 330
                    # follow the server: crop around the head on the game camera is not available; use a fixed crop of the court centre-right
                    im = im.crop((560, 120, 1000, 640))
                im = im.resize((cell, cell))
                x, y = (k % cols) * cell, 30 + si * rws * (cell + 36) + (k // cols) * (cell + 36)
                S.paste(im, (x, y))
                if row >= i_h and row - 4 < i_h: dr.rectangle((x, y, x + cell - 1, y + cell - 1), outline=(80, 255, 120), width=4)
                dr.text((x + 4, y + cell + 2), f'{lab} +{s / 60:.2f}s', fill=(255, 220, 120), font=font)
                dr.text((x + 4, y + cell + 18), f'flex {flexL(r):3.0f} bh {r["ball"][1] - r["head"][1]:+.2f}', fill=(200, 230, 255), font=font)
        S.save(path, quality=88); print('saved', path, S.size)
    sheet('back', [('BEFORE', B, f'{W}/film_before2_{sex}'), ('AFTER', A, f'{W}/film_after_{sex}')], f'{W}/proof/{sex}_sheet_back.jpg',
          f'{sex.upper()} serve toss, back view, every 1/15 s from the first wind-up frame; green outline = the ball reaches head height; flex = left elbow deg, bh = ball minus head height m; BEFORE above, AFTER below')
    sheet('side', [('BEFORE', B, f'{W}/film_before2_{sex}'), ('AFTER', A, f'{W}/film_after_{sex}')], f'{W}/proof/{sex}_sheet_side.jpg',
          f'{sex.upper()} serve toss, side view, every 1/15 s from the first wind-up frame: BEFORE above, AFTER below')
    # ---- mp4: after, game camera
    rows, i_w, i_rel, i_h = A; d = f'{W}/film_after_{sex}'
    r0 = max(0, i_w - 30); r1 = min(len(rows) - 1, i_rel + 90)
    files = [img(d, 'game', r) for r in range(r0 - (r0 % 2), r1, 2)]
    subprocess.run([W + '/scripts/enc', f'{W}/film/serve_toss_{sex}.mp4', '30', '1280', '720'] + files, check=True)
    # ---- mp4: before | after, back view, aligned on the first wind-up frame
    rb, ibw, ibr, ibh = B
    out = []
    for n, k in enumerate(range(-30, 150, 2)):
        ra, rbb = i_w + k, ibw + k
        if ra >= len(rows) or rbb >= len(rb) or ra < 0 or rbb < 0: continue
        im = Image.new('RGB', (1440, 760), (20, 20, 24)); dr = ImageDraw.Draw(im)
        for j, (lab, dd, rr, rowsx) in enumerate((('BEFORE', f'{W}/film_before2_{sex}', rbb, rb), ('AFTER', f'{W}/film_after_{sex}', ra, rows))):
            im.paste(Image.open(img(dd, 'back', rr)).convert('RGB'), (j * 720, 40))
            r = rowsx[rr - (rr % 2)]
            dr.text((j * 720 + 10, 8), f'{lab}  t {(k) / 60:+.2f}s  ball-head {r["ball"][1] - r["head"][1]:+.2f}m  L-elbow {flexL(r):3.0f}deg', fill=(255, 255, 255), font=font)
        p = f'{W}/proof/tmp/{sex}_cmp_{n:04d}.png'; im.save(p); out.append(p)
    subprocess.run([W + '/scripts/enc', f'{W}/film/serve_toss_{sex}_compare.mp4', '30', '1440', '760'] + out, check=True)
