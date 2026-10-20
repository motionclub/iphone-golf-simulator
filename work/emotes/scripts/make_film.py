"""Encode the Unity film frames into work/emotes/film/<Name>_<male|female>.mp4 (the in-game clip: the hero filmed by two cameras placed in the game scene, front | side, 30 fps) and <Name>_<sex>_gamecam.mp4 (the game's own camera + HUD), plus a contact sheet in proof/.
  python3 make_film.py <frames_male_dir> <frames_female_dir>"""
import glob, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/emotes'
enc = W + '/scripts/enc'
NAMES = ['Emote_Scuba', 'Emote_Thrust', 'Emote_Spike', 'Intro_Wave', 'Intro_BringIt', 'Intro_Pushups']
dirs = dict(male=sys.argv[1], female=sys.argv[2])
os.makedirs(W + '/film', exist_ok=True); os.makedirs(W + '/proof', exist_ok=True)
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 13)
for sex, d in dirs.items():
    for n in NAMES:
        g = sorted(glob.glob(f'{d}/{n}/game_*.png'))
        subprocess.run([enc, f'{W}/film/{n}_{sex}_gamecam.mp4', '30', '1280', '720'] + g, check=True, stdout=subprocess.DEVNULL)
        fr = sorted(glob.glob(f'{d}/{n}/front_*.png')); sd = sorted(glob.glob(f'{d}/{n}/side_*.png'))
        tmp = f'{d}/{n}/_views'; os.makedirs(tmp, exist_ok=True)
        files = []
        for i, (a, b) in enumerate(zip(fr, sd)):
            im = Image.new('RGB', (1440, 720)); im.paste(Image.open(a).convert('RGB'), (0, 0)); im.paste(Image.open(b).convert('RGB'), (720, 0))
            p = f'{tmp}/v_{i:04d}.png'; im.save(p); files.append(p)
        subprocess.run([enc, f'{W}/film/{n}_{sex}.mp4', '30', '1440', '720'] + files, check=True, stdout=subprocess.DEVNULL)
        pick = fr[::max(1, len(fr) // 12)][:12]
        cw, ch = 240, 240
        S = Image.new('RGB', (6 * cw, 2 * (ch + 16)), (20, 20, 24)); dr = ImageDraw.Draw(S)
        for j, f in enumerate(pick):
            x, y = (j % 6) * cw, (j // 6) * (ch + 16)
            S.paste(Image.open(f).convert('RGB').resize((cw, ch)), (x, y + 16)); dr.text((x + 3, y + 1), f'{n} {sex} f{j}', fill=(255, 220, 120), font=font)
        S.save(f'{W}/proof/{n}_{sex}_sheet.jpg', quality=85)
        print('film', n, sex, len(g), 'frames')
