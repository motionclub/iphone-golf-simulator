"""film_sheet.py <hero> <clip> <view game|front|side> <n> [cols] : tile n evenly spaced in-game film frames of work/emote-overhaul/film/<hero>/<clip> into proof/film_<hero>_<clip>_<view>.png"""
import sys, os, glob
from PIL import Image, ImageDraw
hero, clip, view, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
cols = int(sys.argv[5]) if len(sys.argv) > 5 else min(n, 6)
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/emote-overhaul'
files = sorted(glob.glob(f'{R}/film/{hero}/{clip}/{view}_*.png'))
pick = [files[int(round(i * (len(files) - 1) / (n - 1)))] for i in range(n)]
im0 = Image.open(pick[0]); w, h = im0.size
sc = (320 / w) if view == 'game' else (260 / w)
tw, th = int(w * sc), int(h * sc)
rows = (n + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, rows * th), (20, 20, 24))
for i, f in enumerate(pick):
    im = Image.open(f).convert('RGB').resize((tw, th), Image.LANCZOS)
    d = ImageDraw.Draw(im); d.text((6, 4), os.path.basename(f)[-9:-4], fill=(255, 220, 120))
    sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
out = f'{R}/proof/film_{hero}_{clip}_{view}.png'
sheet.save(out); print(out, sheet.size)
