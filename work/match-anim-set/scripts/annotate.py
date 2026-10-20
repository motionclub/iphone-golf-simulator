"""Annotate the review frames (system python + Pillow):  python3 annotate.py <male|female>
proof/_frames/<hero>/<clip>_<nnn>.png -> proof/_frames_annotated/<hero>/<nnnn>.png in play order (clip name, time, contact / left-release markers)."""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, '..'))
tag = sys.argv[1]
label = tag.capitalize()
CLIPS = ['ReadyIdle', 'SplitToForehand', 'SplitToBackhand', 'RecoverCenter', 'Forehand', 'ForehandOpen', 'ForehandWide', 'ForehandShort',
         'Backhand', 'BackhandWide', 'SliceApproach', 'Serve', 'Return', 'VolleyForehand', 'VolleyBackhand', 'Overhead']
meta = json.load(open(f'{WORK}/data/bake_{tag}.json'))['clips']
try:
    font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 17)
    font_s = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 13)
except Exception:
    font = font_s = ImageFont.load_default()
src_dir = f'{WORK}/proof/_frames/{tag}'
dst_dir = f'{WORK}/proof/_frames_annotated/{tag}'
os.makedirs(dst_dir, exist_ok=True)
n = 0
for clip in CLIPS:
    c = meta[clip]
    nF = c['frames']
    for fr in range(nF):
        im = Image.open(f'{src_dir}/{clip}_{fr:03d}.png').convert('RGB')
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, im.size[0], 30], fill=(20, 22, 26))
        d.text((8, 7), f'{label}  {clip}   {fr / 30.0:4.2f}s / {(nF - 1) / 30.0:4.2f}s   frame {fr}', fill=(235, 235, 235), font=font_s)
        if c['contact_s'] is not None and abs(fr / 30.0 - c['contact_s']) < 1e-6:
            d.rectangle([0, im.size[1] - 34, im.size[0], im.size[1]], fill=(150, 40, 30))
            d.text((10, im.size[1] - 28), f'CONTACT  {c["contact_s"]:.3f}s' + ('   (THIN)' if c['thin'] else ''), fill=(255, 235, 200), font=font)
        ev = c.get('events', {})
        if ev.get('left_release_s') is not None and abs(fr / 30.0 - ev['left_release_s']) < 1e-6:
            d.rectangle([0, im.size[1] - 34, im.size[0], im.size[1]], fill=(40, 90, 120))
            d.text((10, im.size[1] - 28), 'left hand lets go', fill=(230, 245, 255), font=font)
        im.save(f'{dst_dir}/{n:04d}.png')
        n += 1
print('ANNOTATED', tag, n)
