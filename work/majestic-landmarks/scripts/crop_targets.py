"""Cut the target crop each asset serves out of the hole refs (system python3 + PIL).
python3 crop_targets.py [preview.jpg]"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
REFS = HERE.parents[1] / 'majestic-all-maps/refs/holes'
OUT = HERE.parent / 'targets'; OUT.mkdir(exist_ok=True)
T = json.loads((HERE / 'targets.json').read_text())
tiles = []
for name, (ref, (x0, y0, x1, y1)) in T.items():
    im = Image.open(REFS / f'{ref}.jpg').convert('RGB')
    W, H = im.size
    c = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
    c.save(OUT / f'{name}.jpg', quality=92)
    t = c.copy(); t.thumbnail((320, 240)); bg = Image.new('RGB', (320, 260), 'black'); bg.paste(t, (0, 20))
    ImageDraw.Draw(bg).text((4, 4), f'{name} <- {ref}', fill='white'); tiles.append(bg)
if len(sys.argv) > 1:
    cols = 7; rows = (len(tiles) + cols - 1) // cols
    s = Image.new('RGB', (320 * cols, 260 * rows))
    for k, t in enumerate(tiles): s.paste(t, ((k % cols) * 320, (k // cols) * 260))
    s.save(sys.argv[1], quality=85)
